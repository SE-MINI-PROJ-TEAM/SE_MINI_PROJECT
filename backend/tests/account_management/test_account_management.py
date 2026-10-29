"""US-04 / TC-ACC-04 — account status & role management with audit trail; immediate session revocation."""
import pytest

from app.extensions import db
from app.models import AuditLog
from tests.factories import login, make_user


@pytest.fixture
def admin(ctx, client):
    user = make_user("Admin")
    login(client, user)
    return client, user


def test_search_filters_by_name_role_and_status(admin):
    client, _ = admin
    make_user("Student", name="Zebra Quinn")
    make_user("Faculty", name="Zed Prof", active=False)
    assert client.get("/api/v1/users?search=Zebra").get_json()["total"] == 1
    assert client.get("/api/v1/users?role=Faculty").get_json()["total"] == 1
    assert client.get("/api/v1/users?status=inactive").get_json()["total"] == 1
    assert client.get("/api/v1/users?status=active").get_json()["total"] == 2  # admin + student


def test_search_is_parameterised_against_sql_injection(admin):
    client, _ = admin
    response = client.get("/api/v1/users", query_string={"search": "' OR '1'='1' --"})
    assert response.status_code == 200
    assert response.get_json()["total"] == 0


def test_deactivation_revokes_active_session_immediately_and_is_audited(ctx, client):
    admin = make_user("Admin")
    target = make_user("Student")
    victim = client.application.test_client()
    login(victim, target)
    assert victim.get("/api/v1/catalog").status_code == 200

    login(client, admin)
    response = client.patch(f"/api/v1/users/{target.id}", json={"is_active": False})
    assert response.status_code == 200

    revoked = victim.get("/api/v1/catalog")  # same, still-unexpired JWT
    assert revoked.status_code == 401
    assert revoked.get_json()["code"] == "ACCOUNT_INACTIVE"
    blocked_login = client.application.test_client().post("/api/v1/auth/login", json={"identifier": target.email, "password": "Password@123"})
    assert blocked_login.status_code == 403

    entry = AuditLog.query.filter_by(action="USER_STATUS_CHANGED").one()
    assert entry.actor_id == admin.id and entry.details["old"] == "Active" and entry.details["new"] == "Inactive"

    # re-activation restores access
    client.patch(f"/api/v1/users/{target.id}", json={"is_active": True})
    assert victim.get("/api/v1/catalog").status_code == 200


def test_role_change_is_audited_and_invalidates_old_token(ctx, client):
    admin = make_user("Admin")
    target = make_user("Student")
    old = client.application.test_client()
    login(old, target)
    login(client, admin)
    assert client.patch(f"/api/v1/users/{target.id}", json={"role": "Faculty"}).status_code == 200
    assert AuditLog.query.filter_by(action="USER_ROLE_CHANGED").count() == 1
    assert old.get("/api/v1/auth/me").get_json()["code"] == "ROLE_CHANGED"


def test_admin_cannot_deactivate_or_demote_self(admin):
    client, user = admin
    assert client.patch(f"/api/v1/users/{user.id}", json={"is_active": False}).get_json()["code"] == "SELF_DEACTIVATION"
    assert client.patch(f"/api/v1/users/{user.id}", json={"role": "Student"}).get_json()["code"] == "SELF_ROLE_CHANGE"


def test_validation_and_unknown_user(admin):
    client, _ = admin
    target = make_user("Student")
    assert client.patch(f"/api/v1/users/{target.id}", json={"is_active": "no"}).status_code == 400
    assert client.patch(f"/api/v1/users/{target.id}", json={"role": "Root"}).status_code == 400
    assert client.patch(f"/api/v1/users/{target.id}", json={}).status_code == 400
    assert client.patch("/api/v1/users/99999", json={"is_active": False}).status_code == 404


def test_audit_log_listing_and_immutability(admin):
    client, user = admin
    target = make_user("Student")
    client.patch(f"/api/v1/users/{target.id}", json={"is_active": False})
    body = client.get("/api/v1/admin/audit-logs?action=USER_STATUS_CHANGED").get_json()
    assert body["total"] == 1 and body["logs"][0]["actor"]["institutional_id"] == user.institutional_id

    entry = AuditLog.query.first()
    entry.action = "TAMPERED"
    with pytest.raises(PermissionError):
        db.session.commit()
    db.session.rollback()
    db.session.delete(AuditLog.query.first())
    with pytest.raises(PermissionError):
        db.session.commit()
    db.session.rollback()


def test_only_admins_manage_users(ctx, client):
    login(client, make_user("Faculty"))
    assert client.get("/api/v1/users").status_code == 403
    assert client.get("/api/v1/admin/audit-logs").status_code == 403
