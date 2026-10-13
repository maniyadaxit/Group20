# CampusEats — CS543 Web Services (Group 20)

CampusEats is a campus food-ordering system for students, staff, food vendors, and administrators. This repository consolidates the Group 20 work for CS543 Assignments 01–06, covering HTTP fundamentals, system/data design, SOAP/WSDL integration, REST integration, HTTP methods and headers, and API status codes/error validation.

## Team

| Name | Roll number | Responsibility |
|---|---|---|
| Daxit Maniya | 20251651054 | Team leader / backend |
| Ethasam | 20251651038 | Protocol / API engineering |
| Gulshan Kumar | 20251651040 | QA and testing |

## Assignment index

- [Assignment 1 — HTTP by Hand & Project Setup](./Assignment%201/)
- [Assignment 2 — System design and data schema](./Assignemet%202/)
- [Assignment 3 — SOAP/WSDL integration](./Assignment%203/)
- [Assignment 4 — Service architecture and integration](./Assignment%204/)
- [Assignment 5 — HTTP methods and headers](./Assignment%205/)
- [Assignment 6 — Status codes, errors, and validation](./Assignment%206/)

> Note: The existing folder name `Assignemet 2` is retained to avoid breaking existing links. It can be renamed after confirming no external submission links depend on it.

## Repository layout

```text
Group20/
├── Assignment 1/       # system brief, HTTP request/response log, network analysis
├── Assignemet 2/       # design PDF, schema SQL/diagrams, service diagrams
├── Assignment 3/       # integration PDF, WSDL, SOAP request/response/fault
├── Assignment 4/       # design, schema, services, SOAP examples, request evidence
├── Assignment 5/       # Flask Orders API, OpenAPI contract, tests, transcript
├── Assignment 6/       # validation/error-handling API, OpenAPI contract, tests
├── README.md
└── ReadMe.pdf          # consolidated submission overview
```

## Assignment 5 and 6: Run the API

Python 3.10+ is recommended. The two assignments have their own dependencies and should be run separately.

### Assignment 5

```bash
cd "Assignment 5"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Run tests in a second terminal:

```bash
cd "Assignment 5"
source .venv/bin/activate
pytest -q
```

### Assignment 6

```bash
cd "Assignment 6"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Run tests in a second terminal:

```bash
cd "Assignment 6"
source .venv/bin/activate
pytest -q
```

Use the endpoint and port documented in each assignment's `NOTES.md` and `openapi.yaml`. Do not run both services on the same port simultaneously.

## What to review

- Assignment-wise requirements and implementation notes are in each folder.
- SQL schemas and editable Draw.io diagrams are included where applicable.
- REST API contracts are documented in the OpenAPI YAML files.
- Automated tests and request transcripts are included with Assignments 5 and 6.
- Review the actual test output locally before submission; repository presence alone does not establish that every test passes.

## Submission links

- GitHub repository: https://github.com/maniyadaxit/Group20
- Demonstration video (Google Drive): **Add the final shareable link here before submission.** Set access to **Anyone with the link** and verify the link in a signed-out/private browser window.

## Before submitting

1. Run the Assignment 5 and Assignment 6 test suites and record the results.
2. Review the design PDFs, schema diagrams, WSDL/SOAP examples, OpenAPI contracts, and request transcripts for Assignments 1–6.
3. Record one end-to-end demonstration showing the relevant working tasks.
4. Add the Google Drive demonstration URL to this README and to `ReadMe.pdf`.
5. Submit once per group through the team leader, as instructed.

