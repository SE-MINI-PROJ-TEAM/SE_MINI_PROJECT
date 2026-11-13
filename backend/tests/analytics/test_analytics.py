"""US-14 / TC-REP-01, TC-REP-02 — credit-weighted GPA, grade distributions and the <800 ms budget."""
import pytest

from app.features.analytics.service import _gpa
from tests.factories import enroll, login, make_course, make_user, set_grade


def test_gpa_is_credit_weighted(ctx):
    assert _gpa([{"credits": 4, "points": 10.0}, {"credits": 2, "points": 4.0}]) == 8.0  # (40 + 8) / 6
    assert _gpa([]) is None


@pytest.fixture
def world(ctx, client):
    faculty, student = make_user("Faculty"), make_user("Student")
    a = make_course(faculty, credits=4)       # 95 -> A (10 points)
    c = make_course(faculty, credits=2)       # 72 -> C (6 points)
    hidden = make_course(faculty, credits=3)  # Submitted: must not count
    for course, values, state in ((a, [95, 95], "Published"), (c, [72, 72], "Published"), (hidden, [10, 10], "Submitted")):
        set_grade(enroll(student, course), course, values, state)
    login(client, student)
    return client, faculty, student, (a, c, hidden)


def test_student_gpa_uses_published_grades_only(world):
    client, *_ = world
    body = client.get("/api/v1/analytics/student/summary").get_json()
    assert body["term_gpa"] == pytest.approx((10.0 * 4 + 6.0 * 2) / 6, abs=0.01)  # 8.67 on the 10-point scale
    assert 0 <= body["term_gpa"] <= 10
    assert body["term_credits"] == 6 and body["cumulative_gpa"] == body["term_gpa"]
    assert sorted(c["letter"] for c in body["courses"]) == ["A", "C"]


def test_under_review_grades_still_count_until_resolved(world):
    client, _, student, (a, *_) = world
    from app.models import Enrollment
    from app.extensions import db
    Enrollment.query.filter_by(course_id=a.id).update({"grade_state": "Under Review"})
    db.session.commit()
    assert client.get("/api/v1/analytics/student/summary").get_json()["term_credits"] == 6


def test_student_dashboard_query_is_fast(world):
    client, *_ = world
    body = client.get("/api/v1/analytics/student/summary").get_json()
    assert body["query_ms"] < 800


def test_faculty_distribution_buckets_mean_median(ctx, client):
    faculty = make_user("Faculty")
    course = make_course(faculty, weights=(50, 50))
    for total in (95, 91, 85, 72, 65, 40):
        set_grade(enroll(make_user("Student"), course), course, [total, total], "Submitted")
    enroll(make_user("Student"), course)  # ungraded student
    login(client, faculty)
    body = client.get("/api/v1/analytics/faculty/sections").get_json()
    section = body["sections"][0]
    assert section["distribution"] == {"A": 2, "B": 1, "C": 1, "D": 1, "F": 1}
    assert section["graded"] == 6 and section["enrolled"] == 7
    assert section["mean"] == pytest.approx(74.67, abs=0.01) and section["median"] == pytest.approx(78.5, abs=0.01)
    assert body["query_ms"] < 800


def test_faculty_sees_only_their_sections_and_roles_enforced(ctx, client):
    mine = make_user("Faculty")
    make_course(mine)
    make_course(make_user("Faculty"))
    login(client, mine)
    assert len(client.get("/api/v1/analytics/faculty/sections").get_json()["sections"]) == 1
    assert client.get("/api/v1/analytics/student/summary").status_code == 403
    s_client = client.application.test_client()
    login(s_client, make_user("Student"))
    assert s_client.get("/api/v1/analytics/faculty/sections").status_code == 403


def test_attendance_rate_included_in_section_summary(ctx, client):
    from app.extensions import db
    from app.models import AttendanceRecord
    from tests.factories import make_session
    faculty = make_user("Faculty")
    course = make_course(faculty)
    students = [make_user("Student") for _ in range(2)]
    for s in students:
        enroll(s, course)
    session = make_session(course, hours_ago=5)
    db.session.add_all([AttendanceRecord(session_id=session.id, student_id=students[0].id, is_present=True), AttendanceRecord(session_id=session.id, student_id=students[1].id, is_present=False)])
    db.session.commit()
    login(client, faculty)
    assert client.get("/api/v1/analytics/faculty/sections").get_json()["sections"][0]["attendance_rate"] == 50.0
