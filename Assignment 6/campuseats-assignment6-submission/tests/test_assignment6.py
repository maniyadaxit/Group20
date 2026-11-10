"""
CampusEats Orders Service - Comprehensive Test Suite for Assignment 6
Tests status codes, problem details error shape, field-level 422 validations,
internal error shielding, content negotiation (XML/JSON), and A5 regressions.
"""
import pytest
import json
import xml.etree.ElementTree as ET
from app import app
from store import store

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_store():
    store._orders.clear()
    store._idempotency_cache.clear()
    store._seed_data()

# ------------------------------------------------------------------------------
# 1. HAPPY PATH (201 Created + Location + JSON Body)
# ------------------------------------------------------------------------------
def test_happy_path_201_create(client):
    payload = {
        "student_id": "student_20251651054",
        "vendor_id": "vendor_canteen_central",
        "items": [
            {"item_id": "item_thali", "name": "Special Thali", "quantity": 1, "unit_price": 90.0}
        ],
        "address": "Hostel 4 Ground Floor",
        "delivery_type": "DELIVERY",
        "coupon_code": "CAMPUS50"
    }
    resp = client.post(
        "/orders",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123"
        }
    )
    assert resp.status_code == 201
    assert "Location" in resp.headers
    assert resp.headers["Location"].startswith("/orders/")
    assert "charset=utf-8" in resp.headers["Content-Type"]
    
    data = resp.get_json()
    assert data["status"] == "PLACED"
    assert data["subtotal"] == 90.0
    assert data["final_amount"] == 70.0
    assert data["address"] == "Hostel 4 Ground Floor"

# ------------------------------------------------------------------------------
# 2. FIELD-LEVEL VALIDATION: TWO BAD FIELDS AT ONCE (Part B3, C2, Question 4)
# ------------------------------------------------------------------------------
def test_field_level_422_two_bad_fields(client):
    payload = {
        "student_id": "student_20251651054",
        "vendor_id": "vendor_canteen_central",
        # Bad Field 1: quantity <= 0 (qty = 0)
        "items": [
            {"item_id": "item_thali", "name": "Special Thali", "quantity": 0, "unit_price": 90.0}
        ],
        # Bad Field 2: address is blank/missing
        "address": ""
    }
    resp = client.post(
        "/orders",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123"
        }
    )
    assert resp.status_code == 422
    assert "application/problem+json" in resp.headers["Content-Type"]
    
    data = resp.get_json()
    assert data["status"] == 422
    assert data["title"] == "Unprocessable Entity"
    assert "errors" in data
    
    bad_fields = [err["field"] for err in data["errors"]]
    assert "items[0].quantity" in bad_fields
    assert "address" in bad_fields
    assert len(data["errors"]) >= 2

# ------------------------------------------------------------------------------
# 3. EMPTY CART FAILURE (Part B2: type catalogue 'empty-cart')
# ------------------------------------------------------------------------------
def test_empty_cart_failure(client):
    payload = {
        "student_id": "student_20251651054",
        "vendor_id": "vendor_canteen_central",
        "items": [],  # Empty cart!
        "address": "Hostel 4 Ground Floor"
    }
    resp = client.post(
        "/orders",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123"
        }
    )
    assert resp.status_code == 422
    data = resp.get_json()
    assert "empty-cart" in data["type"]
    assert any("empty cart" in err["message"].lower() for err in data["errors"])

# ------------------------------------------------------------------------------
# 4. UNKNOWN ID (Part B2: type catalogue 'order-not-found')
# ------------------------------------------------------------------------------
def test_unknown_id_404(client):
    resp = client.get("/orders/999999")
    assert resp.status_code == 404
    assert "application/problem+json" in resp.headers["Content-Type"]
    data = resp.get_json()
    assert "order-not-found" in data["type"]
    assert data["status"] == 404

# ------------------------------------------------------------------------------
# 5. ILLEGAL TRANSITION (Part B2: type catalogue 'illegal-transition')
# ------------------------------------------------------------------------------
def test_illegal_transition_409(client):
    # First cancel succeeds (200)
    resp1 = client.post(
        "/orders/42/cancel",
        headers={"Authorization": "Bearer token_valid_123"}
    )
    assert resp1.status_code == 200

    # Second cancel attempts illegal transition from already CANCELLED status -> 409
    resp2 = client.post(
        "/orders/42/cancel",
        headers={"Authorization": "Bearer token_valid_123"}
    )
    assert resp2.status_code == 409
    data = resp2.get_json()
    assert "illegal-transition" in data["type"]
    assert data["status"] == 409

