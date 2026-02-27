from src.helpers.plaid.client import Plaid
from src.helpers.plaid.investments import InvestmentsAPI
from src.requests.payloads import item_payload

from unittest.mock import AsyncMock
import pytest


def plaid_with_mocks():
    plaid = Plaid.__new__(Plaid)
    plaid.secret = "test_secret"
    plaid.client_id = "test_client_id"

    # mock the internal _post used by sub-clients
    plaid._post = AsyncMock()

    # attach real sub-client
    plaid.investments = InvestmentsAPI(plaid)

    return plaid

# Test holdings get
@pytest.mark.asyncio
async def test_investments_holdings():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some investments holdings data"}

    data = await plaid.investments.holdings("test_access_token")

    path = "/investments/holdings/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some investments holdings data"}

@pytest.mark.asyncio
async def test_investments_holdings_with_accounts():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some investments holdings data"}

    data = await plaid.investments.holdings("test_access_token", ["acct1", "acct2"])

    path = "/investments/holdings/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["options"] = {"account_ids": ["acct1", "acct2"]}

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some investments holdings data"}

# Test transactions get
@pytest.mark.asyncio
async def test_investments_transactions():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some investments transactions"}

    data = await plaid.investments.transactions("test_access_token", "test_start", "test_end")

    path = "/investments/transactions/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["start_date"] = "test_start"
    payload["end_date"] = "test_end"

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some investments transactions"}

@pytest.mark.asyncio
async def test_investments_transactions_with_options():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some investments transactions"}

    data = await plaid.investments.transactions("test_access_token", "test_start", "test_end", options={"test_options": "test_setting"})

    path = "/investments/transactions/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["start_date"] = "test_start"
    payload["end_date"] = "test_end"
    payload["options"] = {"test_options": "test_setting"}

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some investments transactions"}
