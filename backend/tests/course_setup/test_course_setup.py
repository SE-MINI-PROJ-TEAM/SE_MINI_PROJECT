"""US-05 / TC-CRS-01 — course offerings, capacities and rubric auto-normalisation to exactly 100%."""
import random
from decimal import Decimal

import pytest

from app.core.rubric import normalize_weights
from tests.factories import enroll, login, make_course, make_user


# ------------------------------------------------------------------ unit
@pytest.mark.parametrize(
    "raw",
    [[1, 1, 1], [20, 30, 20, 30], [25, 25, 35], [10, 40, 50], [1], [0.1, 0.2, 0.3], [33.33, 33.33, 33.33], [7, 11, 13, 17, 19]],
)
def test_weights_always_sum_to_exactly_100(raw):
    result = normalize_weights(raw)
    assert sum(result) == Decimal("100.00")
    assert all(w > 0 for w in result)


def test_normalization_preserves_proportions():
    assert normalize_weights([1, 3]) == [Decimal("25.00"), Decimal("75.00")]
    assert normalize_weights([2, 2, 4]) == [Decimal("25.00"), Decimal("25.00"), Decimal("50.00")]


def test_random_weight_sets_sum_to_100():
    rng = random.Random(1)
    for _ in range(300):
        raw = [round(rng.uniform(0.5, 250), 2) for _ in range(rng.randint(1, 9))]
        assert sum(normalize_weights(raw)) == Decimal("100.00")


@pytest.mark.parametrize("bad", [[], [0, 10], [-5, 5]])
def test_invalid_weights_rejected(bad):
    with pytest.raises(ValueError):
        normalize_weights(bad)


# ------------------------------------------------------------------- API
@pytest.fixture
def setup(ctx, client):
    admin = make_user("Admin")
    faculty = make_user("Faculty")
    login(client, admin)
    payload = {
        "code": "cs777", "title": "Advanced Testing", "section": "a", "credits": 4, "capacity": 25, "assigned_faculty_id": faculty.id,
        "rubric": [{"name": "Assignments", "category": "Assignments", "weight": 1}, {"name": "Midterm", "category": "Exams", "weight": 1}, {"name": "Project", "category": "Projects", "weight": 1}],
    }
    return client, faculty, payload


def test_create_course_normalizes_rubric_on_save(setup):
    client, faculty, payload = setup
    response = client.post("/api/v1/courses", json=payload)
    assert response.status_code == 201
    course = response.get_json()["course"]
    assert course["code"] == "CS777" and course["capacity"] == 25 and course["faculty_name"] == faculty.full_name
    assert sum(r["weight"] for r in course["rubric"]) == pytest.approx(100.0, abs=1e-9)
    assert {r["raw_weight"] for r in course["rubric"]} == {1.0}


def test_duplicate_section_conflicts(setup):
    client, _, payload = setup
    assert client.post("/api/v1/courses", json=payload).status_code == 201
    assert client.post("/api/v1/courses", json=payload).status_code == 409


@pytest.mark.parametrize(
    "change",
    [{"capacity": 0}, {"credits": 9}, {"rubric": []}, {"assigned_faculty_id": 99999}, {"rubric": [{"name": "x", "category": "Exams", "weight": 0}]}, {"rubric": [{"name": "x", "category": "Bogus", "weight": 5}]}],
)
def test_invalid_course_payloads(setup, change):
    client, _, payload = setup
    assert client.post("/api/v1/courses", json={**payload, **change}).status_code == 400


def test_student_cannot_be_assigned_as_faculty(setup):
    client, _, payload = setup
    student = make_user("Student")
    assert client.post("/api/v1/courses", json={**payload, "assigned_faculty_id": student.id}).status_code == 400


def test_edit_capacity_but_not_below_enrolled(setup):
    client, faculty, _ = setup
    course = make_course(faculty, capacity=5)
    for _ in range(3):
        enroll(make_user("Student"), course)
    assert client.put(f"/api/v1/courses/{course.id}", json={"capacity": 2}).get_json()["code"] == "CAPACITY_TOO_LOW"
    ok = client.put(f"/api/v1/courses/{course.id}", json={"capacity": 10})
    assert ok.status_code == 200 and ok.get_json()["course"]["capacity"] == 10


def test_rubric_is_renormalized_on_edit_and_locked_once_marks_exist(setup):
    client, faculty, _ = setup
    course = make_course(faculty, weights=(50, 50))
    response = client.put(f"/api/v1/courses/{course.id}", json={"rubric": [{"name": "A", "category": "Exams", "weight": 3}, {"name": "B", "category": "Projects", "weight": 1}]})
    assert [r["weight"] for r in response.get_json()["course"]["rubric"]] == [75.0, 25.0]

    # once marks exist the rubric is frozen
    student = make_user("Student")
    enrollment = enroll(student, course)
    from tests.factories import set_grade
    from app.models import Course
    fresh = Course.query.get(course.id)
    set_grade(enrollment, fresh, [80, 60], "Draft")
    locked = client.put(f"/api/v1/courses/{course.id}", json={"rubric": [{"name": "A", "category": "Exams", "weight": 1}]})
    assert locked.status_code == 409 and locked.get_json()["code"] == "RUBRIC_LOCKED"


def test_listing_requires_admin(ctx, client):
    login(client, make_user("Faculty"))
    assert client.get("/api/v1/courses").status_code == 403
