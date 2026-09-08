from flask import jsonify


class ValidationError(Exception):
    """400 — a malformed request body or query parameter."""
    def __init__(self, detail, status=400, title="Bad Request"):
        self.detail = detail
        self.status = status
        self.title = title


class NotFoundError(ValidationError):
    def __init__(self, detail):
        super().__init__(detail, status=404, title="Not Found")


class ConflictError(ValidationError):
    def __init__(self, detail):
        super().__init__(detail, status=409, title="Conflict")


class UnprocessableError(ValidationError):
    def __init__(self, detail):
        super().__init__(detail, status=422, title="Unprocessable Entity")


def problem(status, title, detail, type_="about:blank"):
    """
    The one error shape used everywhere: {type, title, status, detail}.
    No endpoint invents its own error format.
    """
    body = {"type": type_, "title": title, "status": status, "detail": detail}
    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"
    return resp
