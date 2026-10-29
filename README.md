# Student Record System

A role-based web application for academic record management: account provisioning, course enrollment, scheduling,
48-hour-locked attendance, a rubric-weighted grade lifecycle with regrade disputes, and analytics.

| Layer | Tech |
| --- | --- |
| Frontend | React 18 · Vite · React Router · hand-rolled design system (light / dark) |
| Backend | Python · Flask · SQLAlchemy ORM · PyJWT · bcrypt |
| Database | MySQL 8 |

Specification documents live in [docs/](docs) (SRS, SAD, STP). The 15 user stories are in [stories.md](stories.md).

---

## Quick start (Docker)

The whole system runs in containers: MySQL, the Flask API (gunicorn, multi-process) and an nginx container that serves the
React build, proxies `/api` and adds the security headers. The host only needs **Docker** (Compose v2).

```powershell
docker compose up -d --build                              # first start takes a few minutes
docker compose run --rm api python manage.py seed --reset # schema + demo data (re-run any time to reset)
```
Open **http://localhost:8080**. Stop with `docker compose down` (data is kept) or `docker compose down -v` (wipe).
Optional overrides (DB password, port, signing key) go in a `.env` next to `docker-compose.yml` (see `.env.example`).

The seed creates **500+ students, 50 faculty, 10 admins, 50 course offerings, 1,000 scheduled sessions**, ~27k attendance
records and ~5k grade records in every lifecycle state (including open regrade disputes) in a few seconds. Session times are
generated relative to *now*, so re-seed whenever you want fresh "open roll-call" sessions (e.g. the next day of testing).

### Alternative: run without Docker (development)
Needs Python 3.11+, Node 20+ and a local MySQL 8 server.
```powershell
cd backend; copy .env.example .env                        # then set DB_USER / DB_PASSWORD / SECRET_KEY
python -m venv ..\.venv; ..\.venv\Scripts\python -m pip install -r requirements.txt
..\.venv\Scripts\python manage.py seed --reset
cd ..\frontend; npm install
cd ..; .\dev.ps1                                          # API on :5000 + Vite dev server on http://localhost:5173
```

### Demo accounts (all seeded accounts use password `Password@123`)
| Role | Login | Notes |
| --- | --- | --- |
| Admin | `admin001@srs.edu` | full console |
| Faculty | `faculty001@srs.edu` | teaches CS101 / CS102 / CS103: open roll-call, submitted & draft grades, open regrade requests |
| Student | `student001@srs.edu` | 4 courses (2 more allowed), one course below 75 % attendance, published + pending grades |
| Student | `student002@srs.edu` | already at the 6-course cap |
| New user | `new.student@srs.edu` / `Temp@12345` | temporary password: forced reset on first login |

The Vite development server (not the Docker build) also shows one-click demo chips on the login page.

---

## Smoke test
See [docs/SMOKE_TEST.md](docs/SMOKE_TEST.md) for a story-by-story walkthrough (US-01 … US-15).

## Quality assurance (STP tooling)
Unit, integration, system, performance, security and accessibility testing are automated, run entirely in Docker, and run on every pull request and merge
through GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)). Locally, one command drives every stage:

```powershell
./qa.sh all      # (Windows: .\qa.ps1 all)  PyTest+Vitest, Bandit/pip-audit/npm audit, Newman, k6, OWASP ZAP, Playwright+axe, then the report
```
Results are assembled into `qa/reports/TEST-EXECUTION-REPORT.md` (STP section 14 metrics, requirement coverage, security and performance
summaries). Details: [docs/qa/TEST-STRATEGY.md](docs/qa/TEST-STRATEGY.md), [qa/README.md](qa/README.md). Findings and decisions:
[docs/qa/SECURITY-TRIAGE.md](docs/qa/SECURITY-TRIAGE.md). Customer acceptance: [docs/uat/](docs/uat) (plan, script, acceptance matrix, results sheet).

## Automated tests
```powershell
cd backend
..\.venv\Scripts\python -m pytest                              # everything (needs MySQL; uses DB `student_record_system_test`)
..\.venv\Scripts\python -m pytest --cov --cov-report=term      # with the >= 70 % coverage gate (SYS-NF-005)
..\.venv\Scripts\python -m pytest tests\admin_metrics -s       # US-15 security + TC-PERF-01/02 benchmarks
cd ..\frontend; npm test                                       # unit tests for client-side helpers
```
The test database is created automatically and dropped afterwards; it never touches the dev database.

## HTTPS / TLS 1.3 (PRJ-SR-001)
Development runs on plain HTTP for convenience. To exercise the transport controls locally:
```powershell
cd backend
..\.venv\Scripts\python scripts\gen_dev_cert.py        # self-signed cert in backend/certs (git-ignored)
# set ENFORCE_HTTPS=true in backend/.env, then
..\.venv\Scripts\python run.py --https                 # TLS 1.3 minimum, HSTS, Secure cookies, HTTP -> HTTPS redirect
```
In production, terminate TLS 1.3 at the reverse proxy (nginx/Caddy/ALB) and set `ENFORCE_HTTPS=true` so the app
sends HSTS, marks cookies `Secure` and redirects any plain-HTTP request.

---

## Architecture

```
React SPA  ──HTTPS/JSON──▶  Flask API (auth + RBAC middleware)  ──ORM──▶  MySQL
 features/*                  features/*  (routes → service)               models/*
 core/ (shell, ui, auth)     core/ (security, errors, domain rules)
```

