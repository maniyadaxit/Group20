# CS543 · Web Services · Assignment 5: HTTP Methods & Headers

## Engineering Documentation & Architectural Audit

**Course:** CS543 · Web Services  
**Institution:** Indian Institute of Information Technology Vadodara (IIITV)  
**Instructor:** Dr. Pramit Mazumdar (`pramit.mazumdar@iiitvadodara.ac.in`)  
**Service:** CampusEats Orders Service  

---

## Team Information

| Serial | Team Member Name | Roll Number | Role |
| :---: | :--- | :---: | :--- |
| **1** | **Daxit Maniya** | **20251651054** | Team Leader & Backend Architect |
| **2** | **Ethasam** | **20251651038** | Protocol & API Engineer |
| **3** | **Gulshan Kumar** | **20251651040** | QA & Test Automation Specialist |

**Team ID:** `CS543-Team-07`  
**Repository:** `campuseats` / `E-commerce-main`  

---

# Part A · Methods & The Message

### A1. CampusEats Method Map
All action verbs have been audited and removed from URL paths. URIs identify nouns/resources exclusively, while the HTTP verbs define the operations.

| Action / Capability | HTTP Method | Target URL | Safe? | Idempotent? | Success Status | Description |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| List & Filter Orders | `GET` | `/orders` | **Yes** | **Yes** | `200 OK` | Paginated search across order summaries filtered by query parameters. |
| Fetch Single Order | `GET` | `/orders/{order_id}` | **Yes** | **Yes** | `200 OK` / `304 Not Modified` | Retrieves representation of an order by its unique ID. Supports conditional reads. |
| Discover Allowed Methods | `OPTIONS` | `/orders/{order_id}` | **Yes** | **Yes** | `200 OK` / `204 No Content` | Returns permitted HTTP verbs via the `Allow` header and CORS options. |
| Create New Order | `POST` | `/orders` | **No** | **No** | `201 Created` | Instantiates a new order resource. Requires Bearer token; made retry-safe via `Idempotency-Key`. |
| Update Order Details | `PUT` | `/orders/{order_id}` | **No** | **Yes** | `200 OK` | Replaces/updates delivery instructions or timeslots. Protected via `If-Match` optimistic locking. |
| Cancel Active Order | `POST` | `/orders/{order_id}/cancel` | **No** | **No** | `200 OK` | Sub-resource state transition. Cancels active unfulfilled orders. |
| Delete / Discard Order | `DELETE` | `/orders/{order_id}` | **No** | **Yes** | `204 No Content` | Removes/purges order record from active tracking. |

---

### A2. Modeling Non-CRUD Actions
RPC-style verbs leaked into endpoints (such as `POST /cancelOrder` or `POST /orders/42/doCheckout`) violate REST resource modeling:
- In REST, an action that changes resource state without simply replacing its entity body is modeled as a **POST to a state-changing sub-resource**.
- In our service, order cancellation is modeled as:
  $$\text{POST } \texttt{/orders/42/cancel}$$
  *(or $\text{POST } \texttt{/orders/42/cancellation}$)*
- This makes the intent explicit: it creates a cancellation event/transition under order `42`, rather than inventing an unversioned top-level verb URL.

---

### A3. Safe & Idempotent Analysis
- **Safe Endpoints (`GET`, `OPTIONS`, `HEAD`):**
  - Calling `GET /orders` or `GET /orders/{order_id}` executes read-only operations. Under RFC 9110 §9.2.1, safe methods must not cause any user-visible state mutation. We guarantee that no `GET` handler modifies database state, charges payments, or alters order progress.
  - Naturally retry-safe: Network dropouts can safely trigger automatic retries.
- **Idempotent Endpoints (`PUT`, `DELETE`):**
  - `PUT /orders/{order_id}`: Overwrites properties to a target state. Sending the same update 5 times leaves the resource in the exact same state as sending it once ($f(f(x)) = f(x)$).
  - `DELETE /orders/{order_id}`: First delete returns `204 No Content`. Subsequent retried deletes find the item already absent and yield `404 Not Found` (or `204`), with no additional database mutation.
- **Neither Safe nor Idempotent (`POST /orders`):**
  - Creating an order alters balance, reduces kitchen capacity, and writes new records. If a network packet is dropped after the server processes the order, an automatic client retry would produce a duplicate order and double-charge the student.
  - **Remedy:** We harden `POST /orders` with the `Idempotency-Key` header (explained in C3).

