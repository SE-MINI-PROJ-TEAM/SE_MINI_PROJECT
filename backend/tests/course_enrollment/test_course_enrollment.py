"""US-06 / TC-CRS-02 — self-enrollment, 6-course cap and live capacity."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.settings import set_setting
from app.extensions import db
from app.models import Enrollment
from tests.factories import bearer, enroll, login, make_course, make_user


@pytest.fixture
def world(ctx, client):
    faculty = make_user("Faculty")
    student = make_user("Student")
    login(client, student)
    return client, faculty, student


def test_catalog_shows_open_sections_with_real_time_capacity(world):
    client, faculty, student = world
    course = make_course(faculty, capacity=3)
    enroll(make_user("Student"), course)
    row = next(c for c in client.get("/api/v1/catalog").get_json()["courses"] if c["id"] == course.id)
    assert row["capacity"] == 3 and row["enrolled"] == 1 and row["seats_available"] == 2 and row["is_enrolled"] is False


def test_enrollment_decrements_available_seats_immediately(world):
    client, faculty, _ = world
    course = make_course(faculty, capacity=2)
    assert client.post("/api/v1/enrollments", json={"course_id": course.id}).status_code == 201
    row = next(c for c in client.get("/api/v1/catalog").get_json()["courses"] if c["id"] == course.id)
    assert row["seats_available"] == 1 and row["is_enrolled"] is True


def test_seventh_course_is_blocked_with_an_error(world):
    client, faculty, student = world
    courses = [make_course(faculty) for _ in range(7)]
    for course in courses[:6]:
        assert client.post("/api/v1/enrollments", json={"course_id": course.id}).status_code == 201
    response = client.post("/api/v1/enrollments", json={"course_id": courses[6].id})
    assert response.status_code == 409
    assert response.get_json()["code"] == "ENROLLMENT_LIMIT_REACHED"
    assert Enrollment.query.filter_by(student_id=student.id).count() == 6
    assert client.get("/api/v1/catalog").get_json()["my_course_count"] == 6


def test_cap_counts_only_the_current_term(world):
    client, faculty, student = world
    for _ in range(6):
        enroll(student, make_course(faculty, term="Spring 2026"))
    course = make_course(faculty)
    assert client.post("/api/v1/enrollments", json={"course_id": course.id}).status_code == 201


def test_full_section_rejected(world):
    client, faculty, _ = world
    course = make_course(faculty, capacity=1)
    enroll(make_user("Student"), course)
    response = client.post("/api/v1/enrollments", json={"course_id": course.id})
    assert response.status_code == 409 and response.get_json()["code"] == "SECTION_FULL"


def test_duplicate_enrollment_rejected(world):
    client, faculty, _ = world
    course = make_course(faculty)
    client.post("/api/v1/enrollments", json={"course_id": course.id})
    assert client.post("/api/v1/enrollments", json={"course_id": course.id}).get_json()["code"] == "ALREADY_ENROLLED"


def test_admin_can_close_the_enrollment_window(ctx, client):
    faculty, student, admin = make_user("Faculty"), make_user("Student"), make_user("Admin")
    course = make_course(faculty)
    admin_client = client.application.test_client()
    login(admin_client, admin)
    assert admin_client.put("/api/v1/enrollments/window", json={"open": False}).status_code == 200
    login(client, student)
    response = client.post("/api/v1/enrollments", json={"course_id": course.id})
    assert response.status_code == 403 and response.get_json()["code"] == "ENROLLMENT_CLOSED"
    admin_client.put("/api/v1/enrollments/window", json={"open": True})
    assert client.post("/api/v1/enrollments", json={"course_id": course.id}).status_code == 201


def test_only_students_enroll_and_unknown_course_404(world):
    client, _, _ = world
    assert client.post("/api/v1/enrollments", json={"course_id": 99999}).status_code == 404
    assert client.post("/api/v1/enrollments", json={}).status_code == 400
    admin_client = client.application.test_client()
    login(admin_client, make_user("Admin"))
    assert admin_client.post("/api/v1/enrollments", json={"course_id": 1}).status_code == 403


def test_my_enrollments_lists_courses(world):
    client, faculty, _ = world
    course = make_course(faculty)
    client.post("/api/v1/enrollments", json={"course_id": course.id})
    assert [e["code"] for e in client.get("/api/v1/enrollments/mine").get_json()["enrollments"]] == [course.code]


def test_concurrent_enrollments_never_exceed_capacity(ctx, client):
    faculty = make_user("Faculty")
    course = make_course(faculty, capacity=5)
    students = [make_user("Student") for _ in range(25)]
    app, course_id = client.application, course.id
    all_headers = [bearer(s) for s in students]  # built here: worker threads have no app context for ORM objects

    def attempt(headers):
        return app.test_client().post("/api/v1/enrollments", json={"course_id": course_id}, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=25) as pool:
        codes = list(pool.map(attempt, all_headers))

    assert codes.count(201) == 5
    assert codes.count(409) == 20
    assert Enrollment.query.filter_by(course_id=course.id).count() == 5
