
import os
import re
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

from models import db, Profile
load_dotenv()
app = Flask(__name__)
CORS(app)

# Configure MySQL through an environment variable.
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Configure it in src/profile/backend/.env"
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
