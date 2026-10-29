from app.extensions import db
from app.models import AuditLog


def log_action(actor_id, action, target_type=None, target_id=None, details=None):
    """Queue an immutable audit entry in the current transaction (caller commits)."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details=details or {},
    )
    db.session.add(entry)
    return entry
