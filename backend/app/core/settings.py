"""Tiny key/value application settings stored in the database."""
from flask import current_app

from app.extensions import db
from app.models import Setting

ENROLLMENT_OPEN = "enrollment_open"
CURRENT_TERM = "current_term"


def get_setting(key, default=None):
    row = db.session.get(Setting, key)
    return row.value if row else default


def set_setting(key, value):
    row = db.session.get(Setting, key)
    if row is None:
        db.session.add(Setting(key=key, value=str(value)))
    else:
        row.value = str(value)


def current_term():
    return get_setting(CURRENT_TERM, current_app.config["DEFAULT_TERM"])


def enrollment_open():
    return get_setting(ENROLLMENT_OPEN, "true") == "true"
