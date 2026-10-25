"""US-06 concurrency tests - REQUIRE A REAL MySQL SERVER.

SQLite cannot reproduce InnoDB row locking, so these tests are skipped unless
TEST_MYSQL_URL is set to a DEDICATED, THROWAWAY test database, e.g.

    mysql+pymysql://tester:testpass@127.0.0.1/student_records_test

The database name must end in "_test": the tests create and DROP the tables
in it. They never use DATABASE_URL.

Each thread plays one browser: its own app context -> own DB session ->
own transaction, all released at the same moment by a Barrier.
"""

import os
import threading
import unittest

from flask import Flask
from sqlalchemy.engine import make_url

from enrollment_service import EnrollmentError, enroll_student
from models import Course, Enrollment, Profile, db

MYSQL_URL = os.environ.get("TEST_MYSQL_URL")


def _db_name_is_safe(url):
    return (make_url(url).database or "").endswith("_test")


@unittest.skipUnless(MYSQL_URL, "TEST_MYSQL_URL not set (needs real MySQL)")
class MySQLConcurrencyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not _db_name_is_safe(MYSQL_URL):
            raise RuntimeError("TEST_MYSQL_URL database must end in '_test'")
        cls.app = Flask("mysql_concurrency_tests")
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URL
        cls.app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_size": 40}
        db.init_app(cls.app)

    def setUp(self):
        with self.app.app_context():
            self.assertEqual(db.engine.dialect.name, "mysql")
            db.drop_all()
            db.create_all()
            db.session.add_all(
                Profile(institutional_id=f"S{i:03d}", role="Student",
                        name="s", phone="9876543210",
                        emergency_contact="9876501234",
                        personal_email="s@example.com")
                for i in range(1, 31)
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def add_course(self, code, capacity, term="T1"):
        with self.app.app_context():
            course = Course(code=code, title=code, section_code="A",
                            term=term, capacity_limit=capacity, status="Open")
            db.session.add(course)
            db.session.commit()
            return course.id

    def race(self, attempts):
        """Run [(student_id, course_id), ...] simultaneously.
        Returns a list of outcomes: 'OK' or the EnrollmentError code."""
        barrier = threading.Barrier(len(attempts))
        outcomes = [None] * len(attempts)

        def worker(index, student_id, course_id):
            with self.app.app_context():
                barrier.wait()
                try:
                    enroll_student(student_id, course_id)
                    outcomes[index] = "OK"
                except EnrollmentError as err:
                    outcomes[index] = err.code
                except Exception as err:  # deadlock etc. must fail the test
                    outcomes[index] = f"UNEXPECTED:{type(err).__name__}:{err}"
                finally:
                    db.session.remove()

        threads = [
            threading.Thread(target=worker, args=(i, s, c))
            for i, (s, c) in enumerate(attempts)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        return outcomes

    def count(self, **filters):
        with self.app.app_context():
            return db.session.query(Enrollment).filter_by(**filters).count()

    # TC-CRS-02-17: 30 students, ONE seat
    def test_last_seat_contended_by_30_students(self):
        cid = self.add_course("LAST", 1)
        outcomes = self.race([(f"S{i:03d}", cid) for i in range(1, 31)])
        self.assertEqual(outcomes.count("OK"), 1, outcomes)
        self.assertEqual(outcomes.count("SECTION_FULL"), 29, outcomes)
        self.assertEqual(self.count(course_id=cid), 1)

    # TC-CRS-02-18: 30 students, 5 seats
    def test_capacity_five_never_exceeded(self):
        cid = self.add_course("FIVE", 5)
        outcomes = self.race([(f"S{i:03d}", cid) for i in range(1, 31)])
        self.assertEqual(outcomes.count("OK"), 5, outcomes)
        self.assertEqual(outcomes.count("SECTION_FULL"), 25, outcomes)
        self.assertEqual(self.count(course_id=cid), 5)

    # TC-CRS-02-19: one student, 10 tabs, 10 different sections -> max 6
    def test_same_student_cannot_exceed_six_courses(self):
        cids = [self.add_course(f"C{i}", 30) for i in range(10)]
        outcomes = self.race([("S001", c) for c in cids])
        self.assertEqual(outcomes.count("OK"), 6, outcomes)
        self.assertEqual(outcomes.count("ENROLLMENT_LIMIT_REACHED"), 4,
                         outcomes)
        self.assertEqual(self.count(student_id="S001"), 6)

    # TC-CRS-02-20: one student double-clicks the same section
    def test_same_student_same_section_enrolled_once(self):
        cid = self.add_course("DUP", 30)
        outcomes = self.race([("S001", cid)] * 8)
        self.assertEqual(outcomes.count("OK"), 1, outcomes)
        self.assertEqual(outcomes.count("ALREADY_ENROLLED"), 7, outcomes)
        self.assertEqual(self.count(student_id="S001", course_id=cid), 1)

    # TC-CRS-02-21: both limits at once, crossing sections and students
    def test_mixed_contention_no_deadlock_no_overbooking(self):
        small = [self.add_course(f"M{i}", 3) for i in range(4)]
        attempts = [(f"S{i:03d}", small[i % 4]) for i in range(1, 25)]
        attempts += [("S001", c) for c in small]
        outcomes = self.race(attempts)
        self.assertFalse(
            [o for o in outcomes if o.startswith("UNEXPECTED")], outcomes
        )
        for cid in small:
            self.assertLessEqual(self.count(course_id=cid), 3)
        with self.app.app_context():
            per_student = (
                db.session.query(Enrollment.student_id, db.func.count())
                .group_by(Enrollment.student_id).all()
            )
        self.assertTrue(all(n <= 6 for _, n in per_student))


if __name__ == "__main__":
    unittest.main()
