# tutorial 7 — Campus Library GraphQL Application

## Overview
This project implements a Campus Library application using Node.js, Apollo Server, GraphQL, and MySQL. It provides queries to retrieve authors and books, relationship resolvers, and a mutation to add new books.

## Technologies Used
- Node.js
- Apollo Server
- GraphQL
- MySQL
- HTML and CSS
- JavaScript

## Database
Database: `gqldemo`

Tables:
- `authors`: stores author IDs, names, and countries.
- `books`: stores book IDs, titles, publication years, and author IDs.

The `books.author_id` field references `authors.id`.

## GraphQL Features
### Queries
- `authors`: retrieves authors.
- `author(id)`: retrieves one author by ID.
- `books`: retrieves all books.

### Relationships
- `Author.books`: retrieves books written by an author.
- `Book.author`: retrieves the author of a book.

### Mutation
- `addBook(title, year, authorId)`: adds a book to the database.

## Running the Application
1. Start the MySQL service.
2. Ensure the `gqldemo` database and its tables are created.
3. Open a terminal in the `Assignment 8` folder.
4. Install dependencies using `npm install`.
5. Start the GraphQL server using `node server.js`.
6. Open `http://localhost:4000/` to access Apollo Sandbox.
7. Open `public/index.html` in a browser to use the front-end interface.

## Screenshots
The `screenshots` folder contains:
1. `01-campus-library.png` — application interface.
2. `02-authors-query.png` — GraphQL authors query.
3. `03-add-book-mutation.png` — adding a book through GraphQL.
4. `04-mysql-records.png` — MySQL book and author records.

## Conclusion
The application demonstrates GraphQL queries, mutations, relational data fetching, and a simple web interface connected to a MySQL database.