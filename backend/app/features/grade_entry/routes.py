from flask import Blueprint, jsonify

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.core.security import auth_required, current_user
from app.core.validation import json_body

from . import service

bp = Blueprint("grade_entry", __name__)


@bp.get("/grades/courses")
@auth_required(ROLE_FACULTY)
def my_courses():
    return jsonify({"status": "success", "courses": service.my_courses(current_user())})


@bp.get("/grades/courses/<int:course_id>")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def course_grid(course_id):
    return jsonify({"status": "success", **service.course_grid(course_id, current_user())})


@bp.put("/grades/courses/<int:course_id>")
@auth_required(ROLE_FACULTY)
def save_drafts(course_id):
    saved = service.save_drafts(course_id, current_user(), json_body().get("students"))
    return jsonify({"status": "success", "message": f"Draft marks saved for {saved} student(s).", "saved": saved})


@bp.put("/grades/courses/<int:course_id>/students/<student_code>")
@auth_required(ROLE_FACULTY)
def save_student(course_id, student_code):
    state, total = service.save_student(course_id, student_code, current_user(), json_body())
    body = {"status": "success", "grade_state": state}
    if total is not None:
        body["weighted_total"] = float(total)
    return jsonify(body)
