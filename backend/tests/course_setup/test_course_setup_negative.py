"""US-05 negative paths: lookups, edits and malformed rubric payloads."""
import pytest

from tests.factories import login, make_course, make_user

RUBRIC = [{"name": "A", "category": "Exams", "weight": 1}]


@pytest.fixture
def admin(ctx, client):
    login(client, make_user("Admin"))
    return client


def test_unknown_course_returns_404(admin):
    assert admin.get("/api/v1/courses/99999").status_code == 404
    assert admin.put("/api/v1/courses/99999", json={"title": "x"}).status_code == 404


def test_get_and_search_courses(admin):
    course = make_course(make_user("Faculty"), code="SRCH101")
    assert admin.get(f"/api/v1/courses/{course.id}").get_json()["course"]["code"] == "SRCH101"
    assert admin.get("/api/v1/courses?search=SRCH").get_json()["total"] == 1
    assert admin.get("/api/v1/courses?search=nomatch").get_json()["total"] == 0
    assert len(admin.get("/api/v1/courses/faculty-options").get_json()["faculty"]) == 1


def test_edit_fields_and_reject_bad_values(admin):
    course = make_course(make_user("Faculty"))
    ok = admin.put(f"/api/v1/courses/{course.id}", json={"title": "Renamed", "code": "new1", "section": "b", "credits": 4})
    assert ok.status_code == 200 and ok.get_json()["course"]["code"] == "NEW1"
    for bad in ({"credits": 0}, {"credits": "x"}, {"capacity": -3}, {"title": "  "}, {"assigned_faculty_id": 99999}):
        assert admin.put(f"/api/v1/courses/{course.id}", json=bad).status_code == 400, bad


def test_edit_into_an_existing_section_conflicts(admin):
    faculty = make_user("Faculty")
    first = make_course(faculty, code="DUP1")
    second = make_course(faculty, code="DUP2")
    assert admin.put(f"/api/v1/courses/{second.id}", json={"code": first.code}).status_code == 409


@pytest.mark.parametrize(
    "rubric",
    [
        None, "text", [], ["not-an-object"], [{"category": "Exams", "weight": 1}], [{"name": "x", "weight": "abc"}],
        [{"name": "x", "weight": -1}], [{"name": "x", "weight": None}], [dict(name=f"c{i}", weight=1) for i in range(13)],
    ],
)
def test_malformed_rubrics_rejected(admin, rubric):
    faculty = make_user("Faculty")
    payload = {"code": "NEG1", "title": "Neg", "capacity": 5, "assigned_faculty_id": faculty.id, "rubric": rubric}
    assert admin.post("/api/v1/courses", json=payload).status_code == 400


def test_non_json_and_missing_fields(admin):
    assert admin.post("/api/v1/courses", data="x", content_type="text/plain").status_code == 400
    assert admin.post("/api/v1/courses", json={"rubric": RUBRIC}).status_code == 400


def test_unauthenticated_and_student_cannot_edit(ctx, client):
    course = make_course(make_user("Faculty"))
    assert client.put(f"/api/v1/courses/{course.id}", json={"title": "x"}).status_code == 401
    login(client, make_user("Student"))
    assert client.put(f"/api/v1/courses/{course.id}", json={"title": "x"}).status_code == 403
