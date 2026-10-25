# Software Test Case Specification
## Student Record System: Course Self-Enrollment & 6-Course Cap

**Requirement:** SYS-F-006 (AC-SYS-F-006) | **Test case reference:** TC-CRS-02 | **GitHub issue:** US-06
**Test framework:** Python `unittest` (the CI pipeline runs `python -m unittest discover`; pytest also works)
**Files:** `tests/backend/courses/test_enrollment.py` (business rules, SQLite), `tests/backend/courses/test_enrollment_mysql.py` (concurrency, real MySQL)

### 1. Assumptions (the SRS/SAD do not specify these)

| # | Question | Assumption used | Where enforced |
|---|---|---|---|
| A1 | Does the limit count courses, sections or records? | Each Active enrollment record = one course section. Limit = 6 **per academic term** (SRS 03 §Constraints: "6 courses per academic term"). | `MAX_COURSES_PER_TERM`, `_term_count()` |
| A2 | Do dropped/cancelled enrollments count? | No. Only `status = 'Active'` counts. (Drop/cancel is not implemented yet.) | `backend/modules/courses/enrollment_service.py` |
| A3 | Duplicate enrollment in the same section? | Prohibited (409 `ALREADY_ENROLLED`), also by DB unique key `(student_id, course_id)`. | service + `uq_enrollment_student_course` |
| A4 | Two different sections of the same course code? | Allowed (each section is a separate record). | none needed |
| A5 | "Open enrollment window set by the Administrator" (SRS) | **Not implemented.** No admin/window model exists. `courses.status = 'Open'/'Closed'` is the only gate. | `SECTION_CLOSED` |
| A6 | Seat availability | Derived: `capacity_limit - Active enrollments`. No stored counter. | `Course.to_dict`, `list_catalog` |
| A7 | Course/section tables | Did not exist. Added `courses` (matches SRS ER entity COURSE) and `enrollments`. SYS-F-005 (admin course setup) will need to reuse `courses`. | `scripts/schema.sql`, `backend/modules/courses/models.py` |

### 2. Preconditions common to all cases
Test DB created fresh per test. Students `STU001-STU003` (role Student) and `FAC001` (role Faculty) exist. Term `2026-ODD`: sections id 1-8 (capacity 30, Open), id 9 (Closed), id 10 (capacity 1, Open). Term `2026-EVEN`: section id 11. Dev identity is enabled (`X-Student-Id` header) because real authentication does not exist yet.

### 3. Automated test cases

