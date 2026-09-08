# NOTES.md — CampusEats Orders Service (Assignment 4)

**Name and Roll No. of all team members:** _[Fill in — Name, Roll No. for each team member]_

Service chosen: **Orders Service** (owns: carts, cart_items, orders, order_items — boundary carried over unchanged from Assignment 2). Not Payments, per the assignment constraint.

---

## Part A2 — SOAP-style starting point

- `placeOrder(studentId, vendorId, items, deliveryType, timeSlot, couponCode, paymentMethod)`
- `getOrderStatus(orderId)`
- `updateOrderStatus(orderId, newStatus)`
- `getOrderHistory(studentId)`
- `cancelOrder(orderId, reason)`

## A4 — Resource table

| Method | URL | What it does | Success | Failure |
|---|---|---|---|---|
| POST | `/orders` | Creates a new order (calls Payments to charge, via a hardened outbound call) | 201 | 400, 422, 503 |
| GET | `/orders/{orderId}` | Reads a single order | 200 | 404 |
| GET | `/orders?studentId=&status=` | Lists orders, filtered by student and/or status | 200 | 400 |
| POST | `/orders/{orderId}/cancellation` | Sub-resource: cancels an order (state-changing) | 202 | 404, 409 |

## A5 — The hard choice: `cancelOrder`

`cancelOrder` mapped least comfortably onto a resource. I rejected `DELETE /orders/{id}`, since a cancelled order isn't erased — it must stay queryable for history and disputes, so `DELETE`'s "remove this resource" semantics were misleading. I also rejected folding it into a generic `PATCH /orders/{id}` with `status=CANCELLED`, because cancellation is a distinct business event (it triggers a refund and a delivery-cancellation side effect) and needs its own idempotency behaviour — a retried cancellation should be a safe no-op, not just another field update. Modelling it as a sub-resource, `POST /orders/{id}/cancellation`, names the durable thing being created (a cancellation record) and gives it a natural home for that event-specific behaviour.

## D3 — Fallback when Payments is unreachable

If the Payments service is unreachable after retries, the Orders service **fails the create** (returns `503`) rather than accepting the order unpaid. Degrading — e.g. accepting the order and marking payment as "pending" — would let a vendor start preparing food with no guaranteed payment behind it, which is real, unrecoverable loss (unlike, say, a "like" or a view count that can be reconciled later). Failing fast keeps the system's guarantee that every `PLACED` order is a paid order, and lets the student simply retry once Payments recovers — using the same `Idempotency-Key`, so retrying is safe and won't double-charge if the first attempt actually succeeded on the Payments side.

---

## Answers

> **A note on Q1, Q2, Q5 below:** these ask you to quote and count lines from your actual Assignment 3 WSDL, which I don't have access to. I've filled in the reasoning and structure — replace the bracketed parts with your real numbers/quotes before submitting.

**1. Line count and what the difference is made of.**
Assignment 3 WSDL: `[N lines]`. This `openapi.yaml`: `[count with e.g. wc -l openapi.yaml]`. The difference is mostly made of infrastructure that WSDL/SOAP needs and REST doesn't: `<binding>` (how to physically invoke the operation — SOAP action, transport), `<port>`/`<service>` address plumbing, and the envelope/encoding declarations. Two things the WSDL declared that OpenAPI doesn't need: **(a)** the SOAP binding/transport details (HTTP is just assumed and the URL *is* the address), and **(b)** an explicit `<message>` wrapper for each request/response — OpenAPI schemas describe the payload shape directly under `components.schemas` without a separate envelope layer.

**2. A SOAP fault vs. a REST problem body.**
Quote from Assignment 3: `[paste one <soap:Fault> block here]`. The equivalent here is a `409 Conflict` with body:
```json
{"type": "about:blank", "title": "Conflict", "status": 409, "detail": "Order ORD-00001 is in status CANCELLED and can no longer be cancelled."}
```
Returning a fault inside a `200 OK` is a problem for the network in between because every intermediary that only looks at the status line — proxies, caches, load balancers, monitoring — sees "success" and behaves accordingly (a cache might cache a failed response as if it were good; a health check counts it as a healthy call). The status code is a signal that infrastructure below the application layer can act on; a fault hidden in the body is invisible until something actually parses the payload.

**3. UDDI's publish / find / bind.**
*Publish* still exists in spirit — publishing `openapi.yaml` (e.g. to a shared repo, or a portal like SwaggerHub) is the modern equivalent of registering a service description. *Find* mostly disappeared as a formal runtime step: instead of a client querying a registry at runtime to discover an endpoint, the org just documents URLs in `openapi.yaml`'s `servers:` block and shares them directly (or via an API gateway/service catalogue that isn't UDDI). *Bind* also disappeared as a distinct step — there's no separate "generate a binding" phase; the client just reads the OpenAPI contract and calls the URL over HTTP directly. What took over the job of dynamic find+bind in most modern systems is a combination of DNS + environment variables (as used here for `PAYMENTS_SERVICE_URL`) and, in larger deployments, a service mesh or API gateway.

**4. What replaced XML Schema validation.**
The function `validate_create_body()` in `app.py` now carries that responsibility — it's called before any field of the request body is touched. One failure that would get through without it: a `quantity` of `0` or a negative number, or a non-integer quantity (e.g. `"quantity": "two"`), would silently reach the pricing calculation (`quantity * price`) and produce a nonsensical total or a runtime `TypeError` deep inside the handler instead of a clean `400` at the door.

**5. Where I'd still choose SOAP.**
`[Somewhere is the stronger argument here.]` I'd still pick the SOAP/WS-* stack for the **Payments → banking network settlement leg** specifically — not the student-facing Payments API, but a hypothetical leg where CampusEats' Payments service reconciles with a bank or card network. There, WS-Security's message-level signing and WS-ReliableMessaging's guaranteed, exactly-once delivery over unreliable transport are guarantees REST doesn't give you for free: REST's idempotency keys get you *safe retries*, but not a standardised, interoperable **guarantee of exactly-once delivery with cryptographic non-repudiation** that a regulator or bank's integration team would already expect out of the box.
