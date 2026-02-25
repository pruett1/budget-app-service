from __future__ import annotations
from src.requests.payloads import item_payload

class LiabilitiesAPI:
    def __init__(self, plaid: Plaid): # type: ignore (added to stop pylance error for annotation)
        self._plaid = plaid

    async def get(self, access_token: str, account_ids: list[str]|None = None) -> dict:
        path = "/liabilities/get"
        payload = item_payload(self.client_id, self.secret, access_token)
        if account_ids:
            payload["options"] = {"account_ids": account_ids}
        
        return await self._plaid._post(path, payload)