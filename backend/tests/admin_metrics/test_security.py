"""US-15 security benchmark: TC-SEC-01 .. TC-SEC-05 (TLS config, bcrypt, JWT, RBAC, ORM / XSS)."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import create_app
from app.config import TestConfig
from app.core.security import issue_token
from app.models import User
from tests.factories import bearer, enroll, login, make_course, make_session, make_user


# ----------------------------------------------------------- TC-SEC-01 (TLS / HTTPS enforcement)
class HttpsConfig(TestConfig):
    ENFORCE_HTTPS = True


def test_plain_http_redirects_to_https_with_hsts(app):
    secure_app = create_app(HttpsConfig)
    client = secure_app.test_client()
    response = client.get("/api/v1/health", base_url="http://example.test")
    assert response.status_code == 301 and response.headers["Location"].startswith("https://")

    ok = client.get("/api/v1/health", base_url="https://example.test")
    assert ok.status_code == 200
    assert "max-age=" in ok.headers["Strict-Transport-Security"]


def test_cookie_is_secure_when_https_enforced(app, ctx):
    user = make_user("Student")
    secure_app = create_app(HttpsConfig)
    response = secure_app.test_client().post(
        "/api/v1/auth/login", json={"identifier": user.email, "password": "Password@123"}, base_url="https://example.test"
    )
    assert "Secure" in response.headers["Set-Cookie"]


def test_https_server_context_refuses_anything_below_tls_1_3(tmp_path):
    import socket
    import ssl
    import threading

    from run import build_ssl_context
    from scripts.gen_dev_cert import generate

    cert_dir = generate(str(tmp_path))
    context = build_ssl_context(cert_dir)
    assert context.minimum_version == ssl.TLSVersion.TLSv1_3

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(2)
    port = listener.getsockname()[1]

    def serve():
        for _ in range(2):
            conn, _ = listener.accept()
            try:
                context.wrap_socket(conn, server_side=True).close()
            except (ssl.SSLError, OSError):
                conn.close()

    threading.Thread(target=serve, daemon=True).start()

    def connect(max_version):
        client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_ctx.check_hostname = False
        client_ctx.verify_mode = ssl.CERT_NONE
        client_ctx.maximum_version = max_version
        with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
            with client_ctx.wrap_socket(raw) as tls:
                return tls.version()

    with pytest.raises(ssl.SSLError):
        connect(ssl.TLSVersion.TLSv1_2)  # a TLS 1.2-only client is rejected
    assert connect(ssl.TLSVersion.TLSv1_3) == "TLSv1.3"
    listener.close()


def test_security_headers_present(client):
    headers = client.get("/api/v1/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff" and headers["X-Frame-Options"] == "DENY"
    assert headers["Cache-Control"] == "no-store"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin" and "Permissions-Policy" in headers
    assert client.get("/not-an-api-path").headers["Cache-Control"] == "no-store"  # even 404s are never cacheable


# ------------------------------------------------------- TC-SEC-03 (HTTP-only 48h JWT sessions)
def test_session_cookie_is_http_only_with_48h_lifetime(ctx, client):
    user = make_user("Student")
    response = client.post("/api/v1/auth/login", json={"identifier": user.email, "password": "Password@123"})
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and f"Max-Age={48 * 3600}" in cookie
    assert "token" not in response.get_json()  # never exposed to JavaScript in the body


def test_jwt_lifetime_is_exactly_48_hours(ctx, app):
    user = make_user("Student")
    claims = jwt.decode(issue_token(user), options={"verify_signature": False})
    assert claims["exp"] - claims["iat"] == 48 * 3600


def test_expired_token_returns_401(ctx, client):
    user = make_user("Student")
    stale = issue_token(user, issued_at=datetime.now(timezone.utc) - timedelta(hours=48, minutes=1))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {stale}"})
    assert response.status_code == 401 and response.get_json()["code"] == "TOKEN_EXPIRED"
    fresh = issue_token(user, issued_at=datetime.now(timezone.utc) - timedelta(hours=47, minutes=55))
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh}"}).status_code == 200


def test_tampered_and_unsigned_tokens_rejected(ctx, client):
    user = make_user("Student")
    token = issue_token(user)
    forged_role = jwt.encode({**jwt.decode(token, options={"verify_signature": False}), "role": "Admin"}, "wrong-secret", algorithm="HS256")
    none_alg = jwt.encode({"sub": str(user.id), "role": "Admin", "iat": 1, "exp": 9999999999}, key=None, algorithm="none")
    for bad in (forged_role, none_alg, token[:-3] + "abc", "garbage"):
        assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


# ---------------------------------------------------------- TC-SEC-04 (RBAC on every endpoint)
ENDPOINTS = [
    # (method, path, roles that MUST be refused with 403)
    ("POST", "/api/v1/users", ("Student", "Faculty")),
    ("GET", "/api/v1/users", ("Student", "Faculty")),
    ("GET", "/api/v1/admin/audit-logs", ("Student", "Faculty")),
    ("GET", "/api/v1/admin/metrics", ("Student", "Faculty")),
    ("GET", "/api/v1/admin/metrics/export.csv", ("Student", "Faculty")),
    ("GET", "/api/v1/courses", ("Student", "Faculty")),
    ("POST", "/api/v1/courses", ("Student", "Faculty")),
    ("POST", "/api/v1/schedule/sessions", ("Student", "Faculty")),
    ("GET", "/api/v1/schedule/my-courses", ("Student", "Admin")),
    ("GET", "/api/v1/schedule/roster/1", ("Student",)),
    ("GET", "/api/v1/attendance/sessions", ("Student", "Admin")),
    ("POST", "/api/v1/attendance/sessions/1", ("Student", "Admin")),
    ("GET", "/api/v1/attendance/override/courses", ("Student", "Faculty")),
    ("PUT", "/api/v1/attendance/override/sessions/1", ("Student", "Faculty")),
    ("GET", "/api/v1/attendance/summary", ("Faculty", "Admin")),
    ("GET", "/api/v1/grades/courses", ("Student", "Admin")),
    ("PUT", "/api/v1/grades/courses/1", ("Student", "Admin")),
    ("POST", "/api/v1/grades/courses/1/submit", ("Student", "Admin")),
    ("GET", "/api/v1/grades/publication/queue", ("Student", "Faculty")),
    ("POST", "/api/v1/grades/publication/publish", ("Student", "Faculty")),
    ("GET", "/api/v1/grades/mine", ("Faculty", "Admin")),
    ("POST", "/api/v1/disputes", ("Faculty", "Admin")),
    ("GET", "/api/v1/disputes", ("Student",)),
    ("POST", "/api/v1/disputes/1/resolve", ("Student",)),
    ("GET", "/api/v1/analytics/student/summary", ("Faculty", "Admin")),
    ("GET", "/api/v1/analytics/faculty/sections", ("Student", "Admin")),
    ("POST", "/api/v1/enrollments", ("Faculty", "Admin")),
    ("PUT", "/api/v1/enrollments/window", ("Student", "Faculty")),
    ("GET", "/api/v1/profile", ("Admin",)),
]


@pytest.mark.parametrize("method,path,forbidden_roles", ENDPOINTS)
def test_endpoints_enforce_role_based_access(ctx, client, method, path, forbidden_roles):
    assert client.open(path, method=method, json={}).status_code == 401  # unauthenticated
    for role in forbidden_roles:
        user = make_user(role)
        response = client.open(path, method=method, json={}, headers=bearer(user))
        assert response.status_code == 403, f"{role} reached {method} {path}"


def test_every_registered_endpoint_is_covered_by_auth(app):
    """Guard against a new route being added without authentication (health + login/logout/policy are public)."""
    public = {"/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/password-policy"}
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or not rule.rule.startswith("/api/") or rule.rule in public:
            continue
        # @auth_required wraps the view with functools.wraps, so an unprotected view has no __wrapped__.
        assert hasattr(app.view_functions[rule.endpoint], "__wrapped__"), f"{rule.rule} is not protected by auth_required"


def test_faculty_cannot_read_another_faculty_roster_or_grades(ctx, client):
    a, b = make_user("Faculty"), make_user("Faculty")
    foreign = make_course(b)
    enroll(make_user("Student"), foreign)
    login(client, a)
    assert client.get(f"/api/v1/schedule/roster/{foreign.id}").status_code == 403
    assert client.get(f"/api/v1/grades/courses/{foreign.id}").status_code == 403
    session = make_session(foreign, hours_ago=1)
    assert client.get(f"/api/v1/attendance/sessions/{session.id}").status_code == 403


# ------------------------------------------------- TC-SEC-05 (parameterised ORM, SQLi / XSS)
SQLI = ["' OR '1'='1", "'; DROP TABLE users; --", "1 UNION SELECT password_hash FROM users", '" OR ""="']


@pytest.mark.parametrize("payload", SQLI)
def test_sql_injection_payloads_are_inert(ctx, client, payload):
    admin = make_user("Admin")
    victim = make_user("Student")
    # login
    assert client.post("/api/v1/auth/login", json={"identifier": payload, "password": payload}).status_code == 401
    login(client, admin)
    assert client.get("/api/v1/users", query_string={"search": payload}).get_json()["total"] == 0
    assert client.get("/api/v1/admin/audit-logs", query_string={"action": payload}).get_json()["total"] == 0
    assert client.get("/api/v1/catalog", query_string={"search": payload}).status_code == 200
    assert User.query.count() == 2 and User.query.get(victim.id) is not None


def test_html_is_stripped_from_user_input(ctx, client):
    admin = make_user("Admin")
    login(client, admin)
    body = {"full_name": "<img src=x onerror=alert(1)>Eve", "email": "eve@test.edu", "role": "Student", "institutional_id": "XSS-1"}
    created = client.post("/api/v1/users", json=body).get_json()["user"]
    assert "<" not in created["full_name"] and created["full_name"] == "Eve"


def test_error_responses_do_not_leak_internals(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404 and response.get_json()["status"] == "error"
    assert "Traceback" not in response.get_data(as_text=True)
