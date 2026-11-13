from datetime import timedelta

from flask import current_app
from sqlalchemy import func

from app.core.access import ensure_course_access, get_session_or_404
from app.core.constants import ENROLLMENT_ENROLLED
from app.core.db_retry import run_with_retry
from app.core.errors import ApiError, bad_request, not_found
from app.core.timeutil import to_iso, utcnow
from app.core.validation import sanitize
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, ScheduleSession, User


def freeze_deadline(session):
    return session.start_time + timedelta(hours=current_app.config["ATTENDANCE_FREEZE_HOURS"])


def is_frozen(session, now=None):
    """Hard backend rule: faculty edits are rejected at or after start_time + 48h (SYS-F-010)."""
    return (now or utcnow()) >= freeze_deadline(session)


def session_status(session, now=None):
    now = now or utcnow()
    if now < session.start_time:
        return "upcoming"
    return "frozen" if is_frozen(session, now) else "open"


def list_sessions(faculty, start, end):
    now = utcnow()
    rows = (
        ScheduleSession.query.join(Course, Course.id == ScheduleSession.course_id)
        .filter(
            Course.assigned_faculty_id == faculty.id,
            ScheduleSession.start_time >= start,
            ScheduleSession.start_time < end,
        )
        .order_by(ScheduleSession.start_time.desc())
        .all()
    )
    session_ids = [s.id for s in rows]
    course_ids = list({s.course_id for s in rows})
    marked = (
        dict(
            db.session.query(AttendanceRecord.session_id, func.count(AttendanceRecord.id))
            .filter(AttendanceRecord.session_id.in_(session_ids))
            .group_by(AttendanceRecord.session_id)
            .all()
        )
        if session_ids
        else {}
    )
    enrolled = (
        dict(
            db.session.query(Enrollment.course_id, func.count(Enrollment.id))
            .filter(Enrollment.course_id.in_(course_ids), Enrollment.status == ENROLLMENT_ENROLLED)
            .group_by(Enrollment.course_id)
            .all()
        )
        if course_ids
        else {}
    )
    return [
        {
            "id": s.id,
            "course_id": s.course_id,
            "course_code": s.course.code,
            "course_title": s.course.title,
            "section": s.course.section,
            "start_time": to_iso(s.start_time),
            "end_time": to_iso(s.end_time),
            "room": s.room_number,
            "status": session_status(s, now),
            "frozen_at": to_iso(freeze_deadline(s)),
            "marked_count": marked.get(s.id, 0),
            "enrolled_count": enrolled.get(s.course_id, 0),
        }
        for s in rows
    ]


def session_roster(session_id, user):
    session = get_session_or_404(session_id)
    course = session.course
    ensure_course_access(course, user)
    students = (
        db.session.query(User, AttendanceRecord)
        .join(Enrollment, Enrollment.student_id == User.id)
        .outerjoin(
            AttendanceRecord,
            (AttendanceRecord.student_id == User.id) & (AttendanceRecord.session_id == session.id),
        )
        .filter(Enrollment.course_id == course.id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(User.institutional_id)
        .all()
    )
    return {
        "session": {
            "id": session.id,
            "course_id": course.id,
            "course_code": course.code,
            "course_title": course.title,
            "section": course.section,
            "start_time": to_iso(session.start_time),
            "end_time": to_iso(session.end_time),
            "room": session.room_number,
            "status": session_status(session),
            "frozen_at": to_iso(freeze_deadline(session)),
        },
        "students": [
            {
                "student_id": u.institutional_id,
                "full_name": u.full_name,
                "is_present": record.is_present if record else None,
                "marked_at": to_iso(record.marked_at) if record else None,
            }
            for u, record in students
        ],
    }


def save_attendance(session_id, faculty, attendance_list):
    if not isinstance(attendance_list, list) or not attendance_list:
        raise bad_request("attendance_list must be a non-empty list.", "INVALID_FIELD")

    marks = {}
    for item in attendance_list:
        if not isinstance(item, dict) or not isinstance(item.get("is_present"), bool):
            raise bad_request("Each entry needs a student_id and a boolean is_present.", "INVALID_FIELD")
        student_code = sanitize(item.get("student_id")).upper()
        if not student_code:
            raise bad_request("Each entry needs a student_id.", "INVALID_FIELD")
        marks[student_code] = item["is_present"]

    def attempt():
        session = get_session_or_404(session_id)
        ensure_course_access(session.course, faculty)
        now = utcnow()
        if now < session.start_time:
            raise bad_request("Attendance cannot be marked before the session starts.", "SESSION_NOT_STARTED")
        if is_frozen(session, now):
            raise ApiError(
                403, "ATTENDANCE_FROZEN",
                "This session is frozen: attendance can no longer be edited 48 hours after it started.",
                {"frozen_at": to_iso(freeze_deadline(session))},
            )

        enrolled = {
            u.institutional_id: u.id
            for u in User.query.join(Enrollment, Enrollment.student_id == User.id)
            .filter(Enrollment.course_id == session.course_id, Enrollment.status == ENROLLMENT_ENROLLED)
            .all()
        }
        unknown = sorted(code for code in marks if code not in enrolled)
        if unknown:
            raise not_found(f"Not enrolled in this section: {', '.join(unknown)}.", "STUDENT_NOT_ENROLLED")

        # Fixed (sorted) write order keeps concurrent submissions from deadlocking each other.
        student_ids = [enrolled[code] for code in sorted(marks, key=lambda c: enrolled[c])]
        existing = {
            r.student_id: r
            for r in AttendanceRecord.query.filter(
                AttendanceRecord.session_id == session.id, AttendanceRecord.student_id.in_(student_ids)
            )
            .with_for_update()
            .all()
        }
        by_internal = {enrolled[code]: present for code, present in marks.items()}
        for student_id in student_ids:
            record = existing.get(student_id)
            if record is None:
                db.session.add(
                    AttendanceRecord(
                        session_id=session.id, student_id=student_id, is_present=by_internal[student_id],
                        marked_at=now, marked_by=faculty.id,
                    )
                )
            elif record.is_present != by_internal[student_id]:
                record.is_present = by_internal[student_id]
                record.marked_at = now
                record.marked_by = faculty.id
        db.session.commit()
        return len(marks), freeze_deadline(session)

    return run_with_retry(attempt)
