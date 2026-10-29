"""Authentication & RBAC (PRJ-SR-002/003/004).

* bcrypt hashing (work factor 12 by default)
* HTTP-only JWT cookie, 48 hour lifetime. A bearer header is also accepted for API clients / test scripts.
* ``auth_required`` enforces authentication, role claims and the temporary-password gate on every endpoint.
"""
import secrets
import string
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, request

from app.core.errors import ApiError, forbidden, unauthorized
from app.extensions import db
from app.models import User

ALGORITHM = "HS256"
MAX_PASSWORD_BYTES = 72  # bcrypt input limit

PASSWORD_RULES = (
    "At least 8 characters",
    "At least one uppercase letter",
    "At least one lowercase letter",
    "At least one digit",
    "At least one special character",
)
_SPECIALS = "!@#$%^&*()-_=+[]{};:,.?/"


# ---------------------------------------------------------------- passwords
def validate_password_strength(password):
    """Return a list of unmet complexity rules (empty list == acceptable)."""
    problems = []
    if not isinstance(password, str) or len(password) < 8:
        problems.append(PASSWORD_RULES[0])
    password = password if isinstance(password, str) else ""
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        problems.append(f"At most {MAX_PASSWORD_BYTES} bytes")
    if not any(c.isupper() for c in password):
        problems.append(PASSWORD_RULES[1])
    if not any(c.islower() for c in password):
        problems.append(PASSWORD_RULES[2])
    if not any(c.isdigit() for c in password):
        problems.append(PASSWORD_RULES[3])
    if not any(not c.isalnum() for c in password):
        problems.append(PASSWORD_RULES[4])
    return problems


def generate_temporary_password(length=12):
    """Cryptographically secure password that always satisfies the complexity policy."""
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%&*?"]
    chars = [secrets.choice(pool) for pool in pools]
    alphabet = "".join(pools)
    chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def hash_password(password, rounds=None):
    rounds = rounds or current_app.config["BCRYPT_ROUNDS"]
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, AttributeError):
        return False


_DUMMY_HASH = None


def burn_password_check(password):
    """Equalise login timing when the account does not exist."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password("dummy-Password-1!")
    verify_password(password, _DUMMY_HASH)


# --------------------------------------------------------------------- JWT
def issue_token(user, issued_at=None):
    issued_at = issued_at or datetime.now(timezone.utc)
    lifetime = timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"])
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": issued_at,
        "exp": issued_at + lifetime,
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=ALGORITHM)


def decode_token(token):
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "sub"]},
    )


def set_auth_cookie(response, token):
    response.set_cookie(
        current_app.config["JWT_COOKIE_NAME"],
        token,
        max_age=current_app.config["JWT_EXPIRY_HOURS"] * 3600,
        httponly=True,
        secure=current_app.config["ENFORCE_HTTPS"] or request.is_secure,  # is_secure honours X-Forwarded-Proto behind the proxy
        samesite="Lax",
        path="/",
    )
    return response


def clear_auth_cookie(response):
    response.delete_cookie(current_app.config["JWT_COOKIE_NAME"], path="/")
    return response


def _extract_token():
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if token:
        return token
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


# -------------------------------------------------------------------- RBAC
def authenticate(allow_temporary=False):
    token = _extract_token()
    if not token:
        raise unauthorized()
    try:
        claims = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise unauthorized("Session expired. Please sign in again.", "TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise unauthorized("Invalid session token.", "INVALID_TOKEN")

    try:
        user = db.session.get(User, int(claims["sub"]))
    except (TypeError, ValueError):
        raise unauthorized("Invalid session token.", "INVALID_TOKEN")

    # Checked against the database on every request so deactivation revokes sessions immediately (US-04).
    if user is None or not user.is_active:
        raise unauthorized("This account is deactivated or no longer exists.", "ACCOUNT_INACTIVE")
    if claims.get("role") != user.role:
        raise unauthorized("Your role changed. Please sign in again.", "ROLE_CHANGED")
    if user.is_temporary_password and not allow_temporary:
        raise ApiError(403, "PASSWORD_RESET_REQUIRED", "You must change your temporary password first.")

    g.current_user = user
    return user


def auth_required(*roles, allow_temporary=False):
    """Decorator: authenticate, then require one of ``roles`` (any authenticated role when empty)."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = authenticate(allow_temporary=allow_temporary)
            if roles and user.role not in roles:
                raise forbidden()
            return fn(*args, **kwargs)

        # Introspected by qa/openapi/generate.py to document who may call each endpoint.
        wrapper.auth_roles = roles
        wrapper.allow_temporary = allow_temporary
        return wrapper

    return decorator


def current_user():
    return g.current_user


def session_payload(user):
    """User representation returned by login / me / change-password."""
    data = user.to_dict()
    data["must_change_password"] = user.is_temporary_password
    return data
