import httpx
import json
from env.envs import Env
from logging import Logger

from src.helpers.requests.payloads import create_link_token_payload, exchange_public_token_payload

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
        
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0, headers={"Content-Type": "application/json"})
        self.logger.info("Plaid client initialized with base URL: %s", self.base_url)
        
    async def create_link_token(self, user_id: str) -> str:
        path = "/link/token/create"
        payload = create_link_token_payload(self.client_id, self.secret, user_id)
        try:
            response = await self.client.post(path, json=payload)
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
        payload = exchange_public_token_payload(self.client_id, self.secret, public_token)
        try:
            response = await self.client.post(path, json=payload)
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


    async def close(self):
        await self.client.aclose()
    