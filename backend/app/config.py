import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def build_database_url(db_name=None):
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = db_name or os.getenv("DB_NAME", "student_record_system")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-please-0123456789")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or build_database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,
        "max_overflow": 60,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_timeout": 60,
        # Avoids gap-lock deadlocks and lets locking reads see the latest committed rows (SYS-NF-002).
        "isolation_level": "READ COMMITTED",
    }

    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "48"))
    JWT_COOKIE_NAME = "srs_token"
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    ENFORCE_HTTPS = _bool("ENFORCE_HTTPS", False)
    # True only behind a reverse proxy that sets X-Forwarded-* (the nginx container): the app then sees the real client
    # IP (login rate limiting) and scheme (HTTPS redirect). Never enable when the app is directly reachable.
    TRUST_PROXY = _bool("TRUST_PROXY", False)
    # One structured JSON line per request (SAD 4.3). Cheap natively, but under container stdout it measurably costs CPU at load.
    LOG_REQUESTS = _bool("LOG_REQUESTS", True)
    LOGIN_RATE_LIMIT_PER_MIN = int(os.getenv("LOGIN_RATE_LIMIT_PER_MIN", "30"))

    ATTENDANCE_FREEZE_HOURS = 48
    MAX_COURSES_PER_TERM = 6
    DEFAULT_TERM = os.getenv("CURRENT_TERM", "Fall 2026")
    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL") or build_database_url(
        os.getenv("TEST_DB_NAME", "student_record_system_test")
    )
    LOGIN_RATE_LIMIT_PER_MIN = 0
    # Low cost only in tests so the suite is fast; a dedicated test asserts the production default is 12.
    BCRYPT_ROUNDS = 4
    ENFORCE_HTTPS = False
