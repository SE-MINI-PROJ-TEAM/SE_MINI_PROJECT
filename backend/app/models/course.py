from app.core.constants import RUBRIC_CATEGORIES
from app.core.timeutil import utcnow
from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = (db.UniqueConstraint("code", "section", "term", name="uq_course_section_term"),)

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    section = db.Column(db.String(10), nullable=False, default="A")
    term = db.Column(db.String(30), nullable=False, index=True)
    credits = db.Column(db.Integer, nullable=False, default=3)
    capacity = db.Column(db.Integer, nullable=False)
    assigned_faculty_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    faculty = db.relationship("User", foreign_keys=[assigned_faculty_id])
    rubric = db.relationship(
        "RubricComponent", back_populates="course", cascade="all, delete-orphan", order_by="RubricComponent.id"
    )


class RubricComponent(db.Model):
    __tablename__ = "rubric_components"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    component_name = db.Column(db.String(80), nullable=False)
    category = db.Column(db.Enum(*RUBRIC_CATEGORIES, name="rubric_category"), nullable=False, default="Assignments")
    raw_weight = db.Column(db.Numeric(8, 2), nullable=False)
    normalized_weight = db.Column(db.Numeric(6, 2), nullable=False)

    course = db.relationship("Course", back_populates="rubric")
