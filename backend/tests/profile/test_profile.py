"""US-03 / TC-ACC-03 — self-service contact details."""
import pytest

from tests.factories import login, make_user


@pytest.fixture
def student_client(ctx, client):
    user = make_user("Student")
    return login(client, user), user


def test_profile_shows_contact_info_and_institutional_id(student_client):
    client, user = student_client
    body = client.get("/api/v1/profile").get_json()["profile"]
    assert body["institutional_id"] == user.institutional_id
    assert body["role"] == "Student"
    assert body["phone"] == ""


def test_update_persists_and_is_returned(student_client):
    client, _ = student_client
    payload = {"phone": "+91 98765 43210", "personal_email": "Me@Example.com", "emergency_contact": "Mum +91 99999 88888", "home_address": "12 Main Rd"}
    assert client.put("/api/v1/profile", json=payload).status_code == 200
    saved = client.get("/api/v1/profile").get_json()["profile"]
    assert saved["phone"] == "+91 98765 43210"
    assert saved["personal_email"] == "me@example.com"
    assert saved["home_address"] == "12 Main Rd"


@pytest.mark.parametrize("field,value", [("phone", "abc"), ("phone", "12"), ("personal_email", "nope@"), ("personal_email", "a b@c.com")])
def test_invalid_formats_rejected(student_client, field, value):
    client, _ = student_client
    response = client.put("/api/v1/profile", json={field: value})
    assert response.status_code == 400
    assert field in response.get_json()["details"]


@pytest.mark.parametrize("field", ["institutional_id", "role", "email", "full_name"])
def test_admin_managed_fields_cannot_be_modified(student_client, field):
    client, user = student_client
    response = client.put("/api/v1/profile", json={field: "hacked", "phone": "+91 98765 43210"})
    assert response.status_code == 403
    assert response.get_json()["code"] == "READ_ONLY_FIELD"
    assert client.get("/api/v1/profile").get_json()["profile"]["role"] == "Student"


def test_markup_is_stripped_from_text(student_client):
    client, _ = student_client
    client.put("/api/v1/profile", json={"home_address": "<script>alert(1)</script>5 Elm St"})
    assert client.get("/api/v1/profile").get_json()["profile"]["home_address"] == "alert(1)5 Elm St"


def test_faculty_can_edit_own_profile(ctx, client):
    login(client, make_user("Faculty"))
    assert client.put("/api/v1/profile", json={"phone": "+91 98765 43210"}).status_code == 200


def test_admin_has_no_self_service_profile(ctx, client):
    login(client, make_user("Admin"))
    assert client.get("/api/v1/profile").status_code == 403
