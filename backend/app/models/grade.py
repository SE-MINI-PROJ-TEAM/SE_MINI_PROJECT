from app.core.constants import DISPUTE_OPEN, GRADE_STATES
from app.core.timeutil import utcnow
from app.extensions import db


class GradeRecord(db.Model):
    __tablename__ = "grade_records"
    __table_args__ = (db.UniqueConstraint("enrollment_id", "rubric_id", name="uq_enrollment_rubric"),)

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubric_components.id", ondelete="CASCADE"), nullable=False)
    numeric_score = db.Column(db.Numeric(5, 2), nullable=False)
    state = db.Column(db.Enum(*GRADE_STATES, name="grade_record_state"), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class GradeDispute(db.Model):
    __tablename__ = "grade_disputes"

    id = db.Column(db.Integer, primary_key=True)
    # UNIQUE: a grade can be disputed only once, even under concurrent requests.
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=DISPUTE_OPEN, index=True)
    previous_total = db.Column(db.Numeric(6, 2))
    resolution_note = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    filed_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolved_at = db.Column(db.DateTime)

    enrollment = db.relationship("Enrollment")
    student = db.relationship("User", foreign_keys=[student_id])
