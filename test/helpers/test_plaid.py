from src.helpers.plaid import Plaid
from src.requests.payloads import create_link_token_payload, exchange_public_token_payload, item_payload
import httpx

from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import logging

def plaid_with_mocks():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_client = MagicMock()

    plaid = Plaid.__new__(Plaid)
    plaid.logger = mock_logger
    plaid.secret = "test_secret"
    plaid.client_id = "test_client_id"
    plaid.client = mock_client
    
    return plaid, mock_client, mock_logger

def test_plaid_init():
    # set up mocks
    mock_logger = MagicMock(spec=logging.Logger)

    with patch("src.helpers.plaid.Env") as mock_env:
        with patch("src.helpers.plaid.httpx.AsyncClient") as mock_client:
            mock_env.return_value = {
                "plaid": {
                    "SECRET": "test_secret",
                    "CLIENT_ID": "test_client_id"
                }
            }

            # init plaid client
            plaid = Plaid("sandbox", mock_logger)

            # assert init was done properly
            assert plaid.secret == "test_secret"
            assert plaid.client_id == "test_client_id"
            assert plaid.base_url == "https://sandbox.plaid.com"

            mock_client.assert_called_once_with(base_url = "https://sandbox.plaid.com", timeout = 10.0, headers = {"Content-Type": "application/json"})
            mock_logger.info.assert_called_once_with("Plaid client initialized with base URL: %s", plaid.base_url)

# POSITIVE test create link token
@pytest.mark.asyncio
async def test_create_link_token_positive():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"link_token": "test_link_token", "expiration": "test_expiration"}

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    token = await plaid.create_link_token("test_user_id")

    # Verify
    path = "/link/token/create"
    payload = create_link_token_payload(plaid.client_id, plaid.secret, "test_user_id")
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    mock_logger.info.assert_called_once_with("Successfully created link token expiring at test_expiration")
    assert token == "test_link_token"

# NEGATIVE tests create link token
@pytest.mark.asyncio
async def test_create_link_token_negative_status_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.text = "error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTPStatusError", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    with pytest.raises(httpx.HTTPStatusError):
        await plaid.create_link_token("test_user_id")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()
    mock_logger.error.assert_called_once_with("HTTP error while creating link token: error")

@pytest.mark.asyncio
async def test_create_link_token_negative_request_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()
    
    mock_client.post = AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.create_link_token("test_user_id")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while creating link token: RequestError")

# POSITIVE test exchange public token
@pytest.mark.asyncio
async def test_exhcange_public_token_positive():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"access_token": "test_access_token", "item_id": "test_item_id"}

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action 
    token, item_id = await plaid.exchange_public_token("test_public_token")

    # Verify
    path = "/item/public_token/exchange"
    payload = exchange_public_token_payload(plaid.client_id, plaid.secret, "test_public_token")
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    mock_logger.info.assert_called_once_with("Successfully exchanged public token for access token and item id")

    assert token == "test_access_token"
    assert item_id == "test_item_id"

# NEGATIVE tests exchange public token
@pytest.mark.asyncio
async def test_exchange_public_token_negative_status_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.text = "error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTPStatusError", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    with pytest.raises(httpx.HTTPStatusError):
        await plaid.exchange_public_token("test_user_id")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()
    mock_logger.error.assert_called_once_with("HTTP error while exchanging public token: error")

@pytest.mark.asyncio
async def test_exchange_public_token_negative_request_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_client.post = AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.exchange_public_token("test_user_id")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while exchanging public token: RequestError")

# POSITIVE test for get item
@pytest.mark.asyncio
async def test_get_item_positive():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"item_data": "some_item_data"}

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    data = await plaid.get_item("test_access_token")
    
    # Verify
    path = "/item/get"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    assert data == {"item_data": "some_item_data"}

# NEGATIVE tests for get item
@pytest.mark.asyncio
async def test_get_item_negative_status_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.text = "error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTPStatusError", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    with pytest.raises(httpx.HTTPStatusError):
        await plaid.get_item("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()
    mock_logger.error.assert_called_once_with("HTTP error while getting item data: error")

@pytest.mark.asyncio
async def test_get_item_negative_request_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_client.post = AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.get_item("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while getting item data: RequestError")

# POSITIVE tests for remove item
@pytest.mark.asyncio
async def test_remove_item_positive_no_reason():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    await plaid.remove_item("test_access_token")

    # Verify
    path = "/item/remove"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_logger.info.assert_called_once_with("Successfully removed item")

@pytest.mark.asyncio
async def test_remove_item_positive_reason():
        # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    await plaid.remove_item("test_access_token", "test_reason_code", "test_reason_note")

    # Verify
    path = "/item/remove"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    payload["reason_code"] = "test_reason_code"
    payload["reason_note"] = "test_reason_note"
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_logger.info.assert_called_once_with("Successfully removed item")

# NEGATIVE tests remove item
@pytest.mark.asyncio
async def test_remove_item_negative_status_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.text = "error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTPStatusError", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    with pytest.raises(httpx.HTTPStatusError):
        await plaid.remove_item("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()
    mock_logger.error.assert_called_once_with("HTTP error while removing item: error")

@pytest.mark.asyncio
async def test_remove_item_negative_request_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_client.post = AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.remove_item("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while removing item: RequestError")

# POSITIVE test invalidate access token
@pytest.mark.asyncio
async def test_invalidate_access_token_positive():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"new_access_token": "test_new_access_token"}

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    new_token = await plaid.invalidate_access_token("test_access_token")

    # Verify
    path = "/item/access_token/invalidate"
    payload = item_payload(plaid.client_id, plaid.secret, "test_access_token")
    mock_client.post.assert_awaited_once_with(path, json=payload)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    mock_logger.info.assert_called_once_with("Successfully rotated access token")

    assert new_token == "test_new_access_token"

# NEGATIVE tests invalidate access token
@pytest.mark.asyncio
async def test_invalidate_access_token_negative_status_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_response = MagicMock()
    mock_response.text = "error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTPStatusError", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value = mock_response)

    # Action
    with pytest.raises(httpx.HTTPStatusError):
        await plaid.invalidate_access_token("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()
    mock_logger.error.assert_called_once_with("HTTP error while rotating access token: error")

@pytest.mark.asyncio
async def test_invalidate_access_token_negative_request_error():
    # Setup mocks
    plaid, mock_client, mock_logger = plaid_with_mocks()

    mock_client.post = AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.invalidate_access_token("test_access_token")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while rotating access token: RequestError")

# POSITIVE test close
@pytest.mark.asyncio
async def test_close():
    # Setup mocks
    plaid, mock_client, _ = plaid_with_mocks()

    mock_client.aclose = AsyncMock(return_value = None)

    # Action
    await plaid.close()

    # Verify
    mock_client.aclose.assert_called_once()