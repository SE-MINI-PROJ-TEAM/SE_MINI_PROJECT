from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.core.errors import register_error_handlers
from app.core.transport import init_transport
from app.extensions import db, limiter
from app.features import register_features


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config.get("TESTING") and len(app.config["SECRET_KEY"].encode()) < 32:
        # JWTs are signed with this key; HS256 needs >= 256 bits (RFC 7518 section 3.2).
        raise RuntimeError("SECRET_KEY must be at least 32 bytes long - set a long random value in backend/.env")

    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    limiter.init_app(app)
    init_transport(app)
    register_error_handlers(app)

    from app import models  # noqa: F401  (register tables with SQLAlchemy metadata)

    register_features(app)

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "success", "features": app.config["LOADED_FEATURES"]})

    return app
