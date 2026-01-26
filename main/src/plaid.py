import requests
from main.env.envs import Env
from logging import Logger

class Plaid:
    def __init__(self, env: str, logger: Logger):
        self.logger = logger

        config = Env(env)['plaid']
        self.client_id = config['CLIENT_ID']
        self.secret = config['SECRET']
        self.base_url = ""

        if env == "sandbox":
            self.base_url = "https://sandbox.plaid.com"
        elif env == "prod":
            self.base_url = "https://production.plaid.com"
        else:
            raise ValueError("Invalid env specified")
        
    def create_link_token(self, user_id: str) -> str:
        pass