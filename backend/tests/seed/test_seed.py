"""The synthetic seed matches the STP test-data spec and produces the demo scenarios the smoke test relies on."""
import pytest

from app.core.settings import enrollment_open
from app.models import AttendanceRecord, Course, Enrollment, GradeDispute, ScheduleSession, User
from app.seed import seed_database
from tests.factories import login

pytestmark = pytest.mark.slow


def test_seed_matches_stp_dataset_and_demo_scenarios(ctx, client):
    summary = seed_database()
    assert summary["students"] >= 500 and summary["faculty"] == 50 and summary["admins"] == 10
    assert Course.query.count() == 50 and ScheduleSession.query.count() == 1000
    assert enrollment_open() is True
    assert AttendanceRecord.query.count() > 10000 and GradeDispute.query.count() >= 4

    # student002 sits on the 6-course cap, student001 can still add two sections
    from app.core.settings import current_term
    def term_count(email):
        user = User.query.filter_by(email=email).one()
        return Enrollment.query.join(Course).filter(Enrollment.student_id == user.id, Course.term == current_term()).count()
    assert term_count("student002@srs.edu") == 6 and term_count("student001@srs.edu") == 4

    # every seeded component mark is a multiple of 0.5 (no 42.67s)
    from sqlalchemy import func
    from app.models import GradeRecord
    assert GradeRecord.query.filter(func.mod(GradeRecord.numeric_score * 2, 1) != 0).count() == 0

    # student002 already used the single regrade on CS101; student001 still has theirs
    s2 = login(client.application.test_client(), User.query.filter_by(email="student002@srs.edu").one(), password="Password@123")
    cs101 = next(g for g in s2.get("/api/v1/grades/mine").get_json()["grades"] if g["code"] == "CS101")
    assert cs101["state"] == "Published" and cs101["can_dispute"] is False and cs101["dispute"]["open"] is False
    s1 = login(client.application.test_client(), User.query.filter_by(email="student001@srs.edu").one(), password="Password@123")
    mine = next(g for g in s1.get("/api/v1/grades/mine").get_json()["grades"] if g["code"] == "CS101")
    assert mine["can_dispute"] is True
    assert 0 < s1.get("/api/v1/analytics/student/summary").get_json()["term_gpa"] <= 10

    # one section is full, one nearly full
    counts = {c.code: Enrollment.query.filter_by(course_id=c.id).count() for c in Course.query.filter(Course.capacity < 60)}
    assert any(n >= Course.query.filter_by(code=code).one().capacity for code, n in counts.items())

    # demo accounts log in; the "new user" is forced through the password reset
    login(client, User.query.filter_by(email="admin001@srs.edu").one(), password="Password@123")
    fresh = client.application.test_client()
    response = fresh.post("/api/v1/auth/login", json={"identifier": "new.student@srs.edu", "password": "Temp@12345"})
    assert response.get_json()["user"]["must_change_password"] is True

    # FAC001 has an open (editable) session with no attendance yet
    faculty = login(client.application.test_client(), User.query.filter_by(email="faculty001@srs.edu").one(), password="Password@123")
    sessions = faculty.get("/api/v1/attendance/sessions").get_json()["sessions"]
    assert any(s["status"] == "open" and s["marked_count"] == 0 for s in sessions)
    assert any(s["status"] == "frozen" for s in sessions)
