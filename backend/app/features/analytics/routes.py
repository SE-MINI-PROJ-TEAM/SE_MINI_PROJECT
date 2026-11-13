import time

from flask import Blueprint, jsonify

from app.core.constants import ROLE_FACULTY, ROLE_STUDENT
from app.core.security import auth_required, current_user

from . import service

bp = Blueprint("analytics", __name__)


@bp.get("/analytics/student/summary")
@auth_required(ROLE_STUDENT)
def student_summary():
    started = time.perf_counter()
    data = service.student_summary(current_user().id)
    return jsonify({"status": "success", **data, "query_ms": round((time.perf_counter() - started) * 1000, 1)})


@bp.get("/analytics/faculty/sections")
@auth_required(ROLE_FACULTY)
def faculty_sections():
    started = time.perf_counter()
    sections = service.faculty_sections(current_user())
    return jsonify(
        {"status": "success", "sections": sections, "query_ms": round((time.perf_counter() - started) * 1000, 1)}
    )
