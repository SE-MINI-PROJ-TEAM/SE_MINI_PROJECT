from sqlalchemy.exc import IntegrityError

from app.core.audit import log_action
from app.core.constants import AUDIT_USER_CREATED, ROLES
from app.core.errors import bad_request, conflict
from app.core.security import generate_temporary_password, hash_password
from app.core.validation import clean_text, valid_email
from app.extensions import db
from app.models import Profile, User


def create_user(actor, data):
    """Create an account with a generated temporary password. Returns (user, temporary_password)."""
    full_name = clean_text(data, "full_name", max_len=120, label="full name")
    email = clean_text(data, "email", max_len=255).lower()
    institutional_id = clean_text(data, "institutional_id", max_len=32, label="institutional ID").upper()
    role = data.get("role")

    if not valid_email(email):
        raise bad_request("Enter a valid email address.", "INVALID_EMAIL")
    if role not in ROLES:
        raise bad_request(f"Role must be one of: {', '.join(ROLES)}.", "INVALID_ROLE")

    if User.query.filter_by(institutional_id=institutional_id).first():
        raise conflict("A user with this institutional ID already exists.", "DUPLICATE_INSTITUTIONAL_ID")
    if User.query.filter_by(email=email).first():
        raise conflict("A user with this email already exists.", "DUPLICATE_EMAIL")

    temporary_password = generate_temporary_password()
    user = User(
        institutional_id=institutional_id,
        email=email,
        full_name=full_name,
        role=role,
        password_hash=hash_password(temporary_password),
        is_temporary_password=True,
        is_active=True,
    )
    user.profile = Profile()
    db.session.add(user)
    try:
        db.session.flush()
        log_action(
            actor.id, AUDIT_USER_CREATED, "User", user.id,
            {"institutional_id": institutional_id, "role": role},
        )
        db.session.commit()
    except IntegrityError:
        # Lost a race with a concurrent request creating the same email / ID.
        db.session.rollback()
        raise conflict("A user with this email or institutional ID already exists.", "DUPLICATE_USER")
    return user, temporary_password
