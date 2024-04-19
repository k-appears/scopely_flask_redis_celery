from random import randint

from celery.utils.log import get_task_logger
from redis_om import get_redis_connection

from models import Battle, Leaderboard, Player

logger = get_task_logger(__name__)


# @app.task
def process_battle(battle):
    """
    a. requirements
        i. Battles must happen in the order that they were submitted "Celery preserves the order of task execution based on the order of task submissions."
        ii. Each battle should only be executed once
        iii. No battles should be missed
        iv. Battles should be processed as soon as possible, but there is no hard requirement
    b. Processor should implement at least the following steps for each battle in the queue i.
        i. Process the battle
             a. The battle
                    i. The battle system is turn based, with whoever submitted the battle going first
                    ii. With each attack, the attacker must calculate the damage it can do. The attack value is proportional to the players hit points. The lower the hit points - the lower the attack, with a cap at 50% of the base attack value.
                    1. For example: with the loss of 1% of health, reduce attack by 1% rounded up, so starting health 100, attack 70, every time 10 damage is taken, the attack value is reduced by 7. In this scenario, the attack can never be reduced below
                    35 which is 50% of the base attack value.
                    iii. The attacker then becomes the defender, and the defender the attacker.
                    iv. Use the luck value of the defender to decide if an attack misses.
                    v. The battle continues until one of the players hit points value reaches zero.
            b. Resources stolen should be between 10% and 20% of their total amount of resources, evenly distributed across their resources
            c. A battle report should be generated - which contains a detailed log of everything that happened during the battle.
            d. Implement concurrent execution of non-conflicting battles
        ii. Battle should be logged
        iii. Resource should be subtracted from losing player
        iv. Resource should be added to winning player
        v. The total amount of resources stolen should be submitted to the leaderboard
    :param battle:
    :return:
    """
    logger.info(f"Processing battle: {battle}")

    redis = get_redis_connection()

    # Ensure the battle is executed only once
    # with redis.lock(f"battle:{battle.battle_id}", blocking_timeout=5):
    #     if Battle.get(battle.pk).winner_id != "":
    #         return

    # Get player data
    attacker = Player.get(battle.attacker_id)
    defender = Player.get(battle.defender_id)

    # Battle loop
    while attacker.hit_points > 0 and defender.hit_points > 0:
        # Attacker's turn
        attack_value = calculate_attack_value(attacker.attack, attacker.hit_points)
        if randint(1, 100) > defender.luck:
            defender.hit_points -= attack_value
            battle.battle_log += f"Attacker ({attacker.name}) hit Defender ({defender.name}) for {attack_value} damage.\n"
        else:
            battle.battle_log += f"Attacker ({attacker.name}) missed Defender ({defender.name}).\n"

        # Swap attacker and defender
        attacker, defender = defender, attacker

    if attacker.hit_points > 0:
        winner = attacker
        loser = defender
    else:
        winner = defender
        loser = attacker
    loser.hit_points = 0

    battle.winner_id = winner.id

    stolen_resources = steal_resources(loser)
    battle.battle_log += f"Attacker ({winner.name}) stole {stolen_resources} from Defender ({loser.name}).\n"

    add_resources(winner, stolen_resources)
    subtract_resources(loser, stolen_resources)

    battle.save()

    update_leaderboard(winner.id, sum(stolen_resources.values()))
    update_leaderboard(loser.id, -sum(stolen_resources.values()))


def calculate_attack_value(base_attack, hit_points):
    health_percentage = hit_points / 100
    attack_reduction = 1 - health_percentage
    attack_value = base_attack * (1 - min(attack_reduction, 0.5))
    return int(attack_value)


def steal_resources(player):
    total_resources = player.gold + player.silver
    steal_percentage = randint(10, 20) / 100
    steal_amount = int(total_resources * steal_percentage)

    stolen_resources = {}

    stolen_gold = min(steal_amount, player.gold)
    stolen_resources["gold"] = stolen_gold

    stolen_silver = min(steal_amount, player.silver)
    stolen_resources["silver"] = stolen_silver

    return stolen_resources


def add_resources(player, stolen_resources):
    for resource, amount in stolen_resources.items():
        if resource == "gold":
            player.gold += amount
        elif resource == "silver":
            player.silver += amount

    player.save()

def subtract_resources(player, stolen_resources):
    for resource, amount in stolen_resources.items():
        if resource == "gold":
            player.gold = max(0, player.gold - amount)
        elif resource == "silver":
            player.silver = max(0, player.silver - amount)

    player.save()


def update_leaderboard(player_id, total_resources_stolen):
    """
    Update the leaderboard with the given player's total resources stolen.
    """
    entries = Leaderboard.find(Leaderboard.player_id == player_id).all()

    if len(entries) == 1:
        # Update the existing entry
        entries[0].total_resources_stolen += total_resources_stolen
        entries[0].save()
    else:
        # Create a new entry
        new_entry = Leaderboard(
            player_id=player_id,
            total_resources_stolen=total_resources_stolen,
        )
        new_entry.save()

