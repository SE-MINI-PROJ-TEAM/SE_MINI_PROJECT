"""Builds the Test Execution & Acceptance Report from the real result files in qa/reports/.

    python qa/report.py        ->  qa/reports/TEST-EXECUTION-REPORT.md   (+ summary.json, GitHub step summary when in CI)

Implements the STP section 14 metrics: % test cases executed, % passed, requirement coverage. Nothing in the report is
typed by hand: every number is read from a JUnit / JSON result file, so it is only as good as the last test run.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPORTS = os.path.join(HERE, "reports")
sys.path.insert(0, os.path.join(HERE, "traceability"))
from tc_map import TC_EVIDENCE  # noqa: E402


# ------------------------------------------------------------------------------------------ loaders
def load_json(*parts):
    path = os.path.join(REPORTS, *parts)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def load_junit(*parts):
    """-> list of {suite, name, status('passed'|'failed'|'skipped'), time}; None when the file is missing."""
    path = os.path.join(REPORTS, *parts)
    if not os.path.exists(path):
        return None
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        status = "passed"
        if case.find("failure") is not None or case.find("error") is not None:
            status = "failed"
        elif case.find("skipped") is not None:
            status = "skipped"
        cases.append({"suite": case.get("classname", ""), "name": case.get("name", ""), "status": status, "time": float(case.get("time") or 0)})
    return cases


def load_newman():
    data = load_json("integration", "newman.json")
    collection_path = os.path.join(HERE, "newman", "collection.json")
    if data is None:
        return None
    if not os.path.exists(collection_path):  # CI report job: the collection is generated, not committed
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "newman", "build_collection.py")], check=True, capture_output=True)
    folders = []
    for folder in json.load(open(collection_path, encoding="utf-8"))["item"]:
        folders += [folder["name"]] * len(folder["item"])
    executions = data["run"]["executions"]
    rows = []
    for index, ex in enumerate(executions):
        folder = folders[index] if index < len(folders) else "?"
        assertions = ex.get("assertions", [])
        failed = sum(1 for a in assertions if a.get("error"))
        rows.append({"folder": folder, "name": ex["item"]["name"], "assertions": len(assertions), "failed": failed})
    return rows


def parse_stp_traceability():
    """requirement -> [TC ids] from STP section 13."""
    text = open(os.path.join(ROOT, "docs", "stp", "markdown", "13-test-case-management-and-traceability.md"), encoding="utf-8").read()
    mapping = {}
    for m in re.finditer(r"\|\s*\*\*([A-Z]+-[A-Z]+-\d+)\*\*\s*\|(.+?)\|\s*`(TC-[A-Z]+-\d+)`", text):
        mapping.setdefault(m.group(1), {"summary": m.group(2).strip(), "tcs": []})["tcs"].append(m.group(3))
    return mapping


# ------------------------------------------------------------------------------------------ evaluation
class Results:
    def __init__(self):
        self.unit = load_junit("unit", "junit.xml")
        self.vitest = load_junit("unit", "frontend-junit.xml")
        self.e2e = load_junit("e2e", "junit.xml")
        self.newman = load_newman()
        self.k6 = load_json("k6", "summary.json")
        self.zap = {n: load_json("zap", f"{n}.json") for n in ("zap-api", "zap-baseline", "zap-ui")}
        self.bandit = load_json("static", "bandit.json")
        self.pip = load_json("static", "pip-audit.json")
        self.npm = load_json("static", "npm-audit.json")
        self.coverage = self._coverage()

    def _coverage(self):
        path = os.path.join(REPORTS, "unit", "coverage.xml")
        if not os.path.exists(path):
            return None
        root = ET.parse(path).getroot()
        return {"line": float(root.get("line-rate", 0)) * 100, "branch": float(root.get("branch-rate", 0)) * 100}

    # each evaluator returns (executed, failed) counts of individual checks, or None if its stage was not run
    def check(self, selector):
        kind = selector[0]
        if kind == "unit":
            return self._junit(self.unit, selector[1], selector[2] if len(selector) > 2 else None, by="suite")
        if kind == "e2e":
            return self._junit(self.e2e, selector[1], selector[2] if len(selector) > 2 else None, by="any")
        if kind == "newman":
            if self.newman is None:
                return None
            rows = [r for r in self.newman if r["folder"].startswith(selector[1])]
            return (sum(r["assertions"] for r in rows), sum(r["failed"] for r in rows)) if rows else (0, 0)
        if kind == "k6":
            if self.k6 is None:
                return None
            metrics = self.k6["metrics"]
            executed = failed = 0
            for key in selector[1]:
                thresholds = metrics.get(key, {}).get("thresholds", {})
                executed += len(thresholds)
                failed += sum(1 for breached in thresholds.values() if breached)
            return executed, failed
        if kind == "zap":
            highs = [self.zap_high(r) for r in self.zap.values() if r is not None]
            return (len(highs), sum(1 for h in highs if h)) if highs else None
        if kind == "static":
            return self.static_counts()
        if kind == "coverage":
            return None if self.coverage is None else (1, 0 if self.coverage["line"] >= selector[1] else 1)
        return None

    @staticmethod
    def _junit(cases, needle, names, by):
        if cases is None:
            return None
        selected = [c for c in cases if (needle in c["suite"] if by == "suite" else needle in c["suite"] + " " + c["name"])]
        if names:
            selected = [c for c in selected if any(n in c["name"].lower() for n in names)]
        selected = [c for c in selected if c["status"] != "skipped"]
        return len(selected), sum(1 for c in selected if c["status"] == "failed")

    @staticmethod
    def zap_high(report):
        return [a["name"] for s in report.get("site", []) for a in s.get("alerts", []) if int(a.get("riskcode", 0)) >= 3]

    def static_counts(self):
        if self.bandit is None and self.pip is None and self.npm is None:
            return None
        failed = executed = 0
        if self.bandit is not None:
            executed += 1
            t = self.bandit["metrics"]["_totals"]
            failed += 1 if (t.get("SEVERITY.HIGH", 0) or t.get("SEVERITY.MEDIUM", 0)) else 0
        if self.pip is not None:
            executed += 1
            failed += 1 if any(d.get("vulns") for d in self.pip["dependencies"]) else 0
        if self.npm is not None:
            executed += 1
            v = self.npm.get("metadata", {}).get("vulnerabilities", {})
            failed += 1 if (v.get("high", 0) or v.get("critical", 0)) else 0
        return executed, failed


def evaluate_tcs(results):
    out = {}
    for tc, selectors in TC_EVIDENCE.items():
        if selectors[0][0] == "waived":
            out[tc] = {"status": "WAIVED", "evidence": [("waived by agreement", selectors[0][1])], "executed": 0, "failed": 0}
            continue
        if selectors[0][0] == "manual":
            out[tc] = {"status": "MANUAL", "evidence": [("manual", selectors[0][1])], "executed": 0, "failed": 0}
            continue
        evidence, executed, failed = [], 0, 0
        for selector in selectors:
            counts = results.check(selector)
            name = selector[0] + (f": {selector[1]}" if len(selector) > 1 and isinstance(selector[1], str) else "")
            if counts is None:
                evidence.append((name, "not run"))
                continue
            evidence.append((name, f"{counts[0] - counts[1]}/{counts[0]} ok"))
            executed += counts[0]
            failed += counts[1]
        status = "NOT RUN" if executed == 0 else ("FAIL" if failed else "PASS")
        out[tc] = {"status": status, "evidence": evidence, "executed": executed, "failed": failed}
    return out


# ------------------------------------------------------------------------------------------ rendering
def suite_row(label, cases):
    if cases is None:
        return f"| {label} | not run | | | |"
    passed = sum(1 for c in cases if c["status"] == "passed")
    failed = sum(1 for c in cases if c["status"] == "failed")
    skipped = sum(1 for c in cases if c["status"] == "skipped")
    return f"| {label} | {len(cases)} | {passed} | {failed} | {sum(c['time'] for c in cases):.0f} s |" + (f" ({skipped} skipped)" if skipped else "")


def uat_status():
    path = os.path.join(ROOT, "docs", "uat", "UAT-RESULTS.md")
    if not os.path.exists(path):
        return None
    rows = re.findall(r"^\| (US-\d+\.\d+) \|.*?\|\s*(PASS|FAIL|BLOCKED)?\s*\|", open(path, encoding="utf-8").read(), re.M)
    total = len(rows)
    counts = {k: sum(1 for _, r in rows if r == k) for k in ("PASS", "FAIL", "BLOCKED")}
    return {"total": total, **counts, "pending": total - sum(counts.values())}


def acceptance_status():
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "traceability", "acceptance.py"), "--check"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout.strip() or r.stderr.strip()).splitlines()[0] if (r.stdout or r.stderr) else ""


def build():
    results = Results()
    tcs = evaluate_tcs(results)
    requirements = parse_stp_traceability()

    total_tc = len(tcs)
    executed = [t for t, v in tcs.items() if v["status"] in ("PASS", "FAIL")]
    passed = [t for t in executed if tcs[t]["status"] == "PASS"]
    waived = [t for t, v in tcs.items() if v["status"] == "WAIVED"]
    req_ok = [r for r, v in requirements.items() if all(tcs.get(tc, {}).get("status") in ("PASS", "WAIVED") for tc in v["tcs"])]

    gates = []

    def gate(name, ok, detail):
        gates.append((name, ok, detail))

    gate("All executed test cases pass", len(executed) > 0 and len(passed) == len(executed), f"{len(passed)}/{len(executed)} executed TCs pass")
    gate("Backend coverage >= 70% (SYS-NF-005)", results.coverage is not None and results.coverage["line"] >= 70,
         f"{results.coverage['line']:.1f}% lines / {results.coverage['branch']:.1f}% branches" if results.coverage else "not run")
    if results.k6:
        m = results.k6["metrics"]
        p95 = m["http_req_duration{scenario:sessions}"]["p(95)"]
        breached = [k for k, v in m.items() for ok in v.get("thresholds", {}).values() if ok]
        gate("p95 latency < 800 ms with 500 sessions (SYS-NF-001)", p95 < 800 and not breached, f"p95 = {p95:.1f} ms")
        burst = m["checks{scenario:burst}"]
        gate("200 simultaneous submissions, 0 failures (SYS-NF-002)", burst["fails"] == 0 and burst["passes"] >= 200, f"{burst['passes']} ok / {burst['fails']} failed")
    else:
        gate("Performance (k6)", False, "not run")
    highs = [h for r in results.zap.values() if r for h in results.zap_high(r)]
    gate("No High/Critical ZAP alerts (PRJ-SR-001..005)", all(r is not None for r in results.zap.values()) and not highs,
         "no alerts above Medium" if not highs else f"{sorted(set(highs))}")
    static = results.static_counts()
    gate("Static analysis & dependency audit clean", static is not None and static[1] == 0, "Bandit / pip-audit / npm audit" if static else "not run")
    acc_ok, acc_msg = acceptance_status()
    gate("Every acceptance criterion has automated evidence", acc_ok, acc_msg)
    overall = all(ok for _, ok, _ in gates)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = [
        "# Test Execution & Acceptance Report",
        "",
        f"_Generated {now} by `qa/report.py` from the result files in `qa/reports/`. Every figure is read from tool output._",
        "",
        f"## Verdict: automated quality gates **{'PASS' if overall else 'FAIL'}**",
        "",
        "| Gate | Result | Detail |", "| --- | --- | --- |",
    ]
    L += [f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |" for n, ok, d in gates]

    L += ["", "## Execution summary", "", "| Suite (tool) | Tests | Passed | Failed | Duration |", "| --- | --- | --- | --- | --- |",
          suite_row("Unit + API (PyTest, MySQL)", results.unit), suite_row("Frontend unit (Vitest)", results.vitest),
          suite_row("E2E / usability / accessibility (Playwright + axe)", results.e2e)]
    if results.newman is not None:
        asserts = sum(r["assertions"] for r in results.newman)
        bad = sum(r["failed"] for r in results.newman)
        L.append(f"| Integration (Newman) | {len(results.newman)} requests / {asserts} assertions | {asserts - bad} | {bad} | |")
    else:
        L.append("| Integration (Newman) | not run | | | |")

    L += ["", "## STP section 14 metrics", "",
          "| Metric | Value |", "| --- | --- |",
          f"| Test cases executed | **{len(executed)} / {total_tc}** ({100 * len(executed) / total_tc:.0f}%) - the rest is listed below as manual or waived |",
          f"| Test cases closed by agreement with the instructor (not executable here) | **{len(waived)}** ({', '.join(waived) or 'none'}) |",
          f"| Test cases passed | **{len(passed)} / {len(executed) or 1}** ({100 * len(passed) / (len(executed) or 1):.0f}%) |",
          f"| Requirement coverage (verified requirements) | **{len(req_ok)} / {len(requirements)}** ({100 * len(req_ok) / max(len(requirements), 1):.0f}%) |",
          "| Defect density / aging | tracked in GitHub issues (label `defect`); not derivable from test output |", ""]

    L += ["## Test case results", "", "| TC | Status | Evidence |", "| --- | --- | --- |"]
    for tc, v in tcs.items():
        L.append(f"| {tc} | {v['status']} | " + "; ".join(f"{n} ({r})" for n, r in v["evidence"]) + " |")

    L += ["", "## Requirement coverage", "", "| Requirement | Summary | Test cases | Verified |", "| --- | --- | --- | --- |"]
    for req, v in requirements.items():
        statuses = [tcs.get(tc, {}).get("status") for tc in v["tcs"]]
        ok = all(s in ("PASS", "WAIVED") for s in statuses)
        verdict = ("waived by agreement" if "WAIVED" in statuses else "yes") if ok else ("manual" if "MANUAL" in statuses else "NO")
        L.append(f"| {req} | {v['summary']} | {', '.join(v['tcs'])} | {verdict} |")

    if results.k6:
        m = results.k6["metrics"]
        d = m["http_req_duration{scenario:sessions}"]
        L += ["", "## Performance (k6)", "",
              f"500 concurrent sessions, {m['http_reqs{scenario:sessions}']['count']:,} requests at {m['http_reqs{scenario:sessions}']['rate']:.0f} req/s "
              f"(4 server processes), then a 200-request simultaneous submission burst.", "",
              "| Metric | Value |", "| --- | --- |",
              f"| Latency avg / median | {d['avg']:.1f} ms / {d['med']:.1f} ms |", f"| Latency p90 / p95 / p99 | {d['p(90)']:.1f} / {d['p(95)']:.1f} / {d['p(99)']:.1f} ms |",
              f"| Max latency | {d['max']:.0f} ms |",
              f"| Failed requests (sessions) | {m['http_req_failed{scenario:sessions}']['passes']} of {m['http_reqs{scenario:sessions}']['count']:,} |",
              f"| Burst: submissions accepted | {m['checks{scenario:burst}']['passes']} / 200 |"]

    L += ["", "## Security", ""]
    if results.bandit:
        t = results.bandit["metrics"]["_totals"]
        L.append(f"- **Bandit** (Python SAST): {t.get('SEVERITY.HIGH', 0)} high, {t.get('SEVERITY.MEDIUM', 0)} medium, {t.get('SEVERITY.LOW', 0)} low findings.")
    if results.pip:
        vulnerable = [d["name"] for d in results.pip["dependencies"] if d.get("vulns")]
        L.append(f"- **pip-audit**: {len(results.pip['dependencies'])} Python packages checked, {len(vulnerable)} with known vulnerabilities{': ' + ', '.join(vulnerable) if vulnerable else ''}.")
    if results.npm:
        v = results.npm.get("metadata", {}).get("vulnerabilities", {})
        L.append(f"- **npm audit** (production deps): {v.get('critical', 0)} critical, {v.get('high', 0)} high, {v.get('moderate', 0)} moderate, {v.get('low', 0)} low.")
    for name, report in results.zap.items():
        if report:
            by_risk = {}
            for s in report.get("site", []):
                for a in s.get("alerts", []):
                    by_risk.setdefault(a["riskdesc"].split(" ")[0], []).append(a["name"])
            summary = ", ".join(f"{k}: {len(v)}" for k, v in sorted(by_risk.items())) or "no alerts"
            L.append(f"- **OWASP ZAP {name.replace('zap-', '')} scan**: {summary}.")

    uat = uat_status()
    L += ["", "## Acceptance", "",
          f"- Acceptance criteria with automated evidence: **{acc_msg}**",
          "- Matrix: `docs/uat/ACCEPTANCE-MATRIX.md`; script: `docs/uat/UAT-SCRIPT.md`."]
    if uat:
        L.append(f"- UAT results (`docs/uat/UAT-RESULTS.md`): {uat['PASS']} pass, {uat['FAIL']} fail, {uat['BLOCKED']} blocked, {uat['pending']} pending of {uat['total']} criteria. "
                 + ("**UAT not started.**" if uat["pending"] == uat["total"] else ""))
    L.append("")

    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "TEST-EXECUTION-REPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    summary = {"verdict": "PASS" if overall else "FAIL", "gates": [{"name": n, "ok": ok, "detail": d} for n, ok, d in gates],
               "test_cases": {"total": total_tc, "executed": len(executed), "passed": len(passed)},
               "requirements": {"total": len(requirements), "verified": len(req_ok)}}
    json.dump(summary, open(os.path.join(REPORTS, "summary.json"), "w", encoding="utf-8"), indent=2)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(L[:30]) + "\n")
    print("\n".join(f"{'PASS' if ok else 'FAIL'}  {n}: {d}" for n, ok, d in gates))
    print(f"\nTest cases executed {len(executed)}/{total_tc}, passed {len(passed)}; requirements verified {len(req_ok)}/{len(requirements)}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(build())
