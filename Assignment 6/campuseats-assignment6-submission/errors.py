"""
CampusEats Orders Service - Standard RFC 7807 / RFC 9457 Problem Details
CS543 · Web Services · Assignment 6: Honest responses: status codes, errors & validation
"""
import json
from flask import Response

# Base URI for stable error type catalogue (Part B2)
TYPE_BASE_URI = "https://campuseats.univ.edu/errors"

TYPE_CATALOGUE = {
    # Assignment 6 specific type strings (B2)
    "empty-cart": f"{TYPE_BASE_URI}/empty-cart",
    "item-unavailable": f"{TYPE_BASE_URI}/item-unavailable",
    "payment-declined": f"{TYPE_BASE_URI}/payment-declined",
    "order-not-found": f"{TYPE_BASE_URI}/order-not-found",
    "illegal-transition": f"{TYPE_BASE_URI}/illegal-transition",
    "validation-error": f"{TYPE_BASE_URI}/validation-error",
    
    # Standard HTTP failure types
    "bad-request": f"{TYPE_BASE_URI}/bad-request",
    "unauthorized": f"{TYPE_BASE_URI}/unauthorized",
    "not-found": f"{TYPE_BASE_URI}/not-found",
    "conflict": f"{TYPE_BASE_URI}/conflict",
    "precondition-failed": f"{TYPE_BASE_URI}/precondition-failed",
    "not-acceptable": f"{TYPE_BASE_URI}/not-acceptable",
    "rate-limit-exceeded": f"{TYPE_BASE_URI}/rate-limit-exceeded",
    "service-unavailable": f"{TYPE_BASE_URI}/service-unavailable",
    "internal-error": f"{TYPE_BASE_URI}/internal-error",
}

STATUS_TO_DEFAULT_TYPE = {
    400: "bad-request",
    401: "unauthorized",
    404: "order-not-found",
    406: "not-acceptable",
    409: "illegal-transition",
    412: "precondition-failed",
    422: "validation-error",
    429: "rate-limit-exceeded",
    500: "internal-error",
    503: "service-unavailable",
}

STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    404: "Order Not Found",
    406: "Not Acceptable",
    409: "Illegal State Transition",
    412: "Precondition Failed",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

def problem(
    status: int,
    detail: str,
    title: str = None,
    error_type: str = None,
    errors: list = None,
    headers: dict = None
) -> Response:
    """
    Standard Problem Details response constructor (RFC 7807 / RFC 9457).
    Guarantees Content-Type: application/problem+json; charset=utf-8.
    Includes optional field-level validation errors[] array for 422 (Part B3).
    """
    resolved_title = title or STATUS_TITLES.get(status, "Error")
    
    # Resolve stable type URI from catalogue
    if error_type:
        resolved_type = TYPE_CATALOGUE.get(error_type, error_type)
    else:
        default_key = STATUS_TO_DEFAULT_TYPE.get(status, "internal-error")
        resolved_type = TYPE_CATALOGUE.get(default_key, f"{TYPE_BASE_URI}/{default_key}")

    body = {
        "type": resolved_type,
        "title": resolved_title,
        "status": status,
        "detail": detail
    }

    # B3: Field-level validation errors array
    if errors:
        body["errors"] = errors

    json_payload = json.dumps(body, indent=2)
    response = Response(
        response=json_payload,
        status=status,
        mimetype="application/problem+json"
    )
    # C4: Set Content-Type with charset=utf-8 on every response
    response.headers["Content-Type"] = "application/problem+json; charset=utf-8"

    if headers:
        for k, v in headers.items():
            response.headers[k] = v

    return response
