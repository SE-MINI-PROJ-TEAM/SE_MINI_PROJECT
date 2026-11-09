from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN
from app.core.security import auth_required, current_user
from app.core.validation import json_body, to_int

from . import service

bp = Blueprint("attendance_override", __name__)


@bp.get("/attendance/override/courses")
@auth_required(ROLE_ADMIN)
def courses():
    return jsonify({"status": "success", "courses": service.course_options()})


@bp.get("/attendance/override/sessions")
@auth_required(ROLE_ADMIN)
def sessions():
    course_id = to_int(request.args.get("course_id"), "course_id", minimum=1)
    return jsonify({"status": "success", "sessions": service.list_sessions(course_id)})


@bp.get("/attendance/override/sessions/<int:session_id>")
@auth_required(ROLE_ADMIN)
def session_detail(session_id):
    return jsonify({"status": "success", **service.session_detail(session_id)})


@bp.put("/attendance/override/sessions/<int:session_id>")
@auth_required(ROLE_ADMIN)
def override(session_id):
    applied = service.override(current_user(), session_id, json_body())
    return jsonify(
        {"status": "success", "message": f"{applied} attendance record(s) overridden and logged.", "changed": applied}
    )
