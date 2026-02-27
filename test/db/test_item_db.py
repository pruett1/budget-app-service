from src.db.item_db import ItemDB

from unittest.mock import MagicMock
import logging

def item_db_with_mocks() -> ItemDB:
    # Setup mocks
    mock_logger = MagicMock(spec=logging.Logger)
    mock_collection = MagicMock()

    # Init itemDB 
    itemDB = ItemDB.__new__(ItemDB)
    itemDB.collection = mock_collection
    itemDB.logger = mock_logger
    return itemDB, mock_collection, mock_logger

def test_db_item_init():
    # Setup mocks; logger and db factory chain
    mock_logger = MagicMock(spec=logging.Logger)
    mock_collection = MagicMock()

    mock_db = MagicMock()
    mock_db.items = mock_collection

    mock_db_instance = MagicMock()
    mock_db_instance.get_db.return_value = mock_db

    mock_db_factory = MagicMock()
    mock_db_factory.return_value = mock_db_instance
    
    # Initialize ItemDB with mocks
    item_db = ItemDB(env="test", logger=mock_logger, db_factory=mock_db_factory)

    # Assertions to verify correct initialization
    mock_db_factory.assert_called_once_with("test")
    mock_db_instance.get_db.assert_called_once()
    assert item_db.collection == mock_collection

    mock_logger.info.assert_called_with("ItemDB initialized.")

# POSITIVE test for insert method
def test_db_item_insert_positive():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Call insert method
    itemDB.insert("test_user_id")

    # Verify that collection.insert_one was called with correct data
    mock_collection.insert_one.assert_called_once_with({"user_id": "test_user_id", "items": []})
    mock_logger.info.assert_any_call("Inserting new item...")

# NEGATIVE test for insert method
def test_db_item_insert_negative_invalid_data_type():
    itemDB, _, _ = item_db_with_mocks()

    # Test data - invalid type (string instead of dict)
    invalid_user_id = 12345  # Not a string

    try:
        itemDB.insert(invalid_user_id)
        assert False, "Expected ValueError for invalid user_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id provided for insertion."

def test_db_item_insert_negative_empty_user_id():
    itemDB, _, _ = item_db_with_mocks()

    # Test data - empty string
    empty_user_id = ""

    try:
        itemDB.insert(empty_user_id)
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id provided for insertion."

def test_db_item_inert_negative_insert_exception():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to raise exception on insert_one
    mock_collection.insert_one.side_effect = Exception("Database error")

    try:
        itemDB.insert("test_user_id")
        assert False, "Expected Exception for database error during insert"
    except Exception as e:
        mock_collection.insert_one.assert_called_once_with({"user_id": "test_user_id", "items": []})
        assert str(e) == "Database error"
        mock_logger.error.assert_called_with("Failed to insert new item: %s", e)

# POSITIVE test for append_item method
def test_db_item_append_item_positive():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to simulate existing user_id
    mock_collection.find_one.side_effect = [
        {"user_id": "test_user_id", "items": []},  # For user_id check
        None  # For existing item check
    ]

    # Call append_item method
    itemDB.append_item("test_user_id", "item_123", "access_token_abc")

    # Verify that collection.update_one was called with correct data
    mock_collection.update_one.assert_called_once_with(
        {"user_id": "test_user_id"}, 
        {"$push": {"items": {"item_id": "item_123", "access_token": "access_token_abc", "item_data": None}}}
    )

def test_db_item_append_item_positive_with_data():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to simulate existing user_id
    mock_collection.find_one.side_effect = [
        {"user_id": "test_user_id", "items": []},  # For user_id check
        None  # For existing item check
    ]

    # Call append_item method
    test_item_data = {"test_field": "test_val"}
    itemDB.append_item("test_user_id", "item_123", "access_token_abc", data=test_item_data)

    # Verify that collection.update_one was called with correct data
    mock_collection.update_one.assert_called_once_with(
        {"user_id": "test_user_id"}, 
        {"$push": {"items": {"item_id": "item_123", "access_token": "access_token_abc", "item_data": test_item_data}}}
    )

