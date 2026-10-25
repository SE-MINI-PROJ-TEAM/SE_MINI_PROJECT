from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Profile(db.Model):
    __tablename__ = "profiles"

    institutional_id = db.Column(db.String(50), primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)
    personal_email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    is_temporary_password = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "institutionalId": self.institutional_id,
            "role": self.role,
            "name": self.name or "",
            "phone": self.phone or "",
            "emergencyContact": self.emergency_contact or "",
            "personalEmail": self.personal_email or "",
            "isTemporaryPassword": self.is_temporary_password,
            "isActive": self.is_active,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.String(50), nullable=False)
    target_user_id = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "adminId": self.admin_id,
            "targetUserId": self.target_user_id,
            "action": self.action,
            "details": self.details or "",
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
        }