from datetime import timedelta

from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.core.errors import bad_request
from app.core.security import auth_required, current_user
from app.core.timeutil import parse_iso, utcnow
from app.core.validation import json_body, page_params, to_int

from . import service

bp = Blueprint("schedule", __name__)


@bp.get("/schedule/course-options")
@auth_required(ROLE_ADMIN)
def course_options():
    return jsonify({"status": "success", "courses": service.course_options()})


@bp.post("/schedule/sessions")
@auth_required(ROLE_ADMIN)
def create_sessions():
    sessions = service.create_sessions(json_body())
    return jsonify({"status": "success", "message": f"{len(sessions)} session(s) scheduled.", "sessions": sessions}), 201


@bp.get("/schedule/sessions")
@auth_required(ROLE_ADMIN)
def list_sessions():
    page, per_page = page_params(default_per_page=20)
    course_id = request.args.get("course_id")
    result, items = service.list_sessions(to_int(course_id, "course_id", minimum=1) if course_id else None, page, per_page)
    return jsonify(
        {"status": "success", "sessions": items, "page": result.page, "pages": result.pages, "total": result.total}
    )


@bp.delete("/schedule/sessions/<int:session_id>")
@auth_required(ROLE_ADMIN)
def delete_session(session_id):
    service.delete_session(session_id)
    return jsonify({"status": "success", "message": "Session removed."})


@bp.get("/schedule/calendar")
@auth_required()
def calendar():
    try:
        start = parse_iso(request.args["from"]) if request.args.get("from") else utcnow() - timedelta(days=1)
        end = parse_iso(request.args["to"]) if request.args.get("to") else start + timedelta(days=8)
    except (ValueError, TypeError):
        raise bad_request("'from' and 'to' must be ISO-8601 date-times.", "INVALID_DATETIME")
    if end <= start or end - start > timedelta(days=62):
        raise bad_request("The calendar range must be between 1 and 62 days.", "INVALID_TIME_RANGE")
    course_id = request.args.get("course_id")
    sessions = service.calendar(
        current_user(), start, end, to_int(course_id, "course_id", minimum=1) if course_id else None
    )
    return jsonify({"status": "success", "sessions": sessions})


@bp.get("/schedule/my-courses")
@auth_required(ROLE_FACULTY)
def my_courses():
    return jsonify({"status": "success", "courses": service.my_courses(current_user())})


@bp.get("/schedule/roster/<int:course_id>")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def roster(course_id):
    course, students = service.roster(course_id, current_user())
    return jsonify(
        {
            "status": "success",
            "course": {"id": course.id, "code": course.code, "title": course.title, "section": course.section},
            "students": students,
        }
    )
