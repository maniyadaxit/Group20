import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import app as app_module
from store import store as global_store


@pytest.fixture(autouse=True)
def reset_store():
    global_store._orders.clear()
    global_store._idempotency.clear()
    global_store._next_id = 1
    yield


@pytest.fixture
def client(monkeypatch):
    def fake_initiate_payment(order_id, amount, method, idempotency_key, **kwargs):
        return {"paymentId": "PAY-TEST", "status": "SUCCESS", "amount": amount}

    monkeypatch.setattr(app_module, "initiate_payment", fake_initiate_payment)
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def sample_body():
    return {
        "studentId": "stu-1",
        "vendorId": "ven-1",
        "items": [{"menuItemId": "item-1", "quantity": 2}],
        "deliveryType": "PICKUP",
        "paymentMethod": "WALLET",
    }


def test_create_order_succeeds(client):
    resp = client.post("/orders", json=sample_body())
    assert resp.status_code == 201
    assert "Location" in resp.headers
    body = resp.get_json()
    assert body["status"] == "PLACED"
    assert body["totalAmount"] == 240.0


def test_create_order_idempotent_repeat_returns_original(client):
    headers = {"Idempotency-Key": "key-123"}
    first = client.post("/orders", json=sample_body(), headers=headers)
    second = client.post("/orders", json=sample_body(), headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.get_json()["orderId"] == second.get_json()["orderId"]


def test_create_order_malformed_body_returns_400(client):
    bad_body = {"studentId": "stu-1"}  # missing required fields
    resp = client.post("/orders", json=bad_body)
    assert resp.status_code == 400
    problem = resp.get_json()
    assert problem["status"] == 400
    assert "title" in problem and "detail" in problem


def test_get_unknown_order_returns_404(client):
    resp = client.get("/orders/ORD-99999")
    assert resp.status_code == 404
    problem = resp.get_json()
    assert problem["status"] == 404