# NEGATIVE tests for append_item method
def test_db_item_append_item_negative_invalid_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item(12345, "item_123", "access_token_abc")  # Invalid user_id type
        assert False, "Expected ValueError for invalid user_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_invalid_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item("test_user_id", 12345, "access_token_abc")  # Invalid item_id type
        assert False, "Expected ValueError for invalid item_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_invalid_access_token():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item("test_user_id", "item_123", 12345)  # Invalid access_token type
        assert False, "Expected ValueError for invalid access_token type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_empty_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item("", "item_123", "access_token_abc")  # Empty user_id
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_empty_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item("test_user_id", "", "access_token_abc")  # Empty item_id
        assert False, "Expected ValueError for empty item_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_empty_access_token():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.append_item("test_user_id", "item_123", "")  # Empty access_token
        assert False, "Expected ValueError for empty access_token"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or access_token provided for appending item."

def test_db_item_append_item_negative_user_id_not_found():
    itemDB, mock_collection, _ = item_db_with_mocks()

    # Setup mock to simulate user_id not found
    mock_collection.find_one.return_value = None

    try:
        itemDB.append_item("nonexistent_user_id", "item_123", "access_token_abc")
        assert False, "Expected ValueError for user_id not found"
    except ValueError as e:
        assert str(e) == "User_id not found"

def test_db_item_append_item_negative_item_already_exists():
    itemDB, mock_collection, _ = item_db_with_mocks()

    # Setup mock to simulate existing user_id and existing item
    mock_collection.find_one.side_effect = [
        {"user_id": "test_user_id", "items": [{"item_id": "item_123", "access_token": "access_token_123"}]},  # For user_id check
        {"user_id": "test_user_id", "items": [{"item_id": "item_123", "access_token": "access_token_abc"}]}  # For existing item check
    ]

    try:
        itemDB.append_item("test_user_id", "item_123", "access_token_abc")
        assert False, "Expected ValueError for item already exists"
    except ValueError as e:
        assert str(e) == "Item already exists"

def test_db_item_append_item_negative_insert_exception():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to simulate existing user_id and no existing item
    mock_collection.find_one.side_effect = [
        {"user_id": "test_user_id", "items": []},  # For user_id check
        None  # For existing item check
    ]

    # Setup mock to raise exception on update_one
    mock_collection.update_one.side_effect = Exception("Database error")

    try:
        itemDB.append_item("test_user_id", "item_123", "access_token_abc")
        assert False, "Expected Exception for database error during append_item"
    except Exception as e:
        mock_collection.update_one.assert_called_once_with(
            {"user_id": "test_user_id"}, 
            {"$push": {"items": {"item_id": "item_123", "access_token": "access_token_abc", "item_data": None}}}
            )
        assert str(e) == "Database error"
        mock_logger.error.assert_called_with("Failed to append item: %s", e)

# POSTIVE tests for get_items method
def test_db_item_get_items_positive():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to simulate existing user_id with items
    mock_collection.find_one.return_value = {
        "user_id": "test_user_id",
        "items": [{"item_id": "12345", "access_token": "acces_token"}]
    }

    # Call get_items method
    result = itemDB.get_items("test_user_id")

    # Verify that collection.find_one was called with correct query and result is correct
    mock_collection.find_one.assert_called_once_with({"user_id": "test_user_id"})
    assert result == [{"item_id": "12345", "access_token": "acces_token"}]

def test_db_item_get_items_positive_no_user():
    item_db, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to simulate no user found
    mock_collection.find_one.return_value = None

    # Call get_items method
    result = item_db.get_items("nonexistent_user_id")

    # Verify that collection.find_one was called with correct query and result is empty list
    mock_collection.find_one.assert_called_once_with({"user_id": "nonexistent_user_id"})
    assert result == []
    mock_logger.warning.assert_called_with("No user found")

# NEGATIVE test for get_items method
def test_db_item_get_items_negative_invalid_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.get_items(12345)  # Invalid user_id type
        assert False, "Expected ValueError for invalid user_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id provided for retrieving items."

def test_db_item_get_items_negative_empty_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.get_items("")  # Empty user_id
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id provided for retrieving items."

# POSITIVE tests for remove_item method
def test_db_item_remove_item_positive():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Call remove_item method
    itemDB.remove_item("test_user_id", "item_123")

    # Verify that collection.update_one was called with correct data
    mock_collection.update_one.assert_called_once_with(
        {"user_id": "test_user_id"}, 
        {"$pull": {"items": {"item_id": "item_123"}}}
    )
    mock_logger.info.assert_called_with("Removing item_id: %s from user_id: %s", "item_123", "test_user_id")

