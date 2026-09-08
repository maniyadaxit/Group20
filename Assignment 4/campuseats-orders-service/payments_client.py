import os
import time
import random
import requests

# Resolved from an environment variable — never hard-coded.
PAYMENTS_SERVICE_URL = os.environ.get("PAYMENTS_SERVICE_URL", "http://localhost:6001")


class PaymentFailed(Exception):
    """The Payments service rejected the request (a 4xx). Never retried."""


class PaymentUnavailable(Exception):
    """The Payments service could not be reached after all retries."""


def initiate_payment(order_id, amount, method, idempotency_key, max_retries=3, timeout=2.0):
    """
    Calls Payments to charge for an order.

    Hardening (Assignment 4, Part D):
      - timeout on every attempt
      - exponential backoff with jitter between retries
      - only network errors / 5xx are retried; a 4xx is never retried,
        since the request itself is invalid and retrying won't fix that
      - every attempt (including retries) carries the same
        Idempotency-Key, so a retried create never double-charges
    """
    url = f"{PAYMENTS_SERVICE_URL}/payments"
    payload = {"orderId": order_id, "amount": amount, "method": method}
    headers = {"Idempotency-Key": idempotency_key}

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            if attempt < max_retries:
                _sleep_backoff(attempt)
            continue

        if resp.status_code < 300:
            return resp.json()

        if 400 <= resp.status_code < 500:
            raise PaymentFailed(f"Payments rejected the request: {resp.status_code} {resp.text}")

        # 5xx — safe to retry
        last_error = f"{resp.status_code} {resp.text}"
        if attempt < max_retries:
            _sleep_backoff(attempt)

    raise PaymentUnavailable(f"Payments service unreachable after {max_retries} attempts: {last_error}")


def _sleep_backoff(attempt):
    backoff = (2 ** (attempt - 1)) + random.uniform(0, 0.5)  # exponential + jitter
    time.sleep(backoff)
