// server.js
const express = require('express');
const app = express();

app.use(express.json());         
app.use(express.static('public'));

let items = [
  { id: 1, name: "Mushroom", price: 110, veg: true },
  { id: 2, name: 'Paneer Roll', price: 70, veg: true },
];
let nextId = 3;


app.get('/items', (req, res) => {
  const { veg } = req.query;
  if (veg === 'true' || veg === 'false') {
    return res.json(items.filter(i => i.veg === (veg === 'true')));
  }
  res.json(items);
});

// GET /items/:id -- one dish, or 404
app.get('/items/:id', (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'not found' });
  res.json(item);
});

// POST /items -- add a dish
app.post('/items', (req, res) => {
  const { name, price, veg } = req.body;
  if (!name) return res.status(422).json({ error: 'name required' });
  const item = {
    id: nextId++,
    name,
    price: Number(price) || 0,
    veg: veg === undefined ? true : Boolean(veg),
  };
  items.push(item);
  res.status(201).json(item); // 201 Created + the new dish
});

// DELETE /items/:id -- remove a dish, reply 204
app.delete('/items/:id', (req, res) => {
  const id = Number(req.params.id);
  const index = items.findIndex(i => i.id === id);
  if (index === -1) return res.status(404).json({ error: 'not found' });
  items.splice(index, 1);
  res.status(204).end();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`CampusEats Catalogue running on port ${PORT}`));
