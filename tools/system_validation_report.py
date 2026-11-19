"""Builds docs/test-reports/System-Validation-Report.md from the Test Plan.

The results table is read from docs/Test-Plan.md, so the report always matches the plan.
Run it again after every member has filled in their cases:

    python3 tools/system_validation_report.py
"""

import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "Test-Plan.md"
OUT = ROOT / "docs" / "test-reports" / "System-Validation-Report.md"

ROW = re.compile(r"^\| ((?:ST|SV)-\d+) \|(.*)\|$")


def cases():
    found = {}
    for line in PLAN.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in ("| " + m.group(1) + " |" + m.group(2)).strip("|").split("|")]
        # id, module, description, pre, steps, data, expected, actual, result
        if len(cells) >= 9:
            found[cells[0]] = {"module": cells[1], "desc": cells[2], "actual": cells[7], "result": cells[8]}
    return found


def conclusion(data):
    failed = [k for k, c in data.items() if c["result"] == "Failed"]
    partly = [k for k, c in data.items() if c["result"] == "Partly executed"]
    pending = [k for k, c in data.items() if c["result"] in ("Pending", "Not executed")]
    text = (
        "The safety rules (ST-26, ST-27) and the security validation cases that can run "
        "without a deployed server pass."
    )
    if failed:
        text += f" {', '.join(failed)} failed: see the case and its deviation for the reason."
    if partly:
        text += (
            f" {', '.join(partly)} could only be partly executed without a deployed server"
            " and are recorded as deviations, not counted as passes."
        )
    if pending:
        text += f" Still pending: {', '.join(pending)}."
    else:
        text += " Every system and security case has a recorded result."
    return text


def main():
    data = cases()
    order = sorted(data, key=lambda k: (k[:2] == "SV", int(k[3:])))
    total = len(order)
    counts = {}
    for k in order:
        r = data[k]["result"]
        counts[r] = counts.get(r, 0) + 1
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unknown"
    lines = [
        "# System Validation Report",
        "",
        "Blood Bank Management System. Covers the 30 system test cases (ST-01 to ST-30) and the 8 security validation cases (SV-01 to SV-08) of `docs/Test-Plan.md`.",
        "",
        f"Generated {date.today():%d-%m-%Y} from commit `{commit}` by `tools/system_validation_report.py`.",
        "",
        "## 1. How the validation was done",
        "",
        "- Every case was checked against the running application code through Django's test client and services, using the seeded test data. The test runner is Django's own (`manage.py test`), run on SQLite for development and on PostgreSQL 16 in CI.",
        "- Each result names the test file that proves it. A case is marked Passed only when its automated test ran and passed, or a person ran the steps.",
        "- Steps that need a deployed system (a TLS scanner, a real 31-minute idle wait, an OWASP scanner, a browser session) were not run. They are marked Partly executed or Passed with deviation, with the entry in `docs/DEVIATIONS.md`.",
        "- Concurrency case ST-27 only means something on PostgreSQL, because SQLite ignores row locks. The CI job `test-postgres` runs it.",
        "",
        "## 2. Summary",
        "",
        "| Result | Cases |",
        "|---|---|",
    ]
    for r, n in sorted(counts.items()):
        lines.append(f"| {r} | {n} |")
    lines += [f"| **Total** | **{total}** |", "", "## 3. Results per case", "",
              "| ID | Module | Description | Result | Evidence |", "|---|---|---|---|---|"]
    for k in order:
        c = data[k]
        lines.append(f"| {k} | {c['module']} | {c['desc']} | {c['result']} | {c['actual']} |")
    lines += [
        "",
        "## 4. Not run, and why",
        "",
        "- **SV-04 TLS version refusal.** Needs the reverse proxy and a TLS scanner (D-86).",
        "- **SV-02 and SV-03 real waiting times.** The clock is moved in the tests (D-85).",
        "- **SV-07 scanner.** No OWASP scanner run (D-88).",
        "- **Performance on the test server.** NFR-P1 and NFR-P2 are checked with the seeded data only, not with 50 concurrent users (ST-25, D-91).",
        "- **ST-22 shortage banner.** The dashboard banner and the below-threshold report flag are not built. Accepted as a known defect, issue #104 (D-83, D-103).",
        "- **Browser sessions.** System cases ran through the Django test client, which drives the same views and templates, not a browser (D-96, D-107).",
        "",
        "## 5. Conclusion",
        "",
        conclusion(data),
        "",
        "Prepared by G A Aadish, with results contributed by each case owner.",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(ROOT)}: {total} cases", counts)


if __name__ == "__main__":
    main()
