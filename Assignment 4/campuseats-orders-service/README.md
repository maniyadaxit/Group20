# CampusEats Orders Service — Assignment 4

## Setup
```bash
pip install -r requirements.txt
```

## Run
Two processes: the Orders service, and a stand-in for your Payments service
(replace with your real Tutorial 4 Payments service when you have it — see
the note at the top of `mock_payments.py`).

```bash
# terminal 1
python3 mock_payments.py            # runs on :6001

# terminal 2
PAYMENTS_SERVICE_URL=http://localhost:6001 python3 app.py   # runs on :6000
```

## Test
```bash
pytest tests/ -v
```

## Validate the OpenAPI contract
```bash
python3 -m openapi_spec_validator openapi.yaml
```

## Files
- `openapi.yaml` — the contract (Part B)
- `models.py`, `store.py`, `errors.py`, `app.py` — implementation (Part C)
- `payments_client.py` — hardened outbound call to Payments (Part D)
- `mock_payments.py` — throwaway stand-in for your real Payments service, for local testing only
- `tests/test_orders.py` — the four required tests (C8)
- `curl_transcript.txt` — real transcript captured from a live run (create, idempotent repeat, 400, 404, 409, 422)
- `pytest_output.txt`, `openapi_validation_output.txt` — captured terminal output for submission
- `NOTES.md` — resource table, A5 justification, D3 fallback reasoning, and the 5 write-up answers (fill in the Assignment-3-specific placeholders)
