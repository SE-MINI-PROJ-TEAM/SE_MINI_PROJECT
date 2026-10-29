from sqlalchemy import or_

from app.core.audit import log_action
from app.core.constants import AUDIT_USER_ROLE_CHANGED, AUDIT_USER_STATUS_CHANGED, ROLES
from app.core.errors import bad_request, not_found
from app.extensions import db
from app.models import AuditLog, User


def search_users(search, role, status, page, per_page):
    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(User.full_name.like(like), User.email.like(like), User.institutional_id.like(like))
        )
    if role in ROLES:
        query = query.filter(User.role == role)
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))
    return query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)


def update_user(actor, user_id, data):
    user = db.session.get(User, user_id)
    if user is None:
        raise not_found("User not found.", "USER_NOT_FOUND")

    changed = False
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            raise bad_request("is_active must be true or false.", "INVALID_FIELD")
        if user.id == actor.id and not data["is_active"]:
            raise bad_request("You cannot deactivate your own account.", "SELF_DEACTIVATION")
        if data["is_active"] != user.is_active:
            log_action(
                actor.id, AUDIT_USER_STATUS_CHANGED, "User", user.id,
                {"old": "Active" if user.is_active else "Inactive", "new": "Active" if data["is_active"] else "Inactive",
                 "institutional_id": user.institutional_id},
            )
            # Sessions are validated against this flag on every request, so deactivation revokes JWTs immediately.
            user.is_active = data["is_active"]
            changed = True

    if "role" in data:
        if data["role"] not in ROLES:
            raise bad_request(f"Role must be one of: {', '.join(ROLES)}.", "INVALID_ROLE")
        if user.id == actor.id and data["role"] != user.role:
            raise bad_request("You cannot change your own role.", "SELF_ROLE_CHANGE")
        if data["role"] != user.role:
            log_action(
                actor.id, AUDIT_USER_ROLE_CHANGED, "User", user.id,
                {"old": user.role, "new": data["role"], "institutional_id": user.institutional_id},
            )
            user.role = data["role"]
            changed = True

    if not changed and not ({"is_active", "role"} & set(data)):
        raise bad_request("Nothing to update.", "NOTHING_TO_UPDATE")
    db.session.commit()
    return user


def list_audit_logs(action, page, per_page):
    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
