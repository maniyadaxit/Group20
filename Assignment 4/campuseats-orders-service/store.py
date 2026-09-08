class OrderStore:
    """
    In-process storage for the Orders service.
    No other CampusEats service may import this module directly —
    everything crosses the boundary through the HTTP contract only.
    """

    def __init__(self):
        self._orders = {}        # order_id -> Order
        self._idempotency = {}   # idempotency_key -> order_id
        self._next_id = 1

    def next_id(self):
        oid = f"ORD-{self._next_id:05d}"
        self._next_id += 1
        return oid

    def save(self, order):
        self._orders[order.order_id] = order
        if order.idempotency_key:
            self._idempotency[order.idempotency_key] = order.order_id

    def get(self, order_id):
        return self._orders.get(order_id)

    def find_by_idempotency_key(self, key):
        oid = self._idempotency.get(key)
        return self._orders.get(oid) if oid else None

    def list(self, student_id=None, status=None):
        results = list(self._orders.values())
        if student_id is not None:
            results = [o for o in results if o.student_id == student_id]
        if status is not None:
            results = [o for o in results if o.status == status]
        return results


store = OrderStore()
