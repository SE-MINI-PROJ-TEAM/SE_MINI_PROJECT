from flask import Blueprint, jsonify

from app.core.constants import ROLE_STUDENT
from app.core.security import auth_required, current_user

from . import service

bp = Blueprint("attendance_dashboard", __name__)


@bp.get("/attendance/summary")
@auth_required(ROLE_STUDENT)
def summary():
    return jsonify({"status": "success", **service.summary(current_user().id)})


@bp.get("/attendance/summary/<int:course_id>")
@auth_required(ROLE_STUDENT)
def course_detail(course_id):
    return jsonify({"status": "success", **service.course_detail(current_user().id, course_id)})
