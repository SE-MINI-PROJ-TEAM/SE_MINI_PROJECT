import csv
import io
import statistics
from decimal import Decimal

from sqlalchemy import case, func

from app.core.constants import ENROLLMENT_ENROLLED, GRADE_DRAFT, ROLE_ADMIN, ROLE_FACULTY, ROLE_STUDENT, DISPUTE_OPEN
from app.core.timeutil import to_iso, utcnow
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, GradeDispute, ScheduleSession, User

CSV_COLUMNS = [
    "term", "course_code", "section", "title", "faculty", "capacity", "enrolled",
    "sessions_held", "attendance_records", "attendance_rate_pct",
    "grades_not_started", "grades_draft", "grades_submitted", "grades_published", "grades_under_review",
    "average_weighted_total",
]
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value):
    """Neutralise spreadsheet formula injection (CSV injection)."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _course_rows():
    now = utcnow()
    courses = Course.query.order_by(Course.term.desc(), Course.code, Course.section).all()

    state_counts = {}
    for course_id, state, n in (
        db.session.query(Enrollment.course_id, Enrollment.grade_state, func.count(Enrollment.id))
        .filter(Enrollment.status == ENROLLMENT_ENROLLED)
        .group_by(Enrollment.course_id, Enrollment.grade_state)
        .all()
    ):
        state_counts.setdefault(course_id, {})[state] = n

    averages = dict(
        db.session.query(Enrollment.course_id, func.avg(Enrollment.weighted_total))
        .filter(Enrollment.weighted_total.isnot(None))
        .group_by(Enrollment.course_id)
        .all()
    )
    held = dict(
        db.session.query(ScheduleSession.course_id, func.count(ScheduleSession.id))
        .filter(ScheduleSession.start_time <= now)
        .group_by(ScheduleSession.course_id)
        .all()
    )
    attendance = {
        row[0]: (int(row[1]), int(row[2] or 0))
        for row in db.session.query(
            ScheduleSession.course_id,
            func.count(AttendanceRecord.id),
            func.sum(case((AttendanceRecord.is_present.is_(True), 1), else_=0)),
        )
        .join(AttendanceRecord, AttendanceRecord.session_id == ScheduleSession.id)
        .group_by(ScheduleSession.course_id)
        .all()
    }

    rows = []
    for course in courses:
        states = state_counts.get(course.id, {})
        marked, present = attendance.get(course.id, (0, 0))
        avg = averages.get(course.id)
        rows.append(
            {
                "term": course.term,
                "course_code": course.code,
                "section": course.section,
                "title": course.title,
                "faculty": course.faculty.full_name if course.faculty else "",
                "capacity": course.capacity,
                "enrolled": sum(states.values()),
                "sessions_held": held.get(course.id, 0),
                "attendance_records": marked,
                "attendance_rate_pct": round(present * 100.0 / marked, 1) if marked else "",
                "grades_not_started": states.get(None, 0),
                "grades_draft": states.get("Draft", 0),
                "grades_submitted": states.get("Submitted", 0),
                "grades_published": states.get("Published", 0),
                "grades_under_review": states.get("Under Review", 0),
                "average_weighted_total": round(float(avg), 2) if avg is not None else "",
            }
        )
    return rows


def overview():
    """Institution-level totals for the admin dashboard (SYS-F-020)."""
    role_counts = dict(db.session.query(User.role, func.count(User.id)).group_by(User.role).all())
    enrollments = Enrollment.query.filter_by(status=ENROLLMENT_ENROLLED).count()
    unsubmitted = (
        Enrollment.query.filter(Enrollment.status == ENROLLMENT_ENROLLED)
        .filter((Enrollment.grade_state.is_(None)) | (Enrollment.grade_state == GRADE_DRAFT))
        .count()
    )
    total_marked, total_present = db.session.query(
        func.count(AttendanceRecord.id),
        func.sum(case((AttendanceRecord.is_present.is_(True), 1), else_=0)),
    ).one()
    return {
        "students": role_counts.get(ROLE_STUDENT, 0),
        "faculty": role_counts.get(ROLE_FACULTY, 0),
        "admins": role_counts.get(ROLE_ADMIN, 0),
        "active_users": User.query.filter_by(is_active=True).count(),
        "courses": Course.query.count(),
        "total_enrollments": enrollments,
        "unsubmitted_grades": unsubmitted,
        "open_disputes": GradeDispute.query.filter_by(status=DISPUTE_OPEN).count(),
        "attendance_rate_pct": round(int(total_present or 0) * 100.0 / total_marked, 1) if total_marked else None,
        "generated_at": to_iso(utcnow()),
    }


def build_csv():
    rows = _course_rows()
    summary = overview()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([_safe_cell(row[col]) for col in CSV_COLUMNS])
    # Institution-level totals row
    writer.writerow(
        [
            "ALL", "TOTAL", "", "Institution total", "",
            sum(r["capacity"] for r in rows), summary["total_enrollments"],
            sum(r["sessions_held"] for r in rows), sum(r["attendance_records"] for r in rows),
            summary["attendance_rate_pct"] if summary["attendance_rate_pct"] is not None else "",
            sum(r["grades_not_started"] for r in rows), sum(r["grades_draft"] for r in rows),
            sum(r["grades_submitted"] for r in rows), sum(r["grades_published"] for r in rows),
            sum(r["grades_under_review"] for r in rows), "",
        ]
    )
    return buffer.getvalue()
