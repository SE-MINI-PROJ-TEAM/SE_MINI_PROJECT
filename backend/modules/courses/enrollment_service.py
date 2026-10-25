"""Business logic for student self-enrollment (SYS-F-006, US-06).

Layering: app.py (HTTP) -> this module (rules + transaction) -> models.py (ORM).

Rules enforced here, on the server, regardless of what the UI does:
  * the student and the section must exist, and the caller must be a Student
  * the section must be Open and have a free seat
  * no duplicate enrollment in the same section
  * at most MAX_COURSES_PER_TERM Active enrollments per student per term

Concurrency strategy (MySQL / InnoDB)
-------------------------------------
Everything happens in ONE transaction that starts with two row locks
(`SELECT ... FOR UPDATE`), always taken in the SAME ORDER:

  1. the student's `profiles` row  -> serialises two requests from the same
     student, so two tabs cannot both claim that student's 6th course;
  2. the section's `courses` row   -> serialises everybody competing for the
     same section, so two students cannot both claim its last seat.

Only after both locks are held do we count and insert. Because the order is
always student -> course, two transactions can never wait on each other in a
cycle (no deadlock). The lock acquisition must be the FIRST statement of the
transaction: under InnoDB's default REPEATABLE READ, the first plain SELECT
fixes the read snapshot, and counting from an older snapshot could miss a
seat that another transaction just took. The route layer therefore does no
database reads before calling `enroll_student`.

SQLite (used by the unit tests) ignores FOR UPDATE, so the tests there verify
the business rules, not the locking. The locking is verified by
test_enrollment_mysql.py against a real MySQL server.
"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from models import (
    COURSE_STATUS_OPEN,
    ENROLLMENT_STATUS_ACTIVE,
    Course,
    Enrollment,
    Profile,
    db,
)

# Assumption A1 (see TEST_cases_enrollment.md): the limit counts Active
# enrollment records (= course sections) per academic term.
MAX_COURSES_PER_TERM = 6


class EnrollmentError(Exception):
    """A business-rule or lookup failure that maps to an HTTP error."""

    def __init__(self, code, message, status):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _enrolled_count(course_id):
    return db.session.execute(
        select(func.count(Enrollment.id)).where(
            Enrollment.course_id == course_id,
            Enrollment.status == ENROLLMENT_STATUS_ACTIVE,
        )
    ).scalar_one()


def _term_count(student_id, term):
    return db.session.execute(
        select(func.count(Enrollment.id))
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Enrollment.student_id == student_id,
            Enrollment.status == ENROLLMENT_STATUS_ACTIVE,
            Course.term == term,
        )
    ).scalar_one()


def list_catalog(term=None):
    """Return every section with live seat availability (acceptance #1)."""
    counts = (
        select(
            Enrollment.course_id.label("course_id"),
            func.count(Enrollment.id).label("enrolled"),
        )
        .where(Enrollment.status == ENROLLMENT_STATUS_ACTIVE)
        .group_by(Enrollment.course_id)
        .subquery()
    )

    query = (
        select(Course, func.coalesce(counts.c.enrolled, 0))
        .outerjoin(counts, counts.c.course_id == Course.id)
        .order_by(Course.term, Course.code, Course.section_code)
    )
    if term:
        query = query.where(Course.term == term)

    rows = db.session.execute(query).all()
    return [course.to_dict(int(enrolled)) for course, enrolled in rows]


def get_student_enrollments(student_id):
    """Return the student's Active enrollments and per-term counts."""
    student = db.session.get(Profile, student_id)
    if student is None:
        raise EnrollmentError(
            "STUDENT_NOT_FOUND", "Student not found.", 404
        )

    rows = db.session.execute(
        select(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Enrollment.student_id == student_id,
            Enrollment.status == ENROLLMENT_STATUS_ACTIVE,
        )
        .order_by(Course.term, Course.code, Course.section_code)
    ).all()

    counts_by_term = {}
    enrollments = []
    for enrollment, course in rows:
        counts_by_term[course.term] = counts_by_term.get(course.term, 0) + 1
        enrollments.append(_enrollment_dict(enrollment, course))

    return {
        "studentId": student_id,
        "limit": MAX_COURSES_PER_TERM,
        "countsByTerm": counts_by_term,
        "enrollments": enrollments,
    }


def _enrollment_dict(enrollment, course):
    return {
        "id": enrollment.id,
        "courseId": course.id,
        "code": course.code,
        "title": course.title,
        "sectionCode": course.section_code,
        "term": course.term,
        "status": enrollment.status,
        "enrolledAt": (
            enrollment.enrolled_at.isoformat()
            if enrollment.enrolled_at
            else None
        ),
    }


def enroll_student(student_id, course_id):
    """Enroll the student in the section, atomically.

    Returns a dict describing the new enrollment, the section's updated
    capacity and the student's updated count. Raises EnrollmentError (after
    rolling back) if any rule fails, leaving the database unchanged.
    """
    try:
        # 1. Lock the student row (always first - see module docstring).
        student = db.session.execute(
            select(Profile)
            .where(Profile.institutional_id == student_id)
            .with_for_update()
        ).scalar_one_or_none()

        if student is None:
            raise EnrollmentError(
                "STUDENT_NOT_FOUND", "Student not found.", 404
            )
        if student.role != "Student":
            raise EnrollmentError(
                "FORBIDDEN_ROLE",
                "Only students can self-enroll in courses.",
                403,
            )

        # 2. Lock the section row (always second).
        course = db.session.execute(
            select(Course).where(Course.id == course_id).with_for_update()
        ).scalar_one_or_none()

        if course is None:
            raise EnrollmentError(
                "COURSE_NOT_FOUND", "Course section not found.", 404
            )

        # 3. Rules. Both locks are held, so these counts cannot be changed
        #    underneath us by another enrollment request.
        already = db.session.execute(
            select(Enrollment.id).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.status == ENROLLMENT_STATUS_ACTIVE,
            )
        ).first()
        if already is not None:
            raise EnrollmentError(
                "ALREADY_ENROLLED",
                "You are already enrolled in this section.",
                409,
            )

        if course.status != COURSE_STATUS_OPEN:
            raise EnrollmentError(
                "SECTION_CLOSED",
                "This section is closed for enrollment.",
                409,
            )

        current_count = _term_count(student_id, course.term)
        if current_count >= MAX_COURSES_PER_TERM:
            raise EnrollmentError(
                "ENROLLMENT_LIMIT_REACHED",
                f"You can enroll in at most {MAX_COURSES_PER_TERM} courses "
                f"per term.",
                409,
            )

        enrolled = _enrolled_count(course_id)
        if enrolled >= course.capacity_limit:
            raise EnrollmentError(
                "SECTION_FULL", "This section is full.", 409
            )

        # 4. Create the enrollment; seat availability is derived, so adding
        #    this row is what "reserves" the seat. Commit releases the locks.
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=ENROLLMENT_STATUS_ACTIVE,
        )
        db.session.add(enrollment)
        db.session.commit()

    except EnrollmentError:
        db.session.rollback()
        raise
    except IntegrityError:
        # Safety net: the unique constraint caught a duplicate that slipped
        # past the check (should not happen while the locks are held).
        db.session.rollback()
        raise EnrollmentError(
            "ALREADY_ENROLLED",
            "You are already enrolled in this section.",
            409,
        )
    except Exception:
        db.session.rollback()
        raise

    # Read back fresh values for the response (new transaction).
    course = db.session.get(Course, course_id)
    enrollment = db.session.get(Enrollment, enrollment.id)
    return {
        "enrollment": _enrollment_dict(enrollment, course),
        "course": course.to_dict(_enrolled_count(course_id)),
        "enrollmentSummary": {
            "term": course.term,
            "count": _term_count(student_id, course.term),
            "limit": MAX_COURSES_PER_TERM,
        },
    }
