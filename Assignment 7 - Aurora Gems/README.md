# Aurora Gems — GraphQL Catalogue Service (CS543 Assignment 7)

**Course:** CS543 Web Services · IIIT Vadodara  
**Team:** CS543-Team-07 / Group 20  
**Repository:** https://github.com/maniyadaxit/Group20

> Project note: the repository's course project is CampusEats. This folder fulfills the Assignment 7 GraphQL deliverable as a small Catalogue/Menu service. “Aurora Gems” is the user-requested project label and is used for the presentation/theme; the API models catalogue products as menu items.

## Service selected
**Catalogue/Menu service**. The GraphQL API lists catalogue items and allows creating an item. The SQL table is named `menu_items`, compatible with the existing CampusEats schema concepts.

## Architecture
Browser (HTML/CSS/JS) → GraphQL endpoint (Apollo Server / Node.js) → MySQL (`mysql2`).

## Files
- `schema.graphql`: GraphQL object, Query and Mutation.
- `server.js`: Apollo Server and SQL resolvers.
- `db.js`: MySQL connection pool configured by environment variables.
- `schema.sql`: standalone database/table and four seed rows.
- `public/index.html`: responsive catalogue interface using `fetch()`.
- `.env.example`: safe local configuration template.
- `package.json`: run scripts and dependencies.
- `docs/TESTING.md`: GraphQL test requests and troubleshooting.
- `docs/DEMO_CHECKLIST.md`: before/after screenshot/video checklist.

## Requirements
- Node.js 18+
- MySQL 8+ (or compatible MySQL server)
- npm

## Run locally
From this folder:

```bash
cp .env.example .env
# Edit .env with your local MySQL username/password. Never commit .env.
npm install
mysql -u root -p < schema.sql
npm start
```

Open [http://localhost:4000/app/](http://localhost:4000/app/) for the UI. The GraphQL endpoint is [http://localhost:4000/graphql](http://localhost:4000/graphql); use the JSON examples in `docs/TESTING.md` to test queries and mutations. A health check is available at `/health`.

## Required GraphQL operations
List items:
```graphql
query { menuItems { id name price available category } }
```

Create an item:
```graphql
mutation {
  addMenuItem(input: { name: "Paneer Roll", price: 90, category: "Snacks" }) {
    id
    name
    price
    available
  }
}
```

## Answers to the assignment README questions
1. **Service picked:** CampusEats Catalogue/Menu service.
2. **Skippable field:** `category` can be skipped because it is nullable. **Non-skippable field:** `name` is declared `String!`, so clients must request a valid non-null name in the mutation and the API guarantees that returned field is non-null.
3. **WHERE mapping:** `menuItem(id: ID!)` maps the argument to `WHERE id = ?` in `Query.menuItem`. **INSERT mapping:** `Mutation.addMenuItem` executes the parameterized `INSERT INTO menu_items ...` statement and reads back the inserted row.

## Demo evidence to add before final submission
The code and seed data are prepared, but screenshots/video must be captured after you run the app against your own local MySQL instance. Save them under `docs/screenshots/before.png` and `docs/screenshots/after.png`, and add your real shareable Google Drive video URL here:
- Demonstration video: **PENDING — add the actual Google Drive share URL**.

## Security
Use `.env` for local credentials. The committed `.env.example` includes placeholders only. Use a dedicated database user rather than a privileged production account.
