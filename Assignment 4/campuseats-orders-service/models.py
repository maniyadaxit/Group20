import datetime


class OrderItem:
    def __init__(self, menu_item_id, quantity, price_at_order):
        self.menu_item_id = menu_item_id
        self.quantity = quantity
        self.price_at_order = price_at_order

    def as_json(self):
        return {
            "menuItemId": self.menu_item_id,
            "quantity": self.quantity,
            "priceAtOrder": self.price_at_order,
        }


class Order:
    """
    Internal record for one order. Holds everything the service needs
    to operate, including fields that must NEVER be published:

      - idempotency_key: used only to dedupe retried create requests
      - payment_attempt_log: internal audit trail of calls made to the
        Payments service (may contain internal payment provider detail)

    as_json() is the public representation and deliberately omits both.
    """

    def __init__(self, order_id, student_id, vendor_id, items, delivery_type,
                 time_slot, coupon_code, total_amount, idempotency_key=None):
        self.order_id = order_id
        self.student_id = student_id
        self.vendor_id = vendor_id
        self.items = items
        self.delivery_type = delivery_type
        self.time_slot = time_slot
        self.coupon_code = coupon_code
        self.total_amount = total_amount
        self.status = "PLACED"
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
        self.updated_at = self.created_at

        # internal-only — excluded from as_json()
        self.idempotency_key = idempotency_key
        self.payment_attempt_log = []

    def as_json(self):
        return {
            "orderId": self.order_id,
            "studentId": self.student_id,
            "vendorId": self.vendor_id,
            "items": [i.as_json() for i in self.items],
            "deliveryType": self.delivery_type,
            "timeSlot": self.time_slot,
            "couponCode": self.coupon_code,
            "totalAmount": self.total_amount,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def as_summary_json(self):
        return {
            "orderId": self.order_id,
            "studentId": self.student_id,
            "vendorId": self.vendor_id,
            "status": self.status,
            "totalAmount": self.total_amount,
            "createdAt": self.created_at,
        }
