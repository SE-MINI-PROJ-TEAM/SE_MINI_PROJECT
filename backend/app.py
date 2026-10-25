import logging
import os
import re
import secrets
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

from modules.auth.models import db, Profile, AuditLog
from modules.courses import models as course_models  # noqa: F401  (registers tables)
from modules.courses.enrollment_service import (
    EnrollmentError,
    enroll_student,
    get_student_enrollments,
    list_catalog,
)
from modules.courses.identity import get_authenticated_student_id

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = Flask(__name__)
CORS(app)

# --- Configure Dedicated Audit Logger in backend/logs/ ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

audit_file_path = LOG_DIR / "audit.log"
audit_logger = logging.getLogger("audit_logger")
audit_logger.setLevel(logging.INFO)

if not audit_logger.handlers:
    file_handler = logging.FileHandler(audit_file_path, encoding="utf-8")
    formatter = logging.Formatter(
        "[%(asctime)s] AUDIT: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)

# --- Dynamic Database URL Resolution (Zero Hardcoded DB Credentials) ---
DB_DIALECT = os.environ.get("DB_DIALECT", "sqlite")
DB_NAME = os.environ.get("DB_NAME", "student_records")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")

default_db_url = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    if DB_DIALECT == "mysql"
    else f"sqlite:///{BASE_DIR / f'{DB_NAME}.db'}"
)

database_url = os.environ.get("DATABASE_URL", default_db_url)

if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
    db_filename = database_url.replace("sqlite:///", "")
    database_url = f"sqlite:///{BASE_DIR / db_filename}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["ALLOW_INSECURE_DEV_IDENTITY"] = (
    os.environ.get("ALLOW_INSECURE_DEV_IDENTITY", "false").strip().lower() == "true"
)

db.init_app(app)


def valid_phone(phone):
    return bool(re.fullmatch(r"\+?[0-9\s()-]{7,20}", phone))


def valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


# ---------------------------------------------------------------------------
# US-03: Profile View & Contact Details Update Endpoints
# ---------------------------------------------------------------------------

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
        return jsonify({"error": "Only contact details can be updated."}), 400

    phone = data.get("phone", profile.phone)
    emergency = data.get("emergencyContact", profile.emergency_contact)
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


# ---------------------------------------------------------------------------
# US-01: Administrative User Provisioning Endpoint
# ---------------------------------------------------------------------------

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

    if db.session.get(Profile, inst_id):
        return jsonify({"error": f"Institutional ID '{inst_id}' already exists."}), 409

    if Profile.query.filter_by(personal_email=email).first():
        return jsonify({"error": f"Email address '{email}' is already in use."}), 409

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

    audit_logger.info(
        f"PROVISION_USER: Admin [ADM001] provisioned new user [{inst_id}] with role [{role}]."
    )

    return jsonify({
        "message": "User provisioned successfully.",
        "user": new_user.to_dict(),
        "temporaryPassword": temp_password,
    }), 201


# ---------------------------------------------------------------------------
# US-04: Admin Account Status & Role Management Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/admin/users", methods=["GET"])
def get_all_users():
    search_query = request.args.get("search", "").strip().lower()

    query = Profile.query
    if search_query:
        query = query.filter(
            (Profile.institutional_id.ilike(f"%{search_query}%"))
            | (Profile.name.ilike(f"%{search_query}%"))
            | (Profile.personal_email.ilike(f"%{search_query}%"))
            | (Profile.role.ilike(f"%{search_query}%"))
        )

    users = query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@app.route("/api/admin/users/<institutional_id>/status", methods=["PUT"])
def update_user_status(institutional_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON object is required."}), 400

    target_user = db.session.get(Profile, institutional_id)
    if not target_user:
        return jsonify({"error": f"User '{institutional_id}' not found."}), 404

    is_active = data.get("isActive")
    new_role = data.get("role")
    admin_id = data.get("adminId", "ADM001")

    if is_active is None and not new_role:
        return jsonify({"error": "No update fields provided ('isActive' or 'role')."}), 400

    changes = []

    if is_active is not None and isinstance(is_active, bool):
        if target_user.is_active != is_active:
            target_user.is_active = is_active
            status_str = "ACTIVE" if is_active else "INACTIVE (JWT Sessions Revoked)"
            changes.append(f"Status changed to {status_str}")

    if new_role:
        valid_roles = {"Student", "Faculty", "Admin"}
        if new_role not in valid_roles:
            return jsonify({"error": f"Role must be one of {sorted(list(valid_roles))}."}), 400
        if target_user.role != new_role:
            changes.append(f"Role updated from '{target_user.role}' to '{new_role}'")
            target_user.role = new_role

    if not changes:
        return jsonify({"message": "No changes made.", "user": target_user.to_dict()}), 200

    details_str = "; ".join(changes)

    audit_entry = AuditLog(
        admin_id=admin_id,
        target_user_id=target_user.institutional_id,
        action="ACCOUNT_METADATA_UPDATE",
        details=details_str,
    )

    try:
        db.session.add(audit_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Account status update failed")
        return jsonify({"error": "Could not update user account status."}), 500

    audit_logger.info(
        f"UPDATE_ACCOUNT: Admin [{admin_id}] updated target user [{target_user.institutional_id}]: {details_str}"
    )

    return jsonify({
        "message": f"User {target_user.institutional_id} updated successfully.",
        "user": target_user.to_dict(),
        "auditLog": audit_entry.to_dict(),
    }), 200


@app.route("/api/admin/audit-logs", methods=["GET"])
@app.route("/api/admin/users/audit-logs", methods=["GET"])
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify({"auditLogs": [l.to_dict() for l in logs]}), 200


# ---------------------------------------------------------------------------
# US-06 / SYS-F-006: Course Catalog and Student Self-Enrollment Endpoints
# ---------------------------------------------------------------------------

def api_error(code, message, status):
    return jsonify({"error": message, "code": code}), status


@app.route("/api/v1/courses", methods=["GET"])
def get_course_catalog():
    term = request.args.get("term", "").strip() or None
    return jsonify({"courses": list_catalog(term)}), 200


@app.route("/api/v1/enrollments/me", methods=["GET"])
def get_my_enrollments():
    student_id = get_authenticated_student_id()
    if student_id is None:
        return api_error("UNAUTHENTICATED", "Authentication required.", 401)

    try:
        return jsonify(get_student_enrollments(student_id)), 200
    except EnrollmentError as err:
        return api_error(err.code, err.message, err.status)


@app.route("/api/v1/enrollments", methods=["POST"])
def create_enrollment():
    student_id = get_authenticated_student_id()
    if student_id is None:
        return api_error("UNAUTHENTICATED", "Authentication required.", 401)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("INVALID_REQUEST", "A valid JSON object is required.", 400)

    if set(data.keys()) != {"courseId"}:
        return api_error(
            "INVALID_REQUEST",
            "Request must contain only 'courseId'.",
            400,
        )

    course_id = data["courseId"]
    if isinstance(course_id, bool) or not isinstance(course_id, int) or course_id <= 0:
        return api_error(
            "INVALID_REQUEST", "'courseId' must be a positive integer.", 400
        )

    try:
        result = enroll_student(student_id, course_id)
    except EnrollmentError as err:
        return api_error(err.code, err.message, err.status)
    except Exception:
        app.logger.exception("Enrollment failed")
        return api_error("INTERNAL_ERROR", "Could not complete the enrollment.", 500)

    result["message"] = "Enrollment confirmed."
    return jsonify(result), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)