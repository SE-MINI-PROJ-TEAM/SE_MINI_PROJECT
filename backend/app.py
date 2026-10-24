import os
import re
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

import secrets
from modules.auth.models import db, Profile

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = Flask(__name__)
CORS(app)

# Configure database URL with a default fallback if .env is missing
database_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Configure it in backend/.env"
    )

# Convert relative SQLite URLs into absolute paths targeting the backend directory
if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
    db_filename = database_url.replace("sqlite:///", "")
    database_url = f"sqlite:///{BASE_DIR / db_filename}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def valid_phone(phone):
    return bool(re.fullmatch(r"\+?[0-9\s()-]{7,20}", phone))


def valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


@app.route("/api/profile/<institutional_id>", methods=["GET"])
def get_profile(institutional_id):
    profile = db.session.get(Profile, institutional_id)

    if profile is None:
        return jsonify({"error": "Profile not found."}), 404

    return jsonify(profile.to_dict()), 200


@app.route("/api/profile/<institutional_id>", methods=["PUT"])
def update_profile(institutional_id):
    profile = db.session.get(Profile, institutional_id)

    if profile is None:
        return jsonify({"error": "Profile not found."}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON object is required."}), 400

    allowed_fields = {"phone", "emergencyContact", "personalEmail"}

    if not set(data.keys()).issubset(allowed_fields):
        return jsonify({
            "error": "Only contact details can be updated."
        }), 400

    phone = data.get("phone", profile.phone)
    emergency = data.get(
        "emergencyContact", profile.emergency_contact
    )
    email = data.get("personalEmail", profile.personal_email)

    if not all(isinstance(value, str) for value in [phone, emergency, email]):
        return jsonify({"error": "Contact details must be text."}), 400

    phone = phone.strip()
    emergency = emergency.strip()
    email = email.strip()

    if not valid_phone(phone):
        return jsonify({"error": "Invalid phone number."}), 400

    if not valid_phone(emergency):
        return jsonify({"error": "Invalid emergency contact number."}), 400

    if not valid_email(email):
        return jsonify({"error": "Invalid personal email address."}), 400

    profile.phone = phone
    profile.emergency_contact = emergency
    profile.personal_email = email

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Profile update failed")
        return jsonify({"error": "Could not save profile changes."}), 500

    return jsonify({
        "message": "Profile updated successfully.",
        "profile": profile.to_dict(),
    }), 200

@app.route("/api/admin/users", methods=["POST"])
def provision_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON object is required."}), 400

    required_fields = ["institutionalId", "name", "personalEmail", "role"]
    for field in required_fields:
        if not data.get(field) or not str(data[field]).strip():
            return jsonify({"error": f"Field '{field}' is required."}), 400

    inst_id = data["institutionalId"].strip()
    name = data["name"].strip()
    email = data["personalEmail"].strip()
    role = data["role"].strip()

    valid_roles = {"Student", "Faculty", "Admin"}
    if role not in valid_roles:
        return jsonify({"error": f"Role must be one of {sorted(list(valid_roles))}."}), 400

    if not valid_email(email):
        return jsonify({"error": "Invalid personal email address."}), 400

    # Check for duplicate Institutional ID -> 409 Conflict
    if db.session.get(Profile, inst_id):
        return jsonify({"error": f"Institutional ID '{inst_id}' already exists."}), 409

    # Check for duplicate Personal Email -> 409 Conflict
    if Profile.query.filter_by(personal_email=email).first():
        return jsonify({"error": f"Email address '{email}' is already in use."}), 409

    # Secure temporary password generation
    temp_password = secrets.token_urlsafe(10)

    new_user = Profile(
        institutional_id=inst_id,
        name=name,
        personal_email=email,
        role=role,
        is_temporary_password=True,
    )
    new_user.set_password(temp_password)

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("User provisioning failed")
        return jsonify({"error": "Could not provision user account."}), 500

    return jsonify({
        "message": "User provisioned successfully.",
        "user": new_user.to_dict(),
        "temporaryPassword": temp_password,
    }), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed default demo user if missing
        if not db.session.get(Profile, "STU001"):
            db.session.add(
                Profile(
                    institutional_id="STU001",
                    role="Student",
                    name="Demo Student",
                    phone="9876543210",
                    emergency_contact="9876501234",
                    personal_email="student@example.com",
                )
            )
            db.session.commit()
    app.run(debug=True, port=5000)