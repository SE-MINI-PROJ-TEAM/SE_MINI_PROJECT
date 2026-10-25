"""Course-section and enrollment models (US-06, SYS-F-006).

Uses the project's single shared SQLAlchemy instance (`db`) from
modules.auth.models; the `enrollments.student_id` foreign key points at the
existing `profiles` table. Do not create a second SQLAlchemy() instance.
"""

from modules.auth.models import db

# ---------------------------------------------------------------------------
# US-06 / SYS-F-006: course sections and student self-enrollment
# ---------------------------------------------------------------------------

COURSE_STATUS_OPEN = "Open"
COURSE_STATUS_CLOSED = "Closed"
ENROLLMENT_STATUS_ACTIVE = "Active"


class Course(db.Model):
    """A course section that students can enroll in.

    Matches the COURSE entity of the SRS ER diagram (course_id, code, title,
    capacity_limit). `section_code`, `term` and `status` are additions needed
    by US-06 (see the assumptions in TEST_cases_enrollment.md).

    Available seats are NOT stored. They are always derived as
    capacity_limit - (number of Active enrollments), so there is no second
    counter that could drift out of sync.
    """

    __tablename__ = "courses"
    __table_args__ = (
        db.UniqueConstraint(
            "code", "section_code", "term", name="uq_course_section_term"
        ),
        db.Index("ix_courses_term", "term"),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    section_code = db.Column(db.String(10), nullable=False, default="A")
    term = db.Column(db.String(30), nullable=False)
    capacity_limit = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.String(10), nullable=False, default=COURSE_STATUS_OPEN
    )

    def to_dict(self, enrolled_count):
        available = max(self.capacity_limit - enrolled_count, 0)

        if self.status != COURSE_STATUS_OPEN:
            availability = "closed"
        elif available == 0:
            availability = "full"
        else:
            availability = "open"

        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "sectionCode": self.section_code,
            "term": self.term,
            "capacity": self.capacity_limit,
            "enrolled": enrolled_count,
            "availableSeats": available,
            "status": self.status,
            "availability": availability,
        }


class Enrollment(db.Model):
    """A student's enrollment in one course section."""

    __tablename__ = "enrollments"
    __table_args__ = (
        # Database-level duplicate protection (one row per student+section).
        db.UniqueConstraint(
            "student_id", "course_id", name="uq_enrollment_student_course"
        ),
        db.Index("ix_enrollments_course", "course_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.String(50),
        db.ForeignKey("profiles.institutional_id"),
        nullable=False,
    )
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id"), nullable=False
    )
    status = db.Column(
        db.String(10), nullable=False, default=ENROLLMENT_STATUS_ACTIVE
    )
    enrolled_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    course = db.relationship("Course")
