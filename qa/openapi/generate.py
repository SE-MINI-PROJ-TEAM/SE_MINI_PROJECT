"""Generate the OpenAPI 3 specification straight from the Flask routes.

    python qa/openapi/generate.py          # writes qa/openapi/openapi.json
    python qa/openapi/generate.py --check  # exit 1 if the committed file is out of date (used in CI)

The spec is derived (never hand-edited) so it cannot drift from the code. Roles come from the ``auth_required``
decorator; request examples for the main write endpoints live in EXAMPLES below. It feeds Swagger tooling,
the ZAP API scan and the Newman collection builder.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app import create_app  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "openapi.json")
PUBLIC = {"/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/password-policy"}

EXAMPLES = {
    "POST /api/v1/auth/login": {"identifier": "admin001@srs.edu", "password": "Password@123"},
    "POST /api/v1/auth/change-password": {"current_password": "Password@123", "new_password": "Brand#New9pass"},
    "POST /api/v1/users": {"full_name": "Asha Rao", "email": "asha.rao@srs.edu", "role": "Student", "institutional_id": "PES1UG26CS101"},
    "PATCH /api/v1/users/{user_id}": {"is_active": True},
    "PUT /api/v1/profile": {"phone": "+91 98765 43210", "personal_email": "me@example.com", "home_address": "12 Main Rd", "emergency_contact": "Mum +91 99999 88888"},
    "POST /api/v1/courses": {
        "code": "CS999", "title": "Example Course", "section": "A", "credits": 3, "capacity": 40, "assigned_faculty_id": 12,
        "rubric": [{"name": "Assignments", "category": "Assignments", "weight": 1}, {"name": "Exam", "category": "Exams", "weight": 2}],
    },
    "POST /api/v1/enrollments": {"course_id": 1},
    "PUT /api/v1/enrollments/window": {"open": True},
    "POST /api/v1/schedule/sessions": {"course_id": 1, "room": "LH-9", "start_time": "2026-11-02T04:30:00Z", "end_time": "2026-11-02T05:30:00Z", "repeat_weeks": 1},
    "POST /api/v1/attendance/sessions/{session_id}": {"attendance_list": [{"student_id": "PES1UG24CS001", "is_present": True}]},
    "PUT /api/v1/attendance/override/sessions/{session_id}": {"changes": [{"student_id": "PES1UG24CS001", "is_present": True}], "reason": "Medical certificate verified"},
    "PUT /api/v1/grades/courses/{course_id}": {"students": [{"student_id": "PES1UG24CS001", "rubric_scores": [{"rubric_id": 1, "score": 80}]}]},
    "PUT /api/v1/grades/courses/{course_id}/students/{student_code}": {"rubric_scores": [{"rubric_id": 1, "score": 85.0}], "target_state": "Draft"},
    "POST /api/v1/grades/publication/publish": {"course_ids": [2]},
    "POST /api/v1/disputes": {"enrollment_id": 1, "reason": "Question 3 was marked incorrectly."},
    "POST /api/v1/disputes/{dispute_id}/resolve": {"resolution_note": "Re-marked", "rubric_scores": [{"rubric_id": 1, "score": 90}]},
}

TAG_DESCRIPTIONS = {
    "auth_session": "Login / logout / current session (shared foundation)",
    "user_provisioning": "US-01 Admin provisioning",
    "password_reset": "US-02 Mandatory password reset",
    "profile": "US-03 Profile contact details",
    "account_management": "US-04 Account status, roles, audit log",
    "course_setup": "US-05 Course offerings & rubric normalisation",
    "course_enrollment": "US-06 Self-enrollment & 6-course cap",
    "schedule": "US-07 Timetable & faculty roster isolation",
    "attendance_marking": "US-08 Roll-call & 48-hour lock",
    "attendance_override": "US-09 Admin attendance override",
    "attendance_dashboard": "US-10 Student attendance summary",
    "grade_entry": "US-11 Draft rubric scores",
    "grade_publication": "US-12 Submission & publication",
    "regrade_disputes": "US-13 Regrade disputes",
    "analytics": "US-14 GPA & grade distributions",
    "admin_metrics": "US-15 Metrics & CSV export",
}


def _path(rule):
    return re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule)


def _params(rule):
    out = []
    for arg in sorted(rule.arguments):
        schema = {"type": "integer"} if rule._converters[arg].__class__.__name__ == "IntegerConverter" else {"type": "string"}
        out.append({"name": arg, "in": "path", "required": True, "schema": schema})
    return out


def build_spec():
    app = create_app()
    paths = {}
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if not rule.rule.startswith("/api/v1"):
            continue
        view = app.view_functions[rule.endpoint]
        blueprint = rule.endpoint.split(".")[0]
        path = _path(rule)
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            roles = list(getattr(view, "auth_roles", ()))
            is_public = rule.rule in PUBLIC
            op = {
                "tags": [blueprint],
                "operationId": f"{rule.endpoint.replace('.', '_')}_{method.lower()}",
                "summary": view.__name__.replace("_", " ").capitalize(),
                "parameters": _params(rule) + (
                    [{"name": n, "in": "query", "schema": {"type": "string"}} for n in ("page", "per_page", "search")]
                    if method == "GET" and path.endswith(("/users", "/courses", "/audit-logs", "/sessions")) else []
                ),
                "responses": {"200": {"description": "Success"}},
            }
            doc = (view.__doc__ or "").strip()
            if doc:
                op["description"] = doc
            if not is_public:
                op["security"] = [{"cookieAuth": []}, {"bearerAuth": []}]
                op["x-roles"] = roles or ["Student", "Faculty", "Admin"]
                op["responses"]["401"] = {"description": "Missing, expired or invalid session"}
                op["responses"]["403"] = {"description": "Role not permitted / temporary password / not assigned to this resource"}
            if method in ("POST", "PUT", "PATCH"):
                example = EXAMPLES.get(f"{method} {path}")
                op["requestBody"] = {
                    "required": example is not None,
                    "content": {"application/json": {"schema": {"type": "object"}, **({"example": example} if example else {})}},
                }
                op["responses"]["400"] = {"description": "Validation error"}
            if method == "POST" and path in ("/api/v1/users", "/api/v1/courses", "/api/v1/enrollments", "/api/v1/schedule/sessions"):
                op["responses"]["409"] = {"description": "Conflict (duplicate / capacity / limit)"}
            paths.setdefault(path, {})[method.lower()] = op

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Student Record System API",
            "version": "1.0.0",
            "description": "Generated from the Flask routes by qa/openapi/generate.py. Sessions use an HTTP-only JWT cookie "
                           "(48 h); a Bearer token is also accepted for API clients. Errors use {status, code, message}.",
        },
        "servers": [{"url": "http://localhost:5000"}],
        "tags": [{"name": k, "description": v} for k, v in TAG_DESCRIPTIONS.items()],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "cookieAuth": {"type": "apiKey", "in": "cookie", "name": "srs_token"},
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
            }
        },
    }


def main():
    text = json.dumps(build_spec(), indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("openapi.json is out of date - run: python qa/openapi/generate.py")
            sys.exit(1)
        print("openapi.json is up to date")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    operations = sum(len(v) for v in json.loads(text)["paths"].values())
    print(f"Wrote {OUT} ({operations} operations)")


if __name__ == "__main__":
    main()
