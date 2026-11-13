"""US-08 negative paths: bad query parameters, malformed entries and unknown resources."""
import pytest

from tests.factories import enroll, login, make_course, make_session, make_user


@pytest.fixture
def faculty_client(ctx, client):
    faculty = make_user("Faculty")
    login(client, faculty)
    return client, faculty


@pytest.mark.parametrize(
    "query",
    [
        {"from": "nope"},
        {"from": "2026-01-02T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
        {"from": "2020-01-01T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
    ],
)
def test_session_list_rejects_bad_ranges(faculty_client, query):
    client, _ = faculty_client
    assert client.get("/api/v1/attendance/sessions", query_string=query).status_code == 400


def test_unknown_session_returns_404(faculty_client):
    client, _ = faculty_client
    payload = {"attendance_list": [{"student_id": "X", "is_present": True}]}
    assert client.get("/api/v1/attendance/sessions/99999").status_code == 404
    assert client.post("/api/v1/attendance/sessions/99999", json=payload).status_code == 404


def test_non_boolean_presence_and_blank_ids_rejected(faculty_client):
    client, faculty = faculty_client
    course = make_course(faculty)
    student = make_user("Student")
    enroll(student, course)
    session = make_session(course, hours_ago=1)
    bad_entries = (
        {"student_id": student.institutional_id, "is_present": "yes"},
        {"student_id": student.institutional_id, "is_present": 1},
        {"student_id": "  ", "is_present": True},
    )
    for entry in bad_entries:
        assert client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": [entry]}).status_code == 400, entry


def test_invalid_bearer_token_is_rejected(client):
    response = client.post("/api/v1/attendance/sessions/1", json={}, headers={"Authorization": "Bearer expired.or.bad"})
    assert response.status_code == 401
