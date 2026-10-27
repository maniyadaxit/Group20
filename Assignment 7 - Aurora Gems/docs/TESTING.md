# Testing and GraphQL examples

Start MySQL and create the database:

```bash
mysql -u root -p < schema.sql
```

Copy the local configuration and install packages:

```bash
cp .env.example .env
# Update DB_PASSWORD in .env before use
npm install
npm run check
npm start
```

## Query all menu items

POST JSON to `http://localhost:4000/graphql`:

```json
{
  "query": "query { menuItems { id name price available category description } }"
}
```

## Query by id (WHERE clause)

```json
{
  "query": "query GetMenuItem($id: ID!) { menuItem(id: $id) { id name price available } }",
  "variables": { "id": "1" }
}
```

The `Query.menuItem` resolver runs `SELECT ... FROM menu_items WHERE id = ?` with a parameterized value.

## Mutation (INSERT)

```json
{
  "query": "mutation Add($input: AddMenuItemInput!) { addMenuItem(input: $input) { id name price available } }",
  "variables": {
    "input": {
      "name": "Paneer Roll",
      "price": 90,
      "category": "Snacks",
      "description": "Demo item",
      "available": true
    }
  }
}
```

The `Mutation.addMenuItem` resolver inserts with placeholders, then selects the inserted row by `insertId`.

## Expected response shape

```json
{
  "data": {
    "menuItems": [
      {
        "id": "1",
        "name": "Paneer Wrap",
        "price": 110,
        "available": true,
        "category": "Wraps",
        "description": "Paneer, fresh vegetables and house sauce"
      }
    ]
  }
}
```

The browser UI is served from the same origin at `http://localhost:4000/app/`, and the health check is `http://localhost:4000/health`.

## Troubleshooting
- `ECONNREFUSED`: start MySQL and check `DB_HOST`/port.
- `ER_ACCESS_DENIED_ERROR`: check the local credentials in `.env`.
- `ER_BAD_DB_ERROR`: run `schema.sql` against the same database specified by `DB_NAME`.
- Browser CORS error: use the HTML file through the same origin/static server configured for your local setup, or configure an explicit local-origin CORS policy before running separate dev ports. This server's default starter is GraphQL-only; the UI file can be opened in a browser, but browsers may block cross-origin calls depending on your setup.
