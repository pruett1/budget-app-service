from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
import pytest
import re
import uuid

from src.app import app
from src.helpers.dependencies import get_account_db, get_item_db, get_logger, get_plaid_client, get_session_manager
from src.helpers.encryption import pwd_hash

UUID4_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)

@pytest.fixture(autouse=True)
def client_and_mocks():
    client = TestClient(app)

    account_db = MagicMock()
    item_db = MagicMock()
    session_manager = MagicMock()
    plaid = MagicMock()
    logger = MagicMock()

    # Ensure async method is awaitable
    plaid.create_link_token = AsyncMock()

    app.dependency_overrides[get_account_db] = lambda: account_db
    app.dependency_overrides[get_item_db] = lambda: item_db
    app.dependency_overrides[get_plaid_client] = lambda: plaid
    app.dependency_overrides[get_session_manager] = lambda: session_manager
    app.dependency_overrides[get_logger] = lambda: logger

    # ensure middleware and handlers that read app.state have expected values
    app.state.logger = logger
    app.state.sessionManager = session_manager
    app.state.accountDB = account_db
    app.state.itemDB = item_db
    app.state.plaid = plaid

    yield {
        "client": client,
        "account_db": account_db,
        "item_db": item_db,
        "session_manager": session_manager,
        "plaid": plaid,
        "logger": logger,
    }

    app.dependency_overrides.clear()

def _headers():
    return {"request-id": str(uuid.uuid4())}

