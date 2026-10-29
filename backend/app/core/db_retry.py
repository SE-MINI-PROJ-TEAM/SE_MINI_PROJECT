"""Retry helper for transient MySQL lock errors so 200 concurrent submissions never drop (SYS-NF-002)."""
import random
import time

from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db

_RETRYABLE_OPERATIONAL = {1213, 1205}  # ER_LOCK_DEADLOCK, ER_LOCK_WAIT_TIMEOUT
_DUPLICATE_KEY = 1062  # two writers inserted the same unique row; the retry sees it and updates instead


def _error_code(exc):
    return exc.orig.args[0] if exc.orig is not None and exc.orig.args else None


def run_with_retry(fn, attempts=8):
    """Run ``fn`` (which must perform its own commit); roll back and retry on deadlock / duplicate-key races."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except OperationalError as exc:
            db.session.rollback()
            if _error_code(exc) not in _RETRYABLE_OPERATIONAL or attempt == attempts:
                raise
        except IntegrityError as exc:
            db.session.rollback()
            if _error_code(exc) != _DUPLICATE_KEY or attempt == attempts:
                raise
        except Exception:
            db.session.rollback()
            raise
        time.sleep(random.uniform(0.01, 0.05) * attempt)
