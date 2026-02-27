from src.helpers.plaid.client import Plaid
from src.helpers.plaid.items import ItemsAPI
from src.requests.payloads import exchange_public_token_payload, item_payload

from unittest.mock import AsyncMock
import pytest


def plaid_with_mocks():
    plaid = Plaid.__new__(Plaid)
    plaid.secret = "test_secret"
    plaid.client_id = "test_client_id"

    # mock the internal _post used by sub-clients
    plaid._post = AsyncMock()

    # attach real sub-client
    plaid.items = ItemsAPI(plaid)

    return plaid

# Test exchange public token
@pytest.mark.asyncio
async def test_items_exchange_public_token_positive():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"access_token": "test_access_token", "item_id": "test_item_id"}

    token, item_id = await plaid.items.exchange_public_token("test_public_token")

    path = "/item/public_token/exchange"
    payload = exchange_public_token_payload(plaid.client_id, plaid.secret, "test_public_token")
    plaid._post.assert_awaited_once_with(path, payload)

    assert token == "test_access_token"
    assert item_id == "test_item_id"

# Test get item
@pytest.mark.asyncio
async def test_items_get_positive():
    plaid = plaid_with_mocks()

    plaid._post.return_value = {"item_data": "some_item_data"}

    data = await plaid.items.get("test_access_token")

    path = "/item/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    plaid._post.assert_awaited_once_with(path, payload)

    assert data == {"item_data": "some_item_data"}

# Test remove item
@pytest.mark.asyncio
async def test_items_remove_positive_no_reason():
    plaid = plaid_with_mocks()

    plaid._post.return_value = None

    await plaid.items.remove("test_access_token")

    path = "/item/remove"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    plaid._post.assert_awaited_once_with(path, payload)

@pytest.mark.asyncio
async def test_items_remove_positive_reason():
    plaid = plaid_with_mocks()

    plaid._post.return_value = None

    await plaid.items.remove("test_access_token", "test_reason_code", "test_reason_note")

    path = "/item/remove"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["reason_code"] = "test_reason_code"
    payload["reason_note"] = "test_reason_note"
    plaid._post.assert_awaited_once_with(path, payload)

# Test invalidate access token
@pytest.mark.asyncio
async def test_items_invalidate_access_token_positive():
    plaid = plaid_with_mocks()

    plaid._post = AsyncMock(return_value={"new_access_token": "test_new_access_token"})

    new_token = await plaid.items.invalidate_access_token("test_access_token")

    path = "/item/access_token/invalidate"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    plaid._post.assert_awaited_once_with(path, payload)

    assert new_token == "test_new_access_token"