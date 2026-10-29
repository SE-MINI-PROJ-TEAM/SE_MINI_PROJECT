from sqlalchemy import func

from app.core import grading
from app.core.access import ensure_course_access, get_course_or_404
from app.core.constants import (
    ENROLLMENT_ENROLLED,
    GRADE_DRAFT,
    GRADE_STATES,
    GRADE_SUBMITTED,
)
from app.core.db_retry import run_with_retry
from app.core.errors import ApiError, bad_request, forbidden, not_found
from app.core.validation import sanitize
from app.extensions import db
from app.models import Course, Enrollment, GradeRecord, User

EDITABLE_STATES = (None, GRADE_DRAFT)


def my_courses(faculty):
    courses = Course.query.filter_by(assigned_faculty_id=faculty.id).order_by(Course.term.desc(), Course.code).all()
    ids = [c.id for c in courses]
    counts = {}
    if ids:
        for course_id, state, n in (
            db.session.query(Enrollment.course_id, Enrollment.grade_state, func.count(Enrollment.id))
            .filter(Enrollment.course_id.in_(ids), Enrollment.status == ENROLLMENT_ENROLLED)
            .group_by(Enrollment.course_id, Enrollment.grade_state)
            .all()
        ):
            counts.setdefault(course_id, {})[state or "Not started"] = n
    return [
        {
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "section": c.section,
            "term": c.term,
            "states": counts.get(c.id, {}),
            "enrolled": sum(counts.get(c.id, {}).values()),
        }
        for c in courses
    ]


def _rubric_view(course):
    return [
        {"id": c.id, "name": c.component_name, "category": c.category, "weight": float(c.normalized_weight)}
        for c in course.rubric
    ]


def course_grid(course_id, user):
    course = get_course_or_404(course_id)
    ensure_course_access(course, user)
    rows = (
        db.session.query(Enrollment, User)
        .join(User, User.id == Enrollment.student_id)
        .filter(Enrollment.course_id == course.id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(User.institutional_id)
        .all()
    )
    ids = [e.id for e, _ in rows]
    scores = {}
    if ids:
        for record in GradeRecord.query.filter(GradeRecord.enrollment_id.in_(ids)).all():
            scores.setdefault(record.enrollment_id, {})[record.rubric_id] = float(record.numeric_score)
    students = []
    for enrollment, student in rows:
        own = scores.get(enrollment.id, {})
        total = grading.total_or_none(own, course.rubric)
        students.append(
            {
                "enrollment_id": enrollment.id,
                "student_id": student.institutional_id,
                "full_name": student.full_name,
                "scores": {str(k): v for k, v in own.items()},
                "state": enrollment.grade_state or "Not started",
                "weighted_total": float(total) if total is not None else None,
                "editable": enrollment.grade_state in EDITABLE_STATES,
            }
        )
    return {
        "course": {"id": course.id, "code": course.code, "title": course.title, "section": course.section},
        "rubric": _rubric_view(course),
        "students": students,
    }


def _locked_enrollment(course_id, student_code):
    student = User.query.filter_by(institutional_id=student_code.upper()).first()
    enrollment = None
    if student is not None:
        enrollment = (
            Enrollment.query.filter_by(course_id=course_id, student_id=student.id, status=ENROLLMENT_ENROLLED)
            .with_for_update()
            .first()
        )
    if enrollment is None:
        raise not_found("Student is not enrolled in this course.", "STUDENT_NOT_ENROLLED")
    return enrollment


def _require_editable(enrollment):
    if enrollment.grade_state not in EDITABLE_STATES:
        raise ApiError(
            409, "GRADE_LOCKED",
            f"Marks cannot be edited while the grade is '{enrollment.grade_state}'.",
        )


def save_drafts(course_id, faculty, entries):
    """Bulk save of partial/complete scores for many students; everything stays in Draft."""
    if not isinstance(entries, list) or not entries:
        raise bad_request("students must be a non-empty list.", "INVALID_FIELD")
    if not all(isinstance(entry, dict) for entry in entries):
        raise bad_request("Each student entry must be an object.", "INVALID_FIELD")

    def attempt():
        course = get_course_or_404(course_id)
        ensure_course_access(course, faculty)
        saved = 0
        for entry in sorted(entries, key=lambda e: str(e.get("student_id", ""))):
            if not isinstance(entry, dict):
                raise bad_request("Each student entry must be an object.", "INVALID_FIELD")
            code = sanitize(entry.get("student_id"))
            parsed = grading.parse_scores(entry.get("rubric_scores", []), course.rubric)
            if not parsed:
                continue
            enrollment = _locked_enrollment(course.id, code)
            _require_editable(enrollment)
            grading.upsert_scores(enrollment, parsed, GRADE_DRAFT)
            enrollment.grade_state = GRADE_DRAFT
            enrollment.weighted_total = None
            saved += 1
        db.session.commit()
        return saved

    return run_with_retry(attempt)


def save_student(course_id, student_code, faculty, data):
    """SAD contract: PUT /grades/courses/{courseId}/students/{studentId} with an optional target_state."""
    target = data.get("target_state", GRADE_DRAFT)
    if target not in GRADE_STATES:
        raise bad_request(f"target_state must be one of: {', '.join(GRADE_STATES)}.", "INVALID_STATE")
    if target not in (GRADE_DRAFT, GRADE_SUBMITTED):
        raise forbidden("Your role cannot move a grade to this state.", "STATE_TRANSITION_FORBIDDEN")

    def attempt():
        course = get_course_or_404(course_id)
        ensure_course_access(course, faculty)
        parsed = grading.parse_scores(data.get("rubric_scores", []), course.rubric)
        enrollment = _locked_enrollment(course.id, sanitize(student_code))
        _require_editable(enrollment)
        if parsed:
            grading.upsert_scores(enrollment, parsed, GRADE_DRAFT)
            enrollment.grade_state = GRADE_DRAFT
            db.session.flush()
        if target == GRADE_SUBMITTED:
            total = grading.submit_enrollment(enrollment, course.rubric)
        else:
            if not parsed:
                raise bad_request("Provide at least one rubric score.", "INVALID_FIELD")
            enrollment.weighted_total = None
            total = None
        db.session.commit()
        return enrollment.grade_state, total

    return run_with_retry(attempt)
