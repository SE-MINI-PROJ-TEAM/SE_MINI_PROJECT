from flask import Blueprint, jsonify

from app.core.security import (
    PASSWORD_RULES,
    auth_required,
    current_user,
    issue_token,
    session_payload,
    set_auth_cookie,
)
from app.core.validation import json_body

from . import service

bp = Blueprint("password_reset", __name__)


@bp.get("/auth/password-policy")
def password_policy():
    return jsonify({"status": "success", "rules": list(PASSWORD_RULES)})


@bp.post("/auth/change-password")
@auth_required(allow_temporary=True)
def change_password():
    data = json_body()
    user = service.change_password(current_user(), data.get("current_password"), data.get("new_password"))
    response = jsonify({"status": "success", "message": "Password updated.", "user": session_payload(user)})
    return set_auth_cookie(response, issue_token(user))
