from src.helpers.sessions import SessionManager

from unittest.mock import MagicMock, patch
import logging
import base64
import time

def session_manager_with_mocks() -> SessionManager:
    mock_logger = MagicMock(spec=logging.Logger)

    session_manager = SessionManager.__new__(SessionManager)
    session_manager.sessions = set()
    session_manager.session_duration = 3600
    session_manager.secret_key = "test_secret_key"
    session_manager.cleanup_interval = 600
    session_manager.header_b64 = "test_header_b64"
    session_manager.alg = "SHA1"
    session_manager.logger = mock_logger

    return session_manager, mock_logger

def test_session_manager_init():
    # Setup mocks
    mock_logger = MagicMock(spec=logging.Logger)

    # Patch the Env import
    with patch("src.helpers.sessions.Env") as mock_env:
        mock_env.return_value = {'session': 
            {
                'DURATION_SECONDS': 3600,
                'SECRET_KEY': 'test_secret_key',
                'CLEANUP_INTERVAL_SECONDS': 600,
                'HEADER': {'algorithm': 'HS256'}
            }
        }
        # Initialize SessionManager
        session_manager = SessionManager(env="test", logger=mock_logger)

        # Verify initialization
        assert session_manager.session_duration == 3600
        assert session_manager.secret_key == "test_secret_key"
        assert session_manager.cleanup_interval == 600
        assert session_manager.header_b64 == base64.urlsafe_b64encode(bytes(str({'algorithm': 'HS256'}), encoding='utf-8')).rstrip(b'=').decode()
        assert session_manager.alg == "HS256"
        mock_logger.info.assert_called_with("SessionManager initialized")

# POSTIVE test for create
def test_create_session_positive():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "user123"

    session_token = session_manager.create(user_id)

    assert session_token in session_manager.sessions
    assert isinstance(session_token, str)
    mock_logger.info.assert_not_called()  # No info logs in create

# POSITIVE tests for validate
def test_validate_session_positive_valid_token():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "user123"

    session_token = session_manager.create(user_id)

    validated_user_id = session_manager.validate(session_token)

    assert validated_user_id == user_id
    mock_logger.info.assert_called_with("Valid session token")

def test_validate_session_positive_expired_token():
    session_manager, mock_logger = session_manager_with_mocks()
    session_manager.session_duration = 1 # Set short duration for testing
    user_id = "user123"

    session_token = session_manager.create(user_id)

    time.sleep(2) # wait for token to expire

    try:
        session_manager.validate(session_token)
        assert False, "Expected ValueError for expired token"
    except ValueError as e:
        assert str(e) == "Session token has expired"
        mock_logger.error.assert_called_with("Session token has expired")

# NEGATIVE test for validate
def test_validate_session_negative_invalid_format():
    session_manager, mock_logger = session_manager_with_mocks()
    invalid_token = "header.payload" # missing signature

    try:
        session_manager.validate(invalid_token)
        assert False, "Expected ValueError for invalid token format"
    except ValueError as e:
        assert str(e) == "Invalid session token format"
        mock_logger.error.assert_called_with("Invalid session token format")

def test_validate_session_negative_invalid_signature():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "user123"

    session_token = session_manager.create(user_id)
    # Tamper with the token to invalidate the signature
    tampered_token = session_token.split('.')
    tampered_token[2] = "invalidsignature"
    tampered_token = '.'.join(tampered_token)

    try:
        session_manager.validate(tampered_token)
        assert False, "Expected ValueError for invalid token signature"
    except ValueError as e:
        assert str(e) == "Invalid session token signature"
        mock_logger.error.assert_called_with("Invalid session token signature")

# POSITIVE test for invalidate
def test_invalidate_session_positive():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "user123"

    session_token = session_manager.create(user_id)
    assert session_token in session_manager.sessions

    session_manager.invalidate(session_token)
    assert session_token not in session_manager.sessions
    mock_logger.debug.assert_called_with("Invalidating specified session token")

# NEGATIVE test for invalidate
def test_invalidate_session_negative_nonexistent_token():
    session_manager, mock_logger = session_manager_with_mocks()
    non_existent_token = "nonexistent.token.signature"

    try:
        session_manager.invalidate(non_existent_token)
        assert True
        mock_logger.debug.assert_called_with("Invalidating specified session token")
    except Exception as e:
        assert False, f"Expected no exception for invalidating non-existent token, but got: {e}"

# # POSITIVE test for cleanup
# def test_cleanup_sessions_positive():
#     session_manager, mock_logger = session_manager_with_mocks()
#     session_manager.session_duration = 1 # Set short duration for testing
#     user_id = "user123"

#     first_token = session_manager.create(user_id)
#     assert first_token in session_manager.sessions
    
#     second_token = session_manager.create(user_id + "4")
#     assert second_token in session_manager.sessions

#     time.sleep(2) # wait for tokens to expire

#     session_manager.cleanup()

#     assert first_token not in session_manager.sessions
#     assert second_token not in session_manager.sessions
#     mock_logger.info.assert_called_with("Cleaning up 2 expired sessions")

# def test_cleanup_sessions_positive_some_valid():
#     session_manager, mock_logger = session_manager_with_mocks()
#     session_manager.session_duration = 1 # Set short duration for testing
#     user_id = "user123"

#     first_token = session_manager.create(user_id)
#     assert first_token in session_manager.sessions

#     time.sleep(2) # wait for first token to expire

#     second_token = session_manager.create(user_id + "4")
#     assert second_token in session_manager.sessions

#     session_manager.cleanup()

#     assert first_token not in session_manager.sessions
#     assert second_token in session_manager.sessions
#     mock_logger.info.assert_called_with("Cleaning up 1 expired sessions")