require('dotenv').config();

const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { ApolloServer } = require('@apollo/server');
const { startStandaloneServer } = require('@apollo/server/standalone');
const { ApolloServerPluginLandingPageLocalDefault } = require('@apollo/server/plugin/landingPage/default');
const pool = require('./db');

const typeDefs = fs.readFileSync(path.join(__dirname, 'schema.graphql'), 'utf8');

const resolvers = {
  Query: {
    menuItems: async () => {
      const [rows] = await pool.execute(
        'SELECT id, name, price, available, category, description FROM menu_items ORDER BY id'
      );
      return rows.map(normalizeMenuItem);
    },
    menuItem: async (_parent, { id }) => {
      const [rows] = await pool.execute(
        'SELECT id, name, price, available, category, description FROM menu_items WHERE id = ?',
        [Number(id)]
      );
      return rows[0] ? normalizeMenuItem(rows[0]) : null;
    }
  },
  Mutation: {
    addMenuItem: async (_parent, { input }) => {
      const name = typeof input.name === 'string' ? input.name.trim() : '';
      const price = Number(input.price);
      if (!name) throw new Error('name must not be blank');
      if (!Number.isFinite(price) || price < 0) throw new Error('price must be a non-negative number');

      const available = input.available ?? true;
      const category = input.category?.trim() || null;
      const description = input.description?.trim() || null;

      const [result] = await pool.execute(
        'INSERT INTO menu_items (name, price, is_available, category, description) VALUES (?, ?, ?, ?, ?)',
        [name, price, available, category, description]
      );
      const [rows] = await pool.execute(
        'SELECT id, name, price, is_available AS available, category, description FROM menu_items WHERE id = ?',
        [result.insertId]
      );
      return normalizeMenuItem(rows[0]);
    }
  }
};

function normalizeMenuItem(row) {
  return {
    ...row,
    id: String(row.id),
    price: Number(row.price),
    available: Boolean(row.available ?? row.is_available)
  };
}

async function main() {
  const port = Number(process.env.PORT || 4000);
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    plugins: [ApolloServerPluginLandingPageLocalDefault({ embed: true })]
  });

  const { url } = await startStandaloneServer(server, {
    listen: { port, host: '0.0.0.0' },
    context: async () => ({ pool })
  });

  console.log(`Aurora Gems Catalogue GraphQL API ready at ${url}`);
  console.log(`UI can be served at http://localhost:${port}/app after starting the optional static server below.`);
}

// GraphQL-only endpoint based on the assignment tutorial.
main().catch((error) => {
  console.error('Failed to start GraphQL server:', error.message);
  process.exitCode = 1;
});
