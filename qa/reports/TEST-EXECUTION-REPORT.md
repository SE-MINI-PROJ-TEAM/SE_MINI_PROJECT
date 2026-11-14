# Test Execution & Acceptance Report

_Generated 2026-11-14 15:05 UTC by `qa/report.py` from the result files in `qa/reports/`. Every figure is read from tool output._

## Verdict: automated quality gates **PASS**

| Gate | Result | Detail |
| --- | --- | --- |
| All executed test cases pass | PASS | 29/29 executed TCs pass |
| Backend coverage >= 70% (SYS-NF-005) | PASS | 98.65% lines / 93.26% branches |
| p95 latency < 800 ms with 500 sessions (SYS-NF-001) | PASS | p95 = 31.5 ms |
| 200 simultaneous submissions, 0 failures (SYS-NF-002) | PASS | 200 ok / 0 failed |
| No High/Critical ZAP alerts (PRJ-SR-001..005) | PASS | no alerts above Medium |
| Static analysis & dependency audit clean | PASS | Bandit / pip-audit / npm audit |
| Every acceptance criterion has automated evidence | PASS | Acceptance traceability OK: 51 criteria across 15 stories, every one covered by an automated check. |

## Execution summary

| Suite (tool) | Tests | Passed | Failed | Duration |
| --- | --- | --- | --- | --- |
| Unit + API (PyTest, MySQL) | 313 | 313 | 0 | 49 s |
| Frontend unit (Vitest) | 16 | 16 | 0 | 0 s |
| E2E / usability / accessibility (Playwright + axe) | 24 | 24 | 0 | 72 s |
| Integration (Newman) | 147 requests / 222 assertions | 222 | 0 | |

## STP section 14 metrics

| Metric | Value |
| --- | --- |
| Test cases executed | **29 / 30** (97%) - the rest is listed below as manual or waived |
| Test cases closed by agreement with the instructor (not executable here) | **1** (TC-OPS-01) |
| Test cases passed | **29 / 29** (100%) |
| Requirement coverage (verified requirements) | **30 / 30** (100%) |
| Defect density / aging | tracked in GitHub issues (label `defect`); not derivable from test output |

## Test case results

| TC | Status | Evidence |
| --- | --- | --- |
| TC-ACC-01 | PASS | unit: tests.user_provisioning (10/10 ok); newman: 02 Admin provisioning (11/11 ok); e2e: admin provisions a user (1/1 ok) |
| TC-ACC-02 | PASS | unit: tests.password_reset (7/7 ok); newman: 03 Forced password reset (14/14 ok); e2e: admin provisions a user (1/1 ok) |
| TC-ACC-03 | PASS | unit: tests.profile (13/13 ok); newman: 04 Profile (8/8 ok) |
| TC-ACC-04 | PASS | unit: tests.account_management (8/8 ok); newman: 12 Deactivation (15/15 ok); e2e: deactivating a user (1/1 ok) |
| TC-CRS-01 | PASS | unit: tests.course_setup (40/40 ok); newman: 05 Course setup (11/11 ok) |
| TC-CRS-02 | PASS | unit: tests.course_enrollment (10/10 ok); newman: 06 Enrollment (17/17 ok); e2e: 6-course cap (1/1 ok) |
| TC-CRS-03 | PASS | unit: tests.schedule (23/23 ok); newman: 05 Course setup (11/11 ok) |
| TC-CRS-04 | PASS | unit: tests.schedule (2/2 ok); newman: 07 Roster isolation (16/16 ok) |
| TC-ATT-01 | PASS | unit: tests.attendance_marking (22/22 ok); newman: 07 Roster isolation (16/16 ok); e2e: roll-call (1/1 ok) |
| TC-ATT-02 | PASS | unit: tests.attendance_marking (4/4 ok); newman: 07 Roster isolation (16/16 ok) |
| TC-ATT-03 | PASS | unit: tests.attendance_override (18/18 ok); newman: 08 Admin override (6/6 ok) |
| TC-ATT-04 | PASS | unit: tests.attendance_dashboard (7/7 ok); newman: 09 Student attendance view (7/7 ok) |
| TC-GRD-01 | PASS | unit: tests.grade_entry (27/27 ok); newman: 10 Grade lifecycle (41/41 ok); e2e: grade lifecycle (1/1 ok) |
| TC-GRD-02 | PASS | unit: tests.grade_publication (29/29 ok); newman: 10 Grade lifecycle (41/41 ok) |
| TC-GRD-03 | PASS | unit: tests.grade_publication (10/10 ok); newman: 10 Grade lifecycle (41/41 ok); e2e: grade lifecycle (1/1 ok) |
| TC-GRD-04 | PASS | unit: tests.regrade_disputes (17/17 ok); newman: 10 Grade lifecycle (41/41 ok); e2e: grade lifecycle (1/1 ok) |
| TC-GRD-05 | PASS | unit: tests.regrade_disputes (4/4 ok); newman: 10 Grade lifecycle (41/41 ok); e2e: grade lifecycle (1/1 ok) |
| TC-REP-01 | PASS | unit: tests.analytics (3/3 ok); newman: 11 Analytics (15/15 ok); e2e: GPA is visible (1/1 ok) |
| TC-REP-02 | PASS | unit: tests.analytics (3/3 ok); newman: 11 Analytics (15/15 ok) |
| TC-REP-03 | PASS | unit: tests.admin_metrics.test_admin_metrics (5/5 ok); newman: 11 Analytics (15/15 ok) |
| TC-PERF-01 | PASS | unit: tests.admin_metrics.test_performance (1/1 ok); k6 (2/2 ok) |
| TC-PERF-02 | PASS | unit: tests.admin_metrics.test_performance (1/1 ok); k6 (2/2 ok) |
| TC-OPS-01 | WAIVED | waived by agreement (99% monthly uptime needs a month of production monitoring, infeasible for a course project; closed by agreement with the course instructor (docs/qa/TEST-STRATEGY.md, section 6)) |
| TC-UX-01 | PASS | e2e: 02-usability (7/7 ok) |
| TC-QUAL-01 | PASS | coverage (1/1 ok) |
| TC-SEC-01 | PASS | unit: tests.admin_metrics.test_security (4/4 ok) |
| TC-SEC-02 | PASS | unit: tests.password_reset (1/1 ok); newman: 03 Forced password reset (14/14 ok) |
| TC-SEC-03 | PASS | unit: tests.admin_metrics.test_security (9/9 ok); newman: 01 Authentication (11/11 ok) |
| TC-SEC-04 | PASS | unit: tests.admin_metrics.test_security (31/31 ok); newman: 13 RBAC matrix (35/35 ok); e2e: 01-access-control (8/8 ok) |
| TC-SEC-05 | PASS | unit: tests.admin_metrics.test_security (6/6 ok); newman: 14 Injection (8/8 ok); zap (3/3 ok); static (3/3 ok) |

## Requirement coverage

| Requirement | Summary | Test cases | Verified |
| --- | --- | --- | --- |
| SYS-F-001 | Account provisioning & credential display | TC-ACC-01 | yes |
| SYS-F-002 | Mandate password reset on initial login | TC-ACC-02 | yes |
| SYS-F-003 | Personal contact details update | TC-ACC-03 | yes |
| SYS-F-004 | Admin account metadata/status update | TC-ACC-04 | yes |
| SYS-F-005 | Course setup & rubric weight auto-norm | TC-CRS-01 | yes |
| SYS-F-006 | Student self-enrollment (max 6 courses) | TC-CRS-02 | yes |
| SYS-F-007 | Class schedule creation & publishing | TC-CRS-03 | yes |
| SYS-F-008 | Restrict faculty roster visibility | TC-CRS-04 | yes |
| SYS-F-009 | Digitized binary roll-call submission | TC-ATT-01 | yes |
| SYS-F-010 | 48-hour automated attendance freeze | TC-ATT-02 | yes |
| SYS-F-011 | Administrative attendance override | TC-ATT-03 | yes |
| SYS-F-012 | Student aggregate attendance view | TC-ATT-04 | yes |
| SYS-F-013 | Rubric score entry in `Draft` state | TC-GRD-01 | yes |
| SYS-F-014 | Submit draft grades with rubric weight | TC-GRD-02 | yes |
| SYS-F-015 | Admin grade publication | TC-GRD-03 | yes |
| SYS-F-016 | Student regrade request (`Under Review`, once per grade) | TC-GRD-04 | yes |
| SYS-F-017 | Resolve regrade dispute and re-publish | TC-GRD-05 | yes |
| SYS-F-018 | Student consolidated GPA dashboard | TC-REP-01 | yes |
| SYS-F-019 | Faculty class summary analytics | TC-REP-02 | yes |
| SYS-F-020 | Admin institution metrics export | TC-REP-03 | yes |
| SYS-NF-001 | Latency $\le 800\text{ ms}$ at 95th percentile | TC-PERF-01 | yes |
| SYS-NF-002 | 200 concurrent submission transactions | TC-PERF-02 | yes |
| SYS-NF-003 | 99.0% operational availability | TC-OPS-01 | waived by agreement |
| SYS-NF-004 | Responsive UI & $\le 3$ click roll-call | TC-UX-01 | yes |
| SYS-NF-005 | 3-tier separation & $\ge 70\%$ test coverage | TC-QUAL-01 | yes |
| PRJ-SR-001 | Mandatory TLS 1.3 transit encryption | TC-SEC-01 | yes |
| PRJ-SR-002 | Bcrypt password hashing (factor 12) | TC-SEC-02 | yes |
| PRJ-SR-003 | 48-hour HTTP-only JWT sessions | TC-SEC-03 | yes |
| PRJ-SR-004 | Endpoint RBAC middleware check | TC-SEC-04 | yes |
| PRJ-SR-005 | Parameterized ORM queries (SQLi/XSS) | TC-SEC-05 | yes |

## Performance (k6)

500 concurrent sessions, 13,905 requests at 157 req/s (12 API worker processes), then a 200-request simultaneous submission burst.

| Metric | Value |
| --- | --- |
| Latency avg / median | 14.3 ms / 11.8 ms |
| Latency p90 / p95 / p99 | 25.9 / 31.5 / 46.0 ms |
| Max latency | 126 ms |
| Failed requests (sessions) | 0 of 13,905 |
| Burst: submissions accepted | 200 / 200 |

## Security

- **Bandit** (Python SAST): 0 high, 0 medium, 4 low findings.
- **pip-audit**: 34 Python packages checked, 0 with known vulnerabilities.
- **npm audit** (production deps): 0 critical, 0 high, 2 moderate, 0 low.
- **OWASP ZAP api scan**: Informational: 2, Low: 1.
- **OWASP ZAP baseline scan**: Informational: 1.
- **OWASP ZAP ui scan**: Informational: 1.

## Acceptance

- Acceptance criteria with automated evidence: **Acceptance traceability OK: 51 criteria across 15 stories, every one covered by an automated check.**
- Matrix: `docs/uat/ACCEPTANCE-MATRIX.md`; script: `docs/uat/UAT-SCRIPT.md`.
- UAT results (`docs/uat/UAT-RESULTS.md`): 51 pass, 0 fail, 0 blocked, 0 pending of 51 criteria. 
