from sqlalchemy import func

from app.core import grading
from app.core.access import ensure_course_access, get_course_or_404
from app.core.audit import log_action
from app.core.constants import (
    AUDIT_GRADES_PUBLISHED,
    DISPUTE_OPEN,
    ENROLLMENT_ENROLLED,
    GRADE_DRAFT,
    GRADE_PUBLISHED,
    GRADE_SUBMITTED,
    STUDENT_VISIBLE_GRADE_STATES,
)
from app.core.db_retry import run_with_retry
from app.core.errors import ApiError, bad_request
from app.core.timeutil import to_iso
from app.core.validation import to_int
from app.extensions import db
from app.models import Course, Enrollment, GradeDispute, GradeRecord, User


def submit_course(course_id, faculty):
    """Submit every complete Draft in the section; incomplete ones are reported and left in Draft."""

    def attempt():
        course = get_course_or_404(course_id)
        ensure_course_access(course, faculty)
        enrollments = (
            db.session.query(Enrollment, User)
            .join(User, User.id == Enrollment.student_id)
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.status == ENROLLMENT_ENROLLED,
                Enrollment.grade_state == GRADE_DRAFT,
            )
            .order_by(Enrollment.id)
            .with_for_update()
            .all()
        )
        submitted, skipped = 0, []
        for enrollment, student in enrollments:
            try:
                grading.submit_enrollment(enrollment, course.rubric)
                submitted += 1
            except ApiError as err:
                skipped.append({"student_id": student.institutional_id, "reason": err.message})
        db.session.commit()
        return submitted, skipped

    return run_with_retry(attempt)


def publication_queue():
    rows = (
        db.session.query(Course, func.count(Enrollment.id))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.grade_state == GRADE_SUBMITTED)
        .group_by(Course.id)
        .order_by(Course.code, Course.section)
        .all()
    )
    return [
        {
            "course_id": c.id,
            "code": c.code,
            "title": c.title,
            "section": c.section,
            "term": c.term,
            "faculty_name": c.faculty.full_name if c.faculty else None,
            "submitted_count": n,
        }
        for c, n in rows
    ]


def publish(admin, course_ids):
    if not isinstance(course_ids, list) or not course_ids:
        raise bad_request("Select at least one course to publish.", "INVALID_FIELD")
    ids = sorted({to_int(i, "course_id", minimum=1) for i in course_ids})

    def attempt():
        published = {}
        for course_id in ids:
            course = get_course_or_404(course_id)
            enrollment_ids = [
                row.id
                for row in Enrollment.query.filter_by(course_id=course.id, grade_state=GRADE_SUBMITTED)
                .with_for_update()
                .order_by(Enrollment.id)
                .all()
            ]
            if not enrollment_ids:
                continue
            Enrollment.query.filter(Enrollment.id.in_(enrollment_ids)).update(
                {"grade_state": GRADE_PUBLISHED}, synchronize_session=False
            )
            GradeRecord.query.filter(GradeRecord.enrollment_id.in_(enrollment_ids)).update(
                {"state": GRADE_PUBLISHED}, synchronize_session=False
            )
            published[course.id] = len(enrollment_ids)
            log_action(
                admin.id, AUDIT_GRADES_PUBLISHED, "Course", course.id,
                {"course": f"{course.code}-{course.section}", "grades_published": len(enrollment_ids)},
            )
        if not published:
            raise bad_request("None of the selected courses have submitted grades.", "NOTHING_TO_PUBLISH")
        db.session.commit()
        return published

    return run_with_retry(attempt)


def student_grades(student_id):
    """Marks are only exposed once published; Draft / Submitted show as 'Pending' with no numbers."""
    rows = (
        db.session.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id, Enrollment.status == ENROLLMENT_ENROLLED)
        .order_by(Course.code)
        .all()
    )
    visible = [e.id for e, _ in rows if e.grade_state in STUDENT_VISIBLE_GRADE_STATES]
    scores = {}
    if visible:
        for record in GradeRecord.query.filter(GradeRecord.enrollment_id.in_(visible)).all():
            scores.setdefault(record.enrollment_id, {})[record.rubric_id] = float(record.numeric_score)
    disputes = {}
    if visible:
        for d in (
            GradeDispute.query.filter(GradeDispute.enrollment_id.in_(visible))
            .order_by(GradeDispute.filed_at)
            .all()
        ):
            disputes[d.enrollment_id] = d  # keeps the most recent

    result = []
    for enrollment, course in rows:
        item = {
            "enrollment_id": enrollment.id,
            "course_id": course.id,
            "code": course.code,
            "title": course.title,
            "section": course.section,
            "credits": course.credits,
            "state": enrollment.grade_state if enrollment.grade_state in STUDENT_VISIBLE_GRADE_STATES else "Pending",
        }
        if enrollment.grade_state in STUDENT_VISIBLE_GRADE_STATES:
            own = scores.get(enrollment.id, {})
            total = float(enrollment.weighted_total)
            item.update(
                weighted_total=total,
                letter=grading.letter_for(total),
                components=[
                    {
                        "name": c.component_name,
                        "category": c.category,
                        "weight": float(c.normalized_weight),
                        "score": own.get(c.id),
                    }
                    for c in course.rubric
                ],
            )
            dispute = disputes.get(enrollment.id)
            item["can_dispute"] = enrollment.grade_state == GRADE_PUBLISHED and dispute is None
            if dispute:
                item["dispute"] = {
                    "status": dispute.status,
                    "reason": dispute.reason,
                    "filed_at": to_iso(dispute.filed_at),
                    "resolution_note": dispute.resolution_note,
                    "open": dispute.status == DISPUTE_OPEN,
                }
        result.append(item)
    return result
