from app.core.errors import ApiError, bad_request, unauthorized
from app.core.security import hash_password, validate_password_strength, verify_password
from app.extensions import db


def change_password(user, current_password, new_password):
    """Validate and persist a new bcrypt-hashed password, clearing the temporary-credential flag."""
    if not isinstance(current_password, str) or not verify_password(current_password, user.password_hash):
        raise unauthorized("Current password is incorrect.", "INVALID_CREDENTIALS")
    if not isinstance(new_password, str):
        raise bad_request("A new password is required.", "MISSING_FIELD")

    problems = validate_password_strength(new_password)
    if problems:
        raise ApiError(400, "WEAK_PASSWORD", "New password does not meet the complexity rules.", problems)
    if new_password == current_password:
        raise bad_request("New password must differ from the current password.", "PASSWORD_REUSED")

    user.password_hash = hash_password(new_password)
    user.is_temporary_password = False
    db.session.commit()
    return user
