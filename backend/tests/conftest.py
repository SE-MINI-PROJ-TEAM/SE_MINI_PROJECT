import pymysql
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app import create_app
from app.config import TestConfig
from app.extensions import db


def _ensure_test_database():
    url = make_url(TestConfig.SQLALCHEMY_DATABASE_URI)
    connection = pymysql.connect(host=url.host, port=url.port or 3306, user=url.username, password=url.password or "")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="session")
def app():
    _ensure_test_database()
    application = create_app(TestConfig)
    with application.app_context():
        db.drop_all()
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Empty every table before each test (keeps tests independent without re-creating the schema)."""
    with app.app_context():
        db.session.remove()
        db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        db.session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        db.session.commit()
        db.session.remove()
    yield


@pytest.fixture
def ctx(app):
    """An application context for building fixtures / inspecting the database directly."""
    with app.app_context():
        yield
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
