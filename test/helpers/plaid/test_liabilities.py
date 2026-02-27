from helpers.plaid.client import Plaid
from helpers.plaid.liabilities import LiabilitiesAPI
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
    plaid.liabilities = LiabilitiesAPI(plaid)

    return plaid

# Test liabilities get
@pytest.mark.asyncio
async def test_liabilities_get_positive_no_account_ids():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some liability data"}

    data = await plaid.liabilities.get("test_access_token")

    path = "/liabilities/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some liability data"}


@pytest.mark.asyncio
async def test_liabilities_get_positive_w_account_ids():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"data": "some liability data"}

    data = await plaid.liabilities.get("test_access_token", ["account1", "account2"])

    path = "/liabilities/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["options"] = {"account_ids": ["account1", "account2"]}
    plaid._post.assert_awaited_once_with(path, payload)
    assert data == {"data": "some liability data"}