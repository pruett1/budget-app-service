from src.db.account_db import AccountDB

from unittest.mock import MagicMock
import logging

def account_db_with_mocks() -> AccountDB:
    # Setup mocks
    mock_logger = MagicMock(spec=logging.Logger)
    mock_collection = MagicMock()

    # Init accountDB 
    accountDB = AccountDB.__new__(AccountDB)
    accountDB.collection = mock_collection
    accountDB.logger = mock_logger
    return accountDB, mock_collection, mock_logger

def test_db_account_init():
    # Setup mocks; logger and db factory chain
    mock_logger = MagicMock(spec=logging.Logger)
    mock_collection = MagicMock()

    mock_db = MagicMock()
    mock_db.accounts = mock_collection

    mock_db_instance = MagicMock()
    mock_db_instance.get_db.return_value = mock_db

    mock_db_factory = MagicMock()
    mock_db_factory.return_value = mock_db_instance
    
    # Initialize AccountDB with mocks
    account_db = AccountDB(env="test", logger=mock_logger, db_factory=mock_db_factory)

    # Assertions to verify correct initialization
    mock_db_factory.assert_called_once_with("test")
    mock_db_instance.get_db.assert_called_once()
    assert account_db.collection == mock_collection

    mock_logger.info.assert_called_with("AccountDB initialized.")

# POSITIVE test for insert method
def test_db_account_insert_positive():
    accountDB, mock_collection, mock_logger = account_db_with_mocks()

    # Test data
    test_account_data = {"user": "test_user", "password": "test_password"}

    # Call insert method
    accountDB.insert(test_account_data)

    # Verify that collection.insert_one was called with correct data
    mock_collection.insert_one.assert_called_once_with(test_account_data)
    mock_logger.info.assert_any_call("Inserting new account...")
    mock_logger.info.assert_any_call("Insertion complete.")

# NEGATIVE test for insert method
def test_db_account_insert_negative_invalid_data_type():
    accountDB, _, _ = account_db_with_mocks()

    # Test data - invalid type (string instead of dict)
    invalid_account_data = "invalid_data"

    # Call insert method and expect ValueError
    try:
        accountDB.insert(invalid_account_data)
        assert False, "Expected ValueError for invalid account data type"
    except ValueError as e:
        assert str(e) == "Invalid account data provided for insertion."

def test_db_account_insert_negative_none_data():
    accountDB, _, _ = account_db_with_mocks()

    # Test data - None
    invalid_account_data = None

    # Call insert method and expect ValueError
    try:
        accountDB.insert(invalid_account_data)
        assert False, "Expected ValueError for None account data"
    except ValueError as e:
        assert str(e) == "Invalid account data provided for insertion."

# POSITIVE tests for find_by_field method
def test_db_account_find_by_field_positive_data():
    account_db, mock_collection, _ = account_db_with_mocks()

    # Test data
    data = {"user": "testuser", "password": "testpassword", "_id": "12345"}
    mock_collection.find_one.return_value = data

    # Call find_by_field method
    result = account_db.find_by_field("user", "testuser")

    # Verify that collection.find_one was called with correct query and data was processed correctly
    mock_collection.find_one.assert_called_once_with({"user": "testuser"})

    assert result == {"user": "testuser"}, "Expected result to match the input data without _id and password"

def test_db_account_find_by_field_positive_no_data():
    account_db, mock_collection, _ = account_db_with_mocks()

    # Test data - no matching entry
    mock_collection.find_one.return_value = None

    # Call find_by_field method
    result = account_db.find_by_field("user", "testuser")

    # Verify that collection.find_one was called with correct query and result is None
    mock_collection.find_one.assert_called_once_with({"user": "testuser"})
    assert result is None, "Expected result to be None when no matching entry is found"

# NEGATIVE tests for find_by_field method
def test_db_account_find_by_field_negative_invalid_field_type():
    account_db, _, _ = account_db_with_mocks()

    # Call find_by_field method with invalid field type (int instead of str) and expect ValueError
    try:
        account_db.find_by_field(123, "testuser")
        assert False, "Expected ValueError for invalid field type"
    except ValueError as e:
        assert str(e) == "Invalid field or value provided for search."

