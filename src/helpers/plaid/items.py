from __future__ import annotations
from src.requests.payloads import exchange_public_token_payload, item_payload

class ItemsAPI:
    def __init__(self, plaid: Plaid): # type: ignore (added to stop pylance error for annotation)
        self._plaid = plaid

    async def exchange_public_token(self, public_token: str) -> tuple[str, str]:
        path = "/item/public_token/exchange"
        payload = exchange_public_token_payload(self.client_id, self.secret, public_token)

        data = await self._plaid._post(path, payload)
        return data['access_token'], data['item_id']
    
    async def invalidate_access_token(self, access_token: str) -> str:
        path = "/item/access_token/invalidate"
        payload = item_payload(self.client_id, self.secret, access_token)

        data = self._plaid._post(path, payload)
        return data["new_access_token"]

    async def get(self, access_token: str) -> dict:
        path = "/item/get"
        payload = item_payload(self.client_id, self.secret, access_token)

        return await self._plaid._post(path, payload)

    async def remove(self, access_token: str, reason_code: str|None = None, reason_note: str|None = None) -> None:
        path = "/item/remove"
        payload = item_payload(self.client_id, self.secret, access_token)
        if reason_code:
            payload["reason_code"] = reason_code
        if reason_note:
            payload["reason_note"] = reason_note

        return await self._plaid._post(path, payload)