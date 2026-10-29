"""Database management CLI.

    python manage.py init-db            create the database (if missing) and all tables
    python manage.py seed               populate synthetic data (refuses if users already exist)
    python manage.py seed --reset       drop every table, recreate, then seed
    python manage.py drop               drop every table
"""
import argparse
import sys
import time

import pymysql
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db
from app.models import User
from app.seed import seed_database
from app.seed.seeder import DEMO_PASSWORD, TEMP_USER_PASSWORD


def ensure_database_exists(app):
    url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    connection = pymysql.connect(host=url.host, port=url.port or 3306, user=url.username, password=url.password or "")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


def print_credentials():
    print(
        f"""
Demo logins (password for all seeded accounts: {DEMO_PASSWORD})
  Admin    admin001@srs.edu      (ADM001)
  Faculty  faculty001@srs.edu    (FAC001)  teaches CS101, CS102, CS103 with live attendance / grading demos
  Student  student001@srs.edu    (PES1UG24CS001)  4 courses, 2 seats left before the 6-course cap
  Student  student002@srs.edu    (PES1UG24CS002)  already at the 6-course cap
  New user new.student@srs.edu   temporary password: {TEMP_USER_PASSWORD}  (forces password reset)
"""
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["init-db", "seed", "drop"])
    parser.add_argument("--reset", action="store_true", help="with 'seed': drop and recreate all tables first")
    args = parser.parse_args()

    app = create_app()
    ensure_database_exists(app)
    with app.app_context():
        if args.command == "drop" or (args.command == "seed" and args.reset):
            db.drop_all()
            print("Dropped all tables.")
        if args.command == "drop":
            return
        db.create_all()
        print("Tables ready.")
        if args.command == "seed":
            if User.query.first() is not None:
                print("Database already contains users. Re-run with --reset to wipe and re-seed.")
                sys.exit(1)
            started = time.perf_counter()
            summary = seed_database()
            print(f"Seeded in {time.perf_counter() - started:.1f}s:")
            for key, value in summary.items():
                print(f"  {key:<20}{value:>8,}")
            print_credentials()


if __name__ == "__main__":
    main()
