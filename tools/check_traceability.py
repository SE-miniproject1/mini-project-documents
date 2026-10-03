#!/usr/bin/env python3
"""Check that the SRS traceability matrix and the Test Plan agree.

Fails if a test case identifier is referenced by the matrix but never defined
in the Test Plan, or defined in the Test Plan but never referenced. Also checks
that every REQ tag defined in SRS section 5 appears in Appendix C.

Run from the Deliverable-1 directory:  python3 tools/check_traceability.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRS = ROOT / "docs" / "SRS.md"
TEST_PLAN = ROOT / "docs" / "Test-Plan.md"

CASE = re.compile(r"\b(?:UT|IT|ST)-\d+\b")


def sort_key(identifier):
    return identifier[:2], int(identifier[3:])


def main():
    srs = SRS.read_text(encoding="utf-8")
    plan = TEST_PLAN.read_text(encoding="utf-8")

    defined = set(re.findall(r"^\| ((?:UT|IT|ST)-\d+) \|", plan, re.M))
    referenced = set(CASE.findall(srs))

    declared_reqs = set(re.findall(r"^\*\*(REQ-\d+):", srs, re.M))
    traced_reqs = set(re.findall(r"^\| \d+ \| (REQ-\d+) \|", srs, re.M))

    problems = []
    dangling = sorted(referenced - defined, key=sort_key)
    orphaned = sorted(defined - referenced, key=sort_key)
    untraced = sorted(declared_reqs - traced_reqs, key=lambda r: int(r[4:]))
    phantom = sorted(traced_reqs - declared_reqs, key=lambda r: int(r[4:]))

    if dangling:
        problems.append(f"referenced in the matrix but not defined in the Test Plan: {dangling}")
    if orphaned:
        problems.append(f"defined in the Test Plan but never referenced by the matrix: {orphaned}")
    if untraced:
        problems.append(f"requirements declared in section 5 but missing from Appendix C: {untraced}")
    if phantom:
        problems.append(f"requirements traced in Appendix C but never declared in section 5: {phantom}")

    print(f"test cases defined in the Test Plan : {len(defined)}")
    print(f"test cases referenced by the matrix : {len(referenced)}")
    print(f"functional requirements declared    : {len(declared_reqs)}")
    print(f"functional requirements traced      : {len(traced_reqs)}")

    if problems:
        print("\nFAIL")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("\nOK: traceability is complete in both directions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
