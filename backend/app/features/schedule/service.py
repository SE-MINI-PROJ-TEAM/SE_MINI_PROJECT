from datetime import timedelta

from sqlalchemy import and_

from app.core.access import ensure_course_access, get_course_or_404
from app.core.constants import ENROLLMENT_ENROLLED, ROLE_ADMIN, ROLE_FACULTY, ROLE_STUDENT
from app.core.errors import bad_request, conflict, not_found
from app.core.settings import current_term
from app.core.timeutil import parse_iso, to_iso
from app.core.validation import clean_text, to_int
from app.extensions import db
from app.models import AttendanceRecord, Course, Enrollment, ScheduleSession, User

MAX_SESSION_HOURS = 8
MAX_REPEAT_WEEKS = 20


def serialize_session(session, course=None):
    course = course or session.course
    return {
        "id": session.id,
        "course_id": course.id,
        "course_code": course.code,
        "course_title": course.title,
        "section": course.section,
        "faculty_name": course.faculty.full_name if course.faculty else None,
        "start_time": to_iso(session.start_time),
        "end_time": to_iso(session.end_time),
        "room": session.room_number,
    }


def course_options():
    courses = Course.query.filter_by(term=current_term()).order_by(Course.code, Course.section).all()
    return [
        {
            "id": c.id,
            "label": f"{c.code}-{c.section} · {c.title}",
            "faculty_name": c.faculty.full_name if c.faculty else None,
        }
        for c in courses
    ]


def _check_conflicts(course, start, end, room):
    overlap = and_(ScheduleSession.start_time < end, ScheduleSession.end_time > start)
    room_clash = ScheduleSession.query.filter(overlap, ScheduleSession.room_number == room).first()
    if room_clash:
        raise conflict(f"Room {room} is already booked at that time.", "ROOM_CONFLICT")
    if course.assigned_faculty_id:
        faculty_clash = (
            ScheduleSession.query.join(Course, Course.id == ScheduleSession.course_id)
            .filter(overlap, Course.assigned_faculty_id == course.assigned_faculty_id)
            .first()
        )
        if faculty_clash:
            raise conflict("The assigned instructor already teaches another session at that time.", "FACULTY_CONFLICT")
    section_clash = ScheduleSession.query.filter(overlap, ScheduleSession.course_id == course.id).first()
    if section_clash:
        raise conflict("This section already has a session at that time.", "SECTION_CONFLICT")


def create_sessions(data):
    course = get_course_or_404(to_int(data.get("course_id"), "course_id", minimum=1))
    room = clean_text(data, "room", max_len=40, label="room")
    try:
        start = parse_iso(data.get("start_time"))
        end = parse_iso(data.get("end_time"))
    except (ValueError, TypeError):
        raise bad_request("Start and end time must be valid ISO-8601 date-times.", "INVALID_DATETIME")
    if end <= start:
        raise bad_request("End time must be after start time.", "INVALID_TIME_RANGE")
    if end - start > timedelta(hours=MAX_SESSION_HOURS):
        raise bad_request(f"A session cannot be longer than {MAX_SESSION_HOURS} hours.", "INVALID_TIME_RANGE")
    repeat = to_int(data.get("repeat_weeks", 1), "Repeat weeks", minimum=1, maximum=MAX_REPEAT_WEEKS)

    created = []
    try:
        for week in range(repeat):
            offset = timedelta(weeks=week)
            _check_conflicts(course, start + offset, end + offset, room)
            session = ScheduleSession(
                course_id=course.id, start_time=start + offset, end_time=end + offset, room_number=room
            )
            db.session.add(session)
            db.session.flush()
            created.append(session)
        db.session.commit()
    except Exception:
        db.session.rollback()  # a conflict in any week cancels the whole series
        raise
    return [serialize_session(s, course) for s in created]


def list_sessions(course_id, page, per_page):
    query = ScheduleSession.query
    if course_id:
        query = query.filter(ScheduleSession.course_id == course_id)
    result = query.order_by(ScheduleSession.start_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return result, [serialize_session(s) for s in result.items]


def delete_session(session_id):
    session = db.session.get(ScheduleSession, session_id)
    if session is None:
        raise not_found("Session not found.", "SESSION_NOT_FOUND")
    if AttendanceRecord.query.filter_by(session_id=session_id).first():
        raise conflict("Attendance has already been recorded for this session.", "SESSION_HAS_ATTENDANCE")
    db.session.delete(session)
    db.session.commit()


def calendar(user, start, end, course_id=None):
    query = ScheduleSession.query.join(Course, Course.id == ScheduleSession.course_id).filter(
        ScheduleSession.start_time >= start, ScheduleSession.start_time < end
    )
    if user.role == ROLE_STUDENT:
        enrolled = db.session.query(Enrollment.course_id).filter(
            Enrollment.student_id == user.id, Enrollment.status == ENROLLMENT_ENROLLED
        )
        query = query.filter(ScheduleSession.course_id.in_(enrolled))
    elif user.role == ROLE_FACULTY:
        query = query.filter(Course.assigned_faculty_id == user.id)
    elif course_id:
        query = query.filter(ScheduleSession.course_id == course_id)
    return [serialize_session(s) for s in query.order_by(ScheduleSession.start_time).limit(500).all()]


def my_courses(faculty):
    courses = Course.query.filter_by(assigned_faculty_id=faculty.id).order_by(Course.term.desc(), Course.code).all()
    counts = dict(
        db.session.query(Enrollment.course_id, db.func.count(Enrollment.id))
        .filter(Enrollment.course_id.in_([c.id for c in courses]), Enrollment.status == ENROLLMENT_ENROLLED)
        .group_by(Enrollment.course_id)
        .all()
    ) if courses else {}
    return [
        {
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "section": c.section,
            "term": c.term,
            "credits": c.credits,
            "capacity": c.capacity,
            "enrolled": counts.get(c.id, 0),
        }
        for c in courses
    ]


def roster(course_id, user):
    """Student roster for a section; faculty are limited to sections assigned to them (HTTP 403 otherwise)."""
    course = get_course_or_404(course_id)
    ensure_course_access(course, user)
    students = (
        User.query.join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course.id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(User.institutional_id)
        .all()
    )
    return course, [
        {"id": s.id, "institutional_id": s.institutional_id, "full_name": s.full_name, "email": s.email}
        for s in students
    ]
