"""Entrypoint of the ZAP container (docker-compose.qa.yml, service `zap`).

Runs three scans and applies the STP gate "no High / Critical alert":
  1. API scan   - active, OpenAPI-driven, authenticated as Admin          -> zap-api.json
  2. API baseline - passive checks of the API's own responses              -> zap-baseline.json
  3. UI baseline  - passive checks of the nginx-served front end (headers) -> zap-ui.json
Exit code 1 when any scan reports a High alert or fails to produce a report.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

API = os.environ["API_URL"].rstrip("/")
WEB = os.environ["WEB_URL"].rstrip("/")
WRK = "/zap/wrk"


def wait_for(url, seconds=90):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return
        except Exception:
            time.sleep(1)
    sys.exit(f"timed out waiting for {url}")


def admin_token():
    request = urllib.request.Request(
        f"{API}/api/v1/auth/login",
        data=json.dumps({"identifier": "admin001@srs.edu", "password": "Password@123"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return response.headers["Set-Cookie"].split("srs_token=")[1].split(";")[0]


def high_alerts(path):
    if not os.path.exists(path):
        return None
    report = json.load(open(path, encoding="utf-8"))
    return sorted({a["name"] for site in report.get("site", []) for a in site.get("alerts", []) if int(a.get("riskcode", 0)) >= 3})


def zap(script, *args, report):
    """Run one ZAP script. Its exit codes 1/2 mean "findings"; the gate below reads the JSON report instead.
    A scan launched right after another can fail to boot (the previous ZAP is still releasing its lock), so retry."""
    for attempt in (1, 2, 3):
        shown = " ".join(a if "Bearer" not in a else "<auth config, Bearer token redacted>" for a in args)  # keep credentials out of logs
        print(f"\n>> {script} {shown} (attempt {attempt})", flush=True)
        subprocess.run([script, *args], cwd="/zap")
        if os.path.exists(os.path.join(WRK, report)):
            return
        time.sleep(15)


def main():
    wait_for(f"{API}/api/v1/health")
    wait_for(WEB + "/")
    shutil.copy("/zap/scripts/rules.conf", os.path.join(WRK, "rules.conf"))
    shutil.copy("/zap/openapi/openapi.json", os.path.join(WRK, "openapi.json"))

    auth = (
        "-config replacer.full_list(0).description=auth -config replacer.full_list(0).enabled=true "
        "-config replacer.full_list(0).matchtype=REQ_HEADER -config replacer.full_list(0).matchstring=Authorization "
        f'-config replacer.full_list(0).replacement="Bearer {admin_token()}"'
    )
    zap("zap-api-scan.py", "-t", "/zap/wrk/openapi.json", "-f", "openapi", "-O", WEB, "-c", "rules.conf",
        "-r", "zap-api.html", "-J", "zap-api.json", "-I", "-z", auth, report="zap-api.json")
    zap("zap-baseline.py", "-t", f"{WEB}/api/v1/health", "-c", "rules.conf", "-r", "zap-baseline.html", "-J", "zap-baseline.json", "-I",
        report="zap-baseline.json")
    zap("zap-baseline.py", "-t", WEB + "/", "-c", "rules.conf", "-r", "zap-ui.html", "-J", "zap-ui.json", "-I", report="zap-ui.json")

    failed = False
    print("\n==== ZAP gate: no High or Critical alerts ====")
    for name in ("zap-api", "zap-baseline", "zap-ui"):
        highs = high_alerts(os.path.join(WRK, f"{name}.json"))
        if highs is None:
            print(f"FAIL {name}: no report produced")
            failed = True
        elif highs:
            print(f"FAIL {name}: {highs}")
            failed = True
        else:
            print(f"OK   {name}: no High or Critical alerts")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
