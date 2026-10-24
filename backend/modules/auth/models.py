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
        }
