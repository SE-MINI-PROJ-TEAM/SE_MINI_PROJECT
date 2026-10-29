from sqlalchemy import event

from app.core.timeutil import utcnow
from app.extensions import db


class AuditLog(db.Model):
    """Append-only administrative audit trail. Updates and deletes are rejected at the ORM layer."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(60), nullable=False, index=True)
    target_type = db.Column(db.String(40))
    target_id = db.Column(db.String(40))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    actor = db.relationship("User", foreign_keys=[actor_id])


@event.listens_for(AuditLog, "before_update")
def _block_audit_update(mapper, connection, target):
    raise PermissionError("Audit log entries are immutable.")


@event.listens_for(AuditLog, "before_delete")
def _block_audit_delete(mapper, connection, target):
    raise PermissionError("Audit log entries are immutable.")
