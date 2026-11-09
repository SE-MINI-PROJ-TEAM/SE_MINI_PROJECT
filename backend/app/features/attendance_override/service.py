from datetime import timedelta

from flask import current_app
from sqlalchemy import func

from app.core.access import get_session_or_404
from app.core.audit import log_action
from app.core.constants import AUDIT_ATTENDANCE_OVERRIDE, ENROLLMENT_ENROLLED
from app.core.db_retry import run_with_retry
from app.core.errors import bad_request, not_found
from app.core.timeutil import to_iso, utcnow
from app.core.validation import clean_text, sanitize
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, ScheduleSession, User

LABELS = {True: "Present", False: "Absent", None: "Unmarked"}


def _is_frozen(session, now):
    return now >= session.start_time + timedelta(hours=current_app.config["ATTENDANCE_FREEZE_HOURS"])


def course_options():
    courses = Course.query.order_by(Course.term.desc(), Course.code, Course.section).all()
    return [{"id": c.id, "label": f"{c.code}-{c.section} · {c.title} ({c.term})"} for c in courses]


def list_sessions(course_id):
    now = utcnow()
    sessions = (
        ScheduleSession.query.filter(ScheduleSession.course_id == course_id, ScheduleSession.start_time <= now)
        .order_by(ScheduleSession.start_time.desc())
        .limit(60)
        .all()
    )
    ids = [s.id for s in sessions]
    marked = (
        dict(
            db.session.query(AttendanceRecord.session_id, func.count(AttendanceRecord.id))
            .filter(AttendanceRecord.session_id.in_(ids))
            .group_by(AttendanceRecord.session_id)
            .all()
        )
        if ids
        else {}
    )
    return [
        {
            "id": s.id,
            "start_time": to_iso(s.start_time),
            "room": s.room_number,
            "frozen": _is_frozen(s, now),
            "marked_count": marked.get(s.id, 0),
        }
        for s in sessions
    ]


def session_detail(session_id):
    session = get_session_or_404(session_id)
    rows = (
        db.session.query(User, AttendanceRecord)
        .join(Enrollment, Enrollment.student_id == User.id)
        .outerjoin(
            AttendanceRecord,
            (AttendanceRecord.student_id == User.id) & (AttendanceRecord.session_id == session.id),
        )
        .filter(Enrollment.course_id == session.course_id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(User.institutional_id)
        .all()
    )
    course = session.course
    return {
        "session": {
            "id": session.id,
            "course_code": course.code,
            "course_title": course.title,
            "section": course.section,
            "start_time": to_iso(session.start_time),
            "room": session.room_number,
            "frozen": _is_frozen(session, utcnow()),
        },
        "students": [
            {
                "student_id": u.institutional_id,
                "full_name": u.full_name,
                "is_present": r.is_present if r else None,
            }
            for u, r in rows
        ],
    }


def override(admin, session_id, data):
    reason = clean_text(data, "reason", min_len=5, max_len=500, label="justification reason")
    changes = data.get("changes")
    if not isinstance(changes, list) or not changes:
        raise bad_request("Provide at least one attendance change.", "INVALID_FIELD")
    wanted = {}
    for item in changes:
        if not isinstance(item, dict) or not isinstance(item.get("is_present"), bool):
            raise bad_request("Each change needs a student_id and a boolean is_present.", "INVALID_FIELD")
        wanted[sanitize(item.get("student_id")).upper()] = item["is_present"]

    def attempt():
        session = get_session_or_404(session_id)
        now = utcnow()
        if now < session.start_time:
            raise bad_request("Attendance cannot be overridden before the session starts.", "SESSION_NOT_STARTED")

        enrolled = {
            u.institutional_id: u
            for u in User.query.join(Enrollment, Enrollment.student_id == User.id)
            .filter(Enrollment.course_id == session.course_id, Enrollment.status == ENROLLMENT_ENROLLED)
            .all()
        }
        unknown = sorted(code for code in wanted if code not in enrolled)
        if unknown:
            raise not_found(f"Not enrolled in this section: {', '.join(unknown)}.", "STUDENT_NOT_ENROLLED")

        ordered = sorted(wanted, key=lambda code: enrolled[code].id)
        existing = {
            r.student_id: r
            for r in AttendanceRecord.query.filter(
                AttendanceRecord.session_id == session.id,
                AttendanceRecord.student_id.in_([enrolled[c].id for c in ordered]),
            )
            .with_for_update()
            .all()
        }
        applied = 0
        for code in ordered:
            student = enrolled[code]
            record = existing.get(student.id)
            old = record.is_present if record else None
            new = wanted[code]
            if old == new:
                continue
            if record is None:
                db.session.add(
                    AttendanceRecord(
                        session_id=session.id, student_id=student.id, is_present=new, marked_at=now, marked_by=admin.id
                    )
                )
            else:
                record.is_present = new
                record.marked_at = now
                record.marked_by = admin.id
            log_action(
                admin.id, AUDIT_ATTENDANCE_OVERRIDE, "AttendanceRecord", f"{session.id}:{student.id}",
                {
                    "session_id": session.id,
                    "course": f"{session.course.code}-{session.course.section}",
                    "student_id": code,
                    "old_value": LABELS[old],
                    "new_value": LABELS[new],
                    "reason": reason,
                    "was_frozen": _is_frozen(session, now),
                },
            )
            applied += 1
        if applied == 0:
            raise bad_request("No attendance values were changed.", "NO_CHANGES")
        db.session.commit()
        return applied

    return run_with_retry(attempt)