Strict 3-tier separation (SYS-NF-005): `routes.py` only parses requests and shapes responses, `service.py` holds the
business rules, `app/models` is the only layer that touches table definitions.

### One folder per user story
Both halves are organised so a story is a **self-contained folder** discovered automatically at start-up — no shared
file has to be edited to add or remove a story.

| Story | Backend `backend/app/features/…` | Frontend `frontend/src/features/…` | Tests `backend/tests/…` |
| --- | --- | --- | --- |
| US-01 Provisioning | `user_provisioning` | `user_provisioning` | `user_provisioning` |
| US-02 Password reset | `password_reset` | `password_reset` | `password_reset` |
| US-03 Profile | `profile` | `profile` | `profile` |
| US-04 Account management | `account_management` | `account_management` | `account_management` |
| US-05 Course setup | `course_setup` | `course_setup` | `course_setup` |
| US-06 Enrollment | `course_enrollment` | `course_enrollment` | `course_enrollment` |
| US-07 Schedule & roster isolation | `schedule` | `schedule` | `schedule` |
| US-08 Roll-call & 48 h lock | `attendance_marking` | `attendance_marking` | `attendance_marking` |
| US-09 Attendance override | `attendance_override` | `attendance_override` | `attendance_override` |
| US-10 Attendance dashboard | `attendance_dashboard` | `attendance_dashboard` | `attendance_dashboard` |
| US-11 Draft grade entry | `grade_entry` | `grade_entry` | `grade_entry` |
| US-12 Submit & publish grades | `grade_publication` | `grade_publication` | `grade_publication` |
| US-13 Regrade disputes | `regrade_disputes` | `regrade_disputes` | `regrade_disputes` |
| US-14 GPA & analytics | `analytics` | `analytics` | `analytics` |
| US-15 Metrics, CSV, security & perf | `admin_metrics` | `admin_metrics` | `admin_metrics` |

**Shared foundation** (not a story): `backend/app/{core,models,config.py,extensions.py,seed,__init__.py}`,
`backend/app/features/auth_session` (login / logout / me), `backend/{manage.py,run.py,requirements.txt,pytest.ini}`,
`backend/tests/{conftest.py,factories.py,core,seed}`, and `frontend/src/{core,styles,App.jsx,main.jsx}` plus tooling files.

* **Backend discovery** — every `app/features/<name>/__init__.py` exposes a Flask `bp`; `register_features()` mounts all of
  them under `/api/v1`.
* **Frontend discovery** — every `src/features/<name>/manifest.js` declares routes (with roles + sidebar entry) and
  *slot* contributions. `core/registry.js` collects them with `import.meta.glob`.
* **Slots** let stories extend each other's screens without importing one another: the dashboards render
  `<role>-dashboard` slots, the grade sheet renders `grade-entry-actions` (US-12 adds "Submit grades"), and the grades list
  renders `grade-row-actions` (US-13 adds the "Dispute" button).

## Requirement coverage
| Requirement | Where |
| --- | --- |
| SYS-F-001…004 | `user_provisioning`, `password_reset`, `profile`, `account_management` |
| SYS-F-005…008 | `course_setup`, `course_enrollment`, `schedule` (+ `core/access.py` roster isolation) |
| SYS-F-009…012 | `attendance_marking` (`ATTENDANCE_FREEZE_HOURS=48` enforced in the service), `attendance_override`, `attendance_dashboard` |
| SYS-F-013…017 | `grade_entry`, `grade_publication`, `regrade_disputes` (+ `core/grading.py` state machine) |
| SYS-F-018…020 | `analytics`, `admin_metrics` |
| SYS-NF-001/002 | indexed queries, pooled connections, READ COMMITTED + deadlock retry (`core/db_retry.py`); `tests/admin_metrics/test_performance.py` |
| SYS-NF-004 | responsive layout 375 → 1920 px; roll-call reachable in ≤ 3 clicks from login |
| SYS-NF-005 | layered structure; `pytest --cov` gate ≥ 70 % |
| PRJ-SR-001 | `core/transport.py`, `run.py --https`, `scripts/gen_dev_cert.py` |
| PRJ-SR-002 | bcrypt cost 12 (`core/security.py`) |
| PRJ-SR-003 | HTTP-only JWT cookie, 48 h expiry, re-validated against the DB on every request |
| PRJ-SR-004 | `@auth_required(roles…)` on every endpoint (a test fails if an endpoint is left unprotected) |
| PRJ-SR-005 | SQLAlchemy parameterised queries; input sanitisation in `core/validation.py` |

## Design decisions worth knowing
* **Profile fields** — union of the SRS and US-03: phone, personal email, home address, emergency contact.
* **Enrollment window** — SYS-F-006's admin-controlled window is a single on/off toggle on the catalog page.
* **Grade scale** — 90/80/70/60 cut-offs → A/B/C/D, below 60 → F; GPA on a 10-point scale (A=10, B=8, C=6, D=4, F=0), credit-weighted. Under Review
  grades keep counting toward GPA until a dispute is resolved.
* **Attendance percentage** counts only sessions that have been held *and* marked by faculty.
* **Sessions** are concrete dated events (SRS SYS-F-007) with an optional "repeat weekly" helper in the admin form.
* **Timestamps** are stored in UTC and rendered in the viewer's local time zone.
* Seeded accounts share one bcrypt hash (cost 12) so seeding is fast; accounts created in the app always get a unique salt.
