from __future__ import annotations
from src.requests.payloads import item_payload

class InvestmentsAPI:
    def __init__(self, plaid: "Plaid"): # type: ignore
        self._plaid = plaid

    async def holdings(self, access_token: str, accounts: list[str]|None = None):
        path = "/investments/holdings/get"
        payload = item_payload(self._plaid.client_id, self._plaid.secret, access_token)
        
        if accounts:
            payload["options"] = {"account_ids": accounts}

        return await self._plaid._post(path, payload)
    
    async def transactions(self, access_token: str, start_date: str, end_date: str, options: dict|None = None):
        path = "/investments/transactions/get"
        payload = item_payload(self._plaid.client_id, self._plaid.secret, access_token)
        payload["start_date"] = start_date
        payload["end_date"] = end_date

        if options:
            payload["options"] = options

        return await self._plaid._post(path, payload)