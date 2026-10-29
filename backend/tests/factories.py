"""Test data builders + auth helpers shared by every feature's tests."""
import itertools
from datetime import timedelta
from decimal import Decimal

from app.core.rubric import normalize_weights
from app.core.security import hash_password, issue_token
from app.core.timeutil import utcnow
from app.extensions import db
from app.models import Course, Enrollment, Profile, RubricComponent, ScheduleSession, User

PASSWORD = "Password@123"
_counter = itertools.count(1)


def make_user(role="Student", *, password=PASSWORD, temp=False, active=True, name=None):
    n = next(_counter)
    user = User(
        institutional_id=f"{role[:3].upper()}{n:04d}",
        email=f"{role.lower()}{n}@test.edu",
        full_name=name or f"{role} {n}",
        role=role,
        password_hash=hash_password(password),
        is_temporary_password=temp,
        is_active=active,
    )
    user.profile = Profile()
    db.session.add(user)
    db.session.commit()
    return user


def make_course(faculty, *, capacity=30, credits=3, weights=(40, 60), term="Fall 2026", code=None):
    n = next(_counter)
    course = Course(
        code=code or f"TST{n:03d}", title=f"Test Course {n}", section="A", term=term, credits=credits,
        capacity=capacity, assigned_faculty_id=faculty.id,
    )
    normalized = normalize_weights(weights)
    for i, (raw, norm) in enumerate(zip(weights, normalized)):
        course.rubric.append(
            RubricComponent(component_name=f"Component {i + 1}", category="Exams", raw_weight=raw, normalized_weight=norm)
        )
    db.session.add(course)
    db.session.commit()
    return course


def make_session(course, *, hours_ago=1.0, duration_hours=1, room="R-1"):
    start = utcnow() - timedelta(hours=hours_ago)
    session = ScheduleSession(
        course_id=course.id, start_time=start, end_time=start + timedelta(hours=duration_hours), room_number=room
    )
    db.session.add(session)
    db.session.commit()
    return session


def enroll(student, course):
    enrollment = Enrollment(student_id=student.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()
    return enrollment


def bearer(user):
    return {"Authorization": f"Bearer {issue_token(user)}"}


def login(client, user, password=PASSWORD):
    response = client.post("/api/v1/auth/login", json={"identifier": user.email, "password": password})
    assert response.status_code == 200, response.get_json()
    return client


def scores(course, *values):
    """[{rubric_id, score}] for a course's rubric in order."""
    return [{"rubric_id": c.id, "score": v} for c, v in zip(course.rubric, values)]


def set_grade(enrollment, course, values, state, total=None):
    """Directly persist grade records + enrollment summary (bypassing the API) for arrange steps."""
    from app.core.grading import compute_weighted_total, upsert_scores

    upsert_scores(enrollment, {c.id: Decimal(str(v)) for c, v in zip(course.rubric, values)}, state)
    enrollment.grade_state = state
    enrollment.weighted_total = total if total is not None else compute_weighted_total(
        {c.id: Decimal(str(v)) for c, v in zip(course.rubric, values)}, course.rubric
    )
    db.session.commit()
