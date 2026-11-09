"""US-15 / TC-REP-03 — institution metrics and one-click CSV export."""
import csv
import io

import pytest

from app.features.admin_metrics.service import CSV_COLUMNS, _safe_cell
from tests.factories import enroll, login, make_course, make_user, set_grade


@pytest.fixture
def world(ctx, client):
    admin, faculty = make_user("Admin"), make_user("Faculty")
    course = make_course(faculty, capacity=10, code="=EVIL")  # formula-looking code must be neutralised
    done, pending = enroll(make_user("Student"), course), enroll(make_user("Student"), course)
    set_grade(done, course, [80, 90], "Published")
    login(client, admin)
    return client, course


def test_metrics_summary(world):
    client, _ = world
    metrics = client.get("/api/v1/admin/metrics").get_json()["metrics"]
    assert metrics["students"] == 2 and metrics["faculty"] == 1 and metrics["courses"] == 1
    assert metrics["total_enrollments"] == 2 and metrics["unsubmitted_grades"] == 1


def test_csv_export_contains_attendance_and_grade_metrics(world):
    client, course = world
    response = client.get("/api/v1/admin/metrics/export.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=" in response.headers["Content-Disposition"]
    rows = list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))
    assert list(rows[0].keys()) == CSV_COLUMNS
    course_row, total = rows[0], rows[-1]
    assert course_row["enrolled"] == "2" and course_row["grades_published"] == "1" and course_row["grades_not_started"] == "1"
    assert course_row["average_weighted_total"] == "86.0"
    assert total["course_code"] == "TOTAL" and total["enrolled"] == "2"


def test_csv_cells_cannot_inject_spreadsheet_formulas(world):
    client, _ = world
    text = client.get("/api/v1/admin/metrics/export.csv").get_data(as_text=True)
    assert "'=EVIL" in text and ",=EVIL" not in text
    assert _safe_cell("+1") == "'+1" and _safe_cell("@x") == "'@x" and _safe_cell("safe") == "safe" and _safe_cell(5) == 5


@pytest.mark.parametrize("role", ["Student", "Faculty"])
def test_export_requires_admin(ctx, client, role):
    login(client, make_user(role))
    assert client.get("/api/v1/admin/metrics/export.csv").status_code == 403
    assert client.get("/api/v1/admin/metrics").status_code == 403