---

### A4. Query Parameters for Pure Reads
The `GET /orders` endpoint filters, sorts, and paginates exclusively through query string parameters:
- **Filtering:** `GET /orders?status=CONFIRMED&student_id=student_20251651054`
- **Sorting:** `GET /orders?sort=created_at&order=desc`
- **Pagination:** `GET /orders?page=1&limit=10`
By keeping all query criteria in the URL string, the request remains a pure `GET` that intermediate caching proxies and browser histories can bookmark and cache.

---

### A5. OPTIONS + Allow Header and Method Override
1. **OPTIONS on Single Order (`OPTIONS /orders/42`):**
   ```http
   HTTP/1.1 200 OK
   Allow: GET, PUT, PATCH, DELETE, OPTIONS, HEAD
   Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD
   Content-Length: 0
   ```
2. **`X-HTTP-Method-Override` Fallback:**
   For legacy enterprise firewalls or browser forms that restrict HTTP verbs to `GET` and `POST`, our custom WSGI middleware intercepts incoming requests:
   ```http
   POST /orders/42 HTTP/1.1
   Host: 127.0.0.1:5050
   X-HTTP-Method-Override: PUT
   Content-Type: application/json
   ```
   The middleware rewrites `REQUEST_METHOD` to `PUT` before dispatching to the endpoint handler, enabling safe method tunneling without altering clean REST URI paths.

---

### A6. Complete Labelled HTTP Exchange

#### 1. Request
```http
POST /orders HTTP/1.1                           <-- [Request Line: Verb, URI, HTTP Version]
Host: 127.0.0.1:5050                             <-- [Host Header]
User-Agent: curl/8.7.1                           <-- [Client User-Agent]
Accept: application/json                         <-- [Requested Response Content-Type]
Content-Type: application/json                   <-- [Request Payload MIME Type]
Authorization: Bearer token_daxit_20251651054    <-- [Bearer Authentication Token]
Idempotency-Key: idemp_key_run_001               <-- [Idempotency Token for Safe Retries]
Content-Length: 221                              <-- [Length of Request Body in Bytes]

{                                                <-- [Start of Request JSON Body]
  "student_id": "student_20251651054",
  "vendor_id": "vendor_canteen_central",
  "items": [
    {
      "item_id": "item_thali",
      "name": "Special Thali",
      "quantity": 1,
      "unit_price": 90.0
    }
  ],
  "delivery_type": "PICKUP",
  "coupon_code": "CAMPUS50"
}                                                <-- [End of Request JSON Body]
```

#### 2. Response
```http
HTTP/1.1 201 Created                             <-- [Status Line: HTTP Version, Status Code, Reason]
Server: CampusEats-Orders/1.0 (REST/HTTP)        <-- [Origin Server Fingerprint Header]
Date: Tue, 13 Oct 2026 06:12:00 GMT              <-- [Origin Generation Timestamp Header]
Content-Type: application/json                   <-- [Response Body MIME Type]
Content-Length: 437                              <-- [Response Body Size]
Location: /orders/247144                         <-- [Target URI of Newly Created Resource]
ETag: "9e5c468e2175c2e1"                         <-- [Entity Hash for Caching & Concurrency]
Cache-Control: no-store                          <-- [Fresh Transaction Caching Directive]
X-RateLimit-Limit: 100                           <-- [Allocated Per-Client Request Quota]
X-RateLimit-Remaining: 98                        <-- [Remaining Request Budget in Current Window]
X-Content-Type-Options: nosniff                  <-- [MIME-Sniffing Attack Prevention Header]
Strict-Transport-Security: max-age=31536000      <-- [Enforce HTTPS Transport Layer Security]
Access-Control-Allow-Origin: *                   <-- [Cross-Origin Resource Sharing Permission]

{                                                <-- [Start of Response JSON Body]
  "coupon_code": "CAMPUS50",
  "created_at": "2026-10-13T06:12:00.123456+00:00",
  "delivery_type": "PICKUP",
  "discount_amount": 20.0,
  "drop_zone": null,
  "final_amount": 70.0,
  "id": "247144",
  "items": [
    {
      "item_id": "item_thali",
      "name": "Special Thali",
      "quantity": 1,
      "unit_price": 90.0
    }
  ],
  "payment_method": "WALLET",
  "status": "PLACED",
  "student_id": "student_20251651054",
  "subtotal": 90.0,
  "time_slot": null,
  "updated_at": "2026-10-13T06:12:00.123456+00:00",
  "vendor_id": "vendor_canteen_central",
  "version": 1
}                                                <-- [End of Response JSON Body]
```

