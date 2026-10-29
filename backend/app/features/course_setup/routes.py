from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN
from app.core.security import auth_required
from app.core.validation import json_body, page_params, sanitize

from . import service

bp = Blueprint("course_setup", __name__)


@bp.get("/courses")
@auth_required(ROLE_ADMIN)
def list_courses():
    page, per_page = page_params(default_per_page=20)
    result, items = service.list_courses(sanitize(request.args.get("search")), page, per_page)
    return jsonify(
        {"status": "success", "courses": items, "page": result.page, "pages": result.pages, "total": result.total}
    )


@bp.get("/courses/faculty-options")
@auth_required(ROLE_ADMIN)
def faculty_options():
    return jsonify({"status": "success", "faculty": service.faculty_options()})


@bp.get("/courses/<int:course_id>")
@auth_required(ROLE_ADMIN)
def get_course(course_id):
    course = service.get_course(course_id)
    return jsonify({"status": "success", "course": service.serialize(course, service.enrolled_count(course.id))})


@bp.post("/courses")
@auth_required(ROLE_ADMIN)
def create_course():
    course = service.create_course(json_body())
    return jsonify({"status": "success", "course": service.serialize(course)}), 201


@bp.put("/courses/<int:course_id>")
@auth_required(ROLE_ADMIN)
def update_course(course_id):
    course = service.update_course(course_id, json_body())
    return jsonify({"status": "success", "course": service.serialize(course, service.enrolled_count(course.id))})
