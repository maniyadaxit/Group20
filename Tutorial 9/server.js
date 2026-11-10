require('dotenv').config();

const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '1h';

if (!JWT_SECRET || JWT_SECRET.length < 32) {
  throw new Error('Set JWT_SECRET in your .env file (at least 32 characters).');
}

app.use(express.json({ limit: '10kb' }));
app.use(express.static(path.join(__dirname, 'public')));

// Demo users: passwords are hashed at startup; plaintext passwords are never stored.
const users = [
  {
    id: 1,
    email: 'asha@campus.edu',
    role: 'customer',
    hash: bcrypt.hashSync('customer123', 10)
  },
  {
    id: 2,
    email: 'mealhub@campus.edu',
    role: 'restaurant',
    hash: bcrypt.hashSync('resto123', 10)
  }
];

let items = [
  { id: 1, name: 'Veg Thali', price: 90 },
  { id: 2, name: 'Paneer Roll', price: 70 }
];
let nextId = 3;

// POST /login — verify credentials and issue a signed, expiring JWT.
app.post('/login', (req, res) => {
  const email = typeof req.body?.email === 'string'
    ? req.body.email.trim().toLowerCase()
    : '';
  const password = typeof req.body?.password === 'string'
    ? req.body.password
    : '';

  const user = users.find((candidate) => candidate.email === email);
  if (!user || !bcrypt.compareSync(password, user.hash)) {
    return res.status(401).json({ error: 'bad login' });
  }

  const token = jwt.sign(
    { role: user.role },
    JWT_SECRET,
    { subject: String(user.id), expiresIn: JWT_EXPIRES_IN, algorithm: 'HS256' }
  );

  return res.status(200).json({
    token,
    user: { id: user.id, email: user.email, role: user.role }
  });
});

// Authentication middleware — require a valid Bearer token.
function auth(req, res, next) {
  const header = req.get('Authorization') || '';
  const match = header.match(/^Bearer\s+(.+)$/i);

  if (!match) {
    return res.status(401).json({ error: 'invalid or missing token' });
  }

  try {
    const payload = jwt.verify(match[1], JWT_SECRET, {
      algorithms: ['HS256']
    });
    const userId = Number(payload.sub);
    const user = users.find((candidate) => candidate.id === userId);

    if (!user || user.role !== payload.role) {
      return res.status(401).json({ error: 'invalid or missing token' });
    }

    req.user = { id: user.id, email: user.email, role: user.role };
    return next();
  } catch (error) {
    return res.status(401).json({ error: 'invalid or missing token' });
  }
}

// Authorization middleware — authenticate first, then check the user's role.
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'forbidden' });
    }
    return next();
  };
}

// GET /items — any authenticated user may read the menu.
app.get('/items', auth, (req, res) => {
  return res.status(200).json(items);
});

// GET /items/:id — authenticated users may read an individual dish.
app.get('/items/:id', auth, (req, res) => {
  const id = Number(req.params.id);
  const item = items.find((dish) => dish.id === id);

  if (!Number.isInteger(id) || !item) {
    return res.status(404).json({ error: 'not found' });
  }
  return res.status(200).json(item);
});

// POST /items — only restaurant/admin roles may add dishes.
app.post('/items', auth, requireRole('restaurant', 'admin'), (req, res) => {
  const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
  const price = req.body?.price === '' || req.body?.price === undefined
    ? 0
    : Number(req.body.price);

  if (!name) {
    return res.status(422).json({ error: 'name required' });
  }
  if (name.length > 80 || !Number.isFinite(price) || price < 0) {
    return res.status(422).json({ error: 'invalid name or price' });
  }

  const item = { id: nextId++, name, price };
  items.push(item);
  return res.status(201).json(item);
});

// Malformed JSON should return a clear JSON error.
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({ error: 'invalid JSON body' });
  }
  return next(err);
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Secured CampusEats Catalogue running at http://localhost:${PORT}`);
  });
}

module.exports = { app, auth, requireRole };
