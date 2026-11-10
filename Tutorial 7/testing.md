# Assignment 8 — Testing Report

## 1. Database Setup
**Test:** Create the `gqldemo` database and its tables.

**Expected result:** The `authors` and `books` tables are created successfully with sample records.

**Status:** Passed

## 2. Authors Query
**Query:** `authors`

**Test:** Retrieve all authors, including their names, countries, and associated books.

**Expected result:** Author information and related books are returned.

**Status:** Passed

## 3. Books Query
**Query:** `books`

**Test:** Retrieve the list of books.

**Expected result:** Book IDs, titles, publication years, and author relationships are returned.

**Status:** Passed

## 4. Add Book Mutation
**Mutation:** `addBook(title, year, authorId)`

**Test:** Add a book titled `GraphQL for Beginners` with publication year 2025 and author ID 2.

**Expected result:** The new book is inserted into MySQL and its details are returned.

**Status:** Passed

## 5. Author–Book Relationships
**Test:** Retrieve an author's books and each book's author.

**Expected result:** The API returns the correct relationships using the foreign key `books.author_id`.

**Status:** Passed

## 6. Front-End Testing
**Test:** Open the Campus Library interface, search and filter books, change sorting, and submit the Add Book form.

**Expected result:** The interface displays database records and allows a book to be added through GraphQL.

**Status:** Verify in browser

## Conclusion
The database setup, GraphQL API, and add-book mutation were tested successfully. The front-end interactions should also be checked in the browser before final submission.