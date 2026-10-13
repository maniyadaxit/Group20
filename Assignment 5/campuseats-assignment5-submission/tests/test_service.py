"""
CampusEats Orders Service - Comprehensive Test Suite
Validates all Assignment 5 HTTP Methods & Headers requirements.
"""
import pytest
import json
from app import app
from store import store

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_store():
    # Reset seed data before each test
    store._orders.clear()
    store._idempotency_cache.clear()
    store._seed_data()

# ------------------------------------------------------------------------------
# 1. CREATE & LOCATION HEADER (Part A1, B2)
# ------------------------------------------------------------------------------
def test_create_order_201_and_location(client):
    payload = {
        "student_id": "student_20251651054",
        "vendor_id": "vendor_canteen_central",
        "items": [
            {"item_id": "item_samosa", "name": "Hot Samosa", "quantity": 2, "unit_price": 20.0}
        ],
        "delivery_type": "PICKUP",
        "payment_method": "WALLET"
    }
    response = client.post(
        "/orders",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer valid_token_123"
        }
    )
    assert response.status_code == 201
    assert "Location" in response.headers
    assert response.headers["Location"].startswith("/orders/")
    assert "ETag" in response.headers
    assert response.headers["Content-Type"] == "application/json"
    
    data = response.get_json()
    assert data["status"] == "PLACED"
    assert data["subtotal"] == 40.0
    assert data["final_amount"] == 40.0

# ------------------------------------------------------------------------------
# 2. IDEMPOTENT REPEAT (Part C3)
# ------------------------------------------------------------------------------
def test_idempotent_create_repeat(client):
    payload = {
        "student_id": "student_20251651040",
        "vendor_id": "vendor_canteen_central",
        "items": [
            {"item_id": "item_chai", "name": "Special Tea", "quantity": 1, "unit_price": 15.0}
        ],
        "delivery_type": "PICKUP"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer token_xyz",
        "Idempotency-Key": "idemp_key_req_001"
    }

    # Initial request
    resp1 = client.post("/orders", data=json.dumps(payload), headers=headers)
    assert resp1.status_code == 201
    loc1 = resp1.headers["Location"]
    data1 = resp1.get_json()

    # Re-send same request with same Idempotency-Key
    resp2 = client.post("/orders", data=json.dumps(payload), headers=headers)
    assert resp2.status_code == 201
    assert resp2.headers["Location"] == loc1
    data2 = resp2.get_json()
    assert data2["id"] == data1["id"]
    assert data2["created_at"] == data1["created_at"]

