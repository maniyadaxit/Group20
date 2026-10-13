"""
CampusEats Orders Service - Domain Models
CS543 · Web Services · Assignment 6: Honest responses: status codes, errors & validation
Supports JSON and XML serialization (Content Negotiation) and multi-error field validation.
"""
import hashlib
import json
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

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
        address: str = "Hostel 4 Ground Floor",
        delivery_type: str = "DELIVERY",
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
        self.address = address
        self.delivery_type = delivery_type
        self.time_slot = time_slot
        self.coupon_code = coupon_code
        self.payment_method = payment_method
        self.status = status
        
        # Calculate pricing
        self.subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0.0) for item in items)
        self.discount_amount = 20.0 if coupon_code == "CAMPUS50" else 0.0
        self.final_amount = max(0.0, self.subtotal - self.discount_amount)

        now_iso = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        self.version = version

        # Internal database audit tracking - stripped in representation (Step B4)
        self.internal_audit_id = internal_audit_id or f"internal_tx_{uuid.uuid4().hex[:12]}"

    def as_json(self) -> dict:
        """
        Clean public JSON representation.
        Excludes internal database identifiers and credential tokens.
        """
        return {
            "id": self.id,
            "student_id": self.student_id,
            "vendor_id": self.vendor_id,
            "items": self.items,
            "address": self.address,
            "delivery_type": self.delivery_type,
            "subtotal": round(self.subtotal, 2),
            "discount_amount": round(self.discount_amount, 2),
            "final_amount": round(self.final_amount, 2),
            "time_slot": self.time_slot,
            "coupon_code": self.coupon_code,
            "payment_method": self.payment_method,
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def as_xml(self) -> str:
        """
        Content Negotiation (Part C3 & Question 7):
        Produces standard, clean XML representation when Accept: application/xml is requested.
        """
        root = ET.Element("order")
        ET.SubElement(root, "id").text = self.id
        ET.SubElement(root, "student_id").text = self.student_id
        ET.SubElement(root, "vendor_id").text = self.vendor_id
        ET.SubElement(root, "address").text = self.address
        ET.SubElement(root, "delivery_type").text = self.delivery_type
        ET.SubElement(root, "status").text = self.status
        ET.SubElement(root, "subtotal").text = f"{self.subtotal:.2f}"
        ET.SubElement(root, "discount_amount").text = f"{self.discount_amount:.2f}"
        ET.SubElement(root, "final_amount").text = f"{self.final_amount:.2f}"
        ET.SubElement(root, "payment_method").text = self.payment_method
        ET.SubElement(root, "version").text = str(self.version)
        ET.SubElement(root, "created_at").text = self.created_at
        ET.SubElement(root, "updated_at").text = self.updated_at

        items_elem = ET.SubElement(root, "items")
        for item in self.items:
            item_elem = ET.SubElement(items_elem, "item")
            ET.SubElement(item_elem, "item_id").text = str(item.get("item_id", ""))
            ET.SubElement(item_elem, "name").text = str(item.get("name", ""))
            ET.SubElement(item_elem, "quantity").text = str(item.get("quantity", 0))
            ET.SubElement(item_elem, "unit_price").text = f"{item.get('unit_price', 0.0):.2f}"

        xml_str = ET.tostring(root, encoding="utf-8")
        return '<?xml version="1.0" encoding="utf-8"?>\n' + xml_str.decode("utf-8")

    def compute_etag(self) -> str:
        """
        Computes deterministic ETag based on identity, version, and status.
        """
        state_repr = json.dumps(
            {
                "id": self.id,
                "version": self.version,
                "status": self.status,
                "final_amount": self.final_amount,
                "updated_at": self.updated_at,
            },
            sort_keys=True
        )
        digest = hashlib.sha256(state_repr.encode("utf-8")).hexdigest()[:16]
        return f'"{digest}"'

    @staticmethod
    def validate_create_payload(data: dict) -> tuple[bool, list[dict], str]:
        """
        Part C1 & C2: Validate before doing any work and collect ALL errors, not just the first.
        Returns: (is_valid, field_errors_list, error_type_key)
        """
        errors = []
        error_type = "validation-error"

        if not isinstance(data, dict):
            return False, [{"field": "body", "message": "Request body must be a JSON object."}], "bad-request"

        # Check student_id
        student_id = data.get("student_id")
        if not student_id or not isinstance(student_id, str) or not student_id.strip():
            errors.append({"field": "student_id", "message": "Field 'student_id' is required and must be non-empty."})

        # Check vendor_id
        vendor_id = data.get("vendor_id")
        if not vendor_id or not isinstance(vendor_id, str) or not vendor_id.strip():
            errors.append({"field": "vendor_id", "message": "Field 'vendor_id' is required and must be non-empty."})

        # Check address (Part C1: address required)
        address = data.get("address")
        if not address or not isinstance(address, str) or not address.strip():
            errors.append({"field": "address", "message": "Delivery address is required and cannot be blank."})

        # Check items (Part C1: items non-empty; each qty an integer >= 1)
        items = data.get("items")
        if items is None or not isinstance(items, list):
            errors.append({"field": "items", "message": "Field 'items' must be a list."})
        elif len(items) == 0:
            # Special B2 type catalogue match: empty-cart
            errors.append({"field": "items", "message": "Order items list cannot be empty (empty cart)."})
            error_type = "empty-cart"
        else:
            for idx, it in enumerate(items):
                if not isinstance(it, dict):
                    errors.append({"field": f"items[{idx}]", "message": "Item must be a JSON object."})
                    continue
                
                # Check item quantity >= 1 and integer
                qty = it.get("quantity")
                if qty is None:
                    errors.append({"field": f"items[{idx}].quantity", "message": "Quantity is required."})
                elif not isinstance(qty, int) or qty < 1:
                    errors.append({"field": f"items[{idx}].quantity", "message": "Quantity must be an integer >= 1."})

                # Check unit_price
                price = it.get("unit_price")
                if price is None or not isinstance(price, (int, float)) or price <= 0:
                    errors.append({"field": f"items[{idx}].unit_price", "message": "Unit price must be a positive number."})

                # Check item_id
                if not it.get("item_id"):
                    errors.append({"field": f"items[{idx}].item_id", "message": "Field 'item_id' is required."})

        if errors:
            return False, errors, error_type

        return True, [], ""