| ID | Requirement / AC | Objective | Procedure and test data | Expected result | Actual result | Status |
|---|---|---|---|---|---|---|
| TC-CRS-02-01 | AC-1 | Catalog shows sections with capacity | `GET /api/v1/courses` | 200; 11 sections; section 1 = `capacity 30, enrolled 0, availableSeats 30, availability open`; section 9 `closed`; section 10 has 1 seat | As expected | Pass |
| TC-CRS-02-01b | AC-1 | Term filter | `GET /api/v1/courses?term=2026-EVEN` | Only CS903 returned | As expected | Pass |
| TC-CRS-02-01c | AC-1 | Full section labelled | STU001 takes the only seat of section 10; GET catalog | `availableSeats 0`, `availability full` | As expected | Pass |
| TC-CRS-02-02 | AC-2 | Enroll in an open section | STU001 `POST /api/v1/enrollments {"courseId":1}` | 201; `message "Enrollment confirmed."`; summary `count 1, limit 6`; one Active row in DB | As expected | Pass |
| TC-CRS-02-03 | AC-4 | Capacity decrements | Enroll STU001, then STU002 in section 1 | Response and catalog: 30 -> 29 -> 28 | As expected | Pass |
| TC-CRS-02-04 | AC-2 | Full section rejected | STU001 takes section 10; STU002 tries it | 409 `SECTION_FULL`; DB still 1 row | As expected | Pass |
| TC-CRS-02-05 | AC-2 | Closed section rejected | Enroll in section 9 | 409 `SECTION_CLOSED`; no row | As expected | Pass |
| TC-CRS-02-06 | **AC-3** | 7th course rejected | STU001 enrolls in sections 1-6, then 7 | 409 `ENROLLMENT_LIMIT_REACHED`, message contains "at most 6"; still 6 rows; section 7 still 30 seats | As expected | Pass |
| TC-CRS-02-07 | AC-3 | 6th course accepted (boundary) | STU001 enrolls in sections 1-5, then 6 | 201; `count 6` | As expected | Pass |
| TC-CRS-02-08 | AC-2 | Duplicate rejected | Enroll in section 1 twice | 2nd: 409 `ALREADY_ENROLLED`; seats decremented once; 1 row | As expected | Pass |
| TC-CRS-02-09 | AC-2 | Unknown section / student | Section 999; student `STU999` | 404 `COURSE_NOT_FOUND`; 404 `STUDENT_NOT_FOUND`; no rows | As expected | Pass |
| TC-CRS-02-10 | AC-2 | Malformed requests | Bodies: `{}`, `{"course":1}`, `"1"`, `true`, `0`, `-3`, `1.5`, `null`, extra field, JSON array, invalid JSON, no body | Each: 400 `INVALID_REQUEST`; no rows | As expected (12 inputs) | Pass |
| TC-CRS-02-11a | Security | No identity | POST and GET `/enrollments/me` with no header | 401 `UNAUTHENTICATED` | As expected | Pass |
| TC-CRS-02-11b | Security | Secure by default | Dev identity flag off, header sent | 401 | As expected | Pass |
| TC-CRS-02-11c | Security | Client-supplied student ID not trusted | Header STU001, body `studentId: STU002` | 400; no rows | As expected | Pass |
| TC-CRS-02-11d | Security | Role check | Faculty `FAC001` enrolls | 403 `FORBIDDEN_ROLE` | As expected | Pass |
| TC-CRS-02-12 | AC-3/4 | Failures change nothing | After 6+1 enrollments, attempt 7th, full, closed, duplicate, unknown | All >= 400; enrollment rows and full catalog identical to before | As expected | Pass |
| TC-CRS-02-13 | AC-3 | Limit is per term | 6 in `2026-ODD`, then section 11 (`2026-EVEN`) | 201; counts `{ODD:6, EVEN:1}` | As expected | Pass |
| TC-CRS-02-14 | Security | Own enrollments only | STU001 x2, STU002 x1; `GET /enrollments/me` as STU001 | Only sections 1, 2 listed | As expected | Pass |
| TC-CRS-02-15 | AC-4 | Rollback on unexpected error | Force `commit` to raise | 500 `INTERNAL_ERROR`; no row; seats unchanged | As expected | Pass |
| TC-CRS-02-16 | AC-4 | Last seat, sequential | STU001 then STU002 take section 10 | One 201, one 409; 1 row | As expected | Pass |
| TC-CRS-02-17 | AC-4 | **Concurrency**: 30 students, 1 seat | 30 threads released together (real MySQL 8.0) | Exactly 1 success, 29 `SECTION_FULL`, 1 DB row | As expected | Pass |
| TC-CRS-02-18 | AC-4 | **Concurrency**: 30 students, 5 seats | Same, capacity 5 | 5 successes, 25 `SECTION_FULL`, 5 rows | As expected | Pass |
| TC-CRS-02-19 | AC-3 | **Concurrency**: one student, 10 sections | 10 threads, same student | Exactly 6 successes, 4 `ENROLLMENT_LIMIT_REACHED`, 6 rows | As expected | Pass |
| TC-CRS-02-20 | AC-2 | **Concurrency**: double-click | 8 threads, same student and section | 1 success, 7 `ALREADY_ENROLLED` | As expected | Pass |
| TC-CRS-02-21 | AC-3/4 | **Concurrency**: mixed, no deadlock | 24 students over 4 sections of capacity 3, plus STU001 over all 4 | No unexpected errors; every section <= 3; every student <= 6 | As expected | Pass |

### 4. Manual UI test cases (NOT YET VERIFIED)

The React screen was built and passes `npm run build` and `npm run lint` (0 errors). It was **not** opened in a real browser. Its logic was checked with a throwaway jsdom component test (7 tests, mocked backend, not committed; section 5). Execute these yourself before submission.