# ------------------------------------------------------------------------------
# 3. CONDITIONAL GET -> 304 NOT MODIFIED (Part B4, C1)
# ------------------------------------------------------------------------------
def test_conditional_get_304(client):
    # Step 1: Read order 42 and extract ETag
    resp1 = client.get("/orders/42")
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert "Cache-Control" in resp1.headers

    # Step 2: Send conditional GET with If-None-Match matching the ETag
    resp2 = client.get("/orders/42", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    assert len(resp2.get_data()) == 0  # 304 MUST NOT have body
    assert resp2.headers.get("ETag") == etag

# ------------------------------------------------------------------------------
# 4. CONDITIONAL WRITE -> 412 PRECONDITION FAILED (Part C2)
# ------------------------------------------------------------------------------
def test_conditional_write_412_and_success(client):
    # Get current ETag for order 42
    resp1 = client.get("/orders/42")
    current_etag = resp1.headers["ETag"]

    # Attempt write with mismatched ETag -> 412 Precondition Failed
    mismatched_etag = '"stale_hash_9999"'
    resp_failed = client.put(
        "/orders/42",
        data=json.dumps({"time_slot": "14:30-15:00"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_abc",
            "If-Match": mismatched_etag
        }
    )
    assert resp_failed.status_code == 412
    err_body = resp_failed.get_json()
    assert err_body["title"] == "Precondition Failed"

    # Attempt write with correct matching ETag -> 200 OK
    resp_success = client.put(
        "/orders/42",
        data=json.dumps({"time_slot": "14:30-15:00"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_abc",
            "If-Match": current_etag
        }
    )
    assert resp_success.status_code == 200
    new_data = resp_success.get_json()
    assert new_data["time_slot"] == "14:30-15:00"
    assert resp_success.headers["ETag"] != current_etag  # ETag changed!

# ------------------------------------------------------------------------------
# 5. FAILURE PATHS: 400, 401, 404, 422, 406, 409 (Part B1, B2, B3)
# ------------------------------------------------------------------------------
def test_failure_400_malformed_json(client):
    # Syntax error in JSON body
    resp = client.post(
        "/orders",
        data='{"student_id": "s1", "vendor_id": "v1", items: [unquoted]}',
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_123"
        }
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["status"] == 400
    assert "Malformed JSON" in body["detail"]

def test_failure_401_unauthorized(client):
    # Missing Authorization header
    resp = client.post(
        "/orders",
        data=json.dumps({"student_id": "s1"}),
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers
    body = resp.get_json()
    assert body["status"] == 401

def test_failure_404_not_found(client):
    resp = client.get("/orders/nonexistent_999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["status"] == 404

def test_failure_422_domain_refusal(client):
    # Valid JSON syntax, but empty items list violates business domain rule
    payload = {
        "student_id": "student_01",
        "vendor_id": "vendor_01",
        "items": []  # Domain rule refusal
    }
    resp = client.post(
        "/orders",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_123"
        }
    )
    assert resp.status_code == 422
    body = resp.get_json()
    assert body["status"] == 422
    assert "at least one menu item" in body["detail"]

def test_failure_406_not_acceptable(client):
    # Demands XML which server does not produce
    resp = client.get("/orders/42", headers={"Accept": "application/xml"})
    assert resp.status_code == 406
    body = resp.get_json()
    assert body["status"] == 406

def test_failure_409_conflict(client):
    # Cancel order 42 first time -> 200
    resp1 = client.post(
        "/orders/42/cancel",
        headers={"Authorization": "Bearer token_123"}
    )
    assert resp1.status_code == 200

    # Cancel order 42 second time -> 409 Conflict
    resp2 = client.post(
        "/orders/42/cancel",
        headers={"Authorization": "Bearer token_123"}
    )
    assert resp2.status_code == 409
    body = resp2.get_json()
    assert body["status"] == 409
    assert "already cancelled" in body["detail"]

# ------------------------------------------------------------------------------
# 6. OPTIONS & X-HTTP-METHOD-OVERRIDE (Part A5)
# ------------------------------------------------------------------------------
def test_options_resource(client):
    resp = client.open("/orders/42", method="OPTIONS")
    assert resp.status_code in (200, 204)
    assert "Allow" in resp.headers
    allow = resp.headers["Allow"]
    assert "GET" in allow and "PUT" in allow and "DELETE" in allow

def test_method_override_post_to_put(client):
    resp = client.post(
        "/orders/42",
        data=json.dumps({"time_slot": "15:00-15:30"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_123",
            "X-HTTP-Method-Override": "PUT"
        }
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["time_slot"] == "15:00-15:30"

# ------------------------------------------------------------------------------
# 7. RATE LIMITING & SECURITY HEADERS (Part B5, B7)
# ------------------------------------------------------------------------------
def test_headers_and_rate_limiting(client):
    resp = client.get("/orders/42")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Strict-Transport-Security" in resp.headers
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers

    # Simulate 429 quota exhaustion
    resp_429 = client.get("/orders/42", headers={"X-Simulate-Rate-Limit": "true"})
    assert resp_429.status_code == 429
    assert resp_429.headers.get("Retry-After") == "60"
    assert resp_429.headers.get("X-RateLimit-Remaining") == "0"

# ------------------------------------------------------------------------------
# 8. DELETE ORDER 204 (Part A1, B2)
# ------------------------------------------------------------------------------
def test_delete_order_204(client):
    resp = client.delete(
        "/orders/101",
        headers={"Authorization": "Bearer token_123"}
    )
    assert resp.status_code == 204
    assert len(resp.get_data()) == 0

    # Verify deleted
    resp_get = client.get("/orders/101")
    assert resp_get.status_code == 404
