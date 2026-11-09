from sqlalchemy import case, func

from app.core.constants import ENROLLMENT_ENROLLED
from app.core.errors import forbidden, not_found
from app.core.timeutil import to_iso, utcnow
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, ScheduleSession

ALERT_THRESHOLD = 75.0


def _pct(attended, total):
    return round(attended * 100.0 / total, 1) if total else None


def summary(student_id):
    """Per-course totals. Only sessions already held and marked by faculty count towards the percentage."""
    now = utcnow()
    courses = (
        db.session.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == student_id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(Course.code)
        .all()
    )
    totals = {
        row.course_id: (int(row.total), int(row.attended or 0))
        for row in db.session.query(
            ScheduleSession.course_id.label("course_id"),
            func.count(AttendanceRecord.id).label("total"),
            func.sum(case((AttendanceRecord.is_present.is_(True), 1), else_=0)).label("attended"),
        )
        .join(AttendanceRecord, AttendanceRecord.session_id == ScheduleSession.id)
        .filter(AttendanceRecord.student_id == student_id, ScheduleSession.start_time <= now)
        .group_by(ScheduleSession.course_id)
        .all()
    }
    result = []
    for course in courses:
        total, attended = totals.get(course.id, (0, 0))
        percentage = _pct(attended, total)
        result.append(
            {
                "course_id": course.id,
                "code": course.code,
                "title": course.title,
                "section": course.section,
                "sessions_held": total,
                "sessions_attended": attended,
                "sessions_missed": total - attended,
                "percentage": percentage,
                "below_threshold": percentage is not None and percentage < ALERT_THRESHOLD,
            }
        )
    overall_total = sum(r["sessions_held"] for r in result)
    overall_attended = sum(r["sessions_attended"] for r in result)
    return {
        "threshold": ALERT_THRESHOLD,
        "overall_percentage": _pct(overall_attended, overall_total),
        "courses": result,
    }


def course_detail(student_id, course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        raise not_found("Course not found.", "COURSE_NOT_FOUND")
    enrolled = Enrollment.query.filter_by(student_id=student_id, course_id=course_id, status=ENROLLMENT_ENROLLED).first()
    if enrolled is None:
        raise forbidden("You are not enrolled in this course.", "NOT_ENROLLED")

    now = utcnow()
    rows = (
        db.session.query(ScheduleSession, AttendanceRecord)
        .outerjoin(
            AttendanceRecord,
            (AttendanceRecord.session_id == ScheduleSession.id) & (AttendanceRecord.student_id == student_id),
        )
        .filter(ScheduleSession.course_id == course_id, ScheduleSession.start_time <= now)
        .order_by(ScheduleSession.start_time.desc())
        .all()
    )
    sessions = [
        {
            "session_id": s.id,
            "start_time": to_iso(s.start_time),
            "room": s.room_number,
            "status": "Not marked" if r is None else ("Present" if r.is_present else "Absent"),
        }
        for s, r in rows
    ]
    attended = sum(1 for s in sessions if s["status"] == "Present")
    missed = sum(1 for s in sessions if s["status"] == "Absent")
    total = attended + missed
    percentage = _pct(attended, total)
    return {
        "course": {"id": course.id, "code": course.code, "title": course.title, "section": course.section},
        "sessions_held": total,
        "sessions_attended": attended,
        "sessions_missed": missed,
        "percentage": percentage,
        "below_threshold": percentage is not None and percentage < ALERT_THRESHOLD,
        "threshold": ALERT_THRESHOLD,
        "sessions": sessions,
    }
