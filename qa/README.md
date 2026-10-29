# QA toolbox

Everything that tests the system beyond the PyTest suites in `backend/tests`, all of it **running in Docker**. Overview and rationale: [docs/qa/TEST-STRATEGY.md](../docs/qa/TEST-STRATEGY.md).

The host needs only Docker (Compose v2). No Python, Node, k6, ZAP or browser has to be installed.

## Usage
```powershell
.\qa.ps1 unit              # Windows;  ./qa.sh unit  on macOS / Linux / CI
.\qa.ps1 unit static       # any combination of stages
.\qa.ps1 all               # everything, then TEST-EXECUTION-REPORT.md
.\qa.ps1 down              # remove the QA containers and their data
```

| Stage | Container(s) | What it runs |
| --- | --- | --- |
| `consistency` | qa | OpenAPI spec is current, every acceptance criterion has automated evidence, frontend builds |
| `unit` | qa + MySQL | PyTest (>= 70 % coverage gate) and Vitest |
| `static` | qa | Bandit, pip-audit, npm audit |
| `integration` | qa + API + MySQL | Newman collection (147 requests) against the API container |
| `perf` | k6 + API + MySQL | 500 concurrent sessions and a 200-request burst |
| `zap` | ZAP + nginx + API + MySQL | Authenticated active API scan, API baseline, UI baseline, all through nginx |
| `e2e` | qa + nginx + API + MySQL | Playwright: flows, 3-click roll-call, responsive layout, axe WCAG 2.1 AA |
| `uat` | qa + nginx + API + MySQL | Executes `docs/uat/UAT-SCRIPT.md` through the UI (51 criteria + 5 exploratory charters), saves screenshots to `docs/uat/evidence/` and fills `docs/uat/UAT-RESULTS.md` (run `perf` first: US-15.3 reads the k6 summary) |
| `docs` | qa | Regenerates `openapi.json`, `docs/uat/ACCEPTANCE-MATRIX.md` and `docs/uat/UAT-SCRIPT.md` |
| `demo` | qa + nginx + API + MySQL | Re-records the two sprint demo videos into `demo/videos/` |
| `report` | qa | Builds `qa/reports/TEST-EXECUTION-REPORT.md` from the result files |

The QA stack (`docker-compose.qa.yml`, project `srs-qa`) is isolated from the application stack and from any local MySQL: its database lives in memory and is re-seeded before every black-box stage.

## What lives here
| Folder | Purpose |
| --- | --- |
| `Dockerfile` | The QA runner image (Python 3.12, Node 22, Playwright + Chromium, ffmpeg, Bandit, pip-audit) |
| `run.py` | Stage runner executed inside that container |
| `openapi/` | `generate.py` derives `openapi.json` from the Flask routes (CI fails if it is stale) |
| `newman/` | `build_collection.py` generates the Postman collection |
| `k6/` | `load.js`: the load test with thresholds |
| `zap/` | `scan.py` (the ZAP container's entrypoint) and `rules.conf` (rule overrides; keep empty unless triaged in `docs/qa/SECURITY-TRIAGE.md`) |
| `e2e/` | Playwright tests: access control, usability, accessibility, full workflows |
| `traceability/` | TC-ID evidence map, acceptance-criteria map, UAT document generators |
| `report.py` | The report builder |
| `reports/` | Generated output (git-ignored) |

Regenerate the derived documents with `.\qa.ps1 docs` (the filled-in `docs/uat/UAT-RESULTS.md` is never overwritten).
