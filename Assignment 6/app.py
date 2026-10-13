"""
CampusEats Orders Service - Production REST Application
CS543 · Web Services · Assignment 6: Honest responses: status codes, errors & validation
"""
import uuid
import logging
import traceback
import os
from flask import Flask, request, jsonify, make_response, Response
from werkzeug.exceptions import BadRequest

from models import Order
from store import store
from errors import problem, TYPE_CATALOGUE

# Configure secure server-side logging (Part B4: Don't leak internals)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("campuseats.orders")

app = Flask(__name__)

# Rate limit quota configuration
RATE_LIMIT_MAX = 100
CLIENT_REQUEST_COUNTS = {}

# ------------------------------------------------------------------------------
# WSGI MIDDLEWARE & METHOD OVERRIDE
# ------------------------------------------------------------------------------
class MethodRewriteMiddleware:
    """
    Support X-HTTP-Method-Override for restricted clients (A5 compliance).
    """
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

# ------------------------------------------------------------------------------
# MIDDLEWARE: Content Negotiation, Rate Limiting & Common Headers
# ------------------------------------------------------------------------------
@app.before_request
def handle_content_negotiation():
    """
    Part C3: Honour Accept header.
    Returns JSON by default, XML if explicitly requested.
    Returns 406 Not Acceptable if client demands an unsupported format.
    """
    if request.method == "OPTIONS":
        return None

    accept = request.headers.get("Accept")
    if accept:
        acceptable = False
        for part in accept.split(","):
            part_clean = part.split(";")[0].strip().lower()
            if part_clean in (
                "application/json",
                "application/xml",
                "text/xml",
                "*/*",
                "application/*",
                "text/plain"
            ):
                acceptable = True
                break
        if not acceptable:
            return problem(
                status=406,
                detail=f"Cannot produce requested MIME format '{accept}'. Only 'application/json' and 'application/xml' are supported.",
                error_type="not-acceptable"
            )

@app.before_request
def handle_rate_limiting_and_simulations():
    """
    Part A4 & B5:
    Rate limiting signalling (429 with Retry-After).
    Simulated 503 downstream outage check with Retry-After.
    """
    # 1. Downstream outage simulation (Part A4: 503 with Retry-After)
    if request.headers.get("X-Simulate-Downstream-Outage") == "true":
        resp = problem(
            status=503,
            detail="Payments & Identity cluster is currently unreachable. The request was not processed.",
            error_type="service-unavailable",
            headers={"Retry-After": "30"}
        )
        return resp

    # 2. Rate limit simulation
    if request.headers.get("X-Simulate-Rate-Limit") == "true":
        resp = problem(
            status=429,
            detail="Rate limit exceeded. Your client request quota of 100 requests per minute has been exhausted.",
            error_type="rate-limit-exceeded",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(RATE_LIMIT_MAX),
                "X-RateLimit-Remaining": "0"
            }
        )
        return resp

    # 3. Live rate counting
    client_id = request.headers.get("Authorization") or request.remote_addr or "client-default"
    current_count = CLIENT_REQUEST_COUNTS.get(client_id, 0) + 1
    CLIENT_REQUEST_COUNTS[client_id] = current_count

    if current_count > RATE_LIMIT_MAX:
        resp = problem(
            status=429,
            detail="Rate limit exceeded. Your client request quota has been exhausted.",
            error_type="rate-limit-exceeded",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(RATE_LIMIT_MAX),
                "X-RateLimit-Remaining": "0"
            }
        )
        return resp

@app.after_request
def apply_common_headers(response: Response):
    """
    Part C4: Set Content-Type (+ charset=utf-8) on every response, errors included.
    Security headers (nosniff, HSTS), CORS, and Rate-Limit signals.
    """
    # 1. Rate-limit signalling
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
        "Content-Type, Authorization, If-Match, If-None-Match, Idempotency-Key, "
        "X-HTTP-Method-Override, X-Simulate-Rate-Limit, X-Simulate-Downstream-Outage, X-Simulate-DB-Failure"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"

    # 3. Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "CampusEats-Orders/1.0 (REST/HTTP)"

    # 4. Part C4: Ensure Content-Type has charset=utf-8 on all non-empty bodies
    current_ct = response.headers.get("Content-Type", "")
    if response.status_code not in (204, 304):
        if not current_ct:
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        elif "charset=" not in current_ct:
            response.headers["Content-Type"] = f"{current_ct}; charset=utf-8"

    return response

