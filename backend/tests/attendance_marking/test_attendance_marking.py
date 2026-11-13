"""US-08 / TC-ATT-01, TC-ATT-02 — binary roll-call and the hard 48-hour freeze."""
from datetime import timedelta

import pytest

from app.features.attendance_marking.service import freeze_deadline, is_frozen, session_status
from app.models import AttendanceRecord, ScheduleSession
from app.core.timeutil import utcnow
from tests.factories import enroll, login, make_course, make_session, make_user


@pytest.fixture
def world(ctx, client):
    faculty = make_user("Faculty")
    course = make_course(faculty)
    students = [make_user("Student") for _ in range(3)]
    for s in students:
        enroll(s, course)
    login(client, faculty)
    return client, faculty, course, students


def marks(students, present):
    return [{"student_id": s.institutional_id, "is_present": p} for s, p in zip(students, present)]


def test_roster_lists_enrolled_students_with_current_marks(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=1)
    body = client.get(f"/api/v1/attendance/sessions/{session.id}").get_json()
    assert [s["student_id"] for s in body["students"]] == sorted(s.institutional_id for s in students)
    assert all(s["is_present"] is None for s in body["students"])
    assert body["session"]["status"] == "open"


def test_save_persists_records_and_confirms(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=1)
    response = client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [True, False, True])})
    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Attendance recorded for 3 students."
    assert body["frozen_at"].endswith("Z")
    assert AttendanceRecord.query.filter_by(session_id=session.id, is_present=False).count() == 1


def test_faculty_can_re_edit_within_window(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=30)
    client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [True, True, True])})
    client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [False, True, True])})
    assert AttendanceRecord.query.filter_by(session_id=session.id).count() == 3
    assert AttendanceRecord.query.filter_by(session_id=session.id, is_present=False).count() == 1


def test_edits_after_48_hours_are_rejected_by_the_backend(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=48.5)
    response = client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [True, True, True])})
    assert response.status_code == 403
    assert response.get_json()["code"] == "ATTENDANCE_FROZEN"
    assert AttendanceRecord.query.count() == 0
    assert client.get(f"/api/v1/attendance/sessions/{session.id}").get_json()["session"]["status"] == "frozen"


def test_just_inside_the_window_is_still_editable(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=47.9)
    assert client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [True, True, True])}).status_code == 200


def test_freeze_boundary_is_exactly_48_hours_after_start(ctx):
    course = make_course(make_user("Faculty"))
    session = make_session(course, hours_ago=0)
    deadline = freeze_deadline(session)
    assert deadline - session.start_time == timedelta(hours=48)
    assert is_frozen(session, deadline - timedelta(seconds=1)) is False
    assert is_frozen(session, deadline) is True
    assert session_status(session, session.start_time - timedelta(minutes=1)) == "upcoming"
    assert session_status(session, session.start_time + timedelta(hours=1)) == "open"
    assert session_status(session, deadline + timedelta(seconds=1)) == "frozen"


def test_cannot_mark_before_session_starts(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=-2)
    response = client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks(students, [True, True, True])})
    assert response.status_code == 400 and response.get_json()["code"] == "SESSION_NOT_STARTED"


def test_unenrolled_student_returns_404(world):
    client, _, course, students = world
    session = make_session(course, hours_ago=1)
    outsider = make_user("Student")
    response = client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks([outsider], [True])})
    assert response.status_code == 404 and response.get_json()["code"] == "STUDENT_NOT_ENROLLED"


def test_faculty_cannot_touch_unassigned_sessions(world):
    client, _, _, _ = world
    foreign_course = make_course(make_user("Faculty"))
    student = make_user("Student")
    enroll(student, foreign_course)
    session = make_session(foreign_course, hours_ago=1)
    assert client.get(f"/api/v1/attendance/sessions/{session.id}").status_code == 403
    assert client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": marks([student], [True])}).status_code == 403


@pytest.mark.parametrize("bad", [None, [], [{"student_id": "X"}], [{"is_present": True}], "nope"])
def test_malformed_payloads(world, bad):
    client, _, course, _ = world
    session = make_session(course, hours_ago=1)
    assert client.post(f"/api/v1/attendance/sessions/{session.id}", json={"attendance_list": bad}).status_code == 400


def test_session_list_reports_status_and_progress(world):
    client, _, course, students = world
    open_s = make_session(course, hours_ago=2)
    make_session(course, hours_ago=60)
    make_session(course, hours_ago=-5)
    client.post(f"/api/v1/attendance/sessions/{open_s.id}", json={"attendance_list": marks(students[:2], [True, False])})
    rows = client.get("/api/v1/attendance/sessions").get_json()["sessions"]
    assert sorted(r["status"] for r in rows) == ["frozen", "open", "upcoming"]
    assert next(r for r in rows if r["status"] == "open")["marked_count"] == 2


def test_students_cannot_mark_attendance(ctx, client):
    student = make_user("Student")
    login(client, student)
    assert client.post("/api/v1/attendance/sessions/1", json={"attendance_list": []}).status_code == 403
