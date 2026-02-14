import httpx
import json
from env.envs import Env
from logging import Logger

from src.requests.payloads import create_link_token_payload, exchange_public_token_payload, item_payload

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

    async def exchange_public_token(self, public_token: str) -> tuple[str, str]:
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

    async def get_item(self, access_token: str) -> dict:
        path = "/item/get"
        payload = item_payload(self.client_id, self.secret, access_token)

        try:
            response = await self.client.post(path, json=payload)
            response.raise_for_status()
            data = response.json()
            self.logger.info("Successfully got data for Plaid item")
            return data
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while getting item data: {e.response.text}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while getting item data: {str(e)}")
            raise

    async def remove_item(self, access_token: str, reason_code: str|None = None, reason_note: str|None = None) -> None:
        print("TEST TEST TEST TEST TEST")
        path = "/item/remove"
        payload = item_payload(self.client_id, self.secret, access_token)
        print("BEFORE IFS")
        if reason_code:
            payload["reason_code"] = reason_code
        if reason_note:
            payload["reason_note"] = reason_note

        print("AFTER IFS")

        try:
            response = await self.client.post(path, json=payload)
            response.raise_for_status()
            self.logger.info("Successfully removed item")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while removing item: {e.response.text}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while removing item: {str(e)}")
            raise

    async def invalidate_access_token(self, access_token: str) -> str:
        path = "/item/access_token/invalidate"
        payload = item_payload(self.client_id, self.secret, access_token)
        
        try:
            response = await self.client.post(path, json=payload)
            response.raise_for_status()
            data = response.json()
            self.logger.info("Successfully rotated access token")
            return data["new_access_token"]
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while rotating access token: {e.response.text}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while rotating access token: {str(e)}")
            raise

    async def get_liabilities(self, access_token: str, account_ids: list[str]|None = None) -> dict:
        path = "/liabilities/get"
        payload = item_payload(self.client_id, self.secret, access_token)
        if account_ids:
            payload["options"] = {"account_ids": account_ids}
        
        try:
            response = await self.client.post(path, json=payload)
            response.raise_for_status()
            data = response.json()
            self.logger.info("Successfully got liabilities data")
            return data
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error while getting liabilities data: {e}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error while getting liabilities data: {e}")
            raise

    async def close(self):
        await self.client.aclose()
    