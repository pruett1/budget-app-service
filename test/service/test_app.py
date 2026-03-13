import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
import src.app as app_module
from src.app import app, lifespan


@pytest.fixture(autouse=True)
def patch_resources(monkeypatch):
    class DummyLogger:
        def info(self, *a, **k):
            pass
        def debug(self, *a, **k):
            pass

    monkeypatch.setattr(app_module, "config_logger", lambda *a, **k: None)
    monkeypatch.setattr(app_module, "get_struct_logger", lambda *a, **k: DummyLogger())

    mock_account_db = MagicMock()
    mock_item_db = MagicMock()
    mock_plaid = MagicMock()
    mock_plaid.close = AsyncMock()
    mock_session_manager = MagicMock()

    # We don't patch constructors here; tests use explicit `app.state` values.
    # ensure the imported app has the expected state even if lifespan isn't run
    app.state.logger = DummyLogger()
    app.state.sessionManager = mock_session_manager
    app.state.accountDB = mock_account_db
    app.state.itemDB = mock_item_db
    app.state.plaid = mock_plaid

    yield {
        "account": mock_account_db,
        "item": mock_item_db,
        "plaid": mock_plaid,
        "session": mock_session_manager,
    }


def test_app_ping():
    client = TestClient(app)
    valid_uuid = str(uuid.uuid4())
    response = client.get("/ping", headers={"request-id": valid_uuid})
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


def test_app_middleware_missing_header_returns_400():
    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 400
    assert response.json() == {"error": "Missing request-id header"}


def test_app_middleware_invalid_uuid_returns_400():
    client = TestClient(app)
    response = client.get("/ping", headers={"request-id": "not-a-uuid"})
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid request-id header (must be UUIDv4)"}


def test_app_middleware_valid_uuid_echoes_header():
    client = TestClient(app)
    rid = str(uuid.uuid4())
    response = client.get("/ping", headers={"request-id": rid})
    assert response.status_code == 200
    assert response.headers.get("request-id") == rid


def test_app_middleware_invalid_authorization_scheme_returns_400():
    client = TestClient(app)
    rid = str(uuid.uuid4())
    # send Authorization with wrong scheme
    response = client.get("/ping", headers={"request-id": rid, "Authorization": "Token abc"})
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid Authorization header scheme (must be Bearer)"}


def test_app_middleware_invalid_token_returns_401():
    client = TestClient(app)
    rid = str(uuid.uuid4())
    # make session manager validate raise an exception to simulate invalid token
    client.app.state.sessionManager.validate.side_effect = Exception("bad token")

    response = client.get("/ping", headers={"request-id": rid, "Authorization": "Bearer badtoken"})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_app_middleware_valid_bearer_sets_user_and_echoes_request_id():
    client = TestClient(app)
    rid = str(uuid.uuid4())
    # session manager validate should return a user id
    client.app.state.sessionManager.validate.return_value = "user-123"

    response = client.get("/ping", headers={"request-id": rid, "Authorization": "Bearer goodtoken"})
    assert response.status_code == 200
    assert response.headers.get("request-id") == rid


@pytest.mark.asyncio
async def test_app_lifespan_sets_and_closes_resources(monkeypatch):
    # create lightweight mocks for resources and logger
    class DummyLogger:
        def info(self, *a, **k):
            pass
        def debug(self, *a, **k):
            pass
    # reuse MagicMock / AsyncMock pattern from fixture
    mock_account_db = MagicMock()
    mock_item_db = MagicMock()
    mock_plaid = MagicMock()
    mock_plaid.close = AsyncMock()
    mock_session_manager = MagicMock()

    monkeypatch.setattr(app_module, "config_logger", lambda *a, **k: None)
    monkeypatch.setattr(app_module, "get_struct_logger", lambda *a, **k: DummyLogger())
    monkeypatch.setattr(app_module, "AccountDB", lambda env, logger: mock_account_db)
    monkeypatch.setattr(app_module, "ItemDB", lambda env, logger: mock_item_db)
    monkeypatch.setattr(app_module, "Plaid", lambda env, logger: mock_plaid)
    monkeypatch.setattr(app_module, "SessionManager", lambda env, logger: mock_session_manager)

    test_app = SimpleNamespace()
    test_app.state = SimpleNamespace()

    async with lifespan(test_app):
        assert test_app.state.sessionManager is mock_session_manager
        assert test_app.state.accountDB is mock_account_db
        assert test_app.state.itemDB is mock_item_db
        assert test_app.state.plaid is mock_plaid

    # after context exit resources should be closed/awaited
    mock_account_db.close.assert_called()
    mock_item_db.close.assert_called()
    mock_plaid.close.assert_awaited()