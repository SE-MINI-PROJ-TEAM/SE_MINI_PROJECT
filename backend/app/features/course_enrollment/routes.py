from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN, ROLE_STUDENT
from app.core.security import auth_required, current_user
from app.core.settings import current_term, enrollment_open
from app.core.validation import json_body, sanitize, to_int

from . import service

bp = Blueprint("course_enrollment", __name__)


@bp.get("/catalog")
@auth_required(ROLE_STUDENT, ROLE_ADMIN)
def catalog():
    return jsonify({"status": "success", **service.catalog(current_user().id, sanitize(request.args.get("search")))})


@bp.post("/enrollments")
@auth_required(ROLE_STUDENT)
def enroll():
    course_id = to_int(json_body().get("course_id"), "course_id", minimum=1)
    enrollment, course, enrolled = service.enroll(current_user().id, course_id)
    return (
        jsonify(
            {
                "status": "success",
                "message": f"Enrolled in {course.code} (section {course.section}).",
                "enrollment_id": enrollment.id,
                "seats_available": max(course.capacity - enrolled, 0),
            }
        ),
        201,
    )


@bp.get("/enrollments/mine")
@auth_required(ROLE_STUDENT)
def my_enrollments():
    return jsonify({"status": "success", "enrollments": service.my_enrollments(current_user().id)})


@bp.get("/enrollments/window")
@auth_required()
def get_window():
    return jsonify({"status": "success", "open": enrollment_open(), "term": current_term()})


@bp.put("/enrollments/window")
@auth_required(ROLE_ADMIN)
def set_window():
    is_open = service.set_window(current_user(), json_body().get("open"))
    return jsonify({"status": "success", "open": is_open})
