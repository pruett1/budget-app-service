from __future__ import annotations
from src.requests.payloads import item_payload

class TransactionsAPI:
    def __init__(self, plaid: Plaid): # type: ignore (added to stop pylance error for annotation)
        self._plaid = plaid

    async def sync(self, access_token: str, cursor: str|None = None, count: int|None = 100, options: dict|None = None):
        path = "/transactions/sync"
        payload = item_payload(self._plaid.client_id, self._plaid.secret, access_token)
        payload["count"] = count

        if cursor:
            payload["cursor"] = cursor

        if options:
            payload["options"] = options

        return await self._plaid._post(path, payload)
    
    # because this is being built after Dec 2025 all personal_finance_category_versions will be v2
    # https://plaid.com/docs/api/products/transactions/#transactionsrecurringget
    async def recurring(self, access_token: str, accounts: list[str]|None = None):
        path = "/transactions/recurring/get"
        payload = item_payload(self._plaid.client_id, self._plaid.secret, access_token)
        
        if accounts:
            payload["account_ids"] = accounts

        return await self._plaid._post(path, payload)