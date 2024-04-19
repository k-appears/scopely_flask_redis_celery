# Instructions how to build the project

1. Install Make
2. Install Python 3.12.2. Example, first install `pyenv`, then:
    ```bash
    pyenv install 3.12.2
    $(pyenv which python3.12) -m venv .venv
    ```
3. Install poetry. Example:
   ```bash
    source .venv/bin/activate
    pip install --upgrade pip
    pip install poetry
    poetry install  --no-root
    ```
4. Install docker and docker-compose



## Assumptions

Scores in leaderboard are the number of resources stolen


## How to run the project
```bash
  docker compose up
  make run
```
docker run --name redis-stack -p 6379:6379 -p 8001:8001 -e  redis/redis-stack:latest


## Scopely Backend Development
The main reason for this task is to measure proficiency in programming and ability to learn new
technologies under time pressure. You don’t have to complete all the requirements. You can move on to
the next part, that requires a slightly different skill set, at any time. It’s important that you present your
strongest side in this limited time.


Using language and a framework of your choice implement the backend service for registering
players, providing leaderboards and accepting battle requests. Then implement an engine (worker /
job / script etc) for processing submitted battles.
It is recommended to use Redis as your main database.
1. Model the following in the primary database 
   1. Player - should consist of at least the following
      1. Identifier
      2. Name (max length 20 characters, unique)
      3. Description (max length is 1k characters)
      4. Amount of gold (max value 1 bln)
      5. Amount of silver (max value 1 bln)
      6. Attack value, Hit points and luck value

2. Implement the web application with the following endpoints / handlers
   1. Create player
      1. Validate and store details in database
   2. Submit battle - opponents
      1. Put the battle request into battle processor queue
   3. Retrieve leaderboard
      1. Retrieve list of all the players on the leaderboard, each entry consisting of rank/position, score and player identifier

3. Implement the battle processor
   1. Players will submit battles, specifying who they want to attack. Those submissions should be
   processed by a battle processor that needs to meet the following requirements
      1. Battles must happen in the order that they were submitted
      2. Each battle should only be executed once
      3. No battles should be missed
      4. Battles should be processed as soon as possible, but there is no hard requirement
   2. Processor should implement at least the following steps for each battle in the queue
      1. Process the battle - see sections 2 below
      2. Battle should be logged
      3. Resource should be subtracted from losing player
      4. Resource should be added to winning player
      5. The total amount of resources stolen should be submitted to the leaderboard

### Backend extension for Game Server Development
1. Implement the battle engine
   1. The battle
      1. The battle system is turn based, with whoever submitted the battle going first
      2. With each attack, the attacker must calculate the damage it can do. The attack value is
      proportional to the players hit points. The lower the hit points - the lower the attack, with a
      cap at 50% of the base attack value.
         1. For example: with the loss of 1% of health, reduce attack by 1% rounded up,
   so starting health 100, attack 70, every time 10 damage is taken, the attack
   value is reduced by 7. In this scenario, the attack can never be reduced below
   35 which is 50% of the base attack value.

      3. The attacker then becomes the defender, and the defender the attacker.
      4. Use the luck value of the defender to decide if an attack misses.
      5. The battle continues until one of the players hit points value reaches zero.
      
   2. Resources stolen should be between 10% and 20% of their total amount of resources,
   evenly distributed across their resources
   3. A battle report should be generated - which contains a detailed log of everything that
   happened during the battle.
   4. Implement concurrent execution of non-conflicting battles
2. All endpoints should be protected against public/unauthorised access in some way.