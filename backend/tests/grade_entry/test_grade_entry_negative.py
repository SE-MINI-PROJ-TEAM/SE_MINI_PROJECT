"""US-11 negative paths: malformed bulk saves, locked grades, unknown resources."""
import pytest

from app.models import GradeRecord
from tests.factories import enroll, login, make_course, make_user, scores, set_grade


@pytest.fixture
def world(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    course = make_course(faculty)
    enrollment = enroll(student, course)
    login(client, faculty)
    return client, student, course, enrollment


@pytest.mark.parametrize("students", [None, [], "x", ["not-an-object"]])
def test_bulk_save_requires_a_list_of_entries(world, students):
    client, _, course, _ = world
    assert client.put(f"/api/v1/grades/courses/{course.id}", json={"students": students}).status_code == 400


def test_bulk_save_unknown_student_and_unknown_course(world):
    client, _, course, _ = world
    unknown = {"students": [{"student_id": "NOPE", "rubric_scores": scores(course, 50)}]}
    assert client.put(f"/api/v1/grades/courses/{course.id}", json=unknown).status_code == 404
    assert client.put("/api/v1/grades/courses/99999", json={"students": [{"student_id": "X", "rubric_scores": []}]}).status_code == 404
    assert client.get("/api/v1/grades/courses/99999").status_code == 404


def test_bulk_save_blocked_for_non_draft_and_is_atomic(world):
    client, student, course, enrollment = world
    other = make_user("Student")
    enroll(other, course)
    set_grade(enrollment, course, [60, 60], "Submitted")
    response = client.put(
        f"/api/v1/grades/courses/{course.id}",
        json={
            "students": [
                {"student_id": other.institutional_id, "rubric_scores": scores(course, 10)},
                {"student_id": student.institutional_id, "rubric_scores": scores(course, 99)},
            ]
        },
    )
    assert response.status_code == 409 and response.get_json()["code"] == "GRADE_LOCKED"
    assert GradeRecord.query.count() == 2  # the rejected batch saved nothing, not even the valid student


@pytest.mark.parametrize(
    "body",
    [{"target_state": "Archived"}, {"target_state": "Under Review"}, {"rubric_scores": "x"}, {"rubric_scores": [1]}, {"rubric_scores": []}],
)
def test_single_student_endpoint_rejects_bad_requests(world, body):
    client, student, course, _ = world
    response = client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json=body)
    assert response.status_code in (400, 403)


def test_unauthenticated_and_student_cannot_save(world):
    client, student, course, _ = world
    assert client.application.test_client().put(f"/api/v1/grades/courses/{course.id}", json={"students": []}).status_code == 401
    s_client = client.application.test_client()
    login(s_client, student)
    assert s_client.put(f"/api/v1/grades/courses/{course.id}", json={"students": []}).status_code == 403
