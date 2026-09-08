import datetime
import uuid

from flask import Flask, request, jsonify

from models import Order, OrderItem
from store import store
from errors import ValidationError, NotFoundError, ConflictError, UnprocessableError, problem
from payments_client import initiate_payment, PaymentFailed, PaymentUnavailable

app = Flask(__name__)

VALID_DELIVERY_TYPES = {"PICKUP", "DELIVERY"}
VALID_STATUSES = {"PLACED", "CONFIRMED", "PREPARING", "READY", "COMPLETED", "CANCELLED"}
CANCELLABLE_STATUSES = {"PLACED", "CONFIRMED", "PREPARING"}


def validate_create_body(body):
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object.")
    for field in ["studentId", "vendorId", "items", "deliveryType", "paymentMethod"]:
        if field not in body:
            raise ValidationError(f"Missing required field: {field}")
    if not isinstance(body["items"], list) or len(body["items"]) == 0:
        raise ValidationError("items must be a non-empty list.")
    for item in body["items"]:
        if "menuItemId" not in item or "quantity" not in item:
            raise ValidationError("Each item needs menuItemId and quantity.")
        if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            raise ValidationError("quantity must be a positive integer.")
    if body["deliveryType"] not in VALID_DELIVERY_TYPES:
        raise ValidationError(f"deliveryType must be one of {sorted(VALID_DELIVERY_TYPES)}.")


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return problem(e.status, e.title, e.detail)


@app.route("/orders", methods=["POST"])
def create_order():
    body = request.get_json(silent=True)
    validate_create_body(body)

    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        existing = store.find_by_idempotency_key(idempotency_key)
        if existing:
            resp = jsonify(existing.as_json())
            resp.status_code = 201
            resp.headers["Location"] = f"/orders/{existing.order_id}"
            return resp

    if body["deliveryType"] == "DELIVERY" and not body.get("timeSlot"):
        # Syntactically valid request, but the domain still refuses it -> 422.
        raise UnprocessableError("A timeSlot is required for delivery orders.")

    # In the full system this would call Catalogue.checkItemAvailability
    # per item; simulated here with a fixed unit price for brevity.
    unit_price = 120.0
    items = [OrderItem(i["menuItemId"], i["quantity"], unit_price) for i in body["items"]]
    total_amount = sum(i.quantity * i.price_at_order for i in items)

    order_id = store.next_id()
    order = Order(
        order_id=order_id,
        student_id=body["studentId"],
        vendor_id=body["vendorId"],
        items=items,
        delivery_type=body["deliveryType"],
        time_slot=body.get("timeSlot"),
        coupon_code=body.get("couponCode"),
        total_amount=total_amount,
        idempotency_key=idempotency_key,
    )

    payment_idempotency_key = idempotency_key or str(uuid.uuid4())
    try:
        payment_result = initiate_payment(
            order_id=order.order_id,
            amount=order.total_amount,
            method=body["paymentMethod"],
            idempotency_key=payment_idempotency_key,
        )
        order.payment_attempt_log.append({"outcome": "SUCCESS", "detail": payment_result})
    except PaymentFailed as exc:
        raise UnprocessableError(f"Payment was rejected: {exc}")
    except PaymentUnavailable as exc:
        # D3 fallback: fail fast rather than accept an unpaid order.
        return problem(503, "Dependency Unavailable",
                        f"Could not confirm payment right now; order was not created. ({exc})")

    store.save(order)

    resp = jsonify(order.as_json())
    resp.status_code = 201
    resp.headers["Location"] = f"/orders/{order.order_id}"
    return resp


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = store.get(order_id)
    if not order:
        raise NotFoundError(f"No order with id {order_id}.")
    return jsonify(order.as_json()), 200


@app.route("/orders", methods=["GET"])
def list_orders():
    student_id = request.args.get("studentId")
    status = request.args.get("status")
    if status is not None and status not in VALID_STATUSES:
        raise ValidationError(f"status must be one of {sorted(VALID_STATUSES)}.")
    results = store.list(student_id=student_id, status=status)
    return jsonify([o.as_summary_json() for o in results]), 200


@app.route("/orders/<order_id>/cancellation", methods=["POST"])
def cancel_order(order_id):
    order = store.get(order_id)
    if not order:
        raise NotFoundError(f"No order with id {order_id}.")
    if order.status not in CANCELLABLE_STATUSES:
        raise ConflictError(
            f"Order {order_id} is in status {order.status} and can no longer be cancelled."
        )

    order.status = "CANCELLED"
    order.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"

    resp = jsonify({
        "orderId": order.order_id,
        "status": order.status,
        "message": "Cancellation accepted; refund and delivery cancellation are processed asynchronously.",
    })
    resp.status_code = 202
    return resp


if __name__ == "__main__":
    app.run(port=6000)