# ------------------------------------------------------------------------------
# AUTHENTICATION GUARD
# ------------------------------------------------------------------------------
def require_auth():
    """
    Part A1 & B1: Bearer token validation. Missing/empty -> 401 Unauthorized.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        resp = problem(
            status=401,
            detail="Missing required Authorization header. Expected 'Authorization: Bearer <token>'",
            error_type="unauthorized",
            headers={"WWW-Authenticate": 'Bearer realm="CampusEats", error="missing_token"'}
        )
        return resp
    
    parts = auth_header.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        resp = problem(
            status=401,
            detail="Invalid Authorization header format. Expected 'Bearer <non-empty-token>'",
            error_type="unauthorized",
            headers={"WWW-Authenticate": 'Bearer realm="CampusEats", error="invalid_token"'}
        )
        return resp

    return None

# ------------------------------------------------------------------------------
# REST API ENDPOINTS
# ------------------------------------------------------------------------------

@app.route("/orders", methods=["GET"])
def list_orders():
    """
    GET /orders: Pure read (safe & idempotent).
    Returns 200 OK with paginated list.
    Supports Content Negotiation (JSON or XML).
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
        return problem(
            status=400,
            detail="Query parameters 'page' and 'limit' must be valid integers.",
            error_type="bad-request"
        )

    items, total_count = store.list_orders(
        student_id=student_id,
        vendor_id=vendor_id,
        status=status_filter,
        sort_by=sort_by,
        order=order_dir,
        page=page,
        limit=limit
    )

    resp_data = {
        "items": items,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "has_more": (page * limit) < total_count
    }
    response = jsonify(resp_data)
    response.status_code = 200
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/orders", methods=["POST"])
def create_order():
    """
    POST /orders:
    - Part A3: Returns 201 Created with Location: /orders/{id}
    - Part C1 & C2: Validates body before any action; collects ALL errors into 422 with errors[]
    - Part B4: Internal error shielding (simulated or real DB failure caught & sanitised)
    - Supports Idempotency-Key
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    # Check Idempotency-Key
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached = store.get_idempotency_record(idempotency_key)
        if cached:
            resp = jsonify(cached["body"])
            resp.status_code = cached["status_code"]
            resp.headers["Location"] = cached["location"]
            resp.headers["ETag"] = cached["etag"]
            resp.headers["Content-Type"] = "application/json; charset=utf-8"
            return resp

    # Part B4: Simulate internal failure test hook
    if request.headers.get("X-Simulate-DB-Failure") == "true":
        try:
            # Simulate unexpected internal database deadlock
            raise RuntimeError("CRITICAL: PostgreSQL connection pool exhausted; deadlock on table 'orders_tx' at line 412")
        except Exception as exc:
            incident_id = f"inc_{uuid.uuid4().hex[:8]}"
            logger.error(f"[Incident: {incident_id}] Internal Database Failure: {exc}\n{traceback.format_exc()}")
            return problem(
                status=500,
                detail=f"An unexpected internal error occurred. Incident reference ID: {incident_id}. Our operations team has been notified.",
                error_type="internal-error"
            )

    # Validate JSON syntax (Part A1: 400 for malformed JSON)
    try:
        data = request.get_json(force=False)
    except BadRequest:
        return problem(
            status=400,
            detail="Malformed JSON syntax in request body.",
            error_type="bad-request"
        )

    if data is None:
        return problem(
            status=400,
            detail="Request body must be non-empty valid JSON with Content-Type: application/json.",
            error_type="bad-request"
        )

    # Part C1 & C2: Validate, then act. Collect ALL errors.
    is_valid, validation_errors, error_type_key = Order.validate_create_payload(data)
    if not is_valid:
        return problem(
            status=422,
            detail="Request validation failed. One or more fields violate contract requirements.",
            error_type=error_type_key or "validation-error",
            errors=validation_errors
        )

    # Instantiate order safely
    order_id = str(uuid.uuid4().int)[:6]
    order = Order(
        order_id=order_id,
        student_id=data["student_id"],
        vendor_id=data["vendor_id"],
        items=data["items"],
        address=data["address"],
        delivery_type=data.get("delivery_type", "DELIVERY"),
        time_slot=data.get("time_slot"),
        coupon_code=data.get("coupon_code"),
        payment_method=data.get("payment_method", "WALLET"),
        status="PLACED"
    )
    store.save(order)

    body = order.as_json()
    location_url = f"/orders/{order.id}"
    etag = order.compute_etag()

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
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    """
    GET /orders/{order_id}:
    - 200 OK on read
    - 404 with order-not-found problem details if missing
    - 304 on If-None-Match conditional match
    - Content Negotiation: JSON by default, XML if Accept: application/xml
    """
    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            detail=f"Order '{order_id}' was not found in the campus orders registry.",
            error_type="order-not-found"
        )

    current_etag = order.compute_etag()

    # Conditional GET
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        tags = [t.strip() for t in if_none_match.split(",")]
        if current_etag in tags or "*" in tags:
            resp = make_response("", 304)
            resp.headers["ETag"] = current_etag
            resp.headers["Cache-Control"] = "public, max-age=60, must-revalidate"
            return resp

    # Part C3 & Question 7: Content negotiation
    accept = request.headers.get("Accept", "").lower()
    if "application/xml" in accept or "text/xml" in accept:
        xml_data = order.as_xml()
        resp = Response(xml_data, status=200, mimetype="application/xml")
        resp.headers["Content-Type"] = "application/xml; charset=utf-8"
        resp.headers["ETag"] = current_etag
        resp.headers["Cache-Control"] = "public, max-age=60, must-revalidate"
        return resp

    resp = jsonify(order.as_json())
    resp.status_code = 200
    resp.headers["ETag"] = current_etag
    resp.headers["Cache-Control"] = "public, max-age=60, must-revalidate"
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


@app.route("/orders/<order_id>", methods=["PUT", "PATCH"])
def update_or_patch_order(order_id: str):
    """
    PUT/PATCH /orders/{order_id}:
    - 200 OK on update
    - 412 Precondition Failed if If-Match does not match current ETag
    - 422 if domain validation fails
    - 404 if order missing
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            detail=f"Order '{order_id}' was not found.",
            error_type="order-not-found"
        )

    current_etag = order.compute_etag()

    # Optimistic locking
    if_match = request.headers.get("If-Match")
    if if_match:
        tags = [t.strip() for t in if_match.split(",")]
        if current_etag not in tags and "*" not in tags:
            return problem(
                status=412,
                detail=f"Resource state has modified (current ETag: {current_etag}, supplied: {if_match}). Precondition failed.",
                error_type="precondition-failed"
            )

    try:
        data = request.get_json(force=False)
    except BadRequest:
        return problem(
            status=400,
            detail="Malformed JSON syntax in update payload.",
            error_type="bad-request"
        )

    if not isinstance(data, dict):
        return problem(
            status=400,
            detail="Update payload must be a JSON object.",
            error_type="bad-request"
        )

    # Field updates
    if "address" in data:
        if not str(data["address"]).strip():
            return problem(
                status=422,
                detail="Address cannot be blank.",
                error_type="validation-error",
                errors=[{"field": "address", "message": "Address cannot be blank."}]
            )
        order.address = data["address"]

    if "time_slot" in data:
        order.time_slot = data["time_slot"]

    if "delivery_type" in data:
        if data["delivery_type"] not in Order.VALID_DELIVERY_TYPES:
            return problem(
                status=422,
                detail=f"Invalid delivery_type '{data['delivery_type']}'.",
                error_type="validation-error",
                errors=[{"field": "delivery_type", "message": f"Must be one of {list(Order.VALID_DELIVERY_TYPES)}"}]
            )
        order.delivery_type = data["delivery_type"]

    store.update(order)

    new_etag = order.compute_etag()
    resp = jsonify(order.as_json())
    resp.status_code = 200
    resp.headers["ETag"] = new_etag
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    """
    POST /orders/{order_id}/cancel:
    - 200 OK on cancellation
    - 409 Conflict if order already in terminal status (illegal-transition)
    - 404 Not Found if order missing
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached = store.get_idempotency_record(idempotency_key)
        if cached:
            resp = jsonify(cached["body"])
            resp.status_code = cached["status_code"]
            resp.headers["ETag"] = cached["etag"]
            resp.headers["Content-Type"] = "application/json; charset=utf-8"
            return resp

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            detail=f"Order '{order_id}' was not found.",
            error_type="order-not-found"
        )

    # Part B2: illegal-transition check (409 Conflict)
    if order.status in ("COMPLETED", "DELIVERED"):
        return problem(
            status=409,
            detail=f"Cannot cancel order '{order_id}' because it has already reached terminal status '{order.status}'.",
            error_type="illegal-transition"
        )

    if order.status == "CANCELLED":
        return problem(
            status=409,
            detail=f"Order '{order_id}' is already in CANCELLED status. Duplicate state transition is illegal.",
            error_type="illegal-transition"
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
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    """
    DELETE /orders/{order_id}:
    - 204 No Content with empty body on success
    - 404 with order-not-found problem details if missing
    """
    auth_err = require_auth()
    if auth_err:
        return auth_err

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            detail=f"Order '{order_id}' was not found.",
            error_type="order-not-found"
        )

    store.delete(order_id)
    resp = make_response("", 204)
    return resp


@app.route("/orders/<order_id>", methods=["OPTIONS"])
@app.route("/orders", methods=["OPTIONS"])
def handle_options(order_id=None):
    """
    OPTIONS /orders[/id]: Method discovery
    """
    resp = make_response("", 204)
    if order_id:
        resp.headers["Allow"] = "GET, PUT, PATCH, DELETE, OPTIONS, HEAD"
    else:
        resp.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return resp


# ------------------------------------------------------------------------------
# GENERIC ERROR HANDLERS (Part B4: Don't leak internals)
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def handle_not_found(e):
    return problem(
        status=404,
        detail="The requested URL route was not found on this server.",
        error_type="not-found"
    )

@app.errorhandler(405)
def handle_method_not_allowed(e):
    resp = problem(
        status=405,
        detail="The HTTP method is not allowed for the requested resource URI.",
        error_type="bad-request"
    )
    resp.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    return resp

@app.errorhandler(500)
def handle_internal_error(e):
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    logger.error(f"[Incident: {incident_id}] Uncaught Server Exception: {e}\n{traceback.format_exc()}")
    return problem(
        status=500,
        detail=f"An internal error occurred. Incident reference ID: {incident_id}. Please contact support.",
        error_type="internal-error"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5060))
    app.run(host="127.0.0.1", port=port, debug=False)
