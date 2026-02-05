from fastapi.testclient import TestClient
import pytest
import re

from src.app import app
from test.mocks.dbs import MockAccountDB, MockItemDB
from test.mocks.plaid import MockPlaid
from test.mocks.session_manager import MockSessionManager
from src.helpers.dependencies import get_account_db, get_item_db, get_logger, get_plaid_client, get_session_manager
from src.helpers.encryption import decrypt, pwd_hash

import logging

client = TestClient(app)

# Set up mock dependencies
mock_account_db = MockAccountDB()
mock_item_db = MockItemDB()
mock_plaid = MockPlaid()
mock_session_manager = MockSessionManager()

app.dependency_overrides[get_account_db] = lambda: mock_account_db
app.dependency_overrides[get_item_db] = lambda: mock_item_db
app.dependency_overrides[get_plaid_client] = lambda: mock_plaid
app.dependency_overrides[get_session_manager] = lambda: mock_session_manager

logger = logging.getLogger("test_logger")
logger.setLevel(logging.INFO)
app.dependency_overrides[get_logger] = lambda: logger

@pytest.fixture(autouse=True)
def clear_dbs():
    # Clear mock databases before each test
    mock_account_db.clear()
    mock_item_db.clear()
    yield

# Positive test for account creation
@pytest.mark.usefixtures("caplog")
def test_create_account_positive(caplog):
    # When create a new account with valid details
    request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    response = client.post("/account/create", json=request)
    new_account = mock_account_db.find_by_field("user", "testuser")

    # Then it should succeed, log appropriately, and store the account correctly
    assert "Successfully created account for user: testuser" in caplog.text
    assert response.status_code == 200
    assert response.json() == "Account created successfully"
    
    assert new_account is not None
    assert new_account['user'] == "testuser"
    assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', new_account['user_id'])
    assert new_account['email'] == "testuser@example.com"
    assert new_account['password'] != "testpass" # password not stored in plaintext
    assert new_account['password'] == pwd_hash("testpass")

    assert mock_item_db.items.get(new_account['user_id']) == []

# Negative tests for account creation
@pytest.mark.usefixtures("caplog")
def test_create_account_negative_duplicate_username(caplog):
    # Given an exisiting account
    request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    response = client.post("/account/create", json=request)
    assert response.status_code == 200

    # When trying to create another account with the same username
    response = client.post("/account/create", json=request)

    # Then it should fail and log appropriately
    assert "Username already exists: testuser" in caplog.text
    assert response.status_code == 400
    assert response.json() == "Username already exists"

@pytest.mark.usefixtures("caplog")
def test_reate_account_negative_invalid_email(caplog):
    # When creating an account with an invalid email format
    request = {"username": "testuser", "password": "testpass", "email": "invalidemail"}
    response = client.post("/account/create", json=request)

    # Then it should fail, log appropriately, and not store the account
    assert "Invalid email format: invalidemail" in caplog.text
    assert response.status_code == 400
    assert response.json() == "Invalid email format"
    assert mock_account_db.find_by_field("user", "testuser") is None

@pytest.mark.usefixtures("caplog")
def test_create_account_negative_duplicate_email(caplog):
    # Given an existing account
    request_1 = {"username": "user1", "password": "pass1", "email": "testuser@example.com"}
    response_1 = client.post("/account/create", json=request_1)
    assert response_1.status_code == 200

    # When trying to create another account with the same email
    request_2 = {"username": "user2", "password": "pass2", "email": "testuser@example.com"}
    response_2 = client.post("/account/create", json=request_2)

    # Then it should fail, log appropriately, and not store the second account
    assert "Email already exists: testuser@example.com" in caplog.text
    assert response_2.status_code == 400
    assert response_2.json() == "Email already exists"
    assert mock_account_db.find_by_field("user", "user2") is None

# Positive test for login
def test_login_positive():
    # Given an existing account
    create_request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    create_response = client.post("/account/create", json=create_request)
    assert create_response.status_code == 200
    user_id = mock_account_db.find_by_field("user", "testuser")['user_id']

    # When logging in with correct credentials
    login_request = {"username": "testuser", "password": "testpass"}
    login_response = client.post("/account/login", json=login_request)

    # Then it should succeed and return tokens
    assert login_response.status_code == 200
    assert login_response.json() == {
        "jwt_token": f"{user_id}:mock_session_token",
        "link_token": "mock_link_token"
    }

# Negative test for login
def test_login_negative_invalid_username():
    # Given an existing account
    create_request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    create_response = client.post("/account/create", json=create_request)
    assert create_response.status_code == 200

    # When logging in with an invalid username
    login_request = {"username": "wronguser", "password": "testpass"}
    login_response = client.post("/account/login", json=login_request)

    # Then it should return unauthorized
    assert login_response.status_code == 401
    assert login_response.json() == "Invalid credentials"

def test_login_negative_invalid_password():
    # Given an existing account
    create_request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    create_response = client.post("/account/create", json=create_request)
    assert create_response.status_code == 200

    # When logging in with an invalid password
    login_request = {"username": "testuser", "password": "wrongpass"}
    login_response = client.post("/account/login", json=login_request)

    # Then it should return unauthorized
    assert login_response.status_code == 401
    assert login_response.json() == "Invalid credentials"

# Positive test for exchange_public_token
def test_exchange_public_token_positive():
    # Given an existing account and valid JWT token
    create_request = {"username": "testuser", "password": "testpass", "email": "testuser@example.com"}
    create_response = client.post("/account/create", json=create_request)
    assert create_response.status_code == 200
    
    login_response = client.post("/account/login", json={"username": "testuser", "password": "testpass"})
    assert login_response.status_code == 200
    jwt_token = login_response.json()['jwt_token']

    # When exchanging a public token
    exchange_request = {"jwt_token": jwt_token, "public_token": "mock_public_token"}
    exchange_response = client.post("/account/exchange_public_token", json=exchange_request)

    # Then it should succeed, not return anything, and store the access token and item ID
    assert exchange_response.status_code == 204
    assert exchange_response.content == b""
    
    user_id = mock_session_manager.validate(jwt_token)
    user_items = mock_item_db.items.get(user_id)
    assert len(user_items) == 1
    assert user_items[0]['item_id'] != "mock_item_id" # should be stored encrypted
    assert user_items[0]['access_token'] != "mock_access_token" # should be stored encrypted
    assert decrypt(user_items[0]['item_id']) == "mock_item_id"
    assert decrypt(user_items[0]['access_token']) == "mock_access_token"

# Negative test for exchange_public_token
def test_exchange_public_token_negative_invalid_jwt():
    # When exchanging a public token with an invalid JWT token
    exchange_request = {"jwt_token": "user_id:invalid_jwt_token", "public_token": "mock_public_token"}
    exchange_response = client.post("/account/exchange_public_token", json=exchange_request)

    # Then it should return unauthorized and not store anything
    assert exchange_response.status_code == 401
    assert exchange_response.json() == "Invalid or expired session token"
    assert mock_item_db.items == {}