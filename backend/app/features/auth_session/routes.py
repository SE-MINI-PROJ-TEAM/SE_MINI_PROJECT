from flask import Blueprint, current_app, jsonify

from app.core.errors import ApiError, bad_request, unauthorized
from app.core.security import (
    auth_required,
    burn_password_check,
    clear_auth_cookie,
    current_user,
    issue_token,
    session_payload,
    set_auth_cookie,
    verify_password,
)
from app.core.timeutil import utcnow
from app.core.validation import json_body, sanitize
from app.extensions import db, limiter
from app.models import User

bp = Blueprint("auth_session", __name__)


def _login_limit():
    return f"{current_app.config['LOGIN_RATE_LIMIT_PER_MIN']}/minute"


def _login_limit_disabled():
    return current_app.config["LOGIN_RATE_LIMIT_PER_MIN"] <= 0


@bp.post("/auth/login")
@limiter.limit(_login_limit, exempt_when=_login_limit_disabled)
def login():
    data = json_body()
    identifier = sanitize(data.get("identifier"))
    password = data.get("password")
    if not identifier or not isinstance(password, str) or not password:
        raise bad_request("Email / institutional ID and password are required.", "MISSING_FIELD")

    user = User.query.filter(
        (User.email == identifier.lower()) | (User.institutional_id == identifier.upper())
    ).first()
    if user is None:
        burn_password_check(password)
        raise unauthorized("Invalid credentials.", "INVALID_CREDENTIALS")
    if not verify_password(password, user.password_hash):
        raise unauthorized("Invalid credentials.", "INVALID_CREDENTIALS")
    if not user.is_active:
        raise ApiError(403, "ACCOUNT_INACTIVE", "This account has been deactivated. Contact an administrator.")

    user.last_login_at = utcnow()
    db.session.commit()

    response = jsonify({"status": "success", "user": session_payload(user)})
    return set_auth_cookie(response, issue_token(user))


@bp.post("/auth/logout")
def logout():
    return clear_auth_cookie(jsonify({"status": "success"}))


@bp.get("/auth/me")
@auth_required(allow_temporary=True)
def me():
    return jsonify({"status": "success", "user": session_payload(current_user())})