---

# Part B · Headers On Every Message

### B1. Content-Type & Content Negotiation
- **`Content-Type: application/json`**: Present on every message containing a body.
- **`Accept` Negotiation**: The service parses the client's `Accept` header. If a client explicitly demands an unsupported format (such as `Accept: application/xml` or `Accept: text/csv`), the service responds with `406 Not Acceptable` containing an RFC 7807 problem payload.
- **Gzip Compression**: If client supplies `Accept-Encoding: gzip` and the JSON response exceeds 500 bytes, the server transparently applies gzip compression and sets `Content-Encoding: gzip`.

### B2. Status Codes & The Double Duty of Location
- `201 Created`: Returned upon successful order creation, with the `Location: /orders/{id}` header pointing to the newly minted entity.
- `200 OK`: Returned on successful reads (`GET`) and mutations (`PUT`, `POST /cancel`).
- `204 No Content`: Returned on `DELETE /orders/{id}` with an strictly empty body.
- `400 Bad Request`: Returned when JSON syntax is malformed (e.g. unclosed brackets, missing quotes).
- `401 Unauthorized`: Returned when the `Authorization` header is missing or empty.
- `404 Not Found`: Returned when the requested order ID does not exist in the store.
- `406 Not Acceptable`: Returned when the server cannot fulfill the requested `Accept` MIME type.
- `409 Conflict`: Returned on invalid state transitions (e.g. canceling an order already completed or cancelled).
- `412 Precondition Failed`: Returned when an update's `If-Match` header does not match the current ETag.
- `422 Unprocessable Entity`: Returned when the syntax is valid JSON, but violates business domain validation (e.g., empty `items` array, negative item quantities).
- `429 Too Many Requests`: Returned when client exceeds rate limit budget.
- **The Double Duty of `Location`**:
  1. On a **`201 Created`**, `Location` identifies the identity URL of the **newly created resource** (e.g. `/orders/247144`).
  2. On a **`3xx Redirection`** (e.g. `301 Moved Permanently` or `307 Temporary Redirect`), `Location` identifies the **target destination URL** where the client should immediately redirect its request.

### B3. Authorization Header Handling
All mutating and user-sensitive endpoints inspect the incoming `Authorization` header:
- Requires format: `Authorization: Bearer <token>`.
- If missing or empty: returns `401 Unauthorized` along with the response header:
  `WWW-Authenticate: Bearer realm="CampusEats", error="invalid_token"`

### B4. Caching with Cache-Control and ETag
For single-resource reads (`GET /orders/{order_id}`):
- `ETag`: Formatted as a deterministic SHA-256 hash across entity fields and version: `ETag: "9e5c468e2175c2e1"`.
- `Cache-Control`: Formatted as `public, max-age=60, must-revalidate`.
- Whenever an order transitions or updates, its internal version and state change, instantly producing a new ETag hash.

### B5. Rate-Limit Signalling
To communicate consumption limits transparently, every HTTP response returns:
- `X-RateLimit-Limit: 100` (Max requests allowed per 60-second client window)
- `X-RateLimit-Remaining: 98` (Remaining budget)
When the limit is exhausted ($0$), the server returns `429 Too Many Requests` accompanied by:
- `Retry-After: 60` (Number of seconds client must back off before retrying).
The tracking key is scoped per-client (`Authorization` Bearer token or client IP), never globally, ensuring one aggressive client cannot starve others.

### B6. Cross-Origin Resource Sharing (CORS)
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD`
- `Access-Control-Allow-Headers: Content-Type, Authorization, If-Match, If-None-Match, Idempotency-Key, X-HTTP-Method-Override`

### B7. Security Headers
- `X-Content-Type-Options: nosniff`: Instructs modern browsers never to override MIME types via content sniffing.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`: Mandates HTTPS transport connections for one full year.
- `Server: CampusEats-Orders/1.0 (REST/HTTP)`: Standard system server identifier.
- `Date`: Generated RFC 1123 HTTP timestamp.

---

# Part C · Caching & Safe Retries

### C1. Conditional GET ($\rightarrow 304\text{ Not Modified}$)
When a client caches an order representation, it saves the `ETag`. On subsequent reads, it sends:
```http
GET /orders/42 HTTP/1.1
If-None-Match: "9e5c468e2175c2e1"
```
If the order has not mutated:
1. Server returns `304 Not Modified`.
2. Response contains **zero body bytes**.
3. **Benefits:** Eliminates network payload transmission and serialization overhead.

