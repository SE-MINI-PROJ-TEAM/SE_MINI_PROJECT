"""US-12 / TC-GRD-02, TC-GRD-03 — weighted submission, batch publication and student visibility."""
from decimal import Decimal

import pytest

from app.core import grading
from app.core.errors import ApiError
from app.models import AuditLog, Enrollment
from tests.factories import enroll, login, make_course, make_user, scores


# ------------------------------------------------------------------ unit
def test_weighted_total_applies_normalized_weights(ctx):
    course = make_course(make_user("Faculty"), weights=(20, 30, 50))
    values = {c.id: Decimal(v) for c, v in zip(course.rubric, ("80", "70", "90"))}
    assert grading.compute_weighted_total(values, course.rubric) == Decimal("82.00")  # 16 + 21 + 45


def test_weighted_total_rounds_half_up_and_requires_every_score(ctx):
    course = make_course(make_user("Faculty"), weights=(1, 1, 1))
    values = {c.id: Decimal("50") for c in course.rubric}
    assert grading.compute_weighted_total(values, course.rubric) == Decimal("50.00")
    with pytest.raises(ValueError):
        grading.compute_weighted_total({course.rubric[0].id: Decimal("1")}, course.rubric)


@pytest.mark.parametrize("total,letter", [(100, "A"), (90, "A"), (89.99, "B"), (80, "B"), (70, "C"), (60, "D"), (59.99, "F"), (0, "F")])
def test_letter_boundaries(total, letter):
    assert grading.letter_for(total) == letter


@pytest.mark.parametrize(
    "current,target,ok",
    [
        (None, "Draft", True), ("Draft", "Draft", True), ("Draft", "Submitted", True), ("Submitted", "Published", True),
        ("Published", "Under Review", True), ("Under Review", "Published", True),
        (None, "Published", False), ("Draft", "Published", False), ("Submitted", "Draft", False),
        ("Published", "Draft", False), ("Published", "Submitted", False), ("Under Review", "Draft", False),
    ],
)
def test_state_machine_transitions(current, target, ok):
    if ok:
        grading.assert_transition(current, target)
    else:
        with pytest.raises(ApiError) as err:
            grading.assert_transition(current, target)
        assert err.value.status == 409


def test_grade_points_use_a_ten_point_scale():
    assert [grading.points_for(letter) for letter in grading.LETTERS] == [10, 8, 6, 4, 0]


# ------------------------------------------------------------------- API
@pytest.fixture
def world(ctx, client):
    admin, faculty = make_user("Admin"), make_user("Faculty")
    course = make_course(faculty, weights=(40, 60))
    students = [make_user("Student") for _ in range(3)]
    enrollments = [enroll(s, course) for s in students]
    return client, admin, faculty, course, students, enrollments


def grade(client, course, student, *values, state="Draft"):
    return client.put(f"/api/v1/grades/courses/{course.id}/students/{student.institutional_id}", json={"rubric_scores": scores(course, *values), "target_state": state})


def test_submit_calculates_weighted_total_and_moves_to_submitted(world):
    client, _, faculty, course, students, _ = world
    login(client, faculty)
    response = grade(client, course, students[0], 85, 90, state="Submitted")
    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "grade_state": "Submitted", "weighted_total": 88.0}  # 34 + 54


def test_cannot_submit_with_missing_components(world):
    client, _, faculty, course, students, _ = world
    login(client, faculty)
    response = grade(client, course, students[0], 85, state="Submitted")
    assert response.status_code == 400 and response.get_json()["code"] == "INCOMPLETE_SCORES"


def test_batch_submit_skips_incomplete_students(world):
    client, _, faculty, course, students, enrollments = world
    login(client, faculty)
    grade(client, course, students[0], 80, 80)
    grade(client, course, students[1], 70, 70)
    grade(client, course, students[2], 60)  # incomplete
    body = client.post(f"/api/v1/grades/courses/{course.id}/submit").get_json()
    assert body["submitted"] == 2 and [s["student_id"] for s in body["skipped"]] == [students[2].institutional_id]
    states = {e.id: Enrollment.query.get(e.id).grade_state for e in enrollments}
    assert sorted(states.values()) == ["Draft", "Submitted", "Submitted"]


def test_admin_publishes_and_students_see_grades_immediately(world):
    client, admin, faculty, course, students, enrollments = world
    login(client, faculty)
    for s in students:
        grade(client, course, s, 90, 95, state="Submitted")

    student_client = client.application.test_client()
    login(student_client, students[0])
    assert student_client.get("/api/v1/grades/mine").get_json()["grades"][0]["state"] == "Pending"  # not yet visible

    admin_client = client.application.test_client()
    login(admin_client, admin)
    queue = admin_client.get("/api/v1/grades/publication/queue").get_json()["courses"]
    assert queue[0]["submitted_count"] == 3
    result = admin_client.post("/api/v1/grades/publication/publish", json={"course_ids": [course.id]})
    assert result.status_code == 200 and result.get_json()["published"] == {str(course.id): 3}

    visible = student_client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert visible["state"] == "Published" and visible["weighted_total"] == 93.0 and visible["letter"] == "A"
    assert visible["can_dispute"] is True
    assert [c["score"] for c in visible["components"]] == [90.0, 95.0]
    assert admin_client.get("/api/v1/grades/publication/queue").get_json()["courses"] == []
    assert AuditLog.query.filter_by(action="GRADES_PUBLISHED").count() == 1


def test_publishing_with_nothing_submitted_is_rejected(world):
    client, admin, _, course, *_ = world
    login(client, admin)
    assert client.post("/api/v1/grades/publication/publish", json={"course_ids": [course.id]}).status_code == 400
    assert client.post("/api/v1/grades/publication/publish", json={"course_ids": []}).status_code == 400


def test_only_admin_publishes_and_only_assigned_faculty_submits(world):
    client, _, faculty, course, students, _ = world
    login(client, faculty)
    assert client.post("/api/v1/grades/publication/publish", json={"course_ids": [course.id]}).status_code == 403
    other = client.application.test_client()
    login(other, make_user("Faculty"))
    assert other.post(f"/api/v1/grades/courses/{course.id}/submit").status_code == 403
    s_client = client.application.test_client()
    login(s_client, students[0])
    assert s_client.post("/api/v1/grades/publication/publish", json={"course_ids": [course.id]}).status_code == 403
