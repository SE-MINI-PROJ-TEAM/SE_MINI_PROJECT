from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.core.constants import ENROLLMENT_ENROLLED, ROLE_FACULTY, RUBRIC_CATEGORIES
from app.core.errors import bad_request, conflict, not_found
from app.core.rubric import normalize_weights
from app.core.settings import current_term
from app.core.validation import clean_text, to_decimal, to_int
from app.extensions import db
from app.models import Course, Enrollment, GradeRecord, RubricComponent, User


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


def enrolled_count(course_id):
    return _enrolled_counts([course_id]).get(course_id, 0)


def serialize(course, enrolled=0):
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "section": course.section,
        "term": course.term,
        "credits": course.credits,
        "capacity": course.capacity,
        "enrolled": enrolled,
        "assigned_faculty_id": course.assigned_faculty_id,
        "faculty_name": course.faculty.full_name if course.faculty else None,
        "rubric": [
            {
                "id": c.id,
                "name": c.component_name,
                "category": c.category,
                "raw_weight": float(c.raw_weight),
                "weight": float(c.normalized_weight),
            }
            for c in course.rubric
        ],
    }


def list_courses(search, page, per_page):
    query = Course.query
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Course.code.like(like), Course.title.like(like)))
    result = query.order_by(Course.term.desc(), Course.code, Course.section).paginate(
        page=page, per_page=per_page, error_out=False
    )
    counts = _enrolled_counts([c.id for c in result.items])
    return result, [serialize(c, counts.get(c.id, 0)) for c in result.items]


def get_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        raise not_found("Course not found.", "COURSE_NOT_FOUND")
    return course


def faculty_options():
    faculty = User.query.filter_by(role=ROLE_FACULTY, is_active=True).order_by(User.full_name).all()
    return [{"id": f.id, "full_name": f.full_name, "institutional_id": f.institutional_id} for f in faculty]


def _parse_rubric(raw):
    if not isinstance(raw, list) or not raw:
        raise bad_request("Define at least one rubric component.", "INVALID_RUBRIC")
    if len(raw) > 12:
        raise bad_request("A course can have at most 12 rubric components.", "INVALID_RUBRIC")
    parsed = []
    for item in raw:
        if not isinstance(item, dict):
            raise bad_request("Each rubric component must be an object.", "INVALID_RUBRIC")
        name = clean_text(item, "name", max_len=80, label="component name")
        category = item.get("category", "Assignments")
        if category not in RUBRIC_CATEGORIES:
            raise bad_request(f"Component category must be one of: {', '.join(RUBRIC_CATEGORIES)}.", "INVALID_RUBRIC")
        weight = to_decimal(item.get("weight"), f"Weight for '{name}'", minimum=0.01, maximum=100000)
        parsed.append((name, category, weight))
    return parsed


def _apply_rubric(course, parsed):
    normalized = normalize_weights([w for _, _, w in parsed])
    course.rubric.clear()
    db.session.flush()
    for (name, category, raw), weight in zip(parsed, normalized):
        course.rubric.append(
            RubricComponent(component_name=name, category=category, raw_weight=raw, normalized_weight=weight)
        )


def _validate_faculty(faculty_id):
    faculty_id = to_int(faculty_id, "Assigned faculty", minimum=1)
    faculty = db.session.get(User, faculty_id)
    if faculty is None or faculty.role != ROLE_FACULTY or not faculty.is_active:
        raise bad_request("Assigned faculty must be an active faculty account.", "INVALID_FACULTY")
    return faculty_id


def create_course(data):
    course = Course(
        code=clean_text(data, "code", max_len=20, label="course code").upper(),
        title=clean_text(data, "title", max_len=160),
        section=(clean_text(data, "section", required=False, max_len=10) or "A").upper(),
        term=clean_text(data, "term", required=False, max_len=30) or current_term(),
        credits=to_int(data.get("credits", 3), "Credits", minimum=1, maximum=6),
        capacity=to_int(data.get("capacity"), "Seat capacity", minimum=1, maximum=1000),
        assigned_faculty_id=_validate_faculty(data.get("assigned_faculty_id")),
    )
    parsed = _parse_rubric(data.get("rubric"))
    db.session.add(course)
    try:
        db.session.flush()
        _apply_rubric(course, parsed)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise conflict("This course section already exists for the selected term.", "DUPLICATE_COURSE")
    return course


def update_course(course_id, data):
    course = get_course(course_id)
    if "code" in data:
        course.code = clean_text(data, "code", max_len=20, label="course code").upper()
    if "title" in data:
        course.title = clean_text(data, "title", max_len=160)
    if "section" in data:
        course.section = clean_text(data, "section", max_len=10).upper()
    if "credits" in data:
        course.credits = to_int(data["credits"], "Credits", minimum=1, maximum=6)
    if "assigned_faculty_id" in data:
        course.assigned_faculty_id = _validate_faculty(data["assigned_faculty_id"])
    if "capacity" in data:
        capacity = to_int(data["capacity"], "Seat capacity", minimum=1, maximum=1000)
        enrolled = _enrolled_counts([course.id]).get(course.id, 0)
        if capacity < enrolled:
            raise conflict(f"Capacity cannot be lower than the {enrolled} students already enrolled.", "CAPACITY_TOO_LOW")
        course.capacity = capacity
    if "rubric" in data:
        has_marks = (
            db.session.query(GradeRecord.id)
            .join(Enrollment, Enrollment.id == GradeRecord.enrollment_id)
            .filter(Enrollment.course_id == course.id)
            .first()
        )
        if has_marks:
            raise conflict("The rubric is locked because marks have already been entered.", "RUBRIC_LOCKED")
        _apply_rubric(course, _parse_rubric(data["rubric"]))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise conflict("This course section already exists for the selected term.", "DUPLICATE_COURSE")
    return course
