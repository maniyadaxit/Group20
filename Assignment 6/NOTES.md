# CS543 · Web Services · Assignment 6 of 12

## Honest Responses: Status Codes, Errors & Validation

**Course:** CS543 · Web Services  
**Institution:** Indian Institute of Information Technology Vadodara (IIITV)  
**Instructor:** Dr. Pramit Mazumdar (`pramit.mazumdar@iiitvadodara.ac.in`)  
**Service:** CampusEats Orders Service  

---

## Team Information

| Serial | Team Member Name | Roll Number | Role |
| :---: | :--- | :---: | :--- |
| **1** | **Daxit Maniya** | **20251651054** | Team Leader & Backend Architect |
| **2** | **Ethasam** | **20251651038** | Protocol & Error Handling Engineer |
| **3** | **Gulshan Kumar** | **20251651040** | QA, Validation & Test Automation |

**Team ID:** `CS543-Team-07`  
**Repository:** `campuseats` / `E-commerce-main`  

---

# Part A · Status Codes Architecture

### A1 & A2: Honest Status Mapping (No Fake 200s)
In REST API design, **the HTTP status code IS the outcome**. A server must never return an HTTP `200 OK` containing a failure payload such as `{ "ok": false, "error": "Order not found" }` or `{ "status": "FAIL" }`. 
Such anti-patterns break HTTP caching intermediaries, prevent reverse-proxy failover routing, and force client network code to parse response bodies just to determine whether an operation succeeded.

Every failure in CampusEats Orders Service is mapped to an authoritative, semantic `4xx` or `5xx` status code.

---

# Part B · Standardised Problem Details (RFC 7807 / RFC 9457)

### B1 & B2: Error Shape & Type Catalogue
Every client-facing failure routes through `problem()` and returns:
- `Content-Type: application/problem+json; charset=utf-8`
- Uniform root keys: `type`, `title`, `status`, `detail`, and optional `errors[]`.

---

# Part C · Request Validation & Formats

### C1 & C2: Validate, Then Act
All incoming request payloads are validated **before** any database mutation, external API call, or transaction lock occurs.
Rather than stopping at the first failure, our validator scans the entire payload and accumulates **all** invalid fields into an `errors[]` array, returning a single, comprehensive `422 Unprocessable Entity`.

### C3 & C4: Content Negotiation & Charset Labelling
- **JSON Default:** Client sending `Accept: application/json` or wildcard `*/*` receives `Content-Type: application/json; charset=utf-8`.
- **XML Support:** Client sending `Accept: application/xml` receives clean, valid XML with `Content-Type: application/xml; charset=utf-8`.
- **Unsupported Formats:** Client demanding formats the server cannot generate (e.g. `Accept: text/csv`) receives `406 Not Acceptable` with Problem Details.

---

# Answers to Assignment 6 Questions

### Question 1: Your Status Map
Every endpoint, its success status, and the status for each real failure — one line on why each:

#### 1. `POST /orders` (Order Creation)
- **`201 Created`**: The order was successfully validated, persisted, and minted with canonical URI in `Location`.
- **`400 Bad Request`**: Request body failed basic JSON syntax parsing (malformed quotes, unclosed braces).
- **`401 Unauthorized`**: Missing or empty `Authorization: Bearer <token>` header.
- **`422 Unprocessable Entity`**: Valid JSON syntax, but failed domain validation (empty cart, non-positive quantity, blank delivery address).
- **`429 Too Many Requests`**: Client exceeded allocated rate limit budget (includes `Retry-After: 60`).
- **`500 Internal Server Error`**: Unexpected server-side fault; shielded with an incident ID.
- **`503 Service Unavailable`**: Downstream dependency (Payment/Identity cluster) unreachable; includes `Retry-After: 30`.

#### 2. `GET /orders` (List & Search Orders)
- **`200 OK`**: Paginated list of order summaries returned successfully.
- **`400 Bad Request`**: Query parameters `page` or `limit` cannot be parsed as integers.
- **`406 Not Acceptable`**: Client requested unsupported MIME type in `Accept` (e.g., `text/csv`).
- **`429 Too Many Requests`**: Client exceeded rate limit budget.

#### 3. `GET /orders/{order_id}` (Single Order Representation)
- **`200 OK`**: Order representation found and returned (supports JSON or XML).
- **`304 Not Modified`**: Client's `If-None-Match` header matched current entity `ETag`; payload omitted to conserve bandwidth.
- **`404 Not Found`**: The requested `order_id` does not exist in the store.
- **`406 Not Acceptable`**: Client sent an incompatible `Accept` header.
- **`429 Too Many Requests`**: Rate limit quota exhausted.

#### 4. `PUT` / `PATCH /orders/{order_id}` (Update / Partial Update)
- **`200 OK`**: Order successfully updated with new attributes and fresh `ETag`.
- **`400 Bad Request`**: Malformed JSON syntax in update payload.
- **`401 Unauthorized`**: Caller did not provide valid authentication credentials.
- **`404 Not Found`**: Target order ID does not exist.
- **`412 Precondition Failed`**: Caller's `If-Match` ETag does not match current resource state (lost-update prevention).
- **`422 Unprocessable Entity`**: Provided update values violate domain rules (e.g. blank address).

#### 5. `POST /orders/{order_id}/cancel` (Non-CRUD State Transition)
- **`200 OK`**: Order successfully transitioned to `CANCELLED` status.
- **`401 Unauthorized`**: Caller is unauthenticated.
- **`404 Not Found`**: Order ID does not exist.
- **`409 Conflict`**: Illegal state transition attempted (order already reached `CANCELLED` or `COMPLETED` terminal status).

#### 6. `DELETE /orders/{order_id}` (Order Removal)
- **`204 No Content`**: Order permanently deleted from tracking; response has strictly empty body.
- **`401 Unauthorized`**: Caller lacked authorization.
- **`404 Not Found`**: Target order ID was not found.

---

### Question 2: Your Type Catalogue
The stable URI strings used for each failure and the exact conditions that trigger them:

| Error Type Key | Stable URI String (`type`) | What Triggers It |
| :--- | :--- | :--- |
| `empty-cart` | `https://campuseats.univ.edu/errors/empty-cart` | Client submits `POST /orders` with an empty `items: []` array. |
| `item-unavailable` | `https://campuseats.univ.edu/errors/item-unavailable` | A requested menu item ID is out-of-stock or deleted by the vendor. |
| `payment-declined` | `https://campuseats.univ.edu/errors/payment-declined` | Student wallet balance is insufficient or external card/UPI gateway declines payment. |
| `order-not-found` | `https://campuseats.univ.edu/errors/order-not-found` | Client requests or attempts to mutate an `order_id` that does not exist in store (`404`). |
| `illegal-transition` | `https://campuseats.univ.edu/errors/illegal-transition` | Client attempts an invalid order lifecycle transition, e.g., canceling an already-cancelled or completed order (`409`). |
| `validation-error` | `https://campuseats.univ.edu/errors/validation-error` | Payload violates semantic schema rules (e.g. `quantity <= 0`, missing `address`) (`422`). |
| `bad-request` | `https://campuseats.univ.edu/errors/bad-request` | Malformed JSON syntax or unparseable query parameters (`400`). |
| `unauthorized` | `https://campuseats.univ.edu/errors/unauthorized` | Missing or malformed `Authorization: Bearer <token>` header (`401`). |
| `precondition-failed` | `https://campuseats.univ.edu/errors/precondition-failed` | Mismatched `If-Match` header during write operation (`412`). |
| `not-acceptable` | `https://campuseats.univ.edu/errors/not-acceptable` | Client `Accept` header demands an unsupported MIME type like `text/csv` (`406`). |
| `rate-limit-exceeded` | `https://campuseats.univ.edu/errors/rate-limit-exceeded` | Client budget exceeded allocated 100 requests/min quota (`429`). |
| `service-unavailable` | `https://campuseats.univ.edu/errors/service-unavailable` | Upstream payments or identity cluster is unreachable (`503`). |
| `internal-error` | `https://campuseats.univ.edu/errors/internal-error` | Unexpected server runtime exception; masked to prevent leaking internals (`500`). |

---

### Question 3: Labelled Problem Details Body from Service
Paste of an actual Problem Details response captured from `POST /orders/42/cancel` when order is already cancelled:

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json; charset=utf-8
Content-Length: 263
```
```json
{
  "type": "https://campuseats.univ.edu/errors/illegal-transition",
  "title": "Illegal State Transition",
  "status": 409,
  "detail": "Order '42' is already in CANCELLED status. Duplicate state transition is illegal."
}
```

#### Labelled Breakdown of Fields:
- **`type` (URI)**: Canonical, stable URI reference that identifies the specific error condition. Clients can key their programmatic error handling logic on this string.
- **`title` (String)**: Short, human-readable summary of the problem type. Written in English for developers; does not change between occurrences of the error.
- **`status` (Integer)**: The HTTP status code generated by origin server for this occurrence (`409`). Mirrors the HTTP protocol status line.
- **`detail` (String)**: Human-readable explanation specific to this occurrence of the problem, giving exact context (mentions order `'42'`).

---

### Question 4: Field-Level 422 Reporting Two Bad Fields at Once
When a client sends an order payload where the first item has `quantity = 0` AND the `address` field is blank:

#### Request:
```http
POST /orders HTTP/1.1
Host: 127.0.0.1:5060
Content-Type: application/json
Authorization: Bearer token_daxit_20251651054

{
  "student_id": "student_20251651054",
  "vendor_id": "vendor_canteen_central",
  "items": [
    {
      "item_id": "item_thali",
      "name": "Special Thali",
      "quantity": 0,
      "unit_price": 90.0
    }
  ],
  "address": ""
}
```

#### Response:
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json; charset=utf-8
Content-Length: 421

{
  "type": "https://campuseats.univ.edu/errors/validation-error",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Request validation failed. One or more fields violate contract requirements.",
  "errors": [
    {
      "field": "address",
      "message": "Delivery address is required and cannot be blank."
    },
    {
      "field": "items[0].quantity",
      "message": "Quantity must be an integer >= 1."
    }
  ]
}
```
*Notice:* Both `address` and `items[0].quantity` are collected in a single pass before returning to the client.

---

### Question 5: Safe Retries and Indicating Status Codes
- **Which endpoints are safe to retry?**
  1. **All Safe Endpoints (`GET /orders`, `GET /orders/{id}`, `OPTIONS`)**: Safe by definition under RFC 9110; re-reading state changes nothing.
  2. **Idempotent Update & Delete (`PUT /orders/{id}`, `PATCH /orders/{id}`, `DELETE /orders/{id}`)**: Overwrites to desired state; repeating yields identical end state.
  3. **Idempotency-Key Protected `POST /orders`**: Safe to retry **only if** the client provides the identical `Idempotency-Key` header.
  4. **Never Safe to Retry Unchanged**: Plain `POST /orders` without an `Idempotency-Key` or any request returning a non-transient `4xx` error (such as `400`, `401`, `422`), because sending identical bad data will deterministically fail again.
- **Which status codes tell a client it is safe to retry?**
  - **`429 Too Many Requests`**: Signals that the server rejected the request solely due to temporary rate throttling. The presence of the `Retry-After` header explicitly tells the client it can retry safely after the indicated interval.
  - **`503 Service Unavailable`**: Signals transient server downtime or downstream cluster unavailability. Paired with `Retry-After`, it tells the client that the failure is temporary and safe to retry once the window expires.
  - **`504 Gateway Timeout`**: Signals a transient network hop timeout along the upstream path.

