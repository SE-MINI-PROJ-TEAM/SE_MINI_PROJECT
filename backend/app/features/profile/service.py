from app.core.errors import bad_request, forbidden
from app.core.validation import clean_text, valid_email, valid_phone
from app.extensions import db
from app.models import Profile

EDITABLE_FIELDS = ("phone", "personal_email", "home_address", "emergency_contact")
READ_ONLY_FIELDS = ("institutional_id", "role", "email", "full_name", "id", "is_active")


def get_or_create_profile(user):
    if user.profile is None:
        user.profile = Profile()
        db.session.commit()
    return user.profile


def build_view(user):
    profile = get_or_create_profile(user)
    return {
        "institutional_id": user.institutional_id,
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        **profile.to_dict(),
    }


def update_profile(user, data):
    """Validate and persist editable contact fields. Administrative fields are rejected outright."""
    locked = [f for f in READ_ONLY_FIELDS if f in data]
    if locked:
        raise forbidden(
            f"These fields are managed by an administrator and cannot be changed: {', '.join(locked)}.",
            "READ_ONLY_FIELD",
        )

    phone = clean_text(data, "phone", required=False, max_len=32)
    personal_email = clean_text(data, "personal_email", required=False, max_len=255, label="personal email")
    home_address = clean_text(data, "home_address", required=False, max_len=255, label="home address")
    emergency_contact = clean_text(data, "emergency_contact", required=False, max_len=255, label="emergency contact")

    errors = {}
    if phone and not valid_phone(phone):
        errors["phone"] = "Enter a valid phone number (7-20 digits; optional +, spaces, dashes, brackets)."
    if personal_email and not valid_email(personal_email):
        errors["personal_email"] = "Enter a valid email address."
    if errors:
        raise bad_request("Some contact details are invalid.", "VALIDATION_FAILED", errors)

    profile = get_or_create_profile(user)
    profile.phone = phone or None
    profile.personal_email = personal_email.lower() or None
    profile.home_address = home_address or None
    profile.emergency_contact = emergency_contact or None
    db.session.commit()
    return build_view(user)
