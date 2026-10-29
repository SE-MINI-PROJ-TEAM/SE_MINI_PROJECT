"""US-01 / TC-ACC-01 — administrative provisioning with generated temporary credentials."""
import pytest

from app.core.security import validate_password_strength, verify_password
from app.models import AuditLog, User
from tests.factories import login, make_user

PAYLOAD = {"full_name": "Asha Rao", "email": "Asha.Rao@Test.edu", "role": "Student", "institutional_id": "pes1ug26cs101"}


@pytest.fixture
def admin_client(ctx, client):
    return login(client, make_user("Admin"))


def test_admin_creates_user_and_sees_temporary_password(admin_client):
    response = admin_client.post("/api/v1/users", json=PAYLOAD)
    assert response.status_code == 201
    body = response.get_json()
    assert body["temporary_password"]
    assert validate_password_strength(body["temporary_password"]) == []

    user = User.query.filter_by(email="asha.rao@test.edu").one()
    assert user.is_temporary_password is True
    assert user.institutional_id == "PES1UG26CS101"  # normalised
    assert verify_password(body["temporary_password"], user.password_hash)
    assert user.password_hash != body["temporary_password"]
    assert user.profile is not None


def test_creation_is_audited(admin_client):
    admin_client.post("/api/v1/users", json=PAYLOAD)
    assert AuditLog.query.filter_by(action="USER_CREATED").count() == 1


def test_duplicate_institutional_id_returns_409(admin_client):
    admin_client.post("/api/v1/users", json=PAYLOAD)
    response = admin_client.post("/api/v1/users", json={**PAYLOAD, "email": "other@test.edu"})
    assert response.status_code == 409
    assert response.get_json()["code"] == "DUPLICATE_INSTITUTIONAL_ID"


def test_duplicate_email_returns_409(admin_client):
    admin_client.post("/api/v1/users", json=PAYLOAD)
    response = admin_client.post("/api/v1/users", json={**PAYLOAD, "institutional_id": "NEW-1"})
    assert response.status_code == 409
    assert response.get_json()["code"] == "DUPLICATE_EMAIL"


@pytest.mark.parametrize(
    "change, code",
    [({"role": "Janitor"}, "INVALID_ROLE"), ({"email": "not-an-email"}, "INVALID_EMAIL"), ({"full_name": "  "}, "MISSING_FIELD")],
)
def test_validation_errors(admin_client, change, code):
    response = admin_client.post("/api/v1/users", json={**PAYLOAD, **change})
    assert response.status_code == 400
    assert response.get_json()["code"] == code


@pytest.mark.parametrize("role", ["Student", "Faculty"])
def test_non_admins_cannot_provision(ctx, client, role):
    login(client, make_user(role))
    assert client.post("/api/v1/users", json=PAYLOAD).status_code == 403


def test_unauthenticated_cannot_provision(client):
    assert client.post("/api/v1/users", json=PAYLOAD).status_code == 401
