from src.helpers.sessions import SessionManager

from unittest.mock import MagicMock, patch
import logging
import base64
import time
import hmac
import hashlib
import json

def session_manager_with_mocks() -> SessionManager:
    mock_logger = MagicMock(spec=logging.Logger)

    session_manager = SessionManager.__new__(SessionManager)
    session_manager.deactivated_sessions = set()
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

    assert isinstance(session_token, str)
    # token should validate and return the original user id
    validated = session_manager.validate(session_token)
    assert validated == user_id
    mock_logger.error.assert_not_called()

# POSITIVE tests for validate
def test_validate_session_positive_valid_token():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "user123"

    session_token = session_manager.create(user_id)

    validated_user_id = session_manager.validate(session_token)

    assert validated_user_id == user_id
    mock_logger.error.assert_not_called()

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
        assert session_token in session_manager.deactivated_sessions

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
    # invalidate should add the token to `deactivated_sessions`
    session_manager.invalidate(session_token)
    assert session_token in session_manager.deactivated_sessions
    mock_logger.debug.assert_called_with("Invalidating specified session token")

# NEGATIVE test for invalidate
def test_invalidate_session_negative_nonexistent_token():
    session_manager, mock_logger = session_manager_with_mocks()
    non_existent_token = "nonexistent.token.signature"

    try:
        # invalidating a token that was never issued should still add it
        session_manager.invalidate(non_existent_token)
        assert non_existent_token in session_manager.deactivated_sessions
        mock_logger.debug.assert_called_with("Invalidating specified session token")
    except Exception as e:
        assert False, f"Expected no exception for invalidating non-existent token, but got: {e}"

def test_sessions_create_payload_fields():
    session_manager, mock_logger = session_manager_with_mocks()
    session_manager.session_duration = 120
    user_id = "u-create-payload"

    payload_b64 = session_manager.create_payload(user_id)
    payload_str = base64.urlsafe_b64decode(payload_b64 + '==').decode().replace("'", '"')
    payload = json.loads(payload_str)

    assert payload['id'] == user_id
    assert 'iat' in payload and 'exp' in payload
    assert payload['exp'] - payload['iat'] == session_manager.session_duration


def test_sessions_validate_deactivated_token():
    session_manager, mock_logger = session_manager_with_mocks()
    user_id = "u-deactivated"

    token = session_manager.create(user_id)
    session_manager.deactivated_sessions.add(token)

    try:
        session_manager.validate(token)
        assert False, "Expected ValueError for deactivated token"
    except ValueError as e:
        assert str(e) == "Session token has been deactivated"
        mock_logger.error.assert_called_with("Session token has been deactivated")


def test_sessions_validate_malformed_payload_logs_and_raises():
    session_manager, mock_logger = session_manager_with_mocks()
    # craft a payload that's not valid JSON but with a correct signature
    bad_payload = b"not-json-payload"
    payload_b64 = base64.urlsafe_b64encode(bad_payload).rstrip(b'=').decode()
    header_b64 = session_manager.header_b64

    expected_sig = hmac.new(session_manager.secret_key.encode(), f"{header_b64}.{payload_b64}".encode(), getattr(hashlib, session_manager.alg.lower())).hexdigest()
    signature_b64 = base64.urlsafe_b64encode(bytes(expected_sig, encoding='utf-8')).rstrip(b'=').decode()

    malformed_token = f"{header_b64}.{payload_b64}.{signature_b64}"

    try:
        session_manager.validate(malformed_token)
        assert False, "Expected ValueError for invalid session token payload"
    except ValueError as e:
        assert str(e) == "Invalid session token payload"
        mock_logger.error.assert_called_with("Invalid session token payload")


def test_sessions_cleanup_removes_expired_deactivated_sessions():
    session_manager, mock_logger = session_manager_with_mocks()
    # create one short-lived and one long-lived token
    session_manager.session_duration = 1
    t1 = session_manager.create("a")

    session_manager.session_duration = 3600
    t2 = session_manager.create("b")

    # mark both as deactivated
    session_manager.deactivated_sessions.add(t1)
    session_manager.deactivated_sessions.add(t2)

    time.sleep(2)

    session_manager.cleanup()

    assert t1 not in session_manager.deactivated_sessions
    assert t2 in session_manager.deactivated_sessions
    mock_logger.debug.assert_called_with("Cleaning up 1 expired deactivated sessions")