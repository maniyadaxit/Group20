"""
CampusEats Orders Service - Standard RFC 7807 Problem Details
"""
from flask import jsonify

ERROR_TYPE_MAP = {
    400: "https://campuseats.univ.edu/errors/bad-request",
    401: "https://campuseats.univ.edu/errors/unauthorized",
    403: "https://campuseats.univ.edu/errors/forbidden",
    404: "https://campuseats.univ.edu/errors/not-found",
    405: "https://campuseats.univ.edu/errors/method-not-allowed",
    406: "https://campuseats.univ.edu/errors/not-acceptable",
    409: "https://campuseats.univ.edu/errors/conflict",
    412: "https://campuseats.univ.edu/errors/precondition-failed",
    422: "https://campuseats.univ.edu/errors/unprocessable-entity",
    429: "https://campuseats.univ.edu/errors/too-many-requests",
    500: "https://campuseats.univ.edu/errors/internal-server-error",
}

ERROR_TITLE_MAP = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    409: "Conflict",
    412: "Precondition Failed",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
}

def problem(status: int, detail: str, title: str = None, error_type: str = None):
    """
    Produce a consistent RFC 7807 problem details response.
    No endpoint may invent its own error format.
    """
    resolved_title = title or ERROR_TITLE_MAP.get(status, "Error")
    resolved_type = error_type or ERROR_TYPE_MAP.get(status, "about:blank")
    
    payload = {
        "type": resolved_type,
        "title": resolved_title,
        "status": status,
        "detail": detail
    }
    
    response = jsonify(payload)
    response.status_code = status
    response.content_type = "application/json"
    return response
