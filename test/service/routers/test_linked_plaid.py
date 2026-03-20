import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture(autouse=True)
def patch_resources(monkeypatch):
    mock_item_db = MagicMock()
    mock_plaid = MagicMock()
    mock_plaid.items = MagicMock()
    mock_plaid.items.exchange_public_token = AsyncMock()
    mock_plaid.items.get = AsyncMock()
    mock_plaid.items.remove = AsyncMock()
    mock_plaid.items.invalidate_access_token = AsyncMock()

    mock_logger = MagicMock()

    monkeypatch.setattr("src.helpers.dependencies.get_item_db", lambda request=None: mock_item_db)
    monkeypatch.setattr("src.helpers.dependencies.get_plaid_client", lambda request=None: mock_plaid)
    monkeypatch.setattr("src.helpers.dependencies.get_logger", lambda request=None: mock_logger)
    monkeypatch.setattr("src.helpers.dependencies.require_user", lambda: "user-123")

    app.state.logger = mock_logger
    app.state.sessionManager = MagicMock()
    app.state.sessionManager.validate.return_value = "user-123"
    app.state.accountDB = MagicMock()
    app.state.itemDB = mock_item_db
    app.state.plaid = mock_plaid

    yield {"item": mock_item_db, "plaid": mock_plaid, "logger": mock_logger}


def _hdr():
    return {"request-id": str(uuid.uuid4()), "Authorization": "Bearer goodtoken"}


def test_exchange_public_token_success(patch_resources):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_plaid.items.exchange_public_token.return_value = ("access_tok", "item_1")
    mock_plaid.items.get.return_value = {
        "item": {
            "products": ["auth"],
            "consented_products": ["auth"],
            "created_at": "2020-01-01",
            "institution_name": "Bank"
        }
    }

    client = TestClient(app)
    res = client.post("/plaid/exchange_public_token", json={"public_token": "pt-1"}, headers=_hdr())

    assert res.status_code == 204
    mock_item_db.append_item.assert_called_once()


def test_exchange_public_token_item_exists(patch_resources):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_plaid.items.exchange_public_token.return_value = ("access_tok", "item_1")
    mock_plaid.items.get.return_value = {"item": {}}
    mock_item_db.append_item.side_effect = ValueError("exists")

    client = TestClient(app)
    res = client.post("/plaid/exchange_public_token", json={"public_token": "pt-1"}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Item already exists for user"}


def test_exchange_public_token_plaid_failure(patch_resources):
    mock_plaid = patch_resources["plaid"]
    mock_plaid.items.exchange_public_token.side_effect = Exception("plaid")

    client = TestClient(app)
    res = client.post("/plaid/exchange_public_token", json={"public_token": "pt-1"}, headers=_hdr())

    assert res.status_code == 500
    assert res.json() == {"error": "Failed to exchange public token"}


def test_get_linked_accounts_no_items(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_items.return_value = []

    client = TestClient(app)
    res = client.get("/plaid/accounts/get", headers=_hdr())

    assert res.status_code == 204
    assert res.content == b""


def test_get_linked_accounts_with_items(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_items.return_value = [
        {"item_id": "i1", "item_data": {"k": "v"}},
        {"item_id": "i2", "item_data": {"k2": "v2"}}
    ]

    client = TestClient(app)
    res = client.get("/plaid/accounts/get", headers=_hdr())

    assert res.status_code == 200
    assert res.json() == [{"k": "v", "id": "i1"}, {"k2": "v2", "id": "i2"}]


def test_delete_linked_account_success(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.remove.return_value = None

    client = TestClient(app)
    res = client.put("/plaid/accounts/delete", json={"item_id": "i1", "reason": {"code": "r", "note": ""}}, headers=_hdr())

    assert res.status_code == 204
    mock_plaid.items.remove.assert_called_once()
    mock_item_db.remove_item.assert_called_once_with("user-123", "i1")


def test_delete_linked_account_missing_item(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_item.side_effect = Exception("no item")

    client = TestClient(app)
    res = client.put("/plaid/accounts/delete", json={"item_id": "i1", "reason": {"code": "r", "note": ""}}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Could not find item_id for user"}


def test_delete_linked_account_plaid_remove_fails(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.remove.side_effect = Exception("fail")

    client = TestClient(app)
    res = client.put("/plaid/accounts/delete", json={"item_id": "i1", "reason": {"code": "r", "note": ""}}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Plaid failed to delete item from user"}


def test_delete_linked_account_db_remove_fails(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.remove.return_value = None
    mock_item_db.remove_item.side_effect = Exception("db fail")

    client = TestClient(app)
    res = client.put("/plaid/accounts/delete", json={"item_id": "i1", "reason": {"code": "r", "note": ""}}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Failed to delete item from user"}


def test_update_account_cycle_success(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.invalidate_access_token.return_value = "new_tok"

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1"}, headers=_hdr())

    assert res.status_code == 204
    mock_plaid.items.invalidate_access_token.assert_called_once()
    mock_item_db.update_item_field.assert_called()


def test_update_account_cycle_missing_item(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_item.side_effect = Exception("no item")

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1"}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Could not find item_id for user"}


def test_update_account_cycle_invalidate_fails(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.invalidate_access_token.side_effect = Exception("fail")

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1"}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Failed to invalidate access token"}


def test_update_account_cycle_db_update_fails(patch_resources, monkeypatch):
    mocks = patch_resources
    mock_item_db = mocks["item"]
    mock_plaid = mocks["plaid"]

    mock_item_db.get_item.return_value = {"access_token": "enc_tok"}
    monkeypatch.setattr("src.routers.linked_plaid.decrypt", lambda x: x)
    mock_plaid.items.invalidate_access_token.return_value = "new_tok"
    mock_item_db.update_item_field.side_effect = Exception("db fail")

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1"}, headers=_hdr())

    assert res.status_code == 500
    assert res.json() == {"error": "Failed to update access token in item db"}


def test_update_account_item_data_success(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_item.return_value = {"item_data": {"k": "v"}}

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1", "item_data": {"new": "val"}}, headers=_hdr())

    assert res.status_code == 204
    mock_item_db.update_item_field.assert_called_once()


def test_update_account_item_data_missing_item(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_item.side_effect = Exception("no item")

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1", "item_data": {"new": "val"}}, headers=_hdr())

    assert res.status_code == 400
    assert res.json() == {"error": "Could not find item_id for user"}


def test_update_account_item_data_db_update_fails(patch_resources):
    mock_item_db = patch_resources["item"]
    mock_item_db.get_item.return_value = {"item_data": {"k": "v"}}
    mock_item_db.update_item_field.side_effect = Exception("db fail")

    client = TestClient(app)
    res = client.put("/plaid/accounts/update", json={"item_id": "i1", "item_data": {"new": "val"}}, headers=_hdr())

    assert res.status_code == 500
    assert res.json() == {"error": "Failed to update access token in item db"}
