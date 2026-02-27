from src.helpers.plaid.client import Plaid
from src.helpers.plaid.transactions import TransactionsAPI
from src.helpers.plaid.items import ItemsAPI
from src.helpers.plaid.liabilities import LiabilitiesAPI
from src.helpers.plaid.investments import InvestmentsAPI
from src.requests.payloads import create_link_token_payload
import httpx

from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import logging


def plaid_with_mocks():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_client = AsyncMock()

    plaid = Plaid.__new__(Plaid)
    plaid.logger = mock_logger
    plaid.secret = "test_secret"
    plaid.client_id = "test_client_id"
    plaid.client = mock_client

    # mock the internal _post used by sub-clients
    plaid._post = AsyncMock()

    # attach real sub-clients
    plaid.items = ItemsAPI(plaid)
    plaid.transactions = TransactionsAPI(plaid)
    plaid.liabilities = LiabilitiesAPI(plaid)

    return plaid, mock_client, mock_logger

# Test initialization of plaid client is successful
def test_plaid_init():
    # set up mocks
    mock_logger = MagicMock(spec=logging.Logger)

    with patch("src.helpers.plaid.client.Env") as mock_env:
        with patch("src.helpers.plaid.client.httpx.AsyncClient") as mock_client:
            mock_env.return_value = {
                "plaid": {
                    "SECRET": "test_secret",
                    "CLIENT_ID": "test_client_id"
                }
            }

            # init plaid client
            plaid = Plaid("sandbox", mock_logger)

            # assert init is done correctly
            assert plaid.secret == "test_secret"
            assert plaid.client_id == "test_client_id"
            assert plaid.base_url == "https://sandbox.plaid.com"

            mock_client.assert_called_once_with(base_url = "https://sandbox.plaid.com", timeout = 10.0, headers = {"Content-Type": "application/json"})
            mock_logger.info.assert_called_once_with("Plaid client initialized with base URL: %s", plaid.base_url)

            assert isinstance(plaid.transactions, TransactionsAPI)
            assert isinstance(plaid.items, ItemsAPI)
            assert isinstance(plaid.liabilities, LiabilitiesAPI)
            assert isinstance(plaid.investments, InvestmentsAPI)

# Test _post method
@pytest.mark.asyncio
async def test_plaid__post_positive():
    # setup mocks
    mock_logger = MagicMock(spec=logging.Logger)
    mock_client = AsyncMock()

    plaid = Plaid.__new__(Plaid)
    plaid.logger = mock_logger
    plaid.client = mock_client

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = MagicMock(return_value=200)
    mock_response.content = b'{}'
    mock_response.json.return_value = {"ok": True}

    mock_client.post = AsyncMock(return_value=mock_response)

    # action
    data = await plaid._post('/test/path', {'a': 1})

    # assert
    mock_client.post.assert_awaited_once_with('/test/path', json={'a': 1})
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    mock_logger.info.assert_called_once_with(f"Post: /test/path, Status: {mock_response.status_code()}")
    assert data == {"ok": True}


@pytest.mark.asyncio
async def test_plaid__post_negative_http_status_error():
    # setup mocks
    mock_logger = MagicMock(spec=logging.Logger)
    mock_client = AsyncMock()

    plaid = Plaid.__new__(Plaid)
    plaid.logger = mock_logger
    plaid.client = mock_client

    mock_response = MagicMock()
    mock_response.text = 'err'
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("err", request=MagicMock(), response=mock_response)

    mock_client.post = AsyncMock(return_value=mock_response)

    # action
    result = await plaid._post('/test/path', {'a': 1})

    # assert
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Post to /test/path resulted in HTTP error: err")
    assert result is None


@pytest.mark.asyncio
async def test_plaid__post_negative_request_error():
    # setup mock
    mock_logger = MagicMock(spec=logging.Logger)
    mock_client = AsyncMock()

    plaid = Plaid.__new__(Plaid)
    plaid.logger = mock_logger
    plaid.client = mock_client

    mock_client.post = AsyncMock(side_effect=httpx.RequestError('req_err', request=MagicMock()))

    # action
    result = await plaid._post('/test/path', {'a': 1})

    # assert
    mock_client.post.assert_awaited_once()
    mock_logger.error.assert_called_once_with("Request error with post to /test/path: req_err")
    assert result is None

# Test create link token 
# Bc _post is already unit tested just need to test that it is called properly
@pytest.mark.asyncio
async def test_plaid_create_link_token_positive():
    plaid, _, _ = plaid_with_mocks()

    plaid._post.return_value = {"link_token": "test_link_token", "expiration": "test_expiration"}

    token = await plaid.create_link_token("test_user_id")

    path = "/link/token/create"
    payload = create_link_token_payload(plaid.client_id, plaid.secret, "test_user_id")
    plaid._post.assert_awaited_once_with(path, payload)
    assert token == "test_link_token"

@pytest.mark.asyncio
async def test_plaid_close():
    plaid, mock_client, _ = plaid_with_mocks()

    mock_client.aclose = AsyncMock(return_value = None)

    await plaid.close()

    mock_client.aclose.assert_awaited_once()