# NEGATIVE tests for remove_item method
def test_db_item_remove_item_negative_invalid_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.remove_item(12345, "item_123")  # Invalid user_id type
        assert False, "Expected ValueError for invalid user_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id or item_id provided for removing item."

def test_db_item_remove_item_negative_invalid_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.remove_item("test_user_id", 12345)  # Invalid item_id type
        assert False, "Expected ValueError for invalid item_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id or item_id provided for removing item."

def test_db_item_remove_item_negative_empty_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.remove_item("", "item_123")  # Empty user_id
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id or item_id provided for removing item."

def test_db_item_remove_item_negative_empty_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.remove_item("test_user_id", "")  # Empty item_id
        assert False, "Expected ValueError for empty item_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id or item_id provided for removing item."

def test_db_item_remove_item_negative_update_exception():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to raise exception on update_one
    mock_collection.update_one.side_effect = Exception("Database error")

    try:
        itemDB.remove_item("test_user_id", "item_123")
        assert False, "Expected Exception for database error during remove_item"
    except Exception as e:
        mock_collection.update_one.assert_called_once_with(
            {"user_id": "test_user_id"}, 
            {"$pull": {"items": {"item_id": "item_123"}}}
        )
        assert str(e) == "Database error"
        mock_logger.error.assert_called_with("Failed to remove item: %s", e)

# POSITIVE tests for update_item_access_token method
def test_db_item_update_item_access_token_positive():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Call update_item_access_token method
    itemDB.update_item_access_token("test_user_id", "item_123", "new_access_token_abc")

    # Verify that collection.update_one was called with correct data
    mock_collection.update_one.assert_called_once_with(
        {"user_id": "test_user_id", "items.item_id": "item_123"},
        {"$set": {"items.$.access_token": "new_access_token_abc"}}
    )
    mock_logger.info.assert_called_with("Updating access token for item_id: %s of user_id: %s", "item_123", "test_user_id")

# NEGATIVE test for update_item_access_token method
def test_db_item_update_item_access_token_negative_invalid_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token(12345, "item_123", "new_access_token_abc")  # Invalid user_id type
        assert False, "Expected ValueError for invalid user_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."

def test_db_item_update_item_access_token_negative_invalid_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token("test_user_id", 12345, "new_access_token_abc")  # Invalid item_id type
        assert False, "Expected ValueError for invalid item_id type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."
    
def test_db_item_update_item_access_token_negative_invalid_access_token():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token("test_user_id", "item_123", 12345)  # Invalid access_token type
        assert False, "Expected ValueError for invalid access_token type"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."

def test_db_item_update_item_access_token_negative_empty_user_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token("", "item_123", "new_access_token_abc")  # Empty user_id
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."

def test_db_item_update_item_access_token_negative_empty_item_id():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token("test_user_id", "", "new_access_token_abc")  # Empty item_id
        assert False, "Expected ValueError for empty item_id"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."

def test_db_item_update_item_access_token_negative_empty_access_token():
    itemDB, _, _ = item_db_with_mocks()

    try:
        itemDB.update_item_access_token("test_user_id", "item_123", "")  # Empty access_token
        assert False, "Expected ValueError for empty access_token"
    except ValueError as e:
        assert str(e) == "Invalid user_id, item_id, or new_access_token provided for updating access token."

def test_db_item_update_item_access_token_negative_update_exception():
    itemDB, mock_collection, mock_logger = item_db_with_mocks()

    # Setup mock to raise exception on update_one
    mock_collection.update_one.side_effect = Exception("Database error")

    try:
        itemDB.update_item_access_token("test_user_id", "item_123", "new_access_token_abc")
        assert False, "Expected Exception for database error during update_item_access_token"
    except Exception as e:
        mock_collection.update_one.assert_called_once_with(
            {"user_id": "test_user_id", "items.item_id": "item_123"},
            {"$set": {"items.$.access_token": "new_access_token_abc"}}
        )
        assert str(e) == "Database error"
        mock_logger.error.assert_called_with("Failed to update access token: %s", e)

# POSITIVE test for close method
def test_db_item_close():
    itemDB, mock_collection, _ = item_db_with_mocks()

    # Call close method
    itemDB.close()

    # Verify that collection.database.client.close was called
    mock_collection.database.client.close.assert_called_once()