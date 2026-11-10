# CampusEats Secure Catalogue — CS543 Tutorial 9

This project implements the API Security Tutorial: password hashing with bcrypt, JWT login, authentication middleware, role-based authorization, and a protected catalogue page.

## Requirements

- Node.js 18+
- npm

## Setup

From this `Tutorial 9` directory:

```bash
npm install
cp .env.example .env
```

Edit `.env` and set `JWT_SECRET` to a private random value of at least 32 characters. Never commit `.env`.

Start the server:

```bash
npm start
```

Open http://localhost:3000.

## Demo accounts

| Role | Email | Password | Permissions |
| --- | --- | --- | --- |
| Customer | asha@campus.edu | customer123 | Read the menu |
| Restaurant | mealhub@campus.edu | resto123 | Read the menu and add dishes |

These are tutorial-only accounts. Replace seeded users with database-backed accounts before production use.

## API endpoints

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| POST | `/login` | Public | Verify credentials and return a JWT |
| GET | `/items` | Authenticated | Return all dishes |
| GET | `/items/:id` | Authenticated | Return one dish or 404 |
| POST | `/items` | Restaurant/admin | Validate and add a dish |

### Login

```bash
curl -i -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mealhub@campus.edu","password":"resto123"}'
```

Copy the returned token and set it in your terminal:

```bash
TOKEN="paste-token-here"
```

### Authentication: no token returns 401

```bash
curl -i http://localhost:3000/items
```

### Authenticated menu read returns 200

```bash
curl -i http://localhost:3000/items \
  -H "Authorization: Bearer $TOKEN"
```

### Restaurant can add a dish: 201 Created

```bash
curl -i -X POST http://localhost:3000/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Masala Dosa","price":60}'
```

### Customer cannot add a dish: 403 Forbidden

Log in with the customer account, copy its token, and send the same POST request with that token. The server authenticates the customer but denies the restaurant-only operation.

## Security concepts demonstrated

1. **Password hashing:** bcrypt hashes demo passwords at startup. Passwords are never stored in plaintext.
2. **Authentication:** `POST /login` checks the email and password and signs a JWT.
3. **JWT verification:** the auth middleware requires `Authorization: Bearer <token>`, verifies the HS256 signature and expiry, and resolves the subject to a known user.
4. **Authorization:** `requireRole('restaurant', 'admin')` protects dish creation.
5. **HTTP status codes:** 401 means missing/invalid identity; 403 means identity is known but the action is forbidden; 422 means invalid input.
6. **Secret management:** the signing secret is loaded from `.env` and excluded from Git.
7. **Input validation:** the API validates dish name and non-negative numeric price.

## Important limitations

- Users and dishes are in memory and reset when the server restarts.
- Demo credentials are for classroom practice only.
- The browser keeps the demo JWT in JavaScript memory (not localStorage) and clears it on logout or a 401 response.
- Use HTTPS, persistent database-backed users, rate limiting, secure deployment secrets, and a stronger production session/token strategy before deployment.
- The tutorial does not implement per-resource ownership checks; those are a separate IDOR protection concern.

## Expected authorization flow

- No token / invalid / expired token → **401**.
- Valid customer token + GET menu → **200**.
- Valid restaurant token + GET menu → **200**.
- Valid restaurant token + POST dish → **201**.
- Valid customer token + POST dish → **403**.
- Missing dish name or invalid price → **422**.
