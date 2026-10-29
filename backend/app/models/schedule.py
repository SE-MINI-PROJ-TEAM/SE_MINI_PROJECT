from app.extensions import db


class ScheduleSession(db.Model):
    __tablename__ = "schedule_sessions"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    room_number = db.Column(db.String(40), nullable=False)

    course = db.relationship("Course")
