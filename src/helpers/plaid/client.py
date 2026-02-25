import httpx
from env.envs import Env
from logging import Logger

from src.helpers.plaid.transactions import TransactionsAPI
from src.helpers.plaid.items import ItemsAPI
from src.helpers.plaid.liabilities import LiabilitiesAPI

from src.requests.payloads import create_link_token_payload

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

        # sub-clients
        self.items = ItemsAPI(self)
        self.transactions = TransactionsAPI(self)
        self.liabilities = LiabilitiesAPI(self)

    async def _post(self, path: str, payload: dict):
        try:
            response = await self.client.post(path, json=payload)
            response.raise_for_status()
            self.logger.info(f"Post: {path}, Status: {response.status_code()}")

            if not response.content:
                return None

            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Post to {path} resulted in HTTP error: {e.response.text}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error with post to {path}: {str(e)}")
        
    async def create_link_token(self, user_id: str) -> str:
        path = "/link/token/create"
        payload = create_link_token_payload(self.client_id, self.secret, user_id)

        data = await self._post(path, payload)

        return data['link_token']

    async def close(self):
        await self.client.aclose()
    