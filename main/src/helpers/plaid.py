import httpx
import json
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
        
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
        
    async def create_link_token(self, user_id: str) -> str:
        path = "/link/token/create"
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            "client_name": "pruett1-budget-app",
            "user": {
                "client_user_id": user_id
            },
            "products": ["transactions", "recurring_transactions", "investments", "liabilities"],
            "country_codes": ["US"],
            "language": "en"
        }
        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = await self.client.post(path, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Successfully created link token expiring at {data['expiration']}")
            return data['link_token']
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while creating link token: {e.response.text}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while creating link token: {str(e)}")
            raise

    async def exchange_public_token(self, public_token: str):
        path = "/item/public_token/exchange"
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            "public_token": public_token
        }
        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = await self.client.post(path, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.logger.info("Successfully exchanged public token for access token and item id")
            return data['access_token'], data['item_id']
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while exchanging public token: {e.response.text}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while exchanging public token: {str(e)}")
            raise

    