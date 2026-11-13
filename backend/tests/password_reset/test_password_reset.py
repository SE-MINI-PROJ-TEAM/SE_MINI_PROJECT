"""US-02 / TC-ACC-02, TC-SEC-02 — forced reset of temporary credentials, bcrypt (cost 12)."""
from app.config import Config
from app.core.security import hash_password, validate_password_strength
from app.models import User
from tests.factories import login, make_user

NEW = "Brand#New9pass"


def test_temp_password_user_is_gated_until_reset(ctx, client):
    user = make_user("Student", temp=True)
    response = client.post("/api/v1/auth/login", json={"identifier": user.email, "password": "Password@123"})
    assert response.status_code == 200
    assert response.get_json()["user"]["must_change_password"] is True

    blocked = client.get("/api/v1/catalog")
    assert blocked.status_code == 403
    assert blocked.get_json()["code"] == "PASSWORD_RESET_REQUIRED"
    assert client.get("/api/v1/auth/me").status_code == 200  # still allowed so the UI can redirect


def test_successful_reset_clears_flag_and_unblocks(ctx, client):
    user = make_user("Student", temp=True)
    login(client, user)
    response = client.post("/api/v1/auth/change-password", json={"current_password": "Password@123", "new_password": NEW})
    assert response.status_code == 200
    assert response.get_json()["user"]["must_change_password"] is False
    assert client.get("/api/v1/catalog").status_code == 200

    # old password no longer works, new one does
    fresh = client.application.test_client()
    assert fresh.post("/api/v1/auth/login", json={"identifier": user.email, "password": "Password@123"}).status_code == 401
    assert fresh.post("/api/v1/auth/login", json={"identifier": user.email, "password": NEW}).status_code == 200


def test_weak_passwords_are_rejected_with_reasons(ctx, client):
    login(client, make_user("Student", temp=True))
    response = client.post("/api/v1/auth/change-password", json={"current_password": "Password@123", "new_password": "weak"})
    assert response.status_code == 400
    body = response.get_json()
    assert body["code"] == "WEAK_PASSWORD"
    assert "At least one uppercase letter" in body["details"]


def test_wrong_current_password_rejected(ctx, client):
    login(client, make_user("Student", temp=True))
    response = client.post("/api/v1/auth/change-password", json={"current_password": "nope", "new_password": NEW})
    assert response.status_code == 401


def test_new_password_must_differ(ctx, client):
    login(client, make_user("Student", temp=True))
    response = client.post("/api/v1/auth/change-password", json={"current_password": "Password@123", "new_password": "Password@123"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "PASSWORD_REUSED"


def test_stored_password_is_bcrypt_with_work_factor_12(ctx, client):
    assert Config.BCRYPT_ROUNDS >= 12  # production default (PRJ-SR-002)
    assert hash_password("Whatever#1", rounds=Config.BCRYPT_ROUNDS).startswith("$2b$12$")

    user = make_user("Student", temp=True)
    login(client, user)
    client.post("/api/v1/auth/change-password", json={"current_password": "Password@123", "new_password": NEW})
    stored = User.query.get(user.id).password_hash
    assert stored.startswith("$2b$") and stored != NEW


def test_complexity_rules():
    assert validate_password_strength("Aa1!aaaa") == []
    assert len(validate_password_strength("")) >= 4
    assert any("72" in p for p in validate_password_strength("Aa1!" + "a" * 80))
