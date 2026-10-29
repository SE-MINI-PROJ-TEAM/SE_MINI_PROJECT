"""Resource-level authorisation helpers (faculty roster isolation, SYS-F-008 / PRJ-SO-001)."""
from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.core.errors import forbidden, not_found
from app.extensions import db
from app.models import Course, ScheduleSession


def get_course_or_404(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        raise not_found("Course not found.", "COURSE_NOT_FOUND")
    return course


def ensure_course_access(course, user):
    """Admins may access any course; faculty only the sections assigned to them."""
    if user.role == ROLE_ADMIN:
        return
    if user.role == ROLE_FACULTY and course.assigned_faculty_id == user.id:
        return
    raise forbidden("This course section is not assigned to you.", "NOT_ASSIGNED")


def get_session_or_404(session_id):
    session = db.session.get(ScheduleSession, session_id)
    if session is None:
        raise not_found("Session not found.", "SESSION_NOT_FOUND")
    return session