def test_db_account_find_by_field_negative_invalid_value_type():
    account_db, _, _ = account_db_with_mocks()

    # Call find_by_field method with invalid value type (int instead of str) and expect ValueError
    try:
        account_db.find_by_field("user", 123)
        assert False, "Expected ValueError for invalid value type"
    except ValueError as e:
        assert str(e) == "Invalid field or value provided for search."

def test_db_account_find_by_field_negative_empty_field():
    account_db, _, _ = account_db_with_mocks()

    # Call find_by_field method with empty field and expect ValueError
    try:
        account_db.find_by_field("", "testuser")
        assert False, "Expected ValueError for empty field"
    except ValueError as e:
        assert str(e) == "Invalid field or value provided for search."

def test_db_account_find_by_field_negative_empty_value():
    account_db, _, _ = account_db_with_mocks()

    # Call find_by_field method with empty value and expect ValueError
    try:
        account_db.find_by_field("user", "")
        assert False, "Expected ValueError for empty value"
    except ValueError as e:
        assert str(e) == "Invalid field or value provided for search."

# POSITIVE tests for validate_credentials method
def test_db_account_validate_credentials_positive_valid_credentials():
    account_db, mock_collection, _ = account_db_with_mocks()

    # Test data - valid credentials
    data = {"user": "testuser", "password": "testpassword", "_id": "12345"}
    mock_collection.find_one.return_value = data

    # Call validate_credentials method
    result = account_db.validate_credentials("testuser", "testpassword")

    # Verify that collection.find_one was called with correct query and result is correct
    mock_collection.find_one.assert_called_once_with({"user": "testuser"})
    assert result == {"user": "testuser"}, "Expected result to match the input data without _id and password"

def test_db_account_validate_credentials_positive_invalid_credentials():
    account_db, mock_collection, _ = account_db_with_mocks()

    # Test data - invalid credentials
    data = {"user": "testuser", "password": "testpassword", "_id": "12345"}
    mock_collection.find_one.return_value = data

    # Call validate_credentials method with incorrect password
    result = account_db.validate_credentials("testuser", "wrongpassword")

    # Verify that collection.find_one was called with correct query and result is None for invalid credentials
    mock_collection.find_one.assert_called_once_with({"user": "testuser"})
    assert result is None, "Expected result to be None for invalid credentials"

# NEGATIVE tests for validate_credentials method
def test_db_account_validate_credentials_negative_invalid_username_type():
    account_db, _, _ = account_db_with_mocks()

    # Call validate_credentials method with invalid username type (int instead of str) and expect ValueError
    try:
        account_db.validate_credentials(123, "testpassword")
        assert False, "Expected ValueError for invalid username type"
    except ValueError as e:
        assert str(e) == "Invalid username or password provided for validation."

def test_db_account_validate_credentials_negative_invalid_password_type():
    account_db, _, _ = account_db_with_mocks()

    # Call validate_credentials method with invalid password type (int instead of str) and expect ValueError
    try:
        account_db.validate_credentials("testuser", 123)
        assert False, "Expected ValueError for invalid password type"
    except ValueError as e:
        assert str(e) == "Invalid username or password provided for validation."

def test_db_account_validate_credentials_negative_empty_username():
    account_db, _, _ = account_db_with_mocks()

    # Call validate_credentials method with empty username and expect ValueError
    try:
        account_db.validate_credentials("", "testpassword")
        assert False, "Expected ValueError for empty username"
    except ValueError as e:
        assert str(e) == "Invalid username or password provided for validation."

def test_db_account_validate_credentials_negative_empty_password():
    account_db, _, _ = account_db_with_mocks()

    # Call validate_credentials method with empty password and expect ValueError
    try:
        account_db.validate_credentials("testuser", "")
        assert False, "Expected ValueError for empty password"
    except ValueError as e:
        assert str(e) == "Invalid username or password provided for validation."

# POSTIVE test for close method
def test_db_account_close():
    account_db, mock_collection, _ = account_db_with_mocks()

    # Call close method
    account_db.close()

    # Verify that collection.database.client.close was called
    mock_collection.database.client.close.assert_called_once()