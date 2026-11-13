from sqlalchemy import func

from app.core import grading
from app.core.audit import log_action
from app.core.constants import (
    AUDIT_DISPUTE_RESOLVED,
    DISPUTE_OPEN,
    DISPUTE_RESOLVED,
    GRADE_PUBLISHED,
    GRADE_UNDER_REVIEW,
    ROLE_FACULTY,
)
from app.core.db_retry import run_with_retry
from app.core.errors import ApiError, bad_request, forbidden, not_found
from app.core.timeutil import to_iso, utcnow
from app.core.validation import clean_text, to_int
from app.extensions import db
from app.models import Course, Enrollment, GradeDispute, User


# ------------------------------------------------------------------ student
def file_dispute(student, data):
    enrollment_id = to_int(data.get("enrollment_id"), "enrollment_id", minimum=1)
    reason = clean_text(data, "reason", min_len=10, max_len=1000, label="explanation")

    def attempt():
        enrollment = (
            Enrollment.query.filter_by(id=enrollment_id, student_id=student.id).with_for_update().first()
        )
        if enrollment is None:
            raise not_found("Enrollment not found.", "ENROLLMENT_NOT_FOUND")
        # Checked before the state: after a resolution the grade is Published again, but it is final.
        if GradeDispute.query.filter_by(enrollment_id=enrollment.id).first():
            raise ApiError(
                409, "ALREADY_DISPUTED",
                "This grade has already been disputed. A grade can be disputed only once.",
            )
        if enrollment.grade_state != GRADE_PUBLISHED:
            raise ApiError(409, "NOT_DISPUTABLE", "Only published grades can be disputed.")
        grading.set_state(enrollment, GRADE_UNDER_REVIEW)
        dispute = GradeDispute(
            enrollment_id=enrollment.id, student_id=student.id, reason=reason, previous_total=enrollment.weighted_total
        )
        db.session.add(dispute)
        db.session.commit()
        return dispute

    return run_with_retry(attempt)


def serialize(dispute, with_scores=False):
    enrollment = dispute.enrollment
    course = enrollment.course
    item = {
        "id": dispute.id,
        "status": dispute.status,
        "reason": dispute.reason,
        "filed_at": to_iso(dispute.filed_at),
        "resolved_at": to_iso(dispute.resolved_at),
        "resolution_note": dispute.resolution_note,
        "previous_total": float(dispute.previous_total) if dispute.previous_total is not None else None,
        "current_total": float(enrollment.weighted_total) if enrollment.weighted_total is not None else None,
        "enrollment_id": enrollment.id,
        "course": {"id": course.id, "code": course.code, "title": course.title, "section": course.section},
        "student": {"institutional_id": dispute.student.institutional_id, "full_name": dispute.student.full_name},
    }
    if with_scores:
        scores = grading.scores_for(enrollment.id)
        item["rubric"] = [
            {
                "id": c.id,
                "name": c.component_name,
                "weight": float(c.normalized_weight),
                "score": float(scores[c.id]) if c.id in scores else None,
            }
            for c in course.rubric
        ]
    return item


def my_disputes(student):
    rows = GradeDispute.query.filter_by(student_id=student.id).order_by(GradeDispute.filed_at.desc()).all()
    return [serialize(d) for d in rows]


# ------------------------------------------------------------ faculty/admin
def _scoped_query(user):
    query = GradeDispute.query.join(Enrollment, Enrollment.id == GradeDispute.enrollment_id).join(
        Course, Course.id == Enrollment.course_id
    )
    if user.role == ROLE_FACULTY:
        query = query.filter(Course.assigned_faculty_id == user.id)
    return query


def list_disputes(user, status):
    query = _scoped_query(user)
    if status in (DISPUTE_OPEN, DISPUTE_RESOLVED):
        query = query.filter(GradeDispute.status == status)
    return [serialize(d, with_scores=True) for d in query.order_by(GradeDispute.filed_at.desc()).limit(100).all()]


def pending_count(user):
    return _scoped_query(user).filter(GradeDispute.status == DISPUTE_OPEN).with_entities(func.count(GradeDispute.id)).scalar()


def resolve(user, dispute_id, data):
    note = clean_text(data, "resolution_note", max_len=1000, label="resolution note")

    def attempt():
        dispute = db.session.execute(
            db.select(GradeDispute).where(GradeDispute.id == dispute_id).with_for_update()
        ).scalar_one_or_none()
        if dispute is None:
            raise not_found("Dispute not found.", "DISPUTE_NOT_FOUND")
        enrollment = dispute.enrollment
        course = enrollment.course
        if user.role == ROLE_FACULTY and course.assigned_faculty_id != user.id:
            raise forbidden("This course section is not assigned to you.", "NOT_ASSIGNED")
        if dispute.status != DISPUTE_OPEN or enrollment.grade_state != GRADE_UNDER_REVIEW:
            raise ApiError(409, "ALREADY_RESOLVED", "This dispute has already been resolved.")

        parsed = grading.parse_scores(data.get("rubric_scores", []), course.rubric)
        if parsed:
            grading.upsert_scores(enrollment, parsed, GRADE_UNDER_REVIEW)
            db.session.flush()
        try:
            total = grading.compute_weighted_total(grading.scores_for(enrollment.id), course.rubric)
        except ValueError as missing:
            raise bad_request(f"Score missing for rubric component '{missing}'.", "INCOMPLETE_SCORES")

        previous = enrollment.weighted_total
        grading.set_state(enrollment, GRADE_PUBLISHED)  # Under Review -> Published (re-publication)
        enrollment.weighted_total = total
        dispute.status = DISPUTE_RESOLVED
        dispute.resolution_note = note
        dispute.resolved_by = user.id
        dispute.resolved_at = utcnow()
        log_action(
            user.id, AUDIT_DISPUTE_RESOLVED, "GradeDispute", dispute.id,
            {
                "course": f"{course.code}-{course.section}",
                "student_id": dispute.student.institutional_id,
                "old_total": float(previous) if previous is not None else None,
                "new_total": float(total),
            },
        )
        db.session.commit()
        return dispute

    return run_with_retry(attempt)
