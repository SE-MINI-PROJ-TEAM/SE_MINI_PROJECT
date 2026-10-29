"""US-11 / TC-GRD-01 — rubric score entry in Draft; marks stay hidden from students."""
import pytest

from app.models import Enrollment, GradeRecord
from tests.factories import enroll, login, make_course, make_user, scores


@pytest.fixture
def world(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    course = make_course(faculty, weights=(40, 60))
    enrollment = enroll(student, course)
    login(client, faculty)
    return client, faculty, student, course, enrollment


def test_grid_renders_rubric_components_for_each_enrolled_student(world):
    client, _, student, course, _ = world
    body = client.get(f"/api/v1/grades/courses/{course.id}").get_json()
    assert [r["weight"] for r in body["rubric"]] == [40.0, 60.0]
    row = body["students"][0]
    assert row["student_id"] == student.institutional_id and row["state"] == "Not started" and row["editable"] is True


def test_partial_scores_save_as_draft(world):
    client, _, student, course, enrollment = world
    response = client.put(f"/api/v1/grades/courses/{course.id}", json={"students": [{"student_id": student.institutional_id, "rubric_scores": scores(course, 70)}]})
    assert response.status_code == 200 and response.get_json()["saved"] == 1
    assert Enrollment.query.get(enrollment.id).grade_state == "Draft"
    assert GradeRecord.query.filter_by(enrollment_id=enrollment.id).count() == 1

    # complete the remaining component later: scores are updated in place
    client.put(f"/api/v1/grades/courses/{course.id}", json={"students": [{"student_id": student.institutional_id, "rubric_scores": scores(course, 75, 90)}]})
    assert GradeRecord.query.filter_by(enrollment_id=enrollment.id).count() == 2
    row = client.get(f"/api/v1/grades/courses/{course.id}").get_json()["students"][0]
    assert row["weighted_total"] == 84.0 and row["state"] == "Draft"  # preview only; not stored as an official total
    assert Enrollment.query.get(enrollment.id).weighted_total is None


def test_students_cannot_view_marks_while_draft(world):
    client, _, student, course, _ = world
    client.put(f"/api/v1/grades/courses/{course.id}", json={"students": [{"student_id": student.institutional_id, "rubric_scores": scores(course, 88, 91)}]})
    s_client = client.application.test_client()
    login(s_client, student)
    grade = s_client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert grade["state"] == "Pending"
    assert "weighted_total" not in grade and "components" not in grade
    text = s_client.get("/api/v1/grades/mine").get_data(as_text=True)
    assert "88" not in text and "91" not in text
    assert s_client.get("/api/v1/analytics/student/summary").get_json()["courses"] == []


@pytest.mark.parametrize("score", [-1, 100.5, "abc", None, True])
def test_scores_must_be_numbers_between_0_and_100(world, score):
    client, _, student, course, _ = world
    response = client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json={"rubric_scores": [{"rubric_id": course.rubric[0].id, "score": score}], "target_state": "Draft"})
    assert response.status_code == 400


def test_rubric_id_from_another_course_rejected(world):
    client, _, student, course, _ = world
    other = make_course(make_user("Faculty"))
    response = client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json={"rubric_scores": [{"rubric_id": other.rubric[0].id, "score": 50}]})
    assert response.status_code == 400 and response.get_json()["code"] == "INVALID_RUBRIC"


def test_sad_contract_single_student_draft(world):
    client, _, student, course, _ = world
    response = client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json={"rubric_scores": scores(course, 80), "target_state": "Draft"})
    assert response.status_code == 200 and response.get_json()["grade_state"] == "Draft"


def test_edits_blocked_once_submitted(world):
    client, _, student, course, _ = world
    path = f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}"
    assert client.put(path, json={"rubric_scores": scores(course, 80, 90), "target_state": "Submitted"}).status_code == 200
    again = client.put(path, json={"rubric_scores": scores(course, 10, 10), "target_state": "Draft"})
    assert again.status_code == 409 and again.get_json()["code"] == "GRADE_LOCKED"


def test_faculty_cannot_publish_through_the_grade_endpoint(world):
    client, _, student, course, _ = world
    response = client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json={"rubric_scores": scores(course, 80, 90), "target_state": "Published"})
    assert response.status_code == 403


def test_faculty_cannot_grade_other_faculty_sections(world):
    client, *_ = world
    foreign = make_course(make_user("Faculty"))
    stranger = make_user("Student")
    enroll(stranger, foreign)
    assert client.get(f"/api/v1/grades/courses/{foreign.id}").status_code == 403
    assert client.put(f"/api/v1/grades/courses/{foreign.id}", json={"students": [{"student_id": stranger.institutional_id, "rubric_scores": scores(foreign, 50)}]}).status_code == 403


def test_unknown_student_404_and_students_forbidden(world):
    client, _, _, course, _ = world
    assert client.put(f"/api/v1/grades/courses/{course.id}/students/NOPE", json={"rubric_scores": scores(course, 50)}).status_code == 404
    s_client = client.application.test_client()
    login(s_client, make_user("Student"))
    assert s_client.get(f"/api/v1/grades/courses/{course.id}").status_code == 403


def test_course_list_reports_state_counts(world):
    client, *_, course, _ = world
    body = client.get("/api/v1/grades/courses").get_json()["courses"]
    assert body[0]["states"] == {"Not started": 1}