---

### Question 6: Internal Error Mapping & Information Leakage Shielding
- **Where we mapped an internal error:**
  In `POST /orders`, simulated or unexpected database exceptions (such as connection pool exhaustion, table lock deadlocks, or SQL constraint faults) are trapped in a top-level `try/catch` block.
- **Server-Side Log (Logged Privately):**
  ```text
  2026-10-13 12:18:27 [ERROR] [Incident: inc_65d544e4] Internal Database Failure: 
  CRITICAL: PostgreSQL connection pool exhausted; deadlock on table 'orders_tx' at line 412
  Traceback (most recent call last):
    File "app.py", line 277, in create_order
      raise RuntimeError("CRITICAL: PostgreSQL connection pool exhausted...")
  ```
- **What was sent to the client (`500 Internal Server Error`):**
  ```json
  {
    "type": "https://campuseats.univ.edu/errors/internal-error",
    "title": "Internal Server Error",
    "status": 500,
    "detail": "An unexpected internal error occurred. Incident reference ID: inc_65d544e4. Our operations team has been notified."
  }
  ```
- **What was hidden from the caller:**
  1. The underlying database technology (`PostgreSQL`).
  2. The internal schema and table name (`orders_tx`).
  3. The exact internal file path and line number (`app.py, line 277`).
  4. The complete Python exception traceback.
  *(This prevents attackers from exploiting internal database structures while giving support teams a clean `inc_65d544e4` correlation token to find the exact trace in private log files).*

---

### Question 7: Content Negotiation — Same Order as JSON and XML

#### 1. Requesting JSON Representation (`Accept: application/json`):
```http
GET /orders/101 HTTP/1.1
Host: 127.0.0.1:5060
Accept: application/json
```
```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
ETag: "0dc28dae3f7fae87"
Cache-Control: public, max-age=60, must-revalidate

{
  "address": "Academic Block 1 Lobby",
  "coupon_code": null,
  "created_at": "2026-10-13T06:15:00Z",
  "delivery_type": "PICKUP",
  "discount_amount": 0.0,
  "final_amount": 60.0,
  "id": "101",
  "items": [
    {
      "item_id": "item_cold_coffee",
      "name": "Cold Coffee Frappe",
      "quantity": 1,
      "unit_price": 60.0
    }
  ],
  "payment_method": "UPI",
  "status": "CONFIRMED",
  "student_id": "student_20251651038",
  "subtotal": 60.0,
  "time_slot": "14:00-14:30",
  "updated_at": "2026-10-13T06:15:00Z",
  "vendor_id": "vendor_nescafe_junction",
  "version": 1
}
```

#### 2. Requesting XML Representation (`Accept: application/xml`):
```http
GET /orders/101 HTTP/1.1
Host: 127.0.0.1:5060
Accept: application/xml
```
```http
HTTP/1.1 200 OK
Content-Type: application/xml; charset=utf-8
ETag: "0dc28dae3f7fae87"
Cache-Control: public, max-age=60, must-revalidate

<?xml version="1.0" encoding="utf-8"?>
<order>
  <id>101</id>
  <student_id>student_20251651038</student_id>
  <vendor_id>vendor_nescafe_junction</vendor_id>
  <address>Academic Block 1 Lobby</address>
  <delivery_type>PICKUP</delivery_type>
  <status>CONFIRMED</status>
  <subtotal>60.00</subtotal>
  <discount_amount>0.00</discount_amount>
  <final_amount>60.00</final_amount>
  <payment_method>UPI</payment_method>
  <version>1</version>
  <created_at>2026-10-13T06:15:00Z</created_at>
  <updated_at>2026-10-13T06:15:00Z</updated_at>
  <items>
    <item>
      <item_id>item_cold_coffee</item_id>
      <name>Cold Coffee Frappe</name>
      <quantity>1</quantity>
      <unit_price>60.00</unit_price>
    </item>
  </items>
</order>
```
