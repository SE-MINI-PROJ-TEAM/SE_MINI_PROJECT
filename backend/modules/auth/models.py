
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Profile(db.Model):
    __tablename__ = "profiles"

    institutional_id = db.Column(
        db.String(50), primary_key=True
    )
    role = db.Column(
        db.String(20), nullable=False
    )
    name = db.Column(
        db.String(100), nullable=False, default=""
    )
    phone = db.Column(
        db.String(20), nullable=False
    )
    emergency_contact = db.Column(
        db.String(20), nullable=False
    )
    personal_email = db.Column(
        db.String(255), nullable=False
    )

    def to_dict(self):
        return {
            "institutionalId": self.institutional_id,
            "role": self.role,
            "name": self.name,
            "phone": self.phone,
            "emergencyContact": self.emergency_contact,
            "personalEmail": self.personal_email,
        }
