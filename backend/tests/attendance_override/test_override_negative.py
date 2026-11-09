"""US-09 negative paths."""
import pytest

from app.models import AuditLog
from tests.factories import enroll, login, make_course, make_session, make_user


@pytest.fixture
def world(ctx, client):
    admin, student = make_user("Admin"), make_user("Student")
    course = make_course(make_user("Faculty"))
    enroll(student, course)
    login(client, admin)
    return client, student, course


def change(student):
    return {"changes": [{"student_id": student.institutional_id, "is_present": True}], "reason": "Valid reason"}


def test_unknown_session_and_missing_course_param(world):
    client, student, _ = world
    assert client.put("/api/v1/attendance/override/sessions/99999", json=change(student)).status_code == 404
    assert client.get("/api/v1/attendance/override/sessions/99999").status_code == 404
    assert client.get("/api/v1/attendance/override/sessions").status_code == 400


def test_cannot_override_a_session_that_has_not_started(world):
    client, student, course = world
    future = make_session(course, hours_ago=-5)
    response = client.put(f"/api/v1/attendance/override/sessions/{future.id}", json=change(student))
    assert response.status_code == 400 and response.get_json()["code"] == "SESSION_NOT_STARTED"


@pytest.mark.parametrize("changes", [None, [], "x", [{"student_id": "A"}], [{"student_id": "A", "is_present": "no"}]])
def test_malformed_changes_rejected(world, changes):
    client, _, course = world
    session = make_session(course, hours_ago=80)
    assert client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": changes, "reason": "Valid reason"}).status_code == 400


def test_student_not_in_section_is_rejected_and_nothing_is_logged(world):
    client, _, course = world
    session = make_session(course, hours_ago=80)
    response = client.put(f"/api/v1/attendance/override/sessions/{session.id}", json=change(make_user("Student")))
    assert response.status_code == 404
    assert AuditLog.query.count() == 0
