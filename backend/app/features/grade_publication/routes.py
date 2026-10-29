from flask import Blueprint, jsonify

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY, ROLE_STUDENT
from app.core.security import auth_required, current_user
from app.core.validation import json_body

from . import service

bp = Blueprint("grade_publication", __name__)


@bp.post("/grades/courses/<int:course_id>/submit")
@auth_required(ROLE_FACULTY)
def submit_course(course_id):
    submitted, skipped = service.submit_course(course_id, current_user())
    return jsonify(
        {
            "status": "success",
            "message": f"{submitted} grade(s) submitted for publication.",
            "submitted": submitted,
            "skipped": skipped,
        }
    )


@bp.get("/grades/publication/queue")
@auth_required(ROLE_ADMIN)
def queue():
    return jsonify({"status": "success", "courses": service.publication_queue()})


@bp.post("/grades/publication/publish")
@auth_required(ROLE_ADMIN)
def publish():
    published = service.publish(current_user(), json_body().get("course_ids"))
    total = sum(published.values())
    return jsonify(
        {
            "status": "success",
            "message": f"Published {total} grade(s) across {len(published)} course(s).",
            "published": {str(k): v for k, v in published.items()},
        }
    )


@bp.get("/grades/mine")
@auth_required(ROLE_STUDENT)
def my_grades():
    return jsonify({"status": "success", "grades": service.student_grades(current_user().id)})
