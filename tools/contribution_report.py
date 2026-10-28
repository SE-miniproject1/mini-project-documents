#!/usr/bin/env python3
"""Count who actually committed what, straight from git.

Usage, from the repository root:   python3 tools/contribution_report.py

Two groups are reported. "Merged" is every non-merge commit on origin/main. "Pending" is
every non-merge commit on a remote branch that has not been merged yet, which is work that
exists in open pull requests but is not on main. Merge commits are not counted.

Git records who committed a change, not who drafted the text, so these numbers describe
commits and not effort.
"""

import subprocess
from collections import defaultdict

# One person can commit under several names and addresses.
PEOPLE = {
    "G A Aadish": {"sonuaadish0706as@gmail.com"},
    "Niveditha": {"nnivedithaparmesh@gmail.com"},
    "Balaraj R": {"balarajr483@gmail.com", "balaraj@balarajr483@gmail.com"},
    "Dhanya K M": {"dhanyakm12@gmail.com"},
}
BY_EMAIL = {email: name for name, emails in PEOPLE.items() for email in emails}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def person(email, fallback):
    return BY_EMAIL.get(email.lower(), fallback)


def commits(rev_args):
    """Yield (person, [(added, removed, path), ...]) for each non-merge commit."""
    out = git("log", "--no-merges", "--numstat", "--format=@@%ae|%an", *rev_args)
    current, files = None, []
    for line in out.splitlines():
        if line.startswith("@@"):
            if current is not None:
                yield current, files
            email, _, name = line[2:].partition("|")
            current, files = person(email, name), []
        elif line.strip():
            added, removed, path = line.split("\t", 2)
            files.append((int(added) if added.isdigit() else 0, int(removed) if removed.isdigit() else 0, path))
    if current is not None:
        yield current, files


def summarise(rev_args):
    totals = defaultdict(lambda: {"commits": 0, "added": 0, "removed": 0, "areas": defaultdict(int)})
    for who, files in commits(rev_args):
        entry = totals[who]
        entry["commits"] += 1
        for added, removed, path in files:
            entry["added"] += added
            entry["removed"] += removed
            area = path.split("/")[0] if "/" in path else "(root)"
            entry["areas"][area] += 1
    return totals


def pending_branches():
    remote = git("branch", "-r", "--format=%(refname:short)").split()
    return [b for b in remote if b not in {"origin/main", "origin/HEAD"} and not b.endswith("/HEAD")]


def table(title, totals):
    rows = sorted(totals.items(), key=lambda item: -item[1]["commits"])
    total = sum(entry["commits"] for _, entry in rows) or 1
    lines = [f"### {title}", "", "| Person | Commits | Share | Lines added | Lines removed | Where the commits are |", "|---|---|---|---|---|---|"]
    for name, entry in rows:
        areas = ", ".join(f"{a} ({n})" for a, n in sorted(entry["areas"].items(), key=lambda kv: -kv[1])[:4])
        lines.append(
            f"| {name} | {entry['commits']} | {entry['commits'] * 100 // total}% | {entry['added']} | {entry['removed']} | {areas} |"
        )
    lines.append(f"| **Total** | **{sum(e['commits'] for _, e in rows)}** | | | | |")
    return "\n".join(lines)


def main():
    merged = summarise(["origin/main"])
    branches = pending_branches()
    pending = summarise([*branches, "--not", "origin/main"]) if branches else {}
    print(table("Merged to main", merged))
    print()
    print(table("Pending in open branches, not yet on main", pending))


if __name__ == "__main__":
    main()
