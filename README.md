# CampusEats | CS543 Web Services | Group 20

CampusEats is a proposed campus food-ordering system for students and staff, campus food vendors, and administrators. This repository contains the team's design and web-service artifacts for CS543 Assignments 01–07.

## Team

| Name | Roll number | Responsibility |
|---|---|---|
| Daxit Maniya | 20251651054 | Team leader / backend architecture |
| Ethasam | 20251651038 | Protocol and API engineering |
| Gulshan Kumar | 20251651040 | Testing and QA |

## Assignment index

| Assignment | Focus | Main artifacts |
|---|---|---|
| [01](./Assignment%201/) | HTTP by Hand and project setup | System brief, curl request/response log, DevTools network analysis |
| [02](./Assignemet%202/) | Service boundaries and data design | Design PDF, schema SQL, editable Draw.io and PNG diagrams |
| [03](./Assignment%203/) | SOAP payment-partner contract | Integration PDF, WSDL, SOAP request, success response and fault |
| [04](./Assignment%204/) | Service architecture and integration | Design/integration PDFs, schema, service diagrams, HTTP evidence, WSDL/SOAP examples |
| [05](./Assignment%205/) | HTTP methods and headers | Flask Orders API, OpenAPI contract, automated tests, curl transcript |
| [06](./Assignment%206/) | Status codes, errors and validation | Flask Orders API, OpenAPI contract, automated tests, request transcript |
| [07](./Assignment%207/) | GraphQL API, MySQL catalogue and browser UI | Schema, resolvers, SQL seed data, UI and demo checklist |

## Run Assignment 7 GraphQL catalogue

```bash
cd "Assignment 7"
cp .env.example .env  # edit DB_PASSWORD first
npm install
mysql -u root -p < schema.sql
npm start
```

Open `http://localhost:4000/app/`. GraphQL endpoint: `http://localhost:4000/graphql`. See the folder README and `docs/TESTING.md` for query/mutation examples. The demonstration video and before/after screenshots still need to be captured from a local run.

> The historical folder name `Assignemet 2` is retained so existing paths continue to work.

## Consolidated submission document

- [ReadMe.pdf](./ReadMe.pdf) - assignment descriptions, artifact map, API setup/testing steps, and submission checklist.

## Run Assignment 5 API

From the repository root:

```bash
cd "Assignment 5"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Default local port: **5050** (can be overridden using `PORT`).

In a second terminal, from the repository root:

```bash
cd "Assignment 5"
source .venv/bin/activate
pytest -q tests
```

## Run Assignment 6 API

From the repository root:

```bash
cd "Assignment 6"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Default local port: **5060** (can be overridden using `PORT`).

In a second terminal, from the repository root:

```bash
cd "Assignment 6"
source .venv/bin/activate
pytest -q tests
```

Run only the root `tests/` directory for each assignment. The repository also contains nested copies of the submission packages, so a bare recursive test discovery can collect duplicate test modules.

## Repository layout

```text
Group20/
├── Assignment 1/       # HTTP fundamentals and project brief
├── Assignemet 2/       # system/data design and service diagrams
├── Assignment 3/       # WSDL and SOAP examples
├── Assignment 4/       # architecture, HTTP evidence, schema and integration
├── Assignment 5/       # HTTP methods/headers Orders API
├── Assignment 6/       # status/error/validation Orders API
├── README.md
├── ReadMe.pdf
└── .env.example
```

## Important implementation notes

- Assignment 2's `schema.sql` uses MySQL-style syntax (including `AUTO_INCREMENT` and `ENUM`); select a compatible database or translate the DDL before running it on another engine.
- Assignment 5 and Assignment 6 APIs use an in-memory example store for the lab work. Do not treat them as production persistence or deploy them with permissive demo settings.
- SOAP XML files contain demonstration payloads only. Keys and tokens are placeholders; never commit production credentials. If a value was ever real, revoke/rotate it with its provider.
- This repository contains deliverables and implementation notes, but not a complete archive of the original assignment handouts. Check each folder against the LMS rubric before submission.
- Test files and transcripts are present; run the test commands above and inspect the actual results before claiming the tests pass.

## Submission links

**GitHub repository:** https://github.com/maniyadaxit/Group20

**Google Drive working demonstration:** **PENDING - paste the actual share URL here before submission.** Upload the demonstration video to Drive, set General access to **Anyone with the link** (Viewer), and verify it in a private/incognito browser window. Then regenerate `ReadMe.pdf` with the same URL.

Submit once per group through the team leader, as instructed.
