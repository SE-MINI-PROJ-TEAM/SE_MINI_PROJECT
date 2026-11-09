"""US-09 / TC-ATT-03 — admin override after the freeze with mandatory justification and immutable audit."""
import pytest

from app.models import AttendanceRecord, AuditLog
from tests.factories import enroll, login, make_course, make_session, make_user


@pytest.fixture
def world(ctx, client):
    admin, faculty, student = make_user("Admin"), make_user("Faculty"), make_user("Student")
    course = make_course(faculty)
    enroll(student, course)
    session = make_session(course, hours_ago=72)  # long past the 48h faculty freeze
    from app.extensions import db
    db.session.add(AttendanceRecord(session_id=session.id, student_id=student.id, is_present=False))
    db.session.commit()
    login(client, admin)
    return client, admin, faculty, student, session


def change(student, present=True):
    return [{"student_id": student.institutional_id, "is_present": present}]


def test_admin_overrides_frozen_record_and_audit_entry_is_created(world):
    client, admin, _, student, session = world
    response = client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": change(student), "reason": "Medical certificate verified"})
    assert response.status_code == 200 and response.get_json()["changed"] == 1
    assert AttendanceRecord.query.filter_by(session_id=session.id).one().is_present is True

    entry = AuditLog.query.filter_by(action="ATTENDANCE_OVERRIDE").one()
    assert entry.actor_id == admin.id
    assert entry.created_at is not None
    assert entry.details["old_value"] == "Absent" and entry.details["new_value"] == "Present"
    assert entry.details["reason"] == "Medical certificate verified"
    assert entry.details["student_id"] == student.institutional_id and entry.details["was_frozen"] is True


def test_faculty_is_still_blocked_on_the_same_frozen_session(world, ctx):
    client, _, faculty, student, session = world
    f_client = client.application.test_client()
    login(f_client, faculty)
    assert f_client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": change(student)}).status_code == 403


@pytest.mark.parametrize("reason", ["", "   ", "no", None])
def test_justification_is_mandatory(world, reason):
    client, _, _, student, session = world
    response = client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": change(student), "reason": reason})
    assert response.status_code == 400
    assert AuditLog.query.count() == 0
    assert AttendanceRecord.query.filter_by(session_id=session.id).one().is_present is False


def test_override_can_create_a_missing_record(world):
    client, _, _, _, session = world
    newcomer = make_user("Student")
    enroll(newcomer, session.course)
    client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": change(newcomer, False), "reason": "Late data entry"})
    entry = AuditLog.query.filter(AuditLog.details["student_id"].as_string() == newcomer.institutional_id).one()
    assert entry.details["old_value"] == "Unmarked" and entry.details["new_value"] == "Absent"


def test_unchanged_value_is_rejected(world):
    client, _, _, student, session = world
    response = client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": change(student, False), "reason": "No real change"})
    assert response.status_code == 400 and response.get_json()["code"] == "NO_CHANGES"


def test_non_admins_are_forbidden(world):
    client, _, faculty, student, session = world
    f_client = client.application.test_client()
    login(f_client, faculty)
    assert f_client.put(f"/api/v1/attendance/override/sessions/{session.id}", json={"changes": change(student), "reason": "Because"}).status_code == 403
    assert f_client.get("/api/v1/attendance/override/courses").status_code == 403


def test_detail_and_listing_for_admin(world):
    client, _, _, student, session = world
    detail = client.get(f"/api/v1/attendance/override/sessions/{session.id}").get_json()
    assert detail["session"]["frozen"] is True and detail["students"][0]["is_present"] is False
    listing = client.get(f"/api/v1/attendance/override/sessions?course_id={session.course_id}").get_json()["sessions"]
    assert listing[0]["frozen"] is True and listing[0]["marked_count"] == 1
    assert len(client.get("/api/v1/attendance/override/courses").get_json()["courses"]) == 1
