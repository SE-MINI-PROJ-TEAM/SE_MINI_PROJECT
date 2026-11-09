"""US-07 negative paths: calendar/session validation and missing resources."""
from datetime import timedelta

import pytest

from app.core.timeutil import to_iso, utcnow
from app.extensions import db
from app.models import ScheduleSession
from tests.factories import login, make_course, make_session, make_user


@pytest.fixture
def admin(ctx, client):
    login(client, make_user("Admin"))
    return client


def iso(hours):
    return to_iso((utcnow() + timedelta(hours=hours)).replace(microsecond=0))


@pytest.mark.parametrize(
    "query",
    [{"from": "garbage", "to": iso(24)}, {"from": iso(24), "to": iso(0)}, {"from": iso(0), "to": iso(24 * 90)}, {"course_id": "abc"}],
)
def test_calendar_rejects_bad_ranges(admin, query):
    assert admin.get("/api/v1/schedule/calendar", query_string=query).status_code == 400


def test_calendar_requires_login(client):
    assert client.get("/api/v1/schedule/calendar").status_code == 401


def test_admin_calendar_can_filter_by_course(admin):
    faculty = make_user("Faculty")
    a, b = make_course(faculty), make_course(faculty)
    make_session(a, hours_ago=-2)
    make_session(b, hours_ago=-3)
    window = {"from": iso(-1), "to": iso(24)}
    assert len(admin.get("/api/v1/schedule/calendar", query_string=window).get_json()["sessions"]) == 2
    only_a = admin.get("/api/v1/schedule/calendar", query_string={**window, "course_id": a.id}).get_json()["sessions"]
    assert [s["course_id"] for s in only_a] == [a.id]


def test_session_listing_filters_and_validates(admin):
    course = make_course(make_user("Faculty"))
    make_session(course, hours_ago=-1)
    assert admin.get(f"/api/v1/schedule/sessions?course_id={course.id}").get_json()["total"] == 1
    assert admin.get("/api/v1/schedule/sessions?course_id=abc").status_code == 400
    assert len(admin.get("/api/v1/schedule/course-options").get_json()["courses"]) == 1


def test_create_session_negative_cases(admin):
    course = make_course(make_user("Faculty"))
    ok_slot = {"start_time": iso(24), "end_time": iso(25), "room": "R1"}
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": 99999, **ok_slot}).status_code == 404
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": "abc", **ok_slot}).status_code == 400
    too_long = {**ok_slot, "end_time": iso(24 + 9)}
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": course.id, **too_long}).status_code == 400
    same = {**ok_slot, "end_time": ok_slot["start_time"]}
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": course.id, **same}).status_code == 400
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R1"}).status_code == 400


def test_same_section_cannot_double_book(admin):
    course = make_course(make_user("Faculty"))
    slot = {"start_time": iso(24), "end_time": iso(25)}
    assert admin.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R1", **slot}).status_code == 201
    clash = admin.post("/api/v1/schedule/sessions", json={"course_id": course.id, "room": "R9", **slot})
    assert clash.status_code == 409 and clash.get_json()["code"] in ("SECTION_CONFLICT", "FACULTY_CONFLICT")


def test_repeat_is_atomic_when_a_later_week_conflicts(admin):
    course, other = make_course(make_user("Faculty")), make_course(make_user("Faculty"))
    week_two = (utcnow() + timedelta(hours=24, weeks=1)).replace(microsecond=0)
    blocker = make_session(other, hours_ago=-1)
    blocker.start_time, blocker.end_time, blocker.room_number = week_two, week_two + timedelta(hours=1), "R1"
    db.session.commit()
    response = admin.post(
        "/api/v1/schedule/sessions",
        json={"course_id": course.id, "room": "R1", "start_time": iso(24), "end_time": iso(25), "repeat_weeks": 3},
    )
    assert response.status_code == 409
    assert ScheduleSession.query.filter_by(course_id=course.id).count() == 0  # nothing partially created


def test_delete_unknown_session_and_wrong_role(admin):
    assert admin.delete("/api/v1/schedule/sessions/99999").status_code == 404
    other = admin.application.test_client()
    login(other, make_user("Faculty"))
    assert other.delete("/api/v1/schedule/sessions/1").status_code == 403
    assert other.get("/api/v1/schedule/course-options").status_code == 403
