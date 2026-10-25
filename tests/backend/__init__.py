"""Test-suite safety guard.

app.py builds its database engine when it is first imported, from
DATABASE_URL (default: backend/dev.db). Several test modules call
db.drop_all(), which would DROP THE TABLES of whatever database that is - your
development database included. This package is imported before any test module
under tests/backend/, so forcing an in-memory SQLite database here protects
every suite, however the tests are started (unittest discover, a single module,
or pytest).

The optional MySQL concurrency tests (courses/test_enrollment_mysql.py) never
use DATABASE_URL; they connect only to TEST_MYSQL_URL.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"
