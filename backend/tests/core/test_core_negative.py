"""Shared-layer negative paths: retry policy, 500 handling, login throttling, unauthenticated misuse."""
import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app import create_app
from app.config import TestConfig
from app.core.db_retry import run_with_retry
from app.extensions import limiter
from tests.factories import login, make_user


def db_error(cls, code):
    class Orig(Exception):
        pass

    return cls("stmt", {}, Orig(code, "boom"))


def test_deadlock_is_retried_until_success(ctx, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise db_error(OperationalError, 1213)
        return "done"

    assert run_with_retry(flaky) == "done" and len(calls) == 3


def test_duplicate_key_race_is_retried_once_then_sees_the_row(ctx, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    calls = []

    def racy():
        calls.append(1)
        if len(calls) == 1:
            raise db_error(IntegrityError, 1062)
        return "ok"

    assert run_with_retry(racy) == "ok" and len(calls) == 2


@pytest.mark.parametrize("error", [db_error(OperationalError, 2013), db_error(IntegrityError, 1452), ValueError("bad")])
def test_non_retryable_errors_propagate_immediately(ctx, error):
    calls = []

    def fail():
        calls.append(1)
        raise error

    with pytest.raises(type(error)):
        run_with_retry(fail)
    assert len(calls) == 1


def test_retry_gives_up_after_the_attempt_limit(ctx, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    calls = []

    def always_deadlocks():
        calls.append(1)
        raise db_error(OperationalError, 1213)

    with pytest.raises(OperationalError):
        run_with_retry(always_deadlocks, attempts=3)
    assert len(calls) == 3


def test_unexpected_exceptions_return_a_clean_500_without_internals():
    app = create_app(TestConfig)

    @app.get("/api/v1/_boom")
    def boom():
        raise RuntimeError("secret internal detail")

    response = app.test_client().get("/api/v1/_boom")
    body = response.get_data(as_text=True)
    assert response.status_code == 500 and response.get_json()["code"] == "INTERNAL_ERROR"
    assert "secret internal detail" not in body and "Traceback" not in body


class ThrottledConfig(TestConfig):
    LOGIN_RATE_LIMIT_PER_MIN = 3


def test_login_is_rate_limited_after_repeated_attempts(ctx):
    user = make_user("Student")
    app = create_app(ThrottledConfig)
    limiter.reset()
    client = app.test_client()
    codes = [client.post("/api/v1/auth/login", json={"identifier": user.email, "password": "wrong"}).status_code for _ in range(5)]
    limiter.reset()
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


@pytest.mark.parametrize("method,path", [("POST", "/api/v1/auth/change-password"), ("GET", "/api/v1/auth/me"), ("POST", "/api/v1/disputes")])
def test_unauthenticated_requests_are_rejected(client, method, path):
    assert client.open(path, method=method, json={}).status_code == 401


def test_oversized_and_wrong_type_payloads(ctx, client):
    login(client, make_user("Admin"))
    giant = {"full_name": "A" * 5000, "email": "a@b.co", "role": "Student", "institutional_id": "ID1"}
    assert client.post("/api/v1/users", json=giant).status_code == 400
    assert client.post("/api/v1/users", json=["not", "an", "object"]).status_code == 400
    wrong_types = {"full_name": 123, "email": "a@b.co", "role": "Student", "institutional_id": {"x": 1}}
    assert client.post("/api/v1/users", json=wrong_types).status_code == 400


def test_app_refuses_to_start_with_a_weak_signing_key():
    from app.config import Config

    class WeakKey(Config):
        SECRET_KEY = "too-short"

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(WeakKey)


def test_forwarded_headers_are_trusted_only_when_behind_a_proxy():
    from flask import request

    class Proxied(TestConfig):
        TRUST_PROXY = True

    def client_ip(config):
        app = create_app(config)
        app.add_url_rule("/_ip", "ip", lambda: request.remote_addr)
        return app.test_client().get("/_ip", headers={"X-Forwarded-For": "203.0.113.9"}).get_data(as_text=True)

    assert client_ip(Proxied) == "203.0.113.9"  # behind nginx: the real client, so rate limits are per user
    assert client_ip(TestConfig) != "203.0.113.9"  # directly exposed: a spoofed header is ignored


def test_session_cookie_is_secure_only_when_the_request_came_over_https(ctx):
    class Proxied(TestConfig):
        TRUST_PROXY = True

    user = make_user("Student")
    app = create_app(Proxied)
    body = {"identifier": user.email, "password": "Password@123"}
    https = app.test_client().post("/api/v1/auth/login", json=body, headers={"X-Forwarded-Proto": "https"})
    http = app.test_client().post("/api/v1/auth/login", json=body)
    assert "Secure" in https.headers["Set-Cookie"] and "HttpOnly" in https.headers["Set-Cookie"]
    assert "Secure" not in http.headers["Set-Cookie"]  # plain-HTTP local use still works
