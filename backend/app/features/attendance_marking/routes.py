from datetime import timedelta

from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.core.errors import bad_request
from app.core.security import auth_required, current_user
from app.core.timeutil import parse_iso, to_iso, utcnow
from app.core.validation import json_body

from . import service

bp = Blueprint("attendance_marking", __name__)


@bp.get("/attendance/sessions")
@auth_required(ROLE_FACULTY)
def list_sessions():
    now = utcnow()
    try:
        start = parse_iso(request.args["from"]) if request.args.get("from") else now - timedelta(days=14)
        end = parse_iso(request.args["to"]) if request.args.get("to") else now + timedelta(days=7)
    except (ValueError, TypeError):
        raise bad_request("'from' and 'to' must be ISO-8601 date-times.", "INVALID_DATETIME")
    if end <= start or end - start > timedelta(days=120):
        raise bad_request("The range must be between 1 and 120 days.", "INVALID_TIME_RANGE")
    return jsonify({"status": "success", "sessions": service.list_sessions(current_user(), start, end)})


@bp.get("/attendance/sessions/<int:session_id>")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def get_session(session_id):
    return jsonify({"status": "success", **service.session_roster(session_id, current_user())})


@bp.post("/attendance/sessions/<int:session_id>")
@auth_required(ROLE_FACULTY)
def save_attendance(session_id):
    data = json_body()
    count, frozen_at = service.save_attendance(session_id, current_user(), data.get("attendance_list"))
    return jsonify(
        {
            "status": "success",
            "message": f"Attendance recorded for {count} students.",
            "frozen_at": to_iso(frozen_at),
        }
    )
