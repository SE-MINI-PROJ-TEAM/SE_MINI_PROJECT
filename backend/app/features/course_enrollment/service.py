from flask import current_app
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.core.audit import log_action
from app.core.constants import AUDIT_SETTING_CHANGED, ENROLLMENT_ENROLLED
from app.core.db_retry import run_with_retry
from app.core.errors import ApiError, bad_request, conflict, forbidden, not_found
from app.core.settings import ENROLLMENT_OPEN, current_term, enrollment_open, set_setting
from app.extensions import db
from app.models import Course, Enrollment, User


def _max_courses():
    return current_app.config["MAX_COURSES_PER_TERM"]


def _enrolled_counts(course_ids):
    if not course_ids:
        return {}
    rows = (
        db.session.query(Enrollment.course_id, func.count(Enrollment.id))
        .filter(Enrollment.course_id.in_(course_ids), Enrollment.status == ENROLLMENT_ENROLLED)
        .group_by(Enrollment.course_id)
        .all()
    )
    return dict(rows)


def _term_enrollment_count(student_id, term):
    return (
        db.session.query(func.count(Enrollment.id))
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id, Enrollment.status == ENROLLMENT_ENROLLED, Course.term == term)
        .scalar()
    )


def catalog(student_id, search):
    term = current_term()
    query = Course.query.options(joinedload(Course.faculty)).filter(Course.term == term)  # one query, not one per course
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Course.code.like(like), Course.title.like(like)))
    courses = query.order_by(Course.code, Course.section).all()
    counts = _enrolled_counts([c.id for c in courses])
    mine = {
        row.course_id
        for row in Enrollment.query.filter_by(student_id=student_id, status=ENROLLMENT_ENROLLED).all()
    }
    return {
        "term": term,
        "window_open": enrollment_open(),
        "max_courses": _max_courses(),
        "my_course_count": _term_enrollment_count(student_id, term),
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "section": c.section,
                "credits": c.credits,
                "capacity": c.capacity,
                "enrolled": counts.get(c.id, 0),
                "seats_available": max(c.capacity - counts.get(c.id, 0), 0),
                "faculty_name": c.faculty.full_name if c.faculty else None,
                "is_enrolled": c.id in mine,
            }
            for c in courses
        ],
    }


def enroll(student_id, course_id):
    def attempt():
        if not enrollment_open():
            raise forbidden("Enrollment is currently closed by the administrator.", "ENROLLMENT_CLOSED")

        # Serialise concurrent enrollments: per-student row first, then the course row (fixed lock order).
        db.session.execute(select(User.id).where(User.id == student_id).with_for_update())
        course = db.session.execute(select(Course).where(Course.id == course_id).with_for_update()).scalar_one_or_none()
        if course is None:
            raise not_found("Course section not found.", "COURSE_NOT_FOUND")
        if course.term != current_term():
            raise bad_request("This section is not open for the current term.", "TERM_MISMATCH")

        if Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
            raise conflict("You are already enrolled in this section.", "ALREADY_ENROLLED")
        if _term_enrollment_count(student_id, course.term) >= _max_courses():
            raise ApiError(
                409, "ENROLLMENT_LIMIT_REACHED",
                f"You can enroll in at most {_max_courses()} courses per term.",
            )
        enrolled = Enrollment.query.filter_by(course_id=course_id, status=ENROLLMENT_ENROLLED).count()
        if enrolled >= course.capacity:
            raise conflict("This section is full.", "SECTION_FULL")

        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        return enrollment, course, enrolled + 1

    return run_with_retry(attempt)


def my_enrollments(student_id):
    rows = (
        db.session.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(Course.code)
        .all()
    )
    return [
        {
            "enrollment_id": e.id,
            "course_id": c.id,
            "code": c.code,
            "title": c.title,
            "section": c.section,
            "term": c.term,
            "credits": c.credits,
            "faculty_name": c.faculty.full_name if c.faculty else None,
        }
        for e, c in rows
    ]


def set_window(actor, is_open):
    if not isinstance(is_open, bool):
        raise bad_request("open must be true or false.", "INVALID_FIELD")
    old = enrollment_open()
    set_setting(ENROLLMENT_OPEN, "true" if is_open else "false")
    if old != is_open:
        log_action(actor.id, AUDIT_SETTING_CHANGED, "Setting", ENROLLMENT_OPEN, {"old": old, "new": is_open})
    db.session.commit()
    return is_open
