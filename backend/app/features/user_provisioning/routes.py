from flask import Blueprint, jsonify

from app.core.constants import ROLE_ADMIN
from app.core.security import auth_required, current_user
from app.core.validation import json_body

from . import service

bp = Blueprint("user_provisioning", __name__)


@bp.post("/users")
@auth_required(ROLE_ADMIN)
def create_user():
    user, temporary_password = service.create_user(current_user(), json_body())
    return (
        jsonify(
            {
                "status": "success",
                "user": user.to_dict(),
                # Shown exactly once on the confirmation screen; only the bcrypt hash is stored.
                "temporary_password": temporary_password,
            }
        ),
        201,
    )
