"""Student identity for the enrollment API.

IMPORTANT - READ THIS BEFORE USING IN PRODUCTION
------------------------------------------------
The SAD specifies JWT bearer authentication (PRJ-SR-003) and RBAC middleware
(PRJ-SR-004), but NO authentication exists in this repository yet (SYS-F-001/
SYS-F-002 are not implemented). The student ID must never be taken from the
request body or URL, because the client could put anyone's ID there.

This module is the ONE place that decides "who is calling". Until the real
JWT middleware exists:

* By default (ALLOW_INSECURE_DEV_IDENTITY unset/false) there is NO identity
  and every enrollment endpoint answers 401. Nothing is silently insecure.
* For local development/demo only, set ALLOW_INSECURE_DEV_IDENTITY=true and the
  caller is identified by the `X-Student-Id` header. This is NOT secure:
  anybody can send any header. Never enable it on a real deployment.

When authentication is implemented, replace the body of
`get_authenticated_student_id()` so it validates the JWT and returns the
subject. Nothing else in the enrollment code needs to change.
"""

from flask import current_app, request


def get_authenticated_student_id():
    """Return the caller's institutional ID, or None if unauthenticated."""
    if not current_app.config.get("ALLOW_INSECURE_DEV_IDENTITY", False):
        return None

    student_id = request.headers.get("X-Student-Id", "").strip()
    return student_id or None
