from flask import Blueprint, jsonify

from app.core.constants import ROLE_FACULTY, ROLE_STUDENT
from app.core.security import auth_required, current_user
from app.core.validation import json_body

from . import service

bp = Blueprint("profile", __name__)


@bp.get("/profile")
@auth_required(ROLE_STUDENT, ROLE_FACULTY)
def get_profile():
    return jsonify({"status": "success", "profile": service.build_view(current_user())})


@bp.put("/profile")
@auth_required(ROLE_STUDENT, ROLE_FACULTY)
def update_profile():
    view = service.update_profile(current_user(), json_body())
    return jsonify({"status": "success", "message": "Profile updated.", "profile": view})