| ID | AC | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|
| TC-CRS-02-M1 | AC-1 | Open Course Catalog | Table shows code, title, section, "N of M available", Open/Full/Closed badge; header shows `Enrolled: 0 / 6` | Not yet verified | Not run |
| TC-CRS-02-M2 | AC-2, AC-4 | Click Enroll on an open section | Button shows "Enrolling...", then green confirmation; row shows "Enrolled"; seats drop by 1; count increments; My Enrollments lists it | Not yet verified | Not run |
| TC-CRS-02-M3 | AC-3 | Enroll in 6 sections | Count shows `6 / 6` in red; every remaining Enroll button replaced by "Course limit reached" | Not yet verified | Not run |
| TC-CRS-02-M4 | AC-3 | With 6 enrolled, `POST` a 7th with curl/Postman (UI hides the button) | 409 with the "at most 6" message | Verified over HTTP against MySQL (see section 5); UI not run | Partial |
| TC-CRS-02-M5 | AC-1, AC-4 | Two browsers; take the last seat in browser A; click Enroll in stale browser B | B shows server error, then refreshes to show Full | Not yet verified | Not run |
| TC-CRS-02-M6 | AC-2 | Double-click Enroll quickly | Only one request; one enrollment | Not yet verified | Not run |

### 5. Execution summary (actual results)

Integrated repository (backend/, frontend/, tests/), run in a Linux sandbox (not a Windows machine): Python 3.12.3, Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.6, MySQL 8.0.46 (REPEATABLE-READ), Node/Vite from `frontend/package.json`.

| Command (from repo root, `PYTHONPATH=backend`) | Result |
|---|---|
| `python -m unittest discover -s tests/backend -t . -p "test_*.py"` (the CI command; no MySQL) | **40 tests: 35 passed, 0 failed, 5 skipped** (the 5 skipped are the MySQL tests) |
| Per suite | auth `test_profile` 9 OK; auth `test_user_provisioning` 5 OK; courses `test_enrollment` 21 OK; courses `test_enrollment_mysql` 5 skipped without `TEST_MYSQL_URL` |
| Same CI command with `TEST_MYSQL_URL` pointing to dedicated DB `us06_test` | **40 tests, all passed, 0 skipped** |
| `test_enrollment_mysql` run alone, 3 repeats | 3/3 runs: 5 passed |
| MySQL tests with `TEST_MYSQL_URL` set to a database not ending in `_test` | Refused with `RuntimeError` before connecting |
| Locks removed from `enrollment_service.py` (sensitivity check) | 4 of 5 MySQL tests fail; restored code: 5 pass |
| `npm run build` | OK |
| `npm run lint` | 0 errors, 1 warning (setState inside an effect) |
| Throwaway jsdom component test (7 tests, temp copy, not committed) | 7 passed: catalog fields/status, successful enroll, double-click sends 1 request, 6/6 hides Enroll buttons, stale-seat rejection re-syncs, term filter, load error |
| Live Flask + clean MySQL (tables from `db.create_all()`, `scripts/seed_demo_courses.sql`) | `/api/profile/STU001` 200; enrollment without identity 401; enrollments 1-6 returned 201; 7th returned 409 `ENROLLMENT_LIMIT_REACHED`; `/api/admin/users` route still responds |
| Vite dev proxy to Flask | `/api/v1/courses` and `/api/v1/enrollments/me` reachable through the proxy |

### 6. Limitations
- SQLite tests prove business rules only; locking is proven only by the MySQL tests, run against MySQL 8.0 in a sandbox, not against your team's server.
- Authentication does not exist in the repository. Identity uses an insecure, off-by-default dev header (`identity.py`). Endpoints are NOT secure until JWT validation replaces it (SYS-F-001/002, PRJ-SR-003/004).
- The admin-controlled enrollment window (A5), dropping a course, and admin course setup (SYS-F-005) are not implemented.
- No browser-driven UI test; manual UI cases in section 4 are unexecuted. `scripts/schema.sql` creates `profiles` without the password columns the ORM model now has (pre-existing); for a fresh database let `python app.py` run `db.create_all()`.