### C2. Conditional Write ($\rightarrow 412\text{ Precondition Failed}$)
When multiple clients attempt concurrent updates on an order (such as a student changing delivery drop zone while a vendor confirms preparation):
1. Client fetches order and receives `ETag: "9e5c468e2175c2e1"`.
2. Client submits update with optimistic lock check:
   ```http
   PUT /orders/42 HTTP/1.1
   If-Match: "9e5c468e2175c2e1"
   ```
3. If another user already modified the order in the interim, the server ETag has changed. The server aborts the overwrite and yields `412 Precondition Failed`.
4. **Benefits:** Prevents the classic lost-update (mid-air collision) concurrency hazard.

### C3. Idempotency Key Path
- **Mechanism:** For `POST /orders`, the client attaches a unique `Idempotency-Key: <uuid>`.
- The server stores the resulting `(status_code, headers, body)` mapped to that key in an in-memory idempotency table.
- If network disconnection causes the client to retransmit the exact same request, the server detects the existing key and returns the original cached `201 Created` response without re-executing order placement logic.
- **Where a duplicate would do real damage:**
  1. **Double Financial Charge:** Deducting funds twice from student campus wallets or cards.
  2. **Kitchen Wastage & Chaos:** Printing duplicate kitchen preparation tickets at the campus vendor, causing physical food wastage and dispute reconciliation overhead.

---

### C4. The Safe-Retry Plan

| Endpoint | Method | Risk Level | Primary Hazard | Applied Retry Mechanism | Technical Justification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `/orders` | `POST` | **Critical** | Duplicate order creation, double wallet debit, duplicate food prep. | **`Idempotency-Key`** | `POST` is neither safe nor idempotent. Caching response keyed by UUID guarantees exactly-once execution on network retry. |
| `/orders/{id}` | `GET` | **None** | Stale data read / bandwidth consumption. | **`If-None-Match` (ETag)** | `GET` is safe & idempotent. Conditional revalidation yields `304 Not Modified` with 0 body bytes if unchanged. |
| `/orders/{id}` | `PUT` | **High** | Lost update (mid-air collision between student and vendor). | **`If-Match` (ETag)** | `PUT` is idempotent but unsafe against concurrent overwrite. `If-Match` rejects write with `412` if state modified. |
| `/orders/{id}/cancel` | `POST` | **Medium** | Re-triggering refund / double processing cancellation logic. | **`Idempotency-Key`** | Non-CRUD action. Ensures repeated cancellation request returns identical `200` response safely. |
| `/orders/{id}` | `DELETE` | **Low** | Repeated removal on dropped ACK. | **Native Idempotence** | `DELETE` is idempotent by definition. Repeated attempts safely return `404 Not Found` without side effects. |

---

# Part D · Headers Matrix (D2)

