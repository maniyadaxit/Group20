"""
CampusEats Orders Service - Domain Models
Separates stored record from published representation (per Assignment 4/5 step C2).
"""
import hashlib
import json
from datetime import datetime, timezone
import uuid

class Order:
    VALID_STATUSES = {"PLACED", "CONFIRMED", "PREPARING", "READY", "COMPLETED", "CANCELLED"}
    VALID_DELIVERY_TYPES = {"PICKUP", "DELIVERY"}
    VALID_PAYMENT_METHODS = {"WALLET", "UPI", "CARD", "CASH"}

    def __init__(
        self,
        order_id: str,
        student_id: str,
        vendor_id: str,
        items: list,
        delivery_type: str = "PICKUP",
        drop_zone: str = None,
        time_slot: str = None,
        coupon_code: str = None,
        payment_method: str = "WALLET",
        status: str = "PLACED",
        created_at: str = None,
        updated_at: str = None,
        version: int = 1,
        internal_audit_id: str = None,
    ):
        self.id = str(order_id)
        self.student_id = student_id
        self.vendor_id = vendor_id
        self.items = items
        self.delivery_type = delivery_type
        self.drop_zone = drop_zone
        self.time_slot = time_slot
        self.coupon_code = coupon_code
        self.payment_method = payment_method
        self.status = status
        
        # Calculate subtotal and final amount
        self.subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0.0) for item in items)
        self.discount_amount = 20.0 if coupon_code == "CAMPUS50" else 0.0
        self.final_amount = max(0.0, self.subtotal - self.discount_amount)

        now_iso = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        self.version = version

        # Internal field stored in DB but stripped in as_json() (Step C2 requirement)
        self.internal_audit_id = internal_audit_id or f"audit_rec_{uuid.uuid4().hex[:12]}"

    def as_json(self) -> dict:
        """
        Returns what we publish to clients.
        Omits internal_audit_id and internal DB locks to satisfy C2.
        """
        return {
            "id": self.id,
            "student_id": self.student_id,
            "vendor_id": self.vendor_id,
            "items": self.items,
            "subtotal": round(self.subtotal, 2),
            "discount_amount": round(self.discount_amount, 2),
            "final_amount": round(self.final_amount, 2),
            "delivery_type": self.delivery_type,
            "drop_zone": self.drop_zone,
            "time_slot": self.time_slot,
            "coupon_code": self.coupon_code,
            "payment_method": self.payment_method,
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def compute_etag(self) -> str:
        """
        Compute a strong ETag based on order identity, version, status, and items.
        Must change whenever the resource state updates (B4, C1, C2).
        """
        state_repr = json.dumps(
            {
                "id": self.id,
                "version": self.version,
                "status": self.status,
                "final_amount": self.final_amount,
                "items": self.items,
                "updated_at": self.updated_at,
            },
            sort_keys=True
        )
        digest = hashlib.sha256(state_repr.encode("utf-8")).hexdigest()[:16]
        return f'"{digest}"'

    @staticmethod
    def validate_create_payload(data: dict) -> tuple[bool, str]:
        """
        Validate input for order creation.
        Returns (is_valid, error_detail).
        Distinguishes 400 (malformed structure) from 422 (domain refusal).
        """
        if not isinstance(data, dict):
            return False, "Request body must be a valid JSON object"

        # Mandatory keys
        required_keys = ["student_id", "vendor_id", "items"]
        for key in required_keys:
            if key not in data:
                return False, f"Missing required field: '{key}'"

        if not isinstance(data["student_id"], str) or not data["student_id"].strip():
            return False, "Field 'student_id' must be a non-empty string"

        if not isinstance(data["vendor_id"], str) or not data["vendor_id"].strip():
            return False, "Field 'vendor_id' must be a non-empty string"

        items = data.get("items")
        if not isinstance(items, list):
            return False, "Field 'items' must be a non-empty list"

        if len(items) == 0:
            return False, "Order must contain at least one menu item (domain requirement)"

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return False, f"Item at index {i} must be a JSON object"
            if "item_id" not in item or "quantity" not in item or "unit_price" not in item:
                return False, f"Item at index {i} missing required keys (item_id, quantity, unit_price)"
            if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                return False, f"Item '{item.get('item_id')}' quantity must be a positive integer"
            if not isinstance(item["unit_price"], (int, float)) or item["unit_price"] <= 0:
                return False, f"Item '{item.get('item_id')}' unit_price must be greater than zero"

        delivery_type = data.get("delivery_type", "PICKUP")
        if delivery_type not in Order.VALID_DELIVERY_TYPES:
            return False, f"Invalid delivery_type '{delivery_type}'. Must be one of: {list(Order.VALID_DELIVERY_TYPES)}"

        if delivery_type == "DELIVERY" and not data.get("drop_zone"):
            return False, "Field 'drop_zone' is required when delivery_type is 'DELIVERY'"

        return True, ""
