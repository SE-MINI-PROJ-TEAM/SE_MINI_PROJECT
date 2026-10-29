from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN
from app.core.security import auth_required, current_user
from app.core.timeutil import to_iso
from app.core.validation import json_body, page_params, sanitize

from . import service

bp = Blueprint("account_management", __name__)


@bp.get("/users")
@auth_required(ROLE_ADMIN)
def list_users():
    page, per_page = page_params()
    result = service.search_users(
        sanitize(request.args.get("search")),
        request.args.get("role"),
        request.args.get("status"),
        page,
        per_page,
    )
    return jsonify(
        {
            "status": "success",
            "users": [u.to_dict() for u in result.items],
            "page": result.page,
            "pages": result.pages,
            "total": result.total,
        }
    )


@bp.patch("/users/<int:user_id>")
@auth_required(ROLE_ADMIN)
def update_user(user_id):
    user = service.update_user(current_user(), user_id, json_body())
    return jsonify({"status": "success", "user": user.to_dict()})


@bp.get("/admin/audit-logs")
@auth_required(ROLE_ADMIN)
def audit_logs():
    page, per_page = page_params(default_per_page=20)
    result = service.list_audit_logs(sanitize(request.args.get("action")), page, per_page)
    return jsonify(
        {
            "status": "success",
            "logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "actor": {"id": log.actor_id, "name": log.actor.full_name, "institutional_id": log.actor.institutional_id},
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "details": log.details,
                    "created_at": to_iso(log.created_at),
                }
                for log in result.items
            ],
            "page": result.page,
            "pages": result.pages,
            "total": result.total,
        }
    )
