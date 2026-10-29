"""Standardised REST error envelope: {"status": "error", "code": "...", "message": "..."} (SAD 4.3)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger("srs.errors")


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def bad_request(message, code="BAD_REQUEST", details=None):
    return ApiError(400, code, message, details)


def unauthorized(message="Authentication required.", code="UNAUTHORIZED"):
    return ApiError(401, code, message)


def forbidden(message="You do not have permission to perform this action.", code="FORBIDDEN"):
    return ApiError(403, code, message)


def not_found(message="Resource not found.", code="NOT_FOUND"):
    return ApiError(404, code, message)


def conflict(message, code="CONFLICT"):
    return ApiError(409, code, message)


def _envelope(status, code, message, details=None):
    body = {"status": "error", "code": code, "message": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return _envelope(err.status, err.code, err.message, err.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        code = (err.name or "ERROR").upper().replace(" ", "_")
        return _envelope(err.code or 500, code, err.description)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        log.exception("Unhandled exception")
        return _envelope(500, "INTERNAL_ERROR", "An unexpected error occurred.")