def test_router_account_create_success(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    item_db = c["item_db"]
    logger = c["logger"]

    # No existing user/email
    account_db.find_by_field.return_value = None

    payload = {"username": "u1", "password": "p1", "email": "u1@example.com"}
    resp = client.post("/account/create", json=payload, headers=_headers())

    assert resp.status_code == 200
    assert resp.json() == {"message": "Account created successfully"}

    # Verify insert called with hashed password and uuid
    account_db.insert.assert_called_once()
    inserted = account_db.insert.call_args[0][0]
    assert inserted["user"] == "u1"
    assert inserted["email"] == "u1@example.com"
    assert inserted["password"] == pwd_hash("p1")
    assert UUID4_RE.match(inserted["user_id"]) is not None

    # item_db.insert called with the user_id
    item_db.insert.assert_called_once_with(inserted["user_id"])

    # logger got initial and success debug calls
    logger.debug.assert_any_call("Account Create Attempt", path='/create', route='/account')
    logger.debug.assert_any_call("Successfully created account for user", user="u1")

def test_router_account_create_duplicate_username(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    logger = c["logger"]

    # Simulate username exists
    account_db.find_by_field.side_effect = lambda field, val: {"user": val} if field == "user" else None

    payload = {"username": "u2", "password": "p2", "email": "u2@example.com"}
    resp = client.post("/account/create", json=payload, headers=_headers())

    assert resp.status_code == 400
    assert resp.json() == {"error": "Username already exists"}
    account_db.insert.assert_not_called()
    logger.warning.assert_called_once_with("Username already exists", user="u2")
    logger.debug.assert_any_call("Account Create Attempt", path='/create', route='/account')

def test_router_account_create_invalid_email(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    logger = c["logger"]

    account_db.find_by_field.return_value = None

    payload = {"username": "u3", "password": "p3", "email": "invalid-email"}
    resp = client.post("/account/create", json=payload, headers=_headers())

    assert resp.status_code == 400
    assert resp.json() == {"error": "Invalid email format"}
    account_db.insert.assert_not_called()
    logger.warning.assert_called_once_with("Invalid email format", email="invalid-email")
    logger.debug.assert_any_call("Account Create Attempt", path='/create', route='/account')


def test_router_account_create_duplicate_email(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    logger = c["logger"]

    def find_by_field(field, val):
        if field == "user":
            return None
        if field == "email":
            return {"email": val}
        return None

    account_db.find_by_field.side_effect = find_by_field

    payload = {"username": "u4", "password": "p4", "email": "dup@example.com"}
    resp = client.post("/account/create", json=payload, headers=_headers())

    assert resp.status_code == 400
    assert resp.json() == {"error": "Email already exists"}
    account_db.insert.assert_not_called()
    logger.warning.assert_called_once_with("Email already exists", email="dup@example.com")
    logger.debug.assert_any_call("Account Create Attempt", path='/create', route='/account')

def test_router_account_login_success(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    session_manager = c["session_manager"]
    plaid = c["plaid"]

    user_id = str(uuid.uuid4())
    account_db.validate_credentials.return_value = {"user_id": user_id, "user": "lu"}
    session_manager.create.return_value = "sess-token"
    plaid.create_link_token.return_value = "link-token"

    payload = {"username": "lu", "password": "pw"}
    resp = client.post("/account/login", json=payload, headers=_headers())

    assert resp.status_code == 200
    assert resp.json() == {"jwt_token": "sess-token", "link_token": "link-token"}

    plaid.create_link_token.assert_awaited_once_with(user_id)
    session_manager.create.assert_called_once_with(user_id)
    # initial login debug
    c["logger"].debug.assert_any_call("Login Attempt", user="lu", path='/login', route='/account')

def test_router_account_login_invalid_credentials(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]

    account_db.validate_credentials.return_value = None

    payload = {"username": "no", "password": "no"}
    resp = client.post("/account/login", json=payload, headers=_headers())

    assert resp.status_code == 401
    assert resp.json() == {"error": "Invalid credentials"}
    c["logger"].debug.assert_any_call("Login Attempt", user="no", path='/login', route='/account')

def test_router_account_login_plaid_error_returns_500(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    account_db = c["account_db"]
    plaid = c["plaid"]
    logger = c["logger"]

    user_id = str(uuid.uuid4())
    account_db.validate_credentials.return_value = {"user_id": user_id, "user": "lu"}
    plaid.create_link_token.side_effect = Exception("boom")

    payload = {"username": "lu", "password": "pw"}
    resp = client.post("/account/login", json=payload, headers=_headers())

    assert resp.status_code == 500
    assert resp.json() == {"error": "Failed to create link token"}
    logger.error.assert_called_once_with("Exception while creating link token", exception="boom")
    logger.debug.assert_any_call("Login Attempt", user="lu", path='/login', route='/account')

def test_router_account_logout_valid_session(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    session_manager = c["session_manager"]
    logger = c["logger"]

    token = "tok-123"
    headers = _headers()
    headers["Authorization"] = f"Bearer {token}"

    resp = client.get("/account/logout", headers=headers)
    assert resp.status_code == 204
    session_manager.invalidate.assert_called_once_with(token)
    logger.debug.assert_any_call("Logging Out", path='/logout', route='/account')


def test_router_account_logout_missing_authorization_header(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    logger = c["logger"]

    resp = client.get("/account/logout", headers=_headers())
    assert resp.status_code == 400
    assert resp.json() == {"error": "Missing Authorization header"}
    logger.warning.assert_called_once_with("Logout attempted without Authorization header", path='/logout', route='/account')


def test_router_account_logout_malformed_authorization_header(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    logger = c["logger"]

    headers = _headers()
    headers["Authorization"] = "MalformedHeader"
    resp = client.get("/account/logout", headers=headers)
    assert resp.status_code == 401
    assert resp.json() == {"error": "Invalid or expired token"}
    logger.debug.assert_any_call("Failed to validate token", path='/account/logout', method='GET')


def test_router_account_logout_invalid_scheme(client_and_mocks):
    c = client_and_mocks
    client = c["client"]
    logger = c["logger"]

    headers = _headers()
    headers["Authorization"] = "Token abc123"
    resp = client.get("/account/logout", headers=headers)
    assert resp.status_code == 400
    assert resp.json() == {"error": "Invalid Authorization header scheme (must be Bearer)"}
    logger.debug.assert_any_call("Authorization header has invalid scheme", path='/account/logout', method='GET')