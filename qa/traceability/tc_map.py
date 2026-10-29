"""STP test case (TC-xx) -> the automated results that prove it.

Selectors (tuples), evaluated against the result files in qa/reports/ by qa/report.py:
    ("unit",    "tests.module.prefix", [name substrings] | None)   PyTest JUnit
    ("newman",  "folder prefix")                                    Newman JSON (collection folder)
    ("e2e",     "file or title substring", [title substrings] | None)   Playwright JUnit
    ("k6",      ["metric{tag} threshold keys..."])                  k6 summary export (threshold must not be breached)
    ("zap",)                                                         no High/Critical alert in either ZAP report
    ("static",)                                                      Bandit (>= medium), pip-audit, npm audit (>= high) clean
    ("coverage", 70)                                                 backend line coverage gate
    ("waived",  "why")                                               not feasible to test here; closed by agreement with the instructor
    ("manual",  "why")                                               cannot be automated; documented instead
A TC passes when it has >= 1 executed check and none of them failed.
"""

SECURITY = "tests.admin_metrics.test_security"

TC_EVIDENCE = {
    "TC-ACC-01": [("unit", "tests.user_provisioning"), ("newman", "02 Admin provisioning"), ("e2e", "admin provisions a user")],
    "TC-ACC-02": [("unit", "tests.password_reset"), ("newman", "03 Forced password reset"), ("e2e", "admin provisions a user")],
    "TC-ACC-03": [("unit", "tests.profile"), ("newman", "04 Profile")],
    "TC-ACC-04": [("unit", "tests.account_management"), ("newman", "12 Deactivation"), ("e2e", "deactivating a user")],
    "TC-CRS-01": [("unit", "tests.course_setup"), ("newman", "05 Course setup")],
    "TC-CRS-02": [("unit", "tests.course_enrollment"), ("newman", "06 Enrollment"), ("e2e", "6-course cap")],
    "TC-CRS-03": [("unit", "tests.schedule"), ("newman", "05 Course setup")],
    "TC-CRS-04": [("unit", "tests.schedule", ["roster"]), ("newman", "07 Roster isolation")],
    "TC-ATT-01": [("unit", "tests.attendance_marking"), ("newman", "07 Roster isolation"), ("e2e", "roll-call")],
    "TC-ATT-02": [("unit", "tests.attendance_marking", ["48", "frozen", "freeze", "boundary", "window"]), ("newman", "07 Roster isolation")],
    "TC-ATT-03": [("unit", "tests.attendance_override"), ("newman", "08 Admin override")],
    "TC-ATT-04": [("unit", "tests.attendance_dashboard"), ("newman", "09 Student attendance view")],
    "TC-GRD-01": [("unit", "tests.grade_entry"), ("newman", "10 Grade lifecycle"), ("e2e", "grade lifecycle")],
    "TC-GRD-02": [("unit", "tests.grade_publication"), ("newman", "10 Grade lifecycle")],
    "TC-GRD-03": [("unit", "tests.grade_publication", ["publish"]), ("newman", "10 Grade lifecycle"), ("e2e", "grade lifecycle")],
    "TC-GRD-04": [("unit", "tests.regrade_disputes"), ("newman", "10 Grade lifecycle"), ("e2e", "grade lifecycle")],
    "TC-GRD-05": [("unit", "tests.regrade_disputes", ["resolve", "republish", "final", "again"]), ("newman", "10 Grade lifecycle"), ("e2e", "grade lifecycle")],
    "TC-REP-01": [("unit", "tests.analytics", ["gpa", "student", "fast"]), ("newman", "11 Analytics"), ("e2e", "GPA is visible")],
    "TC-REP-02": [("unit", "tests.analytics", ["faculty", "distribution", "attendance_rate"]), ("newman", "11 Analytics")],
    "TC-REP-03": [("unit", "tests.admin_metrics.test_admin_metrics"), ("newman", "11 Analytics")],
    "TC-PERF-01": [("unit", "tests.admin_metrics.test_performance", ["p95"]), ("k6", ["http_req_duration{scenario:sessions}", "http_req_failed{scenario:sessions}"])],
    "TC-PERF-02": [("unit", "tests.admin_metrics.test_performance", ["200"]), ("k6", ["http_req_failed{scenario:burst}", "checks{scenario:burst}"])],
    "TC-OPS-01": [("waived", "99% monthly uptime needs a month of production monitoring, infeasible for a course project; closed by agreement with the course instructor (docs/qa/TEST-STRATEGY.md, section 6)")],
    "TC-UX-01": [("e2e", "02-usability")],
    "TC-QUAL-01": [("coverage", 70)],
    "TC-SEC-01": [("unit", SECURITY, ["https", "tls", "secure", "header"])],
    "TC-SEC-02": [("unit", "tests.password_reset", ["bcrypt"]), ("newman", "03 Forced password reset")],
    "TC-SEC-03": [("unit", SECURITY, ["jwt", "cookie", "token", "session"]), ("newman", "01 Authentication")],
    "TC-SEC-04": [("unit", SECURITY, ["role_based", "covered_by_auth", "cannot_read"]), ("newman", "13 RBAC matrix"), ("e2e", "01-access-control")],
    "TC-SEC-05": [("unit", SECURITY, ["sql", "html_is_stripped", "leak"]), ("newman", "14 Injection"), ("zap",), ("static",)],
}
