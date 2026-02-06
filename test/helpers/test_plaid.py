from src.helpers.plaid import Plaid
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
    mock_client.post.assert_awaited_once()
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
    
    mock_client.post= AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

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
    mock_client.post.assert_awaited_once()
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

    mock_client.post= AsyncMock(side_effect = httpx.RequestError("RequestError", request = MagicMock(),) )

    # Action
    with pytest.raises(httpx.RequestError):
        await plaid.exchange_public_token("test_user_id")

    # Verify
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error while exchanging public token: RequestError")

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