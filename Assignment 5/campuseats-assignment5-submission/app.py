"""
CampusEats Orders Service - Production REST Application
CS543 · Web Services · Assignment 5: HTTP Methods & Headers
"""
import uuid
import time
import gzip
from datetime import datetime, timezone
from flask import Flask, request, jsonify, make_response, Response
from werkzeug.exceptions import BadRequest

from models import Order
from store import store
from errors import problem

app = Flask(__name__)

# In-memory per-client rate limit tracking (IP-based)
RATE_LIMIT_MAX = 100
CLIENT_REQUEST_COUNTS = {}

# ------------------------------------------------------------------------------
# MIDDLEWARE: Method Override, Content Negotiation, Rate Limiting & Security
# ------------------------------------------------------------------------------

# Custom WSGI middleware for X-HTTP-Method-Override (Part A5)
class MethodRewriteMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        override = environ.get("HTTP_X_HTTP_METHOD_OVERRIDE")
        if override and environ.get("REQUEST_METHOD") == "POST":
            upper_override = override.strip().upper()
            if upper_override in {"GET", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                environ["REQUEST_METHOD"] = upper_override
        return self.wsgi_app(environ, start_response)

app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

@app.before_request
def handle_content_negotiation():
    """
    Part B1: Honour Accept header. Return 406 Not Acceptable if client requests
    an unsupported MIME type that does not accept application/json or */*.
    """
    if request.method == "OPTIONS":
        return None  # Let OPTIONS preflight pass

    accept = request.headers.get("Accept")
    if accept:
        acceptable = False
        for part in accept.split(","):
            part_clean = part.split(";")[0].strip().lower()
            if part_clean in ("application/json", "*/*", "application/*", "text/plain"):
                acceptable = True
                break
        if not acceptable:
            return problem(
                status=406,
                detail=f"Cannot produce requested format '{accept}'. Only 'application/json' is supported."
            )

@app.before_request
def handle_rate_limiting():
    """
    Part B5: Per-client rate limit tracking.
    Return 429 Too Many Requests with Retry-After when budget is exceeded.
    """
    if request.headers.get("X-Simulate-Rate-Limit") == "true":
        resp = problem(
            status=429,
            detail="Rate limit exceeded. Your client request quota of 100 requests per minute has been exhausted."
        )
        resp.headers["Retry-After"] = "60"
        resp.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
        resp.headers["X-RateLimit-Remaining"] = "0"
        return resp

    client_id = request.headers.get("Authorization") or request.remote_addr or "client-default"
    current_count = CLIENT_REQUEST_COUNTS.get(client_id, 0) + 1
    CLIENT_REQUEST_COUNTS[client_id] = current_count

    if current_count > RATE_LIMIT_MAX:
        resp = problem(
            status=429,
            detail="Rate limit exceeded. Your client request quota has been exhausted."
        )
        resp.headers["Retry-After"] = "60"
        resp.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
        resp.headers["X-RateLimit-Remaining"] = "0"
        return resp

@app.after_request
def apply_common_headers(response: Response):
    """
    Part B5, B6, B7:
    - Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
    - CORS (Access-Control-Allow-Origin, etc.)
    - Security headers (X-Content-Type-Options: nosniff, Strict-Transport-Security)
    - Server and Date
    - Optional gzip compression for large JSON payloads
    """
    if response.status_code == 429:
        response.headers["X-RateLimit-Remaining"] = "0"
    else:
        client_id = request.headers.get("Authorization") or request.remote_addr or "client-default"
        count = CLIENT_REQUEST_COUNTS.get(client_id, 1)
        remaining = max(0, RATE_LIMIT_MAX - count)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)

    # 2. CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, If-Match, If-None-Match, Idempotency-Key, X-HTTP-Method-Override, X-Simulate-Rate-Limit"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"

    # 3. Security headers (B7)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "CampusEats-Orders/1.0 (REST/HTTP)"

    # 4. Content-Type on bodies (B1)
    if response.status_code != 304 and response.status_code != 204:
        if not response.headers.get("Content-Type"):
            response.headers["Content-Type"] = "application/json"

    # 5. Gzip compression if requested and body is sizable (B1)
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if "gzip" in accept_encoding and len(response.get_data()) > 500 and not response.headers.get("Content-Encoding"):
        gzipped_data = gzip.compress(response.get_data())
        response.set_data(gzipped_data)
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Content-Length"] = str(len(gzipped_data))

    return response

# ------------------------------------------------------------------------------
# AUTHENTICATION HELPER
# ------------------------------------------------------------------------------

def require_auth():
    """
    Part B3: Protected endpoints require Authorization: Bearer <token>.
    Missing or empty token -> 401 Unauthorized with WWW-Authenticate header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        resp = problem(status=401, detail="Missing required Authorization header. Expected 'Authorization: Bearer <token>'")
        resp.headers["WWW-Authenticate"] = 'Bearer realm="CampusEats", error="missing_token"'
        return resp
    
    parts = auth_header.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        resp = problem(status=401, detail="Invalid Authorization header format. Expected 'Bearer <non-empty-token>'")
        resp.headers["WWW-Authenticate"] = 'Bearer realm="CampusEats", error="invalid_token"'
        return resp

    return None

# ------------------------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------------------------

@app.route("/orders", methods=["GET"])
def list_orders():
    """
    Part A4: Filter, sort, and paginate through query string.
    Pure read: safe & idempotent GET.
    """
    status_filter = request.args.get("status")
    student_id = request.args.get("student_id")
    vendor_id = request.args.get("vendor_id")
    sort_by = request.args.get("sort", "created_at")
    order_dir = request.args.get("order", "desc")
    
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return problem(status=400, detail="Query parameters 'page' and 'limit' must be valid integers.")

    items, total_count = store.list_orders(
        student_id=student_id,
        vendor_id=vendor_id,
        status=status_filter,
        sort_by=sort_by,
        order=order_dir,
        page=page,
        limit=limit
    )

    response = jsonify({
        "items": items,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "has_more": (page * limit) < total_count
    })
    response.status_code = 200
    return response


@app.route("/orders", methods=["POST"])
def create_order():
    """
    Part A1, B2, C3:
    - Create an order -> 201 Created with Location header.
    - Validate body (400 for malformed, 422 for domain refusal).
    - Support Idempotency-Key: repeated calls return original result with no duplicate work.
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    # Check Idempotency-Key (C3)
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached = store.get_idempotency_record(idempotency_key)
        if cached:
            resp = jsonify(cached["body"])
            resp.status_code = cached["status_code"]
            resp.headers["Location"] = cached["location"]
            resp.headers["ETag"] = cached["etag"]
            resp.headers["X-Cache-Lookup"] = "HIT-IDEMPOTENT"
            return resp

    # Validate JSON structure (B2: 400 for malformed JSON)
    try:
        data = request.get_json(force=False)
    except BadRequest:
        return problem(status=400, detail="Malformed JSON syntax in request body.")

    if data is None:
        return problem(status=400, detail="Request body must be non-empty valid JSON with Content-Type: application/json.")

    # Validate Domain semantics (B2: 422 for domain validation refusal)
    is_valid, validation_error = Order.validate_create_payload(data)
    if not is_valid:
        return problem(status=422, detail=validation_error)

    # Generate new order
    order_id = str(uuid.uuid4().int)[:6]
    order = Order(
        order_id=order_id,
        student_id=data["student_id"],
        vendor_id=data["vendor_id"],
        items=data["items"],
        delivery_type=data.get("delivery_type", "PICKUP"),
        drop_zone=data.get("drop_zone"),
        time_slot=data.get("time_slot"),
        coupon_code=data.get("coupon_code"),
        payment_method=data.get("payment_method", "WALLET"),
        status="PLACED"
    )
    store.save(order)

    body = order.as_json()
    location_url = f"/orders/{order.id}"
    etag = order.compute_etag()

    # Store for idempotency repeat if key was provided
    if idempotency_key:
        store.store_idempotency_record(idempotency_key, {
            "status_code": 201,
            "location": location_url,
            "etag": etag,
            "body": body
        })

    resp = jsonify(body)
    resp.status_code = 201
    resp.headers["Location"] = location_url
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    """
    Part B4, C1: Single-item read with Cache-Control and ETag.
    Support If-None-Match conditional GET -> 304 Not Modified when ETag matches.
    """
    order = store.get(order_id)
    if not order:
        return problem(status=404, detail=f"Order '{order_id}' was not found.")

    current_etag = order.compute_etag()

    # Conditional GET check (C1)
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        # Match against current ETag
        tags = [t.strip() for t in if_none_match.split(",")]
        if current_etag in tags or "*" in tags:
            # 304 Not Modified has NO body (RFC 9110)
            resp = make_response("", 304)
            resp.headers["ETag"] = current_etag
            resp.headers["Cache-Control"] = "public, max-age=60, must-revalidate"
            return resp

    resp = jsonify(order.as_json())
    resp.status_code = 200
    resp.headers["ETag"] = current_etag
    resp.headers["Cache-Control"] = "public, max-age=60, must-revalidate"
    return resp


@app.route("/orders/<order_id>", methods=["PUT"])
def update_order(order_id: str):
    """
    Part C2: Conditional write with If-Match.
    If client's If-Match header does not match current ETag -> 412 Precondition Failed.
    Prevents two editors from clobbering each other.
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    order = store.get(order_id)
    if not order:
        return problem(status=404, detail=f"Order '{order_id}' was not found.")

    current_etag = order.compute_etag()

    # Conditional write verification (C2)
    if_match = request.headers.get("If-Match")
    if if_match:
        tags = [t.strip() for t in if_match.split(",")]
        if current_etag not in tags and "*" not in tags:
            return problem(
                status=412,
                detail=f"Resource state has modified (current ETag: {current_etag}, provided: {if_match}). Precondition failed."
            )

    try:
        data = request.get_json(force=False)
    except BadRequest:
        return problem(status=400, detail="Malformed JSON syntax in update payload.")

    if not isinstance(data, dict):
        return problem(status=400, detail="Update payload must be a JSON object.")

    # Update allowed fields
    if "drop_zone" in data:
        order.drop_zone = data["drop_zone"]
    if "time_slot" in data:
        order.time_slot = data["time_slot"]
    if "delivery_type" in data:
        if data["delivery_type"] not in Order.VALID_DELIVERY_TYPES:
            return problem(status=422, detail=f"Invalid delivery_type: {data['delivery_type']}")
        order.delivery_type = data["delivery_type"]

    store.update(order)

    new_etag = order.compute_etag()
    resp = jsonify(order.as_json())
    resp.status_code = 200
    resp.headers["ETag"] = new_etag
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    """
    Part A2: Model non-CRUD actions as POST to a sub-resource (/orders/42/cancel).
    Returns 200 on success, 409 Conflict if order is already completed or cancelled.
    Supports Idempotency-Key.
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    # Idempotency check
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached = store.get_idempotency_record(idempotency_key)
        if cached:
            resp = jsonify(cached["body"])
            resp.status_code = cached["status_code"]
            resp.headers["ETag"] = cached["etag"]
            return resp

    order = store.get(order_id)
    if not order:
        return problem(status=404, detail=f"Order '{order_id}' was not found.")

    # Conflict state check (B2)
    if order.status in ("COMPLETED", "DELIVERED"):
        return problem(
            status=409,
            detail=f"Cannot cancel order '{order_id}' because it has already reached terminal status '{order.status}'."
        )

    if order.status == "CANCELLED":
        return problem(
            status=409,
            detail=f"Order '{order_id}' is already cancelled."
        )

    order.status = "CANCELLED"
    store.update(order)

    body = {
        "order_id": order.id,
        "status": order.status,
        "message": "Order has been successfully cancelled.",
        "cancelled_at": order.updated_at
    }
    etag = order.compute_etag()

    if idempotency_key:
        store.store_idempotency_record(idempotency_key, {
            "status_code": 200,
            "etag": etag,
            "body": body
        })

    resp = jsonify(body)
    resp.status_code = 200
    resp.headers["ETag"] = etag
    return resp


@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    """
    Part A1, B2: DELETE removes resource -> 204 No Content with no body.
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    order = store.get(order_id)
    if not order:
        return problem(status=404, detail=f"Order '{order_id}' was not found.")

    store.delete(order_id)
    # 204 No Content must have empty response body
    return make_response("", 204)


@app.route("/orders/<order_id>", methods=["OPTIONS"])
@app.route("/orders", methods=["OPTIONS"])
def handle_options(order_id=None):
    """
    Part A5: Implement OPTIONS returning an Allow header that lists its methods.
    """
    resp = make_response("", 204)
    if order_id:
        resp.headers["Allow"] = "GET, PUT, PATCH, DELETE, OPTIONS, HEAD"
    else:
        resp.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return resp


# ------------------------------------------------------------------------------
# 404 & 405 STANDARD HANDLERS
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def handle_not_found(e):
    return problem(status=404, detail="The requested URL was not found on this server.")

@app.errorhandler(405)
def handle_method_not_allowed(e):
    resp = problem(status=405, detail="The method is not allowed for the requested URL.")
    resp.headers["Allow"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resp

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    app.run(host="127.0.0.1", port=port, debug=False)
