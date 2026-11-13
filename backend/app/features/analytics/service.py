import statistics
from decimal import Decimal

from sqlalchemy import case, func

from app.core import grading
from app.core.constants import ENROLLMENT_ENROLLED, STUDENT_VISIBLE_GRADE_STATES
from app.core.settings import current_term
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, ScheduleSession

# Faculty analytics include every grade that already has a computed weighted total.
ANALYTICS_STATES = ("Submitted", "Published", "Under Review")


def _gpa(rows):
    credits = sum(r["credits"] for r in rows)
    if not credits:
        return None
    return round(sum(r["points"] * r["credits"] for r in rows) / credits, 2)


def student_summary(student_id):
    """Credit-weighted GPA over Published (and Under Review) grades, one indexed query."""
    rows = (
        db.session.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.status == ENROLLMENT_ENROLLED,
            Enrollment.grade_state.in_(STUDENT_VISIBLE_GRADE_STATES),
        )
        .order_by(Course.term.desc(), Course.code)
        .all()
    )
    term = current_term()
    courses = []
    for enrollment, course in rows:
        letter = grading.letter_for(enrollment.weighted_total)
        courses.append(
            {
                "course_id": course.id,
                "code": course.code,
                "title": course.title,
                "term": course.term,
                "credits": course.credits,
                "weighted_total": float(enrollment.weighted_total),
                "letter": letter,
                "points": float(grading.points_for(letter)),
                "state": enrollment.grade_state,
            }
        )
    term_rows = [c for c in courses if c["term"] == term]
    return {
        "term": term,
        "term_gpa": _gpa(term_rows),
        "term_credits": sum(c["credits"] for c in term_rows),
        "cumulative_gpa": _gpa(courses),
        "cumulative_credits": sum(c["credits"] for c in courses),
        "courses": courses,
    }


def faculty_sections(faculty):
    courses = Course.query.filter_by(assigned_faculty_id=faculty.id).order_by(Course.term.desc(), Course.code).all()
    ids = [c.id for c in courses]
    totals, enrolled, attendance = {}, {}, {}
    if ids:
        for course_id, total in (
            db.session.query(Enrollment.course_id, Enrollment.weighted_total)
            .filter(
                Enrollment.course_id.in_(ids),
                Enrollment.status == ENROLLMENT_ENROLLED,
                Enrollment.grade_state.in_(ANALYTICS_STATES),
                Enrollment.weighted_total.isnot(None),
            )
            .all()
        ):
            totals.setdefault(course_id, []).append(Decimal(total))
        enrolled = dict(
            db.session.query(Enrollment.course_id, func.count(Enrollment.id))
            .filter(Enrollment.course_id.in_(ids), Enrollment.status == ENROLLMENT_ENROLLED)
            .group_by(Enrollment.course_id)
            .all()
        )
        for row in (
            db.session.query(
                ScheduleSession.course_id,
                func.count(AttendanceRecord.id),
                func.sum(case((AttendanceRecord.is_present.is_(True), 1), else_=0)),
            )
            .join(AttendanceRecord, AttendanceRecord.session_id == ScheduleSession.id)
            .filter(ScheduleSession.course_id.in_(ids))
            .group_by(ScheduleSession.course_id)
            .all()
        ):
            attendance[row[0]] = (int(row[1]), int(row[2] or 0))

    sections = []
    for course in courses:
        values = totals.get(course.id, [])
        distribution = {letter: 0 for letter in grading.LETTERS}
        for value in values:
            distribution[grading.letter_for(value)] += 1
        marked, present = attendance.get(course.id, (0, 0))
        sections.append(
            {
                "course_id": course.id,
                "code": course.code,
                "title": course.title,
                "section": course.section,
                "term": course.term,
                "enrolled": enrolled.get(course.id, 0),
                "graded": len(values),
                "mean": round(float(statistics.fmean(values)), 2) if values else None,
                "median": round(float(statistics.median(values)), 2) if values else None,
                "distribution": distribution,
                "attendance_rate": round(present * 100.0 / marked, 1) if marked else None,
            }
        )
    return sections
