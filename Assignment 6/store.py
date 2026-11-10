"""
CampusEats Orders Service - In-Process Storage
CS543 · Web Services · Assignment 6: Honest responses: status codes, errors & validation
"""
from datetime import datetime, timezone
from models import Order

class OrderStore:
    def __init__(self):
        self._orders: dict[str, Order] = {}
        self._idempotency_cache: dict[str, dict] = {}
        self._seed_data()

    def _seed_data(self):
        """Seed initial records for testing and demonstration."""
        order_42 = Order(
            order_id="42",
            student_id="student_20251651054",
            vendor_id="vendor_canteen_central",
            items=[
                {"item_id": "item_thali_deluxe", "name": "Special Veg Thali", "quantity": 1, "unit_price": 90.0},
                {"item_id": "item_masala_chai", "name": "Cutting Masala Chai", "quantity": 2, "unit_price": 15.0}
            ],
            address="Hostel 4 Ground Floor",
            delivery_type="DELIVERY",
            time_slot="13:30-14:00",
            coupon_code="CAMPUS50",
            payment_method="WALLET",
            status="PLACED",
            created_at="2026-10-13T06:00:00Z",
            updated_at="2026-10-13T06:00:00Z",
            version=1,
            internal_audit_id="audit_rec_seed_42"
        )
        self._orders["42"] = order_42

        order_101 = Order(
            order_id="101",
            student_id="student_20251651038",
            vendor_id="vendor_nescafe_junction",
            items=[
                {"item_id": "item_cold_coffee", "name": "Cold Coffee Frappe", "quantity": 1, "unit_price": 60.0}
            ],
            address="Academic Block 1 Lobby",
            delivery_type="PICKUP",
            time_slot="14:00-14:30",
            coupon_code=None,
            payment_method="UPI",
            status="CONFIRMED",
            created_at="2026-10-13T06:15:00Z",
            updated_at="2026-10-13T06:15:00Z",
            version=1,
            internal_audit_id="audit_rec_seed_101"
        )
        self._orders["101"] = order_101

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(str(order_id))

    def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    def update(self, order: Order) -> Order:
        order.version += 1
        order.updated_at = datetime.now(timezone.utc).isoformat()
        self._orders[order.id] = order
        return order

    def delete(self, order_id: str) -> bool:
        if str(order_id) in self._orders:
            del self._orders[str(order_id)]
            return True
        return False

    def list_orders(
        self,
        student_id: str = None,
        vendor_id: str = None,
        status: str = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[dict], int]:
        results = list(self._orders.values())

        if student_id:
            results = [o for o in results if o.student_id == student_id]
        if vendor_id:
            results = [o for o in results if o.vendor_id == vendor_id]
        if status:
            results = [o for o in results if o.status.upper() == status.upper()]

        reverse = (order.lower() == "desc")
        if sort_by == "final_amount":
            results.sort(key=lambda o: o.final_amount, reverse=reverse)
        else:
            results.sort(key=lambda o: o.created_at, reverse=reverse)

        total_count = len(results)
        start = max(0, (page - 1) * limit)
        end = start + limit
        paginated_orders = [o.as_json() for o in results[start:end]]

        return paginated_orders, total_count

    def get_idempotency_record(self, key: str) -> dict | None:
        return self._idempotency_cache.get(key)

    def store_idempotency_record(self, key: str, record: dict):
        self._idempotency_cache[key] = record

# Singleton instance
store = OrderStore()
