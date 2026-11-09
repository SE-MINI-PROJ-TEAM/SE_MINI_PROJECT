"""US-10 / TC-ATT-04 — aggregate attendance percentages and the <75% alert."""
import pytest

from app.extensions import db
from app.models import AttendanceRecord
from tests.factories import enroll, login, make_course, make_session, make_user


def record(session, student, present):
    db.session.add(AttendanceRecord(session_id=session.id, student_id=student.id, is_present=present))
    db.session.commit()


@pytest.fixture
def world(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    good, bad = make_course(faculty, code="GOOD1"), make_course(faculty, code="BAD01")
    enroll(student, good), enroll(student, bad)
    for i in range(4):  # 4/4 present
        record(make_session(good, hours_ago=100 + i), student, True)
    for i, present in enumerate([True, False, False, True]):  # 2/4 present
        record(make_session(bad, hours_ago=100 + i), student, present)
    make_session(bad, hours_ago=-10)  # future: ignored
    login(client, student)
    return client, student, good, bad


def test_percentage_per_course_with_totals(world):
    client, _, good, bad = world
    body = client.get("/api/v1/attendance/summary").get_json()
    by_code = {c["code"]: c for c in body["courses"]}
    assert by_code["GOOD1"]["percentage"] == 100.0
    assert by_code["BAD01"] == {**by_code["BAD01"], "sessions_held": 4, "sessions_attended": 2, "sessions_missed": 2, "percentage": 50.0}
    assert body["overall_percentage"] == 75.0


def test_alert_flag_only_below_75_percent(world):
    client, *_ = world
    by_code = {c["code"]: c for c in client.get("/api/v1/attendance/summary").get_json()["courses"]}
    assert by_code["BAD01"]["below_threshold"] is True
    assert by_code["GOOD1"]["below_threshold"] is False


def test_exactly_75_percent_is_not_flagged(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    course = make_course(faculty)
    enroll(student, course)
    for i, present in enumerate([True, True, True, False]):
        record(make_session(course, hours_ago=100 + i), student, present)
    login(client, student)
    row = client.get("/api/v1/attendance/summary").get_json()["courses"][0]
    assert row["percentage"] == 75.0 and row["below_threshold"] is False


def test_course_with_no_marked_sessions_has_no_percentage(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    enroll(student, make_course(faculty))
    login(client, student)
    row = client.get("/api/v1/attendance/summary").get_json()["courses"][0]
    assert row["percentage"] is None and row["below_threshold"] is False


def test_course_view_breaks_down_sessions(world):
    client, _, _, bad = world
    body = client.get(f"/api/v1/attendance/summary/{bad.id}").get_json()
    assert (body["sessions_held"], body["sessions_attended"], body["sessions_missed"]) == (4, 2, 2)
    assert sorted(s["status"] for s in body["sessions"]) == ["Absent", "Absent", "Present", "Present"]
    assert body["below_threshold"] is True


def test_unmarked_past_session_is_listed_but_not_counted(world):
    client, student, good, _ = world
    make_session(good, hours_ago=10)
    body = client.get(f"/api/v1/attendance/summary/{good.id}").get_json()
    assert body["sessions_held"] == 4 and any(s["status"] == "Not marked" for s in body["sessions"])


def test_cannot_view_a_course_you_are_not_in_and_other_roles_blocked(world):
    client, *_ = world
    other = make_course(make_user("Faculty"))
    assert client.get(f"/api/v1/attendance/summary/{other.id}").status_code == 403
    assert client.get("/api/v1/attendance/summary/99999").status_code == 404
    f_client = client.application.test_client()
    login(f_client, make_user("Faculty"))
    assert f_client.get("/api/v1/attendance/summary").status_code == 403
