"""Shared-layer behaviour: validation helpers, auth session endpoints, error envelope, feature discovery."""
import pytest

from app.core.timeutil import parse_iso, to_iso
from app.core.validation import clean_text, sanitize, valid_email, valid_phone
from app.core.errors import ApiError
from tests.factories import login, make_user


def test_every_story_package_is_registered(app):
    expected = {
        "account_management", "admin_metrics", "analytics", "attendance_dashboard", "attendance_marking",
        "attendance_override", "auth_session", "course_enrollment", "course_setup", "grade_entry",
        "grade_publication", "password_reset", "profile", "regrade_disputes", "schedule", "user_provisioning",
    }
    assert expected <= set(app.config["LOADED_FEATURES"])


def test_login_logout_me_cycle(ctx, client):
    user = make_user("Student")
    assert client.get("/api/v1/auth/me").status_code == 401
    login(client, user)
    me = client.get("/api/v1/auth/me").get_json()["user"]
    assert me["email"] == user.email and "password_hash" not in me
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_by_institutional_id_and_failure_modes(ctx, client):
    user = make_user("Faculty")
    assert client.post("/api/v1/auth/login", json={"identifier": user.institutional_id.lower(), "password": "Password@123"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"identifier": user.email, "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"identifier": "ghost@x.edu", "password": "x"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"identifier": "", "password": ""}).status_code == 400
    assert client.post("/api/v1/auth/login", data="not json", content_type="text/plain").status_code == 400


def test_unknown_routes_and_methods_use_the_error_envelope(client):
    body = client.get("/api/v1/nope").get_json()
    assert body["status"] == "error" and body["code"] == "NOT_FOUND"
    assert client.delete("/api/v1/health").get_json()["code"] == "METHOD_NOT_ALLOWED"


def test_sanitize_and_field_validation():
    assert sanitize("  <b>hi</b>\x00 there ") == "hi there"
    assert clean_text({"a": " x "}, "a") == "x"
    with pytest.raises(ApiError):
        clean_text({"a": "  "}, "a")
    with pytest.raises(ApiError):
        clean_text({"a": "x" * 11}, "a", max_len=10)
    with pytest.raises(ApiError):
        clean_text({"a": ["list"]}, "a")
    assert valid_email("a.b+c@uni.ac.in") and not valid_email("a@b") and not valid_email("a b@c.com")
    assert valid_phone("+91 98765-43210") and valid_phone("(080) 2345 6789") and not valid_phone("12ab56") and not valid_phone("1")


def test_iso_helpers_round_trip():
    moment = parse_iso("2026-10-14T10:00:00+05:30")
    assert to_iso(moment) == "2026-10-14T04:30:00Z"
    assert parse_iso("2026-10-14T10:00:00Z").hour == 10
    with pytest.raises(ValueError):
        parse_iso("")


def test_pagination_params_validated(ctx, client):
    login(client, make_user("Admin"))
    assert client.get("/api/v1/users?page=x").status_code == 400
    assert client.get("/api/v1/users?per_page=1000").get_json()["total"] == 1
