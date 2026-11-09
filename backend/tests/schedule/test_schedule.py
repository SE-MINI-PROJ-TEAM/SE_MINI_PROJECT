"""US-07 / TC-CRS-03, TC-CRS-04 — timetable publishing, calendars and faculty roster isolation."""
from datetime import timedelta

import pytest

from app.core.timeutil import to_iso, utcnow
from tests.factories import enroll, login, make_course, make_session, make_user


def window(days_back=1, days_forward=30):
    now = utcnow()
    return {"from": to_iso(now - timedelta(days=days_back)), "to": to_iso(now + timedelta(days=days_forward))}


@pytest.fixture
def world(ctx, client):
    admin, faculty, student = make_user("Admin"), make_user("Faculty"), make_user("Student")
    course = make_course(faculty)
    enroll(student, course)
    return client, admin, faculty, student, course


def slot(hours_from_now=24, length=1):
    start = (utcnow() + timedelta(hours=hours_from_now)).replace(microsecond=0)
    return {"start_time": to_iso(start), "end_time": to_iso(start + timedelta(hours=length))}


def test_admin_schedules_session_and_it_populates_student_and_faculty_calendars(world):
    client, admin, faculty, student, course = world
    login(client, admin)
    response = client.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "LH-9", **slot()})
    assert response.status_code == 201

    for user in (student, faculty):
        viewer = client.application.test_client()
        login(viewer, user)
        sessions = viewer.get("/api/v1/schedule/calendar", query_string=window()).get_json()["sessions"]
        assert [(s["course_code"], s["room"]) for s in sessions] == [(course.code, "LH-9")]


def test_weekly_repeat_creates_one_session_per_week(world):
    client, admin, *_, course = world
    login(client, admin)
    body = client.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "A1", "repeat_weeks": 4, **slot()}).get_json()
    starts = sorted(s["start_time"] for s in body["sessions"])
    assert len(starts) == 4
    assert all((__import__("datetime").datetime.fromisoformat(b[:-1]) - __import__("datetime").datetime.fromisoformat(a[:-1])) == timedelta(weeks=1) for a, b in zip(starts, starts[1:]))


def test_students_only_see_their_own_courses(world):
    client, admin, faculty, student, course = world
    other = make_course(faculty)
    make_session(other, hours_ago=-5)
    make_session(course, hours_ago=-6)
    login(client, student)
    sessions = client.get("/api/v1/schedule/calendar", query_string=window()).get_json()["sessions"]
    assert {s["course_code"] for s in sessions} == {course.code}


def test_room_and_instructor_conflicts_rejected(world):
    client, admin, faculty, student, course = world
    other = make_course(faculty)  # same instructor
    login(client, admin)
    when = slot(48)
    assert client.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R1", **when}).status_code == 201
    room_clash = client.post("/api/v1/schedule/sessions", json={"course_id": make_course(make_user("Faculty")).id, "room": "R1", **when})
    assert room_clash.status_code == 409 and room_clash.get_json()["code"] == "ROOM_CONFLICT"
    faculty_clash = client.post("/api/v1/schedule/sessions", json={"course_id": other.id, "room": "R2", **when})
    assert faculty_clash.status_code == 409 and faculty_clash.get_json()["code"] == "FACULTY_CONFLICT"


@pytest.mark.parametrize("change", [{"room": ""}, {"end_time": "2000-01-01T00:00:00Z"}, {"start_time": "garbage"}, {"repeat_weeks": 99}])
def test_invalid_session_payloads(world, change):
    client, admin, *_, course = world
    login(client, admin)
    assert client.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R1", **slot(), **change}).status_code == 400


def test_only_admin_can_schedule(world):
    client, _, faculty, _, course = world
    login(client, faculty)
    assert client.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R1", **slot()}).status_code == 403


def test_delete_session_unless_attendance_recorded(world):
    client, admin, faculty, student, course = world
    session = make_session(course, hours_ago=-3)
    login(client, admin)
    assert client.delete(f"/api/v1/schedule/sessions/{session.id}").status_code == 200
    started = make_session(course, hours_ago=2)
    from app.extensions import db
    from app.models import AttendanceRecord
    db.session.add(AttendanceRecord(session_id=started.id, student_id=student.id, is_present=True))
    db.session.commit()
    assert client.delete(f"/api/v1/schedule/sessions/{started.id}").status_code == 409


# ---------------------------------------------------------------- roster isolation (TC-CRS-04)
def test_faculty_sees_roster_only_for_assigned_sections(world):
    client, admin, faculty, student, course = world
    other_faculty = make_user("Faculty")
    foreign = make_course(other_faculty)
    enroll(make_user("Student", name="Hidden Kid"), foreign)

    login(client, faculty)
    mine = client.get(f"/api/v1/schedule/roster/{course.id}")
    assert mine.status_code == 200 and [s["institutional_id"] for s in mine.get_json()["students"]] == [student.institutional_id]

    denied = client.get(f"/api/v1/schedule/roster/{foreign.id}")
    assert denied.status_code == 403 and "Hidden Kid" not in denied.get_data(as_text=True)
    assert [c["id"] for c in client.get("/api/v1/schedule/my-courses").get_json()["courses"]] == [course.id]


def test_students_cannot_read_rosters_and_admin_can(world):
    client, admin, _, student, course = world
    login(client, student)
    assert client.get(f"/api/v1/schedule/roster/{course.id}").status_code == 403
    admin_client = client.application.test_client()
    login(admin_client, admin)
    assert admin_client.get(f"/api/v1/schedule/roster/{course.id}").status_code == 200
    assert admin_client.get("/api/v1/schedule/roster/99999").status_code == 404
