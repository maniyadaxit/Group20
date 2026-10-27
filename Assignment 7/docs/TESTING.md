# CampusEats — Assignment 7 Testing Report

## 1. Project Overview

CampusEats is a campus food catalogue application built using Node.js, Express, GraphQL, and MySQL. It displays menu items, retrieves individual items, and supports adding new catalogue items through a GraphQL mutation.

## 2. Environment Setup

Requirements:
- Node.js and npm
- MySQL Server
- Dependencies listed in `package.json`

Run these commands from the `Assignment 7` directory:

```bash
cp .env.example .env
npm install
npm run check
```

Configure the local `.env` file with the correct database credentials. Do not commit `.env` to GitHub.

Create the database and tables:

```bash
mysql -u root < schema.sql
```

Start the application:

```bash
npm start
```

## 3. Application Endpoints

- Frontend: http://localhost:4000/app/
- GraphQL API: http://localhost:4000/graphql
- Health check: http://localhost:4000/health

## 4. Test Cases and Results

### Test 1: Health Check

Endpoint: `http://localhost:4000/health`

Observed response:

```json
{
  "status": "ok",
  "service": "campuseats-catalogue"
}
```

Result: PASS

### Test 2: Retrieve All Menu Items

```graphql
query {
  menuItems {
    id
    name
    description
    price
    category
    available
  }
}
```

Observed result: The API successfully returned the original catalogue items, including Paneer Wrap, Masala Fries, Cold Coffee, and Veg Sandwich.

Result: PASS

### Test 3: Retrieve One Menu Item

```graphql
query {
  menuItem(id: "1") {
    id
    name
    description
    price
    category
    available
  }
}
```

Observed result: The API returned Paneer Wrap with ID `1` and price `110`.

Result: PASS

### Test 4: Add a Menu Item

```graphql
mutation {
  addMenuItem(
    input: {
      name: "Test Cheese Sandwich"
      description: "Test item for Assignment 7"
      price: 99
      category: "Snacks"
      available: true
    }
  ) {
    id
    name
    description
    price
    category
    available
  }
}
```

Observed result:
The API successfully created a test item and returned its generated ID.

Result: PASS

### Test 5: Verify Database Persistence

The MySQL `menu_items` table was inspected using:

```sql
USE campuseats_catalogue;

SELECT id, name, price, category, is_available
FROM menu_items;
```

The inserted test item appeared in the database. The database uses `is_available` as its column name, while the GraphQL API exposes the field as `available`.

Result: PASS

## 5. Screenshots

Screenshots are stored in `docs/screenshots/`.

They include:
- Frontend catalogue
- Health check response
- GraphQL queries
- GraphQL mutation response
- MySQL records

## 6. Troubleshooting

- `ECONNREFUSED`: Confirm that MySQL is running and check the database host and port.
- `ER_ACCESS_DENIED_ERROR`: Check the local credentials in `.env`.
- `ER_BAD_DB_ERROR`: Confirm that `schema.sql` was executed against the database configured in `.env`.
- GraphQL validation errors: Check the schema and required mutation arguments. The `addMenuItem` mutation requires an `input` object.
- Browser issues: Ensure the application is running and use `http://localhost:4000/app/`.

## 7. Notes

- Do not commit `.env` or database passwords.
- The project was tested locally using MySQL and the GraphQL API.
- Complete any additional submission requirements, such as a demo video, if required.
