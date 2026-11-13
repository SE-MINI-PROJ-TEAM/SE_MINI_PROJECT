"""US-13 / TC-GRD-04, TC-GRD-05 — regrade disputes and re-publication."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import AuditLog, Enrollment, GradeDispute
from tests.factories import bearer, enroll, login, make_course, make_user, scores, set_grade

REASON = "I believe question 3 of the end-term was marked incorrectly."


@pytest.fixture
def world(ctx, client):
    admin, faculty, student = make_user("Admin"), make_user("Faculty"), make_user("Student")
    course = make_course(faculty, weights=(40, 60))
    enrollment = enroll(student, course)
    set_grade(enrollment, course, [70, 80], "Published")
    login(client, student)
    return client, admin, faculty, student, course, enrollment


def file(client, enrollment, reason=REASON):
    return client.post("/api/v1/disputes", json={"enrollment_id": enrollment.id, "reason": reason})


def test_filing_moves_published_grade_to_under_review(world):
    client, *_, enrollment = world
    response = file(client, enrollment)
    assert response.status_code == 201
    assert Enrollment.query.get(enrollment.id).grade_state == "Under Review"
    dispute = GradeDispute.query.one()
    assert dispute.status == "Open" and dispute.reason == REASON and float(dispute.previous_total) == 76.0
    grade = client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert grade["state"] == "Under Review" and grade["dispute"]["open"] is True


@pytest.mark.parametrize("reason", ["", "   ", "too short", None])
def test_explanation_is_required(world, reason):
    client, *_, enrollment = world
    assert file(client, enrollment, reason).status_code == 400
    assert Enrollment.query.get(enrollment.id).grade_state == "Published"


def test_only_published_grades_can_be_disputed_and_only_once(world):
    client, *_, enrollment = world
    assert file(client, enrollment).status_code == 201
    again = file(client, enrollment)
    assert again.status_code == 409 and again.get_json()["code"] == "ALREADY_DISPUTED"

    draft_student = make_user("Student")
    course = make_course(make_user("Faculty"))
    draft = enroll(draft_student, course)
    set_grade(draft, course, [50, 50], "Draft")
    other = client.application.test_client()
    login(other, draft_student)
    assert file(other, draft).status_code == 409


def test_cannot_dispute_someone_elses_grade(world):
    client, *_ = world
    foreign_course = make_course(make_user("Faculty"))
    foreign = enroll(make_user("Student"), foreign_course)
    set_grade(foreign, foreign_course, [50, 50], "Published")
    assert file(client, foreign).status_code == 404


def test_faculty_sees_notification_count_reevaluates_and_republishes(world):
    client, admin, faculty, student, course, enrollment = world
    file(client, enrollment)

    f_client = client.application.test_client()
    login(f_client, faculty)
    assert f_client.get("/api/v1/disputes/pending-count").get_json()["count"] == 1
    item = f_client.get("/api/v1/disputes?status=Open").get_json()["disputes"][0]
    assert item["student"]["institutional_id"] == student.institutional_id
    assert [r["score"] for r in item["rubric"]] == [70.0, 80.0]

    resolved = f_client.post(f"/api/v1/disputes/{item['id']}/resolve", json={"resolution_note": "Q3 re-marked", "rubric_scores": scores(course, 70, 95)})
    assert resolved.status_code == 200
    enrollment_now = Enrollment.query.get(enrollment.id)
    assert enrollment_now.grade_state == "Published" and float(enrollment_now.weighted_total) == 85.0  # 28 + 57
    assert f_client.get("/api/v1/disputes/pending-count").get_json()["count"] == 0
    assert AuditLog.query.filter_by(action="DISPUTE_RESOLVED").count() == 1

    grade = client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert grade["state"] == "Published" and grade["weighted_total"] == 85.0
    assert grade["dispute"]["resolution_note"] == "Q3 re-marked" and grade["dispute"]["open"] is False


def test_resolution_with_unchanged_scores_still_republishes(world):
    client, _, faculty, _, course, enrollment = world
    file(client, enrollment)
    f_client = client.application.test_client()
    login(f_client, faculty)
    dispute = GradeDispute.query.one()
    assert f_client.post(f"/api/v1/disputes/{dispute.id}/resolve", json={"resolution_note": "Marks verified, no change"}).status_code == 200
    assert float(Enrollment.query.get(enrollment.id).weighted_total) == 76.0


def test_admin_can_resolve_too_and_double_resolution_is_rejected(world):
    client, admin, *_, enrollment = world
    file(client, enrollment)
    a_client = client.application.test_client()
    login(a_client, admin)
    dispute = GradeDispute.query.one()
    body = {"resolution_note": "Admin recheck", "rubric_scores": []}
    assert a_client.post(f"/api/v1/disputes/{dispute.id}/resolve", json=body).status_code == 200
    assert a_client.post(f"/api/v1/disputes/{dispute.id}/resolve", json=body).status_code == 409


def test_resolution_note_required_and_roles_enforced(world):
    client, _, faculty, student, course, enrollment = world
    file(client, enrollment)
    dispute = GradeDispute.query.one()
    f_client = client.application.test_client()
    login(f_client, faculty)
    assert f_client.post(f"/api/v1/disputes/{dispute.id}/resolve", json={"resolution_note": " "}).status_code == 400
    # another faculty member and the student cannot resolve it
    other = client.application.test_client()
    login(other, make_user("Faculty"))
    assert other.post(f"/api/v1/disputes/{dispute.id}/resolve", json={"resolution_note": "nope"}).status_code == 403
    assert other.get("/api/v1/disputes").get_json()["disputes"] == []
    assert client.post(f"/api/v1/disputes/{dispute.id}/resolve", json={"resolution_note": "self-service"}).status_code == 403
    assert client.get("/api/v1/disputes/pending-count").status_code == 403


def test_student_lists_own_disputes(world):
    client, *_, enrollment = world
    file(client, enrollment)
    mine = client.get("/api/v1/disputes/mine").get_json()["disputes"]
    assert len(mine) == 1 and mine[0]["status"] == "Open"


# ------------------------------------------------- a grade can be disputed only once
def resolve_as_faculty(client, faculty, note="Rechecked"):
    f_client = client.application.test_client()
    login(f_client, faculty)
    dispute = GradeDispute.query.one()
    assert f_client.post(f"/api/v1/disputes/{dispute.id}/resolve", json={"resolution_note": note}).status_code == 200


def test_cannot_dispute_again_after_the_dispute_was_resolved(world):
    client, _, faculty, _, _, enrollment = world
    assert file(client, enrollment).status_code == 201
    resolve_as_faculty(client, faculty)
    assert Enrollment.query.get(enrollment.id).grade_state == "Published"  # re-published, back to Published...

    second = file(client, enrollment, "I still disagree with the new marks.")
    assert second.status_code == 409 and second.get_json()["code"] == "ALREADY_DISPUTED"  # ...but final
    assert Enrollment.query.get(enrollment.id).grade_state == "Published"  # state untouched by the rejected request
    assert GradeDispute.query.count() == 1


def test_student_view_tells_the_ui_whether_a_regrade_is_still_available(world):
    client, _, faculty, _, _, enrollment = world
    assert client.get("/api/v1/grades/mine").get_json()["grades"][0]["can_dispute"] is True
    file(client, enrollment)
    under_review = client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert under_review["can_dispute"] is False and under_review["dispute"]["open"] is True
    resolve_as_faculty(client, faculty)
    final = client.get("/api/v1/grades/mine").get_json()["grades"][0]
    assert final["state"] == "Published" and final["can_dispute"] is False and final["dispute"]["open"] is False


def test_each_course_grade_has_its_own_single_dispute(world):
    client, _, faculty, student, _, enrollment = world
    file(client, enrollment)
    resolve_as_faculty(client, faculty)
    other_course = make_course(faculty)
    other = enroll(student, other_course)
    set_grade(other, other_course, [55, 65], "Published")
    assert file(client, other).status_code == 201  # a different grade is a fresh allowance
    assert file(client, enrollment).status_code == 409


def test_database_itself_rejects_a_second_dispute_row(world):
    _, _, _, student, _, enrollment = world
    db.session.add(GradeDispute(enrollment_id=enrollment.id, student_id=student.id, reason="first dispute reason"))
    db.session.commit()
    db.session.add(GradeDispute(enrollment_id=enrollment.id, student_id=student.id, reason="sneaky second dispute"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_simultaneous_requests_produce_exactly_one_dispute(world):
    client, _, _, student, _, enrollment = world
    app, enrollment_id, headers = client.application, enrollment.id, bearer(student)

    def attempt(_):
        body = {"enrollment_id": enrollment_id, "reason": REASON}
        return app.test_client().post("/api/v1/disputes", json=body, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(attempt, range(10)))
    assert codes.count(201) == 1 and codes.count(409) == 9
    assert GradeDispute.query.count() == 1
