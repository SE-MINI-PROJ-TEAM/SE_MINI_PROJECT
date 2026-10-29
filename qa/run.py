"""QA stage runner. It executes INSIDE the `qa` container; start it through ./qa.sh (or .\\qa.ps1), never directly.

    consistency   OpenAPI spec is current, every acceptance criterion has automated evidence, frontend builds
    unit          PyTest (MySQL) with the >= 70 % coverage gate + Vitest              (STP: Unit, Integration)
    static        Bandit, pip-audit, npm audit                                          (STP: Security)
    integration   Newman collection against the running API container                  (STP: Integration / System)
    e2e           Playwright against the nginx-served UI: flows, 3-click roll-call,
                  responsive layout, axe WCAG 2.1 AA                                    (STP: System, TC-UX-01)
    docs          Regenerate openapi.json, the acceptance matrix and the UAT script (UAT-RESULTS.md is never overwritten)
    demo          Re-record the two sprint demo videos (60 s / 120 s MP4)
    report        Build qa/reports/TEST-EXECUTION-REPORT.md from the result files

k6 (performance) and OWASP ZAP (security scan) are their own containers: see docker-compose.qa.yml.
The API, nginx and MySQL are sibling containers on the same network; the database is re-seeded before every
black-box stage, so each stage starts from identical demo data. Results land in qa/reports/<stage>/.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QA = os.path.join(ROOT, "qa")
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
DEMO = os.path.join(ROOT, "demo")
REPORTS = os.path.join(QA, "reports")


def say(msg):
    print(f"\n\033[1;36m>> {msg}\033[0m", flush=True)


def run(cmd, cwd=ROOT, env=None, check=False):
    result = subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, text=True)
    if check and result.returncode:
        raise SystemExit(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def report_dir(name):
    path = os.path.join(REPORTS, name)
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return path


def require_container():
    if os.environ.get("QA_IN_DOCKER") != "1":
        raise SystemExit("Run the QA stages through ./qa.sh (or .\\qa.ps1): they need the containers defined in docker-compose.qa.yml.")


def seed():
    say(f"Seeding database `{os.environ.get('DB_NAME')}` (schema reset + demo dataset)")
    run([sys.executable, "manage.py", "seed", "--reset"], cwd=BACKEND, check=True)


# ------------------------------------------------------------------------------------------------ stages
def stage_consistency():
    failures = 0
    say("OpenAPI specification matches the Flask routes")
    failures += run([sys.executable, os.path.join(QA, "openapi", "generate.py"), "--check"]).returncode != 0
    say("Every acceptance criterion has a verified automated check")
    failures += run([sys.executable, os.path.join(QA, "traceability", "acceptance.py"), "--check"]).returncode != 0
    say("Frontend production build")
    failures += run(["npm", "run", "build"], cwd=FRONTEND).returncode != 0
    return 1 if failures else 0


def stage_unit():
    out = report_dir("unit")
    say("Unit + API tests (PyTest, MySQL) with the >= 70 % coverage gate")
    result = run(
        [sys.executable, "-m", "pytest", "-q", f"--junitxml={out}/junit.xml", "--cov", f"--cov-report=xml:{out}/coverage.xml",
         f"--cov-report=html:{out}/htmlcov", "--cov-report=term:skip-covered"],
        cwd=BACKEND,
    )
    say("Frontend unit tests (Vitest)")
    front = run(["npx", "vitest", "run", "--reporter=junit", f"--outputFile={out}/frontend-junit.xml"], cwd=FRONTEND)
    return 1 if (result.returncode or front.returncode) else 0


def stage_static():
    out = report_dir("static")
    failures = 0
    say("Bandit - static analysis of the Python source")
    failures += run([sys.executable, "-m", "bandit", "-r", "backend/app", "-f", "json", "-o", f"{out}/bandit.json",
                     "--severity-level", "medium", "-q"]).returncode != 0
    say("pip-audit - known vulnerabilities in Python dependencies")
    failures += run([sys.executable, "-m", "pip_audit", "-r", "backend/requirements.txt", "-f", "json", "-o", f"{out}/pip-audit.json",
                     "--progress-spinner", "off",
                     "--ignore-vuln", "PYSEC-2025-183"]).returncode != 0  # PyJWT "weak encryption": disputed, no fix (docs/qa/SECURITY-TRIAGE.md)
    say("npm audit - known vulnerabilities in frontend dependencies (high+)")
    audit = subprocess.run(["npm", "audit", "--omit=dev", "--audit-level=high", "--json"], cwd=FRONTEND, text=True, capture_output=True)
    open(os.path.join(out, "npm-audit.json"), "w", encoding="utf-8").write(audit.stdout or "{}")
    failures += audit.returncode != 0
    return 1 if failures else 0


def stage_integration():
    out = report_dir("integration")
    run([sys.executable, os.path.join(QA, "newman", "build_collection.py")], check=True)
    seed()
    say("Newman - black-box API collection (login cookies, RBAC, full grade lifecycle)")
    return run(
        ["npx", "newman", "run", "newman/collection.json", "-e", "newman/environment.json", "--env-var", f"baseUrl={os.environ['QA_API_URL']}",
         "--reporters", "cli,junit,json", "--reporter-junit-export", f"{out}/newman-junit.xml", "--reporter-json-export", f"{out}/newman.json"],
        cwd=QA,
    ).returncode


def stage_e2e():
    out = report_dir("e2e")
    seed()
    say("Playwright - E2E flows, 3-click roll-call, responsive layout, axe accessibility (WCAG 2.1 AA)")
    return run(["npx", "playwright", "test", "--config", "e2e/playwright.config.js"], cwd=QA,
               env={"BASE_URL": os.environ["QA_UI_URL"], "E2E_OUT": out}).returncode


def stage_uat():
    out = report_dir("uat")
    seed()
    say("UAT - docs/uat/UAT-SCRIPT.md executed through the browser (51 criteria + 5 exploratory charters)")
    shutil.rmtree(os.path.join(ROOT, "docs", "uat", "evidence"), ignore_errors=True)
    result = run(["npx", "playwright", "test", "--config", "uat/playwright.config.js"], cwd=QA,
                 env={"BASE_URL": os.environ["QA_UI_URL"], "UAT_REPORTS": out, "UAT_EVIDENCE": os.path.join(ROOT, "docs", "uat", "evidence"),
                      "HTTPS_HOST": "web", "K6_SUMMARY": os.path.join(REPORTS, "k6", "summary.json")})
    say("Writing docs/uat/UAT-RESULTS.md")
    writer = run([sys.executable, os.path.join(QA, "traceability", "uat_results.py")])
    return 1 if (result.returncode or writer.returncode) else 0


def stage_docs():
    failures = 0
    for script in (("openapi", "generate.py"), ("traceability", "acceptance.py"), ("traceability", "uat.py")):
        say(f"Generating {script[1]}")
        failures += run([sys.executable, os.path.join(QA, *script)]).returncode != 0
    return 1 if failures else 0


def stage_demo():
    videos = os.path.join(DEMO, "videos")
    os.makedirs(videos, exist_ok=True)
    for name, seconds, dwell in (("sprint1", 60, "1450"), ("sprint2", 120, "3200")):
        seed()
        say(f"Recording {name} ({seconds} s)")
        result = run(["node", "record.mjs", name], cwd=DEMO, env={"BASE_URL": os.environ["QA_UI_URL"], "CAPTION_DWELL": dwell})
        if result.returncode:
            print(f"Recording {name} failed; see demo/videos/{name}-failure.png")
            return 1
        # -ss drops the blank first paint; -t trims the held final frame so the length is exact.
        run(["ffmpeg", "-v", "error", "-y", "-ss", "0.6", "-i", f"{videos}/{name}-raw.webm", "-t", str(seconds), "-r", "30",
             "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", f"{videos}/{name}.mp4"], check=True)
        for leftover in (f"{name}-raw.webm", f"{name}.json"):
            try:
                os.remove(os.path.join(videos, leftover))
            except FileNotFoundError:
                pass
    return 0


def stage_report():
    say("Building the Test Execution & Acceptance Report")
    return run([sys.executable, os.path.join(QA, "report.py")]).returncode


STAGES = {
    "consistency": stage_consistency, "unit": stage_unit, "static": stage_static, "integration": stage_integration,
    "e2e": stage_e2e, "uat": stage_uat, "docs": stage_docs, "demo": stage_demo, "report": stage_report,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stages", nargs="+", choices=list(STAGES))
    args = parser.parse_args()
    require_container()

    outcome = {}
    for name in args.stages:
        started = time.time()
        outcome[name] = (STAGES[name](), time.time() - started)

    print("\n" + "=" * 60)
    for name, (code, seconds) in outcome.items():
        print(f"{'PASS' if code == 0 else 'FAIL':<5} {name:<12} {seconds:6.1f}s")
    print("=" * 60)
    sys.exit(0 if all(code == 0 for code, _ in outcome.values()) else 1)


if __name__ == "__main__":
    main()
