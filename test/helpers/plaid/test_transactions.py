from helpers.plaid.client import Plaid
from helpers.plaid.transactions import TransactionsAPI
from src.requests.payloads import item_payload

from unittest.mock import AsyncMock
import pytest

def plaid_with_mocks():
    plaid = Plaid.__new__(Plaid)
    plaid.secret = "test_secret"
    plaid.client_id = "test_client_id"

    # mock the internal _post used by sub-clients
    plaid._post = AsyncMock()

    # attach real sub-clients
    plaid.transactions = TransactionsAPI(plaid)

    return plaid

# Test transactions sync
@pytest.mark.asyncio
async def test_transactions_sync_no_optionals():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some transactions data"}

    data = await plaid.transactions.sync("test_access_token")
    
    path = "/transactions/sync"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["count"] = 100

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some transactions data"}

@pytest.mark.asyncio
async def test_transactions_sync_with_cursor():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some transactions data"}

    data = await plaid.transactions.sync("test_access_token", cursor="test_cursor")
    
    path = "/transactions/sync"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["count"] = 100
    payload["cursor"] = "test_cursor"

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some transactions data"}

@pytest.mark.asyncio
async def test_transactions_sync_with_count():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some transactions data"}

    data = await plaid.transactions.sync("test_access_token", count = 50)
    
    path = "/transactions/sync"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["count"] = 50

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some transactions data"}

@pytest.mark.asyncio
async def test_transactions_sync_with_options():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some transactions data"}

    test_options = {"test": "some option"}

    data = await plaid.transactions.sync("test_access_token", options=test_options)
    
    path = "/transactions/sync"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["count"] = 100
    payload["options"] = {"test": "some option"}

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some transactions data"}

# Test transactions recurring get
@pytest.mark.asyncio
async def test_transactions_recurring():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some recurring transactions"}

    data = await plaid.transactions.recurring("test_access_token")

    path = "/transactions/recurring/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some recurring transactions"}

@pytest.mark.asyncio
async def test_transactions_recurring_with_accounts():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some recurring transactions"}

    data = await plaid.transactions.recurring("test_access_token", accounts = ["acct1", "acct2"])

    path = "/transactions/recurring/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["account_ids"] = ["acct1", "acct2"]

    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some recurring transactions"}