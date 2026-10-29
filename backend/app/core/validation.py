"""Input validation / sanitisation helpers (PRJ-SR-005). Queries are always parameterised via the ORM."""
import re
from decimal import Decimal, InvalidOperation

from flask import request

from app.core.errors import bad_request

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9(][0-9 \-()]{5,18}[0-9]$")
_TAG_RE = re.compile(r"<[^>]*>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise bad_request("A JSON object request body is required.", "INVALID_BODY")
    return data


def sanitize(value):
    """Strip markup tags and control characters, then trim whitespace."""
    if value is None:
        return ""
    text = _CTRL_RE.sub("", str(value))
    text = _TAG_RE.sub("", text)
    return text.strip()


def clean_text(data, field, *, required=True, max_len=255, min_len=0, label=None):
    label = label or field.replace("_", " ")
    raw = data.get(field)
    if raw is not None and not isinstance(raw, (str, int, float)):
        raise bad_request(f"{label.capitalize()} must be text.", "INVALID_FIELD")
    text = sanitize(raw)
    if not text:
        if required:
            raise bad_request(f"{label.capitalize()} is required.", "MISSING_FIELD")
        return ""
    if len(text) < min_len:
        raise bad_request(f"{label.capitalize()} must be at least {min_len} characters.", "INVALID_FIELD")
    if len(text) > max_len:
        raise bad_request(f"{label.capitalize()} must be at most {max_len} characters.", "INVALID_FIELD")
    return text


def valid_email(email):
    return bool(EMAIL_RE.match(email or ""))


def valid_phone(phone):
    return bool(PHONE_RE.match(phone or ""))


def to_int(value, label, *, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise bad_request(f"{label} must be a whole number.", "INVALID_FIELD")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise bad_request(f"{label} must be a whole number.", "INVALID_FIELD")
    if minimum is not None and number < minimum:
        raise bad_request(f"{label} must be at least {minimum}.", "INVALID_FIELD")
    if maximum is not None and number > maximum:
        raise bad_request(f"{label} must be at most {maximum}.", "INVALID_FIELD")
    return number


def to_decimal(value, label, *, minimum=None, maximum=None):
    if isinstance(value, bool) or value is None or value == "":
        raise bad_request(f"{label} must be a number.", "INVALID_FIELD")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise bad_request(f"{label} must be a number.", "INVALID_FIELD")
    if not number.is_finite():
        raise bad_request(f"{label} must be a number.", "INVALID_FIELD")
    if minimum is not None and number < Decimal(str(minimum)):
        raise bad_request(f"{label} must be at least {minimum}.", "INVALID_FIELD")
    if maximum is not None and number > Decimal(str(maximum)):
        raise bad_request(f"{label} must be at most {maximum}.", "INVALID_FIELD")
    return number


def page_params(default_per_page=25, max_per_page=100):
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = int(request.args.get("per_page", default_per_page))
    except ValueError:
        raise bad_request("Pagination parameters must be integers.", "INVALID_FIELD")
    return page, max(1, min(per_page, max_per_page))
