from flask import Blueprint, Response, jsonify

from app.core.constants import ROLE_ADMIN
from app.core.security import auth_required
from app.core.timeutil import utcnow

from . import service

bp = Blueprint("admin_metrics", __name__)


@bp.get("/admin/metrics")
@auth_required(ROLE_ADMIN)
def metrics():
    return jsonify({"status": "success", "metrics": service.overview()})


@bp.get("/admin/metrics/export.csv")
@auth_required(ROLE_ADMIN)
def export_csv():
    filename = f"system-metrics-{utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return Response(
        service.build_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
