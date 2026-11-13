from flask import Blueprint, jsonify, request

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY, ROLE_STUDENT
from app.core.security import auth_required, current_user
from app.core.validation import json_body, sanitize

from . import service

bp = Blueprint("regrade_disputes", __name__)


@bp.post("/disputes")
@auth_required(ROLE_STUDENT)
def file_dispute():
    dispute = service.file_dispute(current_user(), json_body())
    return (
        jsonify(
            {
                "status": "success",
                "message": "Regrade request filed. Your grade is now Under Review.",
                "dispute": service.serialize(dispute),
            }
        ),
        201,
    )


@bp.get("/disputes/mine")
@auth_required(ROLE_STUDENT)
def my_disputes():
    return jsonify({"status": "success", "disputes": service.my_disputes(current_user())})


@bp.get("/disputes")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def list_disputes():
    return jsonify(
        {"status": "success", "disputes": service.list_disputes(current_user(), sanitize(request.args.get("status")))}
    )


@bp.get("/disputes/pending-count")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def pending_count():
    return jsonify({"status": "success", "count": service.pending_count(current_user())})


@bp.post("/disputes/<int:dispute_id>/resolve")
@auth_required(ROLE_FACULTY, ROLE_ADMIN)
def resolve(dispute_id):
    dispute = service.resolve(current_user(), dispute_id, json_body())
    return jsonify(
        {
            "status": "success",
            "message": "Dispute resolved and the grade has been re-published.",
            "dispute": service.serialize(dispute),
        }
    )