| Endpoint | HTTP Method | Request Headers Needed / Accepted | Response Headers Set |
| :--- | :---: | :--- | :--- |
| `/orders` | `GET` | `Accept`, `Authorization` *(opt)*, `If-None-Match` | `Content-Type: application/json`, `X-RateLimit-*`, `Access-Control-*`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security` |
| `/orders` | `POST` | `Content-Type: application/json`, `Authorization: Bearer <t>`, `Idempotency-Key: <k>`, `Accept` | `Location: /orders/{id}`, `ETag: "..."`, `Cache-Control: no-store`, `Content-Type: application/json`, `X-RateLimit-*`, `X-Content-Type-Options` |
| `/orders/{id}` | `GET` | `Accept`, `If-None-Match: "..."` | `ETag: "..."`, `Cache-Control: public, max-age=60`, `Content-Type: application/json` *(on 200)*, `X-RateLimit-*`, `Security Headers` |
| `/orders/{id}` | `PUT` | `Content-Type: application/json`, `Authorization: Bearer <t>`, `If-Match: "..."`, `X-HTTP-Method-Override` *(opt)* | `ETag: "<new_hash>"`, `Cache-Control: no-cache`, `Content-Type: application/json`, `X-RateLimit-*`, `Security Headers` |
| `/orders/{id}/cancel` | `POST` | `Authorization: Bearer <t>`, `Idempotency-Key: <k>` | `ETag: "..."`, `Content-Type: application/json`, `X-RateLimit-*`, `Security Headers` |
| `/orders/{id}` | `DELETE` | `Authorization: Bearer <t>` | `X-RateLimit-*`, `Security Headers`, *(empty body, 204 No Content)* |
| `/orders/{id}` | `OPTIONS` | `Origin`, `Access-Control-Request-Method` | `Allow: GET, PUT, PATCH, DELETE, OPTIONS, HEAD`, `Access-Control-Allow-*`, `Content-Length: 0` |

---

# Answers to Assignment 5 Questions

### Question 1: Three Endpoints, Success Status, and the Single Most Important Response Header
1. **`POST /orders` $\rightarrow$ `201 Created` $\rightarrow$ `Location`**
   - *Why it matters most:* A client posting a new resource does not choose the new entity's URI. The `Location` header is the authoritative contract that tells the caller the exact canonical address (`/orders/247144`) where the created entity now lives. Without it, the client cannot inspect, track, or cancel the order it just placed.
2. **`GET /orders/{order_id}` $\rightarrow$ `200 OK` $\rightarrow$ `ETag`**
   - *Why it matters most:* The `ETag` turns a static response into a verifiable state token. It allows the client to perform bandwidth-free conditional checks (`If-None-Match` $\rightarrow$ `304`) and powers optimistic concurrency protection on subsequent writes (`If-Match` $\rightarrow$ `412`).
3. **`GET /orders/{order_id}` $\rightarrow$ `429 Too Many Requests` (Throttled) $\rightarrow$ `Retry-After`**
   - *Why it matters most:* When an API budget is breached, simply returning an error without guidance causes panic retries that amplify server distress. `Retry-After: 60` provides deterministic pacing, instructing the client precisely how many seconds it must hold off before trying again.

---

### Question 2: Safe & Idempotent Breakdown & The Unsafe/Non-Idempotent Remediation
- **Safe Endpoints:** `GET /orders`, `GET /orders/{id}`, `OPTIONS /orders`, `OPTIONS /orders/{id}`. Calling them produces zero state change on the server.
- **Idempotent Endpoints:** All safe endpoints above, plus `PUT /orders/{id}` and `DELETE /orders/{id}`. Repeating them $N$ times leaves system state identical to invoking them once.
- **Neither Safe nor Idempotent:** `POST /orders` (Order Creation) and `POST /orders/{id}/cancel` (Order Cancellation).
  - Calling `POST /orders` multiple times without protection creates multiple distinct orders, reserves multiple batches of kitchen inventory, and attempts multiple payment deductions.
- **How we made it retry-safe:**
  - We implemented client-driven **`Idempotency-Key` tracking** (RFC draft *The Idempotency-Key HTTP Header Field*).
  - When the client initiates `POST /orders`, it includes a unique UUID in `Idempotency-Key: <key>`.
  - The server records the generated `(201, headers, body)` mapped to that key in an atomic cache.
  - If a network dropped-connection occurs and the client retries with the same `Idempotency-Key`, the server intercepts the duplicate, bypasses order generation and payment charging, and immediately replays the cached `201 Created` payload.

---

### Question 3: ETag Demonstration, 304 Request, and 412 Rejection
- **Observed ETag from Service:** `ETag: "9e5c468e2175c2e1"`
- **The Request Returning `304 Not Modified`:**
  ```http
  GET /orders/42 HTTP/1.1
  Host: 127.0.0.1:5050
  If-None-Match: "9e5c468e2175c2e1"
  ```
  *Response:* `HTTP/1.1 304 Not Modified` with zero bytes in body.
  *What it saves:* Saves entire JSON payload retransmission, bandwidth, CPU serialization time, and reduces mobile client data consumption.
- **The Write Returning `412 Precondition Failed`:**
  ```http
  PUT /orders/42 HTTP/1.1
  Host: 127.0.0.1:5050
  Authorization: Bearer token_daxit_20251651054
  If-Match: "stale_etag_hash_0000"
  Content-Type: application/json

  {"time_slot": "15:00-15:30"}
  ```
  *Response:* `HTTP/1.1 412 Precondition Failed`
  *What it prevents:* Prevents the **Lost Update Problem**. If two dispatch managers or a student and vendor edit order attributes simultaneously, the second write will not silently overwrite changes made by the first. The second writer is forced to re-read the updated record and re-apply changes deliberately.

---

### Question 4: 422 vs 400 — Exact Requests & Definitive Difference
1. **The `400 Bad Request` Request:**
   ```http
   POST /orders HTTP/1.1
   Host: 127.0.0.1:5050
   Content-Type: application/json
   Authorization: Bearer token_daxit_20251651054

   {"student_id": "s1", items: [unquoted_broken_syntax]}
   ```
   *Why 400:* The request body violates **HTTP protocol / JSON syntactic syntax**. The parser fails before business logic is ever invoked.
2. **The `422 Unprocessable Entity` Request:**
   ```http
   POST /orders HTTP/1.1
   Host: 127.0.0.1:5050
   Content-Type: application/json
   Authorization: Bearer token_daxit_20251651054

   {
     "student_id": "student_20251651054",
     "vendor_id": "vendor_canteen_central",
     "items": []
   }
   ```
   *Why 422:* The JSON syntax is $100\%$ valid and successfully parsed. However, it violates **semantic domain business rules** (an order cannot contain zero menu items).
3. **The Core Difference:**
   - `400` means *"I cannot even parse what you sent me (syntax failure)."*
   - `422` means *"I understand perfectly what you sent, but business domain logic refuses to accept it (semantic failure)."*

---

### Question 5: Browser Cross-Origin Block with Server 200 OK
- **Who blocked it?** The **Client Browser's Same-Origin Policy (SOP) engine** blocked it, NOT the server.
- **Why the server logs show `200`:** The browser successfully dispatched the HTTP request across the wire to the server, and the server executed it and replied with `200 OK`. However, when the browser inspected the response headers, it found no permission granting the calling webpage's origin access to read the data. Consequently, the browser withheld the response data from the JavaScript application context.
- **Which response header fixes it?**
  $$\texttt{Access-Control-Allow-Origin: *}$$
  *(or $\texttt{Access-Control-Allow-Origin: https://client.campuseats.edu}$)*
  Along with handling preflight `OPTIONS` requests via `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers`.

---

### Question 6: Cache-Control Allowing Caching vs Requiring `no-store`
1. **Where Caching is Allowed:**
   - **Response:** `GET /orders/42`
   - **Directive:** `Cache-Control: public, max-age=60, must-revalidate`
   - **Why:** The order details are stable once fetched, but will be revalidated via ETag before expiration. Allowing intermediate caches and client storage to keep the representation reduces server load and provides instant UI rendering.
2. **Where `no-store` is Mandatory:**
   - **Response:** `POST /orders` (Order Creation with payment transaction response)
   - **Directive:** `Cache-Control: no-store`
   - **Why:** Creating an order produces a ephemeral, high-security financial transaction receipt containing authorization tokens, payment references, and real-time wallet balances. Under RFC 9111, `no-store` instructs all intermediate caches, shared proxies, and browsers never to write any portion of this message to non-volatile disk, protecting student financial credentials from snooping.

---

### Question 7: Search as GET vs When POST is Justified
- **Current Setup:** Search is a `GET /orders?status=...&student_id=...&sort=...`.
- **When `POST` would be the right choice instead:**
  1. **Excessive Query Complexity & Size:** When the search query contains deeply nested JSON filter trees, polygon spatial boundaries for delivery zones, or thousands of item IDs that exceed URL length limits (historically 2048 characters in standard proxies).
  2. **Sensitive Information in Filters:** If the search filter contains sensitive data (e.g., student national IDs or private payment tokens) that must not appear in web server access logs, browser history, or proxy cache indexes.
- **What you give up by switching to `POST`:**
  1. **URL Shareability & Bookmarking:** Users and frontends cannot bookmark, email, or copy-paste a search URL.
  2. **HTTP Caching:** `POST` responses are non-cacheable by default according to standard HTTP intermediary proxies.
  3. **Idempotence & Safety Guarantees:** Browsers will warn users with annoying *"Confirm Form Resubmission"* modals upon page refresh or back-button navigation.

---

### Question 8: The Role of `Location` on `201 Created` vs `3xx Redirection`
- **On a `201 Created`:**
  - `Location: /orders/247144`
  - It points to the **permanent canonical identity URI of the newly created resource**. It tells the client: *"Your creation request succeeded, and this is where the new object lives."*
- **On a `3xx Redirection` (e.g. `301 Moved Permanently` or `307 Temporary Redirect`):**
  - `Location: https://campuseats.univ.edu/api/v1/orders`
  - It points to the **target redirection endpoint where the client should re-send or continue its request**. It tells the client: *"The resource you asked for is not here; follow this link to find it."*
