"""Transport hardening + structured request logging (PRJ-SR-001, SAD 4.3).

TLS 1.3 itself is terminated by the HTTPS listener / reverse proxy (see ``scripts/gen_dev_cert.py`` and
``run.py --https``). This module enforces the application side: HTTP->HTTPS redirect, HSTS, secure cookies
and defensive response headers. Logs are JSON and never contain passwords, tokens or contact details.
"""
import json
import logging
import time

from flask import g, redirect, request

log = logging.getLogger("srs.request")


def _is_secure():
    return request.is_secure or request.headers.get("X-Forwarded-Proto", "").lower() == "https"


def init_transport(app):
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    @app.before_request
    def _start_timer_and_redirect():
        g.started = time.perf_counter()
        if app.config["ENFORCE_HTTPS"] and not _is_secure():
            return redirect(request.url.replace("http://", "https://", 1), code=301)
        return None

    @app.after_request
    def _harden_and_log(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")  # found by OWASP ZAP (rule 90004)
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        response.headers["Cache-Control"] = "no-store"  # this service only returns per-user data (also covers 404s: ZAP 10049)
        if app.config["ENFORCE_HTTPS"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        started = g.get("started")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1) if started else None
        if elapsed_ms is not None:
            response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        if app.config["LOG_REQUESTS"] and not app.config.get("TESTING"):
            user = g.get("current_user")
            log.info(
                json.dumps(
                    {
                        "event": "request",
                        "method": request.method,
                        "path": request.path,
                        "status": response.status_code,
                        "ms": elapsed_ms,
                        "user_id": user.id if user else None,
                    }
                )
            )
        return response
