from pymongo import MongoClient
from env.envs import Env

class DB:
    def __init__(self, env: str):
        config = Env(env)['db']
        client = MongoClient(config['URI'])
        self._db = client[config['DB_NAME']]
        

    def get_db(self):
        return self._db

