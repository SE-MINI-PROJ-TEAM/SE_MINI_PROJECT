from app.core.timeutil import utcnow
from app.extensions import db


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"
    __table_args__ = (
        db.UniqueConstraint("session_id", "student_id", name="uq_session_student"),
        db.Index("ix_attendance_student_session", "student_id", "session_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("schedule_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_present = db.Column(db.Boolean, nullable=False)
    marked_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"))