# ------------------------------------------------------------------------------
# 6. RATE LIMIT & TRANSIENT RETRY (Part A4, B2: 429 & 503 with Retry-After)
# ------------------------------------------------------------------------------
def test_rate_limit_429_with_retry_after(client):
    resp = client.get("/orders/42", headers={"X-Simulate-Rate-Limit": "true"})
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == "60"
    data = resp.get_json()
    assert "rate-limit-exceeded" in data["type"]

def test_service_unavailable_503_with_retry_after(client):
    resp = client.get("/orders/42", headers={"X-Simulate-Downstream-Outage": "true"})
    assert resp.status_code == 503
    assert resp.headers.get("Retry-After") == "30"
    data = resp.get_json()
    assert "service-unavailable" in data["type"]

# ------------------------------------------------------------------------------
# 7. INTERNAL ERROR SHIELDING (Part B4 & Question 6)
# ------------------------------------------------------------------------------
def test_dont_leak_internals_500(client):
    resp = client.post(
        "/orders",
        data=json.dumps({"student_id": "s1"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123",
            "X-Simulate-DB-Failure": "true"
        }
    )
    assert resp.status_code == 500
    data = resp.get_json()
    assert "internal-error" in data["type"]
    assert "incident reference id" in data["detail"].lower()
    # Ensure NO database connection string or stack trace leaked to client
    assert "postgre" not in data["detail"].lower()
    assert "traceback" not in data["detail"].lower()

# ------------------------------------------------------------------------------
# 8. CONTENT NEGOTIATION (Part C3 & Question 7)
# ------------------------------------------------------------------------------
def test_content_negotiation_xml_and_json(client):
    # 1. JSON default read
    resp_json = client.get("/orders/42", headers={"Accept": "application/json"})
    assert resp_json.status_code == 200
    assert "application/json" in resp_json.headers["Content-Type"]
    json_body = resp_json.get_json()
    assert json_body["id"] == "42"

    # 2. XML read
    resp_xml = client.get("/orders/42", headers={"Accept": "application/xml"})
    assert resp_xml.status_code == 200
    assert "application/xml" in resp_xml.headers["Content-Type"]
    
    # Parse returned XML
    root = ET.fromstring(resp_xml.get_data(as_text=True))
    assert root.tag == "order"
    assert root.find("id").text == "42"
    assert root.find("student_id").text == "student_20251651054"

    # 3. 406 Not Acceptable on unsupported MIME
    resp_406 = client.get("/orders/42", headers={"Accept": "text/csv"})
    assert resp_406.status_code == 406
    data_406 = resp_406.get_json()
    assert "not-acceptable" in data_406["type"]

# ------------------------------------------------------------------------------
# 9. NO REGRESSIONS FROM A5 (Part D4)
# ------------------------------------------------------------------------------
def test_no_regressions_idempotency_and_conditional_headers(client):
    payload = {
        "student_id": "student_20251651040",
        "vendor_id": "vendor_canteen_central",
        "items": [
            {"item_id": "item_tea", "name": "Chai", "quantity": 1, "unit_price": 15.0}
        ],
        "address": "Hostel 3 Wing A"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer token_valid_123",
        "Idempotency-Key": "idemp_regression_key_001"
    }
    # Create
    r1 = client.post("/orders", data=json.dumps(payload), headers=headers)
    assert r1.status_code == 201

    # Idempotent repeat
    r2 = client.post("/orders", data=json.dumps(payload), headers=headers)
    assert r2.status_code == 201
    assert r2.headers["Location"] == r1.headers["Location"]

    # Conditional GET (304)
    r_get = client.get("/orders/42")
    etag = r_get.headers["ETag"]
    r_304 = client.get("/orders/42", headers={"If-None-Match": etag})
    assert r_304.status_code == 304

    # Conditional Write (412 on mismatch)
    r_412 = client.patch(
        "/orders/42",
        data=json.dumps({"time_slot": "16:00-16:30"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123",
            "If-Match": '"stale_etag"'
        }
    )
    assert r_412.status_code == 412

    # PATCH success on match (200)
    r_patch = client.patch(
        "/orders/42",
        data=json.dumps({"time_slot": "16:00-16:30"}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer token_valid_123",
            "If-Match": etag
        }
    )
    assert r_patch.status_code == 200

    # Delete (204)
    r_del = client.delete("/orders/101", headers={"Authorization": "Bearer token_valid_123"})
    assert r_del.status_code == 204
