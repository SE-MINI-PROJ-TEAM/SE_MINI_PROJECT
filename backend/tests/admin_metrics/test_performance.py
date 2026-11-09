"""US-15 performance benchmark: TC-PERF-01 (p95 < 800 ms) and TC-PERF-02 (200 concurrent submissions, 0 failures)."""
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.extensions import db
from app.models import AttendanceRecord, Enrollment, GradeRecord
from tests.factories import bearer, enroll, login, make_course, make_session, make_user, scores

pytestmark = pytest.mark.perf


def run_concurrently(app, jobs):
    """Fire every job at the same instant from its own thread/test client; return [(status, seconds)]."""
    gate = threading.Barrier(len(jobs))

    def run(job):
        method, path, kwargs = job
        client = app.test_client()
        gate.wait()
        started = time.perf_counter()
        response = client.open(path, method=method, **kwargs)
        return response.status_code, time.perf_counter() - started

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return list(pool.map(run, jobs))


def test_200_simultaneous_attendance_and_grade_submissions_without_deadlock(ctx, app):
    faculty = make_user("Faculty")
    course = make_course(faculty, capacity=120, weights=(40, 60))
    students = [make_user("Student") for _ in range(100)]
    for s in students:
        enroll(s, course)
    session = make_session(course, hours_ago=2)
    headers = bearer(faculty)

    roster = [{"student_id": s.institutional_id, "is_present": i % 4 != 0} for i, s in enumerate(students)]
    attendance_jobs = [  # 100 overlapping roll-call submissions for the SAME session (worst case for row locks)
        ("POST", f"/api/v1/attendance/sessions/{session.id}", {"json": {"attendance_list": roster}, "headers": headers})
        for _ in range(100)
    ]
    grade_jobs = [  # 100 grade submissions, one per student
        (
            "PUT",
            f"/api/v1/grades/courses/{course.id}/students/{s.institutional_id}",
            {"json": {"rubric_scores": scores(course, 60 + i % 40, 70 + i % 30), "target_state": "Submitted"}, "headers": headers},
        )
        for i, s in enumerate(students)
    ]
    jobs = attendance_jobs + grade_jobs
    assert len(jobs) == 200

    results = run_concurrently(app, jobs)

    failures = [code for code, _ in results if code != 200]
    assert failures == [], f"{len(failures)}/200 requests failed: {sorted(set(failures))}"
    assert AttendanceRecord.query.filter_by(session_id=session.id).count() == 100  # no duplicates / drops
    assert Enrollment.query.filter_by(course_id=course.id, grade_state="Submitted").count() == 100
    assert GradeRecord.query.join(Enrollment, Enrollment.id == GradeRecord.enrollment_id).filter(Enrollment.course_id == course.id).count() == 200


def test_p95_latency_under_800ms_for_standard_requests(ctx, app):
    """Per-request service time (TC-PERF-01). Requests are sequential on purpose: firing them from threads inside this one
    Python process measures the GIL, not the server. Behaviour under 500 concurrent sessions is measured by k6."""
    faculty, admin = make_user("Faculty"), make_user("Admin")
    students = [make_user("Student") for _ in range(40)]
    courses = [make_course(faculty) for _ in range(5)]
    for s in students:
        for c in courses[:4]:
            enroll(s, c)
    for c in courses:
        make_session(c, hours_ago=3)

    client = app.test_client()
    paths = [("/api/v1/catalog", "student"), ("/api/v1/analytics/student/summary", "student"), ("/api/v1/attendance/summary", "student"),
             ("/api/v1/grades/mine", "student")]
    timings = []
    for s in students:
        for path, _ in paths:
            started = time.perf_counter()
            assert client.get(path, headers=bearer(s)).status_code == 200
            timings.append(time.perf_counter() - started)
    for _ in range(20):
        for user, path in ((faculty, "/api/v1/analytics/faculty/sections"), (faculty, "/api/v1/attendance/sessions"), (admin, "/api/v1/admin/metrics")):
            started = time.perf_counter()
            assert client.get(path, headers=bearer(user)).status_code == 200
            timings.append(time.perf_counter() - started)

    assert len(timings) >= 200
    p95 = statistics.quantiles(timings, n=100)[94] * 1000
    print(f"\nTC-PERF-01 (service time): {len(timings)} requests, p95 = {p95:.0f} ms, median = {statistics.median(timings) * 1000:.0f} ms")
    assert p95 < 800
