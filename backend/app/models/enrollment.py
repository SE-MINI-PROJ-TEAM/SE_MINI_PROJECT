from app.core.constants import ENROLLMENT_ENROLLED, GRADE_STATES
from app.core.timeutil import utcnow
from app.extensions import db


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=ENROLLMENT_ENROLLED)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    # Grade summary: authoritative lifecycle state for the whole enrollment (GradeRecord rows mirror it).
    grade_state = db.Column(db.Enum(*GRADE_STATES, name="grade_state"), nullable=True, index=True)
    weighted_total = db.Column(db.Numeric(6, 2), nullable=True)

    student = db.relationship("User", foreign_keys=[student_id])
    course = db.relationship("Course")
