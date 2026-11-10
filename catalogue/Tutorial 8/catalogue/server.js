const express = require('express');
const path = require('path');

const app = express();
const PORT = Number(process.env.PORT) || 3000;

// Middleware: parse JSON request bodies and serve the front-end.
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// In-memory menu data (the tutorial introduces a database in a later lecture).
let items = [
  { id: 1, name: 'Veg Thali', price: 90 },
  { id: 2, name: 'Paneer Roll', price: 70 }
];
let nextId = 3;

// GET /items — return the complete menu.
app.get('/items', (req, res) => {
  res.status(200).json(items);
});

// GET /items/:id — return one dish, or a 404 response.
app.get('/items/:id', (req, res) => {
  const id = Number(req.params.id);

  if (!Number.isInteger(id) || id < 1) {
    return res.status(404).json({ error: 'not found' });
  }

  const item = items.find((dish) => dish.id === id);
  if (!item) {
    return res.status(404).json({ error: 'not found' });
  }

  return res.status(200).json(item);
});

// POST /items — validate and add a dish.
app.post('/items', (req, res) => {
  const body = req.body || {};
  const name = typeof body.name === 'string' ? body.name.trim() : '';
  const price = body.price === '' || body.price === undefined
    ? 0
    : Number(body.price);

  if (!name) {
    return res.status(422).json({ error: 'name required' });
  }

  if (!Number.isFinite(price) || price < 0) {
    return res.status(422).json({ error: 'price must be a non-negative number' });
  }

  const item = { id: nextId++, name, price };
  items.push(item);

  return res.status(201).json(item);
});

// Return JSON for malformed JSON bodies instead of an HTML error page.
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({ error: 'invalid JSON body' });
  }
  return next(err);
});

app.listen(PORT, () => {
  console.log(`CampusEats Catalogue running at http://localhost:${PORT}`);
});
