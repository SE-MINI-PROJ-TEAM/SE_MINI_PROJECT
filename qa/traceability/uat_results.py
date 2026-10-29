"""Fills docs/uat/UAT-RESULTS.md from the Playwright run of qa/uat/uat.spec.js (qa/reports/uat/results.json).

    python qa/traceability/uat_results.py

Only the Result / Defect # / Comment columns of the criteria table and the exploratory findings are rewritten. The
header, the testers, the defect log and the sign-off table are maintained by hand and never touched.
"""
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS = os.path.join(ROOT, "qa", "reports", "uat", "results.json")
TARGET = os.path.join(ROOT, "docs", "uat", "UAT-RESULTS.md")

EXPLORATORY = {
    "EX-1": "Try to break the grade lifecycle as a **student**",
    "EX-2": "Try to see or change **another faculty member's**",
    "EX-3": "Use the whole app with the **keyboard only**",
    "EX-4": "Enter **hostile input** in every text field",
    "EX-5": "Run **two sessions at once**",
}


def cell(text):
    return re.sub(r"\s+", " ", str(text)).replace("|", "\\|").strip()


def collect():
    data = json.load(open(RESULTS, encoding="utf-8"))
    found = {}

    def walk(suite):
        for spec in suite.get("specs", []):
            test = spec["tests"][0]
            result = test["results"][-1] if test["results"] else {}
            ident = spec["title"].split(" ", 1)[0]
            notes = [a["description"] for a in test.get("annotations", []) if a["type"] == "comment"]
            if test["status"] == "skipped":
                status, comment = "BLOCKED", next(iter(test.get("annotations", []) and [a.get("description", "") for a in test["annotations"] if a["type"] == "skip"] or []), "") or "Skipped."
            elif test["status"] == "expected":
                status, comment = "PASS", " ".join(notes)
            else:
                error = (result.get("error", {}).get("message") or "failed").splitlines()
                clean = re.sub(r"\x1b\[[0-9;]*m", "", " ".join(error[:3]))
                status, comment = "FAIL", f"{clean[:300]}"
            found[ident] = (status, comment, round(result.get("duration", 0) / 1000, 1))
        for child in suite.get("suites", []):
            walk(child)

    for top in data["suites"]:
        walk(top)
    return found, data


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def main():
    found, raw = collect()
    text = open(TARGET, encoding="utf-8").read()

    def criterion_row(match):
        ident, criterion = match.group(1), match.group(2)
        if ident not in found:
            return match.group(0)
        status, comment, _ = found[ident]
        defect = "" if status == "PASS" else "see defect log"
        return f"| {ident} | {criterion} | {status} | {defect} | {cell(comment)} |"

    text = re.sub(r"^\| (US-\d+\.\d+) \| (.*?) \|[^\n]*$", criterion_row, text, flags=re.M)

    def exploratory_row(match):
        label = match.group(1)
        for ident, prefix in EXPLORATORY.items():
            if label.startswith(prefix) and ident in found:
                status, comment, _ = found[ident]
                prefix_text = "" if status == "PASS" else "**FAILED** - "
                tester = re.match(r"^\|[^|]*\|([^|]*)\|", match.group(0)).group(1).strip() or "TBD"
                return f"| {label} | {tester} | {prefix_text}{cell(comment)} |"
        return match.group(0)

    text = re.sub(r"^\| (Try to[^|]*|Use the whole[^|]*|Enter \*\*hostile[^|]*|Run \*\*two[^|]*) \|[^\n]*$", exploratory_row, text, flags=re.M)

    # The header (version, environment, testers, dates) and the sign-off table are maintained by hand.
    total = sum(1 for k in found if k.startswith("US-"))
    passed = sum(1 for k, v in found.items() if k.startswith("US-") and v[0] == "PASS")

    open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print(f"UAT-RESULTS.md updated: {passed}/{total} criteria PASS, {len(found) - total} exploratory charters recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
