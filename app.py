import os

import redis
from celery import Celery
from flask import request
from flask_api import FlaskAPI, status
from flask_jwt_extended import jwt_required, JWTManager
from redis_om import Migrator

from models import Battle, Leaderboard, Player
from tasks import process_battle

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')

app = FlaskAPI(__name__)
redis_db = redis.StrictRedis(host=redis_host, port=int(redis_port), db=0, decode_responses=True)
app.config['CELERY_BROKER_URL'] = f'redis://{redis_host}:{redis_port}/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

app.config['JWT_SECRET_KEY'] = 'my-secret-key'
jwt = JWTManager(app)


@jwt_required()
@app.route('/players', methods=['GET', 'POST'])
def create_player():
    if request.method == 'POST':
        data = request.json
        try:
            player = Player(**data)
            player.save()
            return {'message': 'Player created successfully'}, status.HTTP_201_CREATED
        except Exception as e:
            return {'error': str(e)}, status.HTTP_400_BAD_REQUEST
    return [], status.HTTP_200_OK


@jwt_required()
@app.route('/battles', methods=['GET', 'POST'])
def submit_battle():
    if request.method == 'POST':
        battle = Battle(**request.json)
        battle.save()
        # task = celery.send_task("process_battle", args=[request.json])
        process_battle(battle)

        # return {"message": f"Battle request submitted with task ID: {task.id}"}, status.HTTP_202_ACCEPTED
        return {"message": f"Battle request  ID: {battle.battle_id}"}, status.HTTP_202_ACCEPTED
    return [], status.HTTP_200_OK


@jwt_required()
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    NOT LIMITING THE NUMBER OF LEADERBOARD ENTRIES SHOWN

    :return:
    """

    leaderboard_entries = Leaderboard.find().sort_by("-total_resources_stolen").all()
    leaderboard = [
        {
            "rank": index,
            "score": entry.total_resources_stolen,
            "player_id": entry.player_id
        }
        for index, entry in enumerate(leaderboard_entries, start=1)
    ]
    return leaderboard, status.HTTP_200_OK


@app.route('/', methods=['GET'])
def home():
    return 'Welcome to the Battle API'

Migrator().run()

if __name__ == '__main__':
    app.run(debug=True)
