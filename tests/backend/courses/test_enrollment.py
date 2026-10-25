"""US-06 / SYS-F-006 / TC-CRS-02: self-enrollment and the 6-course cap.

These tests use an in-memory SQLite database, so they verify the BUSINESS
RULES (limits, duplicates, status codes, rollback, identity). They do NOT
prove row-locking behaviour; that is covered by test_enrollment_mysql.py,
which needs a real MySQL server.
"""

import os
import unittest
from unittest import mock

# Must happen before `app` is imported (app.py builds its engine on import).
# conftest.py does this for pytest; this line protects plain `unittest` runs.
os.environ["DATABASE_URL"] = "sqlite://"

from app import app, db  # noqa: E402
from models import Course, Enrollment, Profile  # noqa: E402

T1 = "2026-ODD"
T2 = "2026-EVEN"


def make_profile(institutional_id, role="Student"):
    return Profile(
        institutional_id=institutional_id,
        role=role,
        name=institutional_id,
        phone="9876543210",
        emergency_contact="9876501234",
        personal_email=f"{institutional_id.lower()}@example.com",
    )


class EnrollmentTestBase(unittest.TestCase):
    """Fresh isolated database and seed data for every test."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["ALLOW_INSECURE_DEV_IDENTITY"] = True

        with app.app_context():
            # Safety: never run drop_all() against anything but SQLite.
            self.assertEqual(db.engine.dialect.name, "sqlite")
            db.drop_all()
            db.create_all()

            db.session.add_all(
                [
                    make_profile("STU001"),
                    make_profile("STU002"),
                    make_profile("STU003"),
                    make_profile("FAC001", role="Faculty"),
                ]
            )
            # Eight open sections (capacity 30) in T1 -> ids 1..8
            for i in range(1, 9):
                db.session.add(
                    Course(
                        code=f"CS{100 + i}",
                        title=f"Course {i}",
                        section_code="A",
                        term=T1,
                        capacity_limit=30,
                        status="Open",
                    )
                )
            # id 9: closed section; id 10: capacity-1 section (last seat);
            # id 11: an open section in a different term.
            db.session.add_all(
                [
                    Course(code="CS901", title="Closed", section_code="A",
                           term=T1, capacity_limit=30, status="Closed"),
                    Course(code="CS902", title="Last Seat", section_code="A",
                           term=T1, capacity_limit=1, status="Open"),
                    Course(code="CS903", title="Next Term", section_code="A",
                           term=T2, capacity_limit=30, status="Open"),
                ]
            )
            db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        app.config["ALLOW_INSECURE_DEV_IDENTITY"] = True

    # -- helpers ---------------------------------------------------------
    def enroll(self, course_id, student="STU001", **kwargs):
        headers = {"X-Student-Id": student} if student else {}
        return self.client.post(
            "/api/v1/enrollments",
            json={"courseId": course_id},
            headers=headers,
            **kwargs,
        )

    def section(self, course_id):
        body = self.client.get("/api/v1/courses").get_json()
        return next(c for c in body["courses"] if c["id"] == course_id)

    def enrollment_rows(self):
        with app.app_context():
            return sorted(
                (e.student_id, e.course_id, e.status)
                for e in db.session.query(Enrollment).all()
            )

    def fill_to(self, n, student="STU001"):
        """Enroll `student` in sections 1..n through the real API."""
        for course_id in range(1, n + 1):
            self.assertEqual(self.enroll(course_id, student).status_code, 201)


class CatalogTests(EnrollmentTestBase):
    # TC-CRS-02-01 (Acceptance criterion 1)
    def test_catalog_returns_sections_with_capacity(self):
        response = self.client.get("/api/v1/courses")
        self.assertEqual(response.status_code, 200)
        courses = response.get_json()["courses"]
        self.assertEqual(len(courses), 11)

        first = next(c for c in courses if c["id"] == 1)
        self.assertEqual(
            first,
            {
                "id": 1, "code": "CS101", "title": "Course 1",
                "sectionCode": "A", "term": T1, "capacity": 30,
                "enrolled": 0, "availableSeats": 30, "status": "Open",
                "availability": "open",
            },
        )
        self.assertEqual(self.section(9)["availability"], "closed")
        self.assertEqual(self.section(10)["availableSeats"], 1)

    # TC-CRS-02-01b
    def test_catalog_term_filter(self):
        courses = self.client.get(
            f"/api/v1/courses?term={T2}"
        ).get_json()["courses"]
        self.assertEqual([c["code"] for c in courses], ["CS903"])

    # TC-CRS-02-01c
    def test_catalog_marks_full_section(self):
        self.assertEqual(self.enroll(10, "STU001").status_code, 201)
        full = self.section(10)
        self.assertEqual(full["availableSeats"], 0)
        self.assertEqual(full["availability"], "full")


class EnrollmentSuccessTests(EnrollmentTestBase):
    # TC-CRS-02-02 (Acceptance criterion 2)
    def test_successful_enrollment(self):
        response = self.enroll(1)
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["message"], "Enrollment confirmed.")
        self.assertEqual(body["enrollment"]["courseId"], 1)
        self.assertEqual(body["enrollment"]["status"], "Active")
        self.assertEqual(
            body["enrollmentSummary"],
            {"term": T1, "count": 1, "limit": 6},
        )
        self.assertEqual(self.enrollment_rows(), [("STU001", 1, "Active")])

    # TC-CRS-02-03 (Acceptance criterion 4)
    def test_capacity_decrements_after_enrollment(self):
        self.assertEqual(self.section(1)["availableSeats"], 30)
        body = self.enroll(1).get_json()
        self.assertEqual(body["course"]["availableSeats"], 29)
        self.assertEqual(body["course"]["enrolled"], 1)
        self.assertEqual(self.section(1)["availableSeats"], 29)

        self.enroll(1, "STU002")
        self.assertEqual(self.section(1)["availableSeats"], 28)

    # TC-CRS-02-07 (boundary: the 6th course is allowed)
    def test_sixth_enrollment_is_accepted(self):
        self.fill_to(5)
        response = self.enroll(6)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["enrollmentSummary"]["count"], 6)

    # TC-CRS-02-14
    def test_my_enrollments_lists_only_own_records(self):
        self.enroll(1, "STU001")
        self.enroll(2, "STU001")
        self.enroll(3, "STU002")

        mine = self.client.get(
            "/api/v1/enrollments/me", headers={"X-Student-Id": "STU001"}
        )
        self.assertEqual(mine.status_code, 200)
        body = mine.get_json()
        self.assertEqual(body["limit"], 6)
        self.assertEqual(body["countsByTerm"], {T1: 2})
        self.assertEqual(
            sorted(e["courseId"] for e in body["enrollments"]), [1, 2]
        )

    # TC-CRS-02-13
    def test_limit_is_per_term(self):
        self.fill_to(6)
        self.assertEqual(self.enroll(11).status_code, 201)  # T2 section
        body = self.client.get(
            "/api/v1/enrollments/me", headers={"X-Student-Id": "STU001"}
        ).get_json()
        self.assertEqual(body["countsByTerm"], {T1: 6, T2: 1})


class EnrollmentRejectionTests(EnrollmentTestBase):
    # TC-CRS-02-04 (Acceptance criterion 3 relates to -06; this is "full")
    def test_full_section_rejected(self):
        self.assertEqual(self.enroll(10, "STU001").status_code, 201)
        response = self.enroll(10, "STU002")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "SECTION_FULL")
        self.assertEqual(self.enrollment_rows(), [("STU001", 10, "Active")])

    # TC-CRS-02-05
    def test_closed_section_rejected(self):
        response = self.enroll(9)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "SECTION_CLOSED")
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-06 (Acceptance criterion 3)
    def test_seventh_enrollment_rejected(self):
        self.fill_to(6)
        response = self.enroll(7)
        self.assertEqual(response.status_code, 409)
        body = response.get_json()
        self.assertEqual(body["code"], "ENROLLMENT_LIMIT_REACHED")
        self.assertIn("at most 6", body["error"])
        self.assertEqual(len(self.enrollment_rows()), 6)
        self.assertEqual(self.section(7)["availableSeats"], 30)

    # TC-CRS-02-08
    def test_duplicate_enrollment_rejected(self):
        self.assertEqual(self.enroll(1).status_code, 201)
        response = self.enroll(1)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "ALREADY_ENROLLED")
        self.assertEqual(self.section(1)["availableSeats"], 29)
        self.assertEqual(len(self.enrollment_rows()), 1)

    # TC-CRS-02-09
    def test_nonexistent_section_and_student(self):
        r = self.enroll(999)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["code"], "COURSE_NOT_FOUND")

        r = self.enroll(1, student="STU999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["code"], "STUDENT_NOT_FOUND")
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-10
    def test_malformed_requests_rejected(self):
        headers = {"X-Student-Id": "STU001"}
        url = "/api/v1/enrollments"
        bad_bodies = [
            {},
            {"course": 1},
            {"courseId": "1"},
            {"courseId": True},
            {"courseId": 0},
            {"courseId": -3},
            {"courseId": 1.5},
            {"courseId": None},
            {"courseId": 1, "extra": "x"},
            [1],
        ]
        for body in bad_bodies:
            with self.subTest(body=body):
                r = self.client.post(url, json=body, headers=headers)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json()["code"], "INVALID_REQUEST")

        not_json = self.client.post(
            url, data="not json", headers=headers,
            content_type="application/json",
        )
        self.assertEqual(not_json.status_code, 400)
        no_body = self.client.post(url, headers=headers)
        self.assertEqual(no_body.status_code, 400)
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-12
    def test_failed_enrollments_leave_state_unchanged(self):
        self.fill_to(6)
        self.assertEqual(self.enroll(10, "STU002").status_code, 201)

        rows_before = self.enrollment_rows()
        catalog_before = self.client.get("/api/v1/courses").get_json()

        attempts = [
            (7, "STU001"),    # 7th course
            (10, "STU003"),   # full
            (9, "STU003"),    # closed
            (1, "STU001"),    # duplicate
            (999, "STU003"),  # unknown section
        ]
        for course_id, student in attempts:
            with self.subTest(course_id=course_id, student=student):
                self.assertGreaterEqual(
                    self.enroll(course_id, student).status_code, 400
                )

        self.assertEqual(self.enrollment_rows(), rows_before)
        self.assertEqual(
            self.client.get("/api/v1/courses").get_json(), catalog_before
        )

    # TC-CRS-02-15: unexpected failure mid-transaction -> rolled back
    def test_unexpected_error_rolls_back(self):
        with mock.patch.object(
            db.session, "commit", side_effect=RuntimeError("boom")
        ):
            response = self.enroll(1)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["code"], "INTERNAL_ERROR")
        self.assertEqual(self.enrollment_rows(), [])
        self.assertEqual(self.section(1)["availableSeats"], 30)

    # TC-CRS-02-16: last seat, two students, one after the other
    def test_last_seat_goes_to_exactly_one_student(self):
        first = self.enroll(10, "STU001")
        second = self.enroll(10, "STU002")
        self.assertEqual(
            sorted([first.status_code, second.status_code]), [201, 409]
        )
        self.assertEqual(len(self.enrollment_rows()), 1)
        self.assertEqual(self.section(10)["availableSeats"], 0)


class IdentityTests(EnrollmentTestBase):
    # TC-CRS-02-11a
    def test_no_identity_is_unauthorized(self):
        r = self.enroll(1, student=None)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()["code"], "UNAUTHENTICATED")
        r = self.client.get("/api/v1/enrollments/me")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-11b: secure by default - dev identity switched off
    def test_dev_identity_disabled_by_default(self):
        app.config["ALLOW_INSECURE_DEV_IDENTITY"] = False
        r = self.enroll(1, student="STU001")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-11c: a student ID in the body is not trusted
    def test_body_student_id_is_rejected_not_trusted(self):
        r = self.client.post(
            "/api/v1/enrollments",
            json={"courseId": 1, "studentId": "STU002"},
            headers={"X-Student-Id": "STU001"},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.enrollment_rows(), [])

    # TC-CRS-02-11d: only students may self-enroll
    def test_non_student_role_forbidden(self):
        r = self.enroll(1, student="FAC001")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json()["code"], "FORBIDDEN_ROLE")
        self.assertEqual(self.enrollment_rows(), [])


if __name__ == "__main__":
    unittest.main()
