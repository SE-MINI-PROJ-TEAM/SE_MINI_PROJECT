from app.core.constants import ROLES
from app.core.timeutil import to_iso, utcnow
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    institutional_id = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(*ROLES, name="user_role"), nullable=False, index=True)
    password_hash = db.Column(db.String(100), nullable=False)
    is_temporary_password = db.Column(db.Boolean, nullable=False, default=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime)

    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "institutional_id": self.institutional_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_temporary_password": self.is_temporary_password,
            "created_at": to_iso(self.created_at),
            "last_login_at": to_iso(self.last_login_at),
        }


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = db.Column(db.String(32))
    personal_email = db.Column(db.String(255))
    home_address = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="profile")

    def to_dict(self):
        return {
            "phone": self.phone or "",
            "personal_email": self.personal_email or "",
            "home_address": self.home_address or "",
            "emergency_contact": self.emergency_contact or "",
            "updated_at": to_iso(self.updated_at),
        }
