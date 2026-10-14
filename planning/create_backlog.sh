#!/usr/bin/env bash
# Creates labels, sprint milestones, a GitHub Project (board) and one issue per backlog story.
# Usage:  bash create_backlog.sh            (uses defaults below)
#         REPO=owner/repo OWNER=owner bash create_backlog.sh
set -euo pipefail

REPO="${REPO:-SE-miniproject1/mini-project-documents}"
OWNER="${OWNER:-${REPO%/*}}"
PROJECT_TITLE="${PROJECT_TITLE:-BBMS Product Backlog}"

command -v gh >/dev/null || { echo "Install GitHub CLI: https://cli.github.com"; exit 1; }
command -v jq >/dev/null || { echo "Install jq: https://jqlang.github.io/jq/"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run: gh auth login"; exit 1; }
# Projects need the 'project' scope. This is a no-op if you already have it.
gh auth refresh -s project >/dev/null 2>&1 || true

echo "==> Labels"
mk_label() { gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force >/dev/null; }
mk_label "functional"   "1d76db" "Functional requirement story"
mk_label "nonfunctional" "5319e7" "Non-functional requirement story"
mk_label "documentation" "0e8a16" "Documentation or deliverable"
mk_label "priority:high"   "b60205" "High priority"
mk_label "priority:medium" "fbca04" "Medium priority"
for p in 2 3 5 8; do mk_label "SP-$p" "c5def5" "Story points: $p"; done
for e in "Foundation" "SF-1" "SF-2" "SF-3" "SF-4" "SF-5" "SF-6" "Nonfunctional" "Documentation"; do
  mk_label "epic:$e" "bfd4f2" "Epic $e"
done

echo "==> Milestones (sprints)"
mk_ms() { # title, due(or empty), description
  if gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title' | grep -qx "$1"; then return; fi
  if [ -n "$2" ]; then
    gh api "repos/$REPO/milestones" -f title="$1" -f description="$3" -f due_on="${2}T23:59:59Z" >/dev/null
  else
    gh api "repos/$REPO/milestones" -f title="$1" -f description="$3" >/dev/null
  fi
}

mk_ms 'Sprint 1' '2026-10-23' 'Sprint 1 (19 Oct - 23 Oct): donor, collection and screening core with a working demo'
mk_ms 'Sprint 2' '2026-10-30' 'Sprint 2 (26 Oct - 30 Oct): inventory, hospital request/issue, camps, admin, docs; freeze at end'
mk_ms 'Stretch' '' 'Stretch backlog: only if capacity allows; otherwise documented as deferred'

echo "==> Project board"
PROJ_JSON=$(gh project list --owner "$OWNER" --format json --limit 100)
PNUM=$(echo "$PROJ_JSON" | jq -r --arg t "$PROJECT_TITLE" '.projects[] | select(.title==$t) | .number' | head -1)
if [ -z "$PNUM" ]; then
  PNUM=$(gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json | jq -r '.number')
fi
gh project link "$PNUM" --owner "$OWNER" --repo "$REPO" >/dev/null 2>&1 || true
PID=$(gh project view "$PNUM" --owner "$OWNER" --format json | jq -r '.id')

FIELDS=$(gh project field-list "$PNUM" --owner "$OWNER" --format json)
SP_FIELD=$(echo "$FIELDS" | jq -r '.fields[] | select(.name=="Story Points") | .id')
if [ -z "$SP_FIELD" ]; then
  SP_FIELD=$(gh project field-create "$PNUM" --owner "$OWNER" --name "Story Points" --data-type NUMBER --format json | jq -r '.id')
fi
SPR_FIELD=$(echo "$FIELDS" | jq -r '.fields[] | select(.name=="Sprint") | .id')
if [ -z "$SPR_FIELD" ]; then
  SPR_FIELD=$(gh project field-create "$PNUM" --owner "$OWNER" --name "Sprint" --data-type SINGLE_SELECT --single-select-options "Sprint 1,Sprint 2,Stretch" --format json | jq -r '.id')
fi
SPR_JSON=$(gh project field-list "$PNUM" --owner "$OWNER" --format json | jq -c '.fields[] | select(.name=="Sprint")')

add_story() { # title, body, labels, milestone, assignee, points, sprint
  local URL ITEM OPT
  URL=$(gh issue create --repo "$REPO" --title "$1" --body "$2" --label "$3" --milestone "$4" --assignee "$5")
  ITEM=$(gh project item-add "$PNUM" --owner "$OWNER" --url "$URL" --format json | jq -r '.id')
  gh project item-edit --id "$ITEM" --project-id "$PID" --field-id "$SP_FIELD" --number "$6" >/dev/null
  OPT=$(echo "$SPR_JSON" | jq -r --arg s "$7" '.options[] | select(.name==$s) | .id')
  gh project item-edit --id "$ITEM" --project-id "$PID" --field-id "$SPR_FIELD" --single-select-option-id "$OPT" >/dev/null
  echo "  created: $1 -> $URL"
}

echo "==> Issues"
add_story '[US-01] Project setup, CI and linting' '**Epic:** Foundation
**Story points:** 3
**Priority:** High
**Planned:** Sprint 1
**Owner:** Aadish (@Sonuaadi0706)
**SRS non-functional / constraints:** CON-1, CON-3, CON-4

### Acceptance criteria
- [ ] Django 5 project with PostgreSQL settings via environment variables
- [ ] GitHub Actions runs flake8 and tests on every PR
- [ ] Branch protection: PR with one review required on main

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:Foundation' 'Sprint 1' 'Sonuaadi0706' 3 'Sprint 1'
add_story '[US-02] Authentication, roles and access control' '**Epic:** Foundation
**Story points:** 8
**Priority:** High
**Planned:** Sprint 1
**Owner:** Aadish (@Sonuaadi0706)
**SRS non-functional / constraints:** NFR-SEC1, NFR-SEC2, NFR-SEC3, NFR-SEC4, NFR-SEC5, NFR-SEC11

### Acceptance criteria
- [ ] Login and logout with salted-hash passwords
- [ ] Roles: Donor, Staff, Hospital User, Administrator
- [ ] Server-side permission check on every view
- [ ] Password policy, 5-attempt lockout for 15 min, 30 min session timeout

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-8,epic:Foundation' 'Sprint 1' 'Sonuaadi0706' 8 'Sprint 1'
add_story '[US-03] Base layout and role-based navigation' '**Epic:** Foundation
**Story points:** 3
**Priority:** High
**Planned:** Sprint 1
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS non-functional / constraints:** UI-1, UI-2, UI-4

### Acceptance criteria
- [ ] Header, role-scoped left nav, footer, responsive down to 360px
- [ ] Field-level error display and error banner standard

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:Foundation' 'Sprint 1' 'nnivedithaparmesh-cpu' 3 'Sprint 1'
add_story '[US-04] Donor registration and unique donor ID' '**Epic:** SF-1 Donor Registration and Eligibility
**Story points:** 5
**Priority:** High
**Planned:** Sprint 1
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-1, REQ-2

### Acceptance criteria
- [ ] Form captures all REQ-1 fields incl. consent timestamp
- [ ] Donor ID generated as DNR + 8 digits, immutable, shown on confirmation

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-1' 'Sprint 1' 'Dhanya-KM' 5 'Sprint 1'
add_story '[US-05] Registration validation (duplicates and age)' '**Epic:** SF-1 Donor Registration and Eligibility
**Story points:** 3
**Priority:** High
**Planned:** Sprint 1
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-3, REQ-4

### Acceptance criteria
- [ ] Duplicate mobile or email rejected with the exact SRS message; nothing persisted
- [ ] Age outside 18-65 rejected with the exact SRS message

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:SF-1' 'Sprint 1' 'Dhanya-KM' 3 'Sprint 1'
add_story '[US-06] Medical history and permanent deferral' '**Epic:** SF-1 Donor Registration and Eligibility
**Story points:** 3
**Priority:** High
**Planned:** Sprint 2
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-5

### Acceptance criteria
- [ ] Declared permanent-deferral condition marks donor Permanently Deferred
- [ ] Temporary conditions recorded with review date

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:SF-1' 'Sprint 2' 'Dhanya-KM' 3 'Sprint 2'
add_story '[US-07] Eligibility engine' '**Epic:** SF-1 Donor Registration and Eligibility
**Story points:** 5
**Priority:** High
**Planned:** Sprint 1
**Owner:** Balaraj (@balaraj74)
**SRS functional requirements:** REQ-6
**SRS non-functional / constraints:** NFR-Q4

### Acceptance criteria
- [ ] Checks age, weight >=50kg, Hb >=12.5, systolic 100-140, 90 days since last donation
- [ ] Reports every failing criterion, not only the first

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-1' 'Sprint 1' 'balaraj74' 5 'Sprint 1'
add_story '[US-08] Collection guard and next-eligible date' '**Epic:** SF-1 Donor Registration and Eligibility
**Story points:** 3
**Priority:** High
**Planned:** Sprint 1
**Owner:** Aadish (@Sonuaadi0706)
**SRS functional requirements:** REQ-7, REQ-8
**SRS non-functional / constraints:** NFR-S5

### Acceptance criteria
- [ ] Collection blocked for non-Eligible donor with reason and review date
- [ ] Next eligible date = last donation + interval; expired deferral auto-clears

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:SF-1' 'Sprint 1' 'Sonuaadi0706' 3 'Sprint 1'
add_story '[US-09] Record donation and unit ID with barcode' '**Epic:** SF-2 Donation and Collection
**Story points:** 5
**Priority:** High
**Planned:** Sprint 1
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-9, REQ-10

### Acceptance criteria
- [ ] Donation event stores donor, datetime, volume, bag lot, site, staff
- [ ] Unit ID BU + 10 digits, printable label with barcode

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-2' 'Sprint 1' 'nnivedithaparmesh-cpu' 5 'Sprint 1'
add_story '[US-10] Unit state machine and quarantine' '**Epic:** SF-2 Donation and Collection
**Story points:** 5
**Priority:** High
**Planned:** Sprint 1
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-11, REQ-16
**SRS non-functional / constraints:** NFR-S7

### Acceptance criteria
- [ ] New units are Quarantined and excluded from availability, issue and reservation
- [ ] Unit model holds all REQ-16 attributes and status set

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-2' 'Sprint 1' 'Dhanya-KM' 5 'Sprint 1'
add_story '[US-11] Screening results, release and discard' '**Epic:** SF-2 Donation and Collection
**Story points:** 8
**Priority:** High
**Planned:** Sprint 1
**Owner:** Balaraj (@balaraj74)
**SRS functional requirements:** REQ-12, REQ-13, REQ-14
**SRS non-functional / constraints:** NFR-S1

### Acceptance criteria
- [ ] All five tests required before release
- [ ] Available only if all Non-Reactive; any Reactive discards and alerts admin
- [ ] Donor identity in alert restricted to admin

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-8,epic:SF-2' 'Sprint 1' 'balaraj74' 8 'Sprint 1'
add_story '[US-12] Audit log for status transitions' '**Epic:** SF-3 Inventory and Stock
**Story points:** 3
**Priority:** High
**Planned:** Sprint 2
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-23
**SRS non-functional / constraints:** NFR-SEC10, SEC-OBJ-2

### Acceptance criteria
- [ ] Immutable record per status transition with user, time, reason
- [ ] No edit or delete path through any view or admin

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:SF-3' 'Sprint 2' 'Dhanya-KM' 3 'Sprint 2'
add_story '[US-13] Inventory console: stock counts' '**Epic:** SF-3 Inventory and Stock
**Story points:** 5
**Priority:** High
**Planned:** Sprint 1
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-17
**SRS non-functional / constraints:** NFR-P5

### Acceptance criteria
- [ ] Available counts by blood group and component
- [ ] Reflects committed changes within 5 seconds

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-3' 'Sprint 1' 'nnivedithaparmesh-cpu' 5 'Sprint 1'
add_story '[US-14] Inventory filters, transfer and manual discard' '**Epic:** SF-3 Inventory and Stock
**Story points:** 5
**Priority:** Medium
**Planned:** Stretch
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-18, REQ-21, REQ-22

### Acceptance criteria
- [ ] Combined filters on group, component, location, status, expiry range
- [ ] Transfer logs source, destination, user; discard needs reason and confirmation; Issued units cannot be discarded

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-5,epic:SF-3' 'Stretch' 'nnivedithaparmesh-cpu' 5 'Stretch'
add_story '[US-15] Auto-expiry and near-expiry alerts' '**Epic:** SF-3 Inventory and Stock
**Story points:** 5
**Priority:** High
**Planned:** Sprint 2
**Owner:** Aadish (@Sonuaadi0706)
**SRS functional requirements:** REQ-19, REQ-20
**SRS non-functional / constraints:** NFR-S2

### Acceptance criteria
- [ ] Scheduled job moves expired units to Expired at least every 24h
- [ ] Units within 7 days of expiry flagged; daily digest to staff

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-3' 'Sprint 2' 'Sonuaadi0706' 5 'Sprint 2'
add_story '[US-16] Component separation' '**Epic:** SF-2 Donation and Collection
**Story points:** 5
**Priority:** Medium
**Planned:** Sprint 2
**Owner:** Balaraj (@balaraj74)
**SRS functional requirements:** REQ-15

### Acceptance criteria
- [ ] Parent split into PRBC, plasma, platelets with own IDs and expiry
- [ ] Children linked to parent and donor; parent closed

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-5,epic:SF-2' 'Sprint 2' 'balaraj74' 5 'Sprint 2'
add_story '[US-17] Hospital raises blood request' '**Epic:** SF-4 Hospital Request and Issue
**Story points:** 5
**Priority:** High
**Planned:** Sprint 2
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-24, REQ-25
**SRS non-functional / constraints:** BR-7

### Acceptance criteria
- [ ] Request ID REQ + 8 digits; urgency Routine/Urgent/Emergency
- [ ] Non-positive quantity and past required-by rejected with field-named message

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-4' 'Sprint 2' 'nnivedithaparmesh-cpu' 5 'Sprint 2'
add_story '[US-18] Request queue, approve and reject' '**Epic:** SF-4 Hospital Request and Issue
**Story points:** 5
**Priority:** High
**Planned:** Sprint 2
**Owner:** Balaraj (@balaraj74)
**SRS functional requirements:** REQ-26, REQ-27

### Acceptance criteria
- [ ] Queue ordered Emergency first then required-by ascending
- [ ] Reject requires reason communicated to hospital

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-4' 'Sprint 2' 'balaraj74' 5 'Sprint 2'
add_story '[US-19] Allocate, issue and fulfilment status' '**Epic:** SF-4 Hospital Request and Issue
**Story points:** 8
**Priority:** High
**Planned:** Sprint 2
**Owner:** Aadish (@Sonuaadi0706)
**SRS functional requirements:** REQ-28, REQ-29, REQ-30
**SRS non-functional / constraints:** NFR-S3, NFR-S4

### Acceptance criteria
- [ ] Only Available, exact-group, unexpired units allocatable
- [ ] Reserve atomically on allocation, Issued on confirmation with full record
- [ ] Fulfilled vs Partially Fulfilled with shortfall

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-8,epic:SF-4' 'Sprint 2' 'Sonuaadi0706' 8 'Sprint 2'
add_story '[US-20] Cancel request' '**Epic:** SF-4 Hospital Request and Issue
**Story points:** 2
**Priority:** Medium
**Planned:** Stretch
**Owner:** Balaraj (@balaraj74)
**SRS functional requirements:** REQ-31

### Acceptance criteria
- [ ] Hospital cancels own Pending or Approved request; reservations released
- [ ] Blocked once any unit is Issued

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-2,epic:SF-4' 'Stretch' 'balaraj74' 2 'Stretch'
add_story '[US-21] Camps: create, list and enrol' '**Epic:** SF-5 Camp Management
**Story points:** 5
**Priority:** Medium
**Planned:** Sprint 2
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-32, REQ-33, REQ-34, REQ-35

### Acceptance criteria
- [ ] Camp create with future-date and time-range validation
- [ ] Donor listing by date; enrolment refused with next eligible date if ineligible

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-5,epic:SF-5' 'Sprint 2' 'Dhanya-KM' 5 'Sprint 2'
add_story '[US-22] Camp collection link and closure' '**Epic:** SF-5 Camp Management
**Story points:** 3
**Priority:** Medium
**Planned:** Sprint 2
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-36, REQ-37

### Acceptance criteria
- [ ] Units carry camp ID as collection site
- [ ] Close camp shows actual vs target and blocks further collections

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-3,epic:SF-5' 'Sprint 2' 'Dhanya-KM' 3 'Sprint 2'
add_story '[US-23] Availability search for hospitals' '**Epic:** SF-6 Search, Notification and Reporting
**Story points:** 3
**Priority:** High
**Planned:** Stretch
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-38
**SRS non-functional / constraints:** NFR-P2, NFR-SEC7

### Acceptance criteria
- [ ] Counts by group and component only; no unit or donor identifiers for hospital users

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-3,epic:SF-6' 'Stretch' 'nnivedithaparmesh-cpu' 3 'Stretch'
add_story '[US-24] Notifications: dispatcher, reminders, shortage appeal' '**Epic:** SF-6 Search, Notification and Reporting
**Story points:** 8
**Priority:** Medium
**Planned:** Stretch
**Owner:** Aadish (@Sonuaadi0706)
**SRS functional requirements:** REQ-39, REQ-40, REQ-41
**SRS non-functional / constraints:** NFR-P6

### Acceptance criteria
- [ ] Async SMS and email with 3 retries then email fallback
- [ ] Eligibility and 24h camp reminders; shortage appeal max once per 30 days

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-8,epic:SF-6' 'Stretch' 'Sonuaadi0706' 8 'Stretch'
add_story '[US-25] Reports, export and data scoping' '**Epic:** SF-6 Search, Notification and Reporting
**Story points:** 8
**Priority:** Medium
**Planned:** Stretch
**Owner:** Dhanya (@Dhanya-KM)
**SRS functional requirements:** REQ-42, REQ-43, REQ-44
**SRS non-functional / constraints:** NFR-P4, NFR-Q8

### Acceptance criteria
- [ ] Six reports over a date range per Appendix B.7
- [ ] PDF and CSV export with name, range, user, timestamp
- [ ] Hospital users see only own data

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:medium,SP-8,epic:SF-6' 'Stretch' 'Dhanya-KM' 8 'Stretch'
add_story '[US-26] Admin: users, hospitals and configuration' '**Epic:** SF-6 Search, Notification and Reporting
**Story points:** 5
**Priority:** High
**Planned:** Sprint 2
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS functional requirements:** REQ-45, REQ-46
**SRS non-functional / constraints:** NFR-Q10

### Acceptance criteria
- [ ] Create, modify, deactivate users with exactly one role; register hospitals
- [ ] Configurable thresholds (interval, age, weight, Hb, shelf lives) without code change

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'functional,priority:high,SP-5,epic:SF-6' 'Sprint 2' 'nnivedithaparmesh-cpu' 5 'Sprint 2'
add_story '[US-27] Safety rule tests and concurrency hardening' '**Epic:** Nonfunctional
**Story points:** 3
**Priority:** High
**Planned:** Sprint 2
**Owner:** Balaraj (@balaraj74)
**SRS non-functional / constraints:** NFR-S1, NFR-S2, NFR-S3, NFR-S4

### Acceptance criteria
- [ ] Negative tests: untested, expired, wrong-group units cannot be issued
- [ ] Concurrent allocation of same unit test passes

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'nonfunctional,priority:high,SP-3,epic:Nonfunctional' 'Sprint 2' 'balaraj74' 3 'Sprint 2'
add_story '[US-28] Security, quality and performance hardening' '**Epic:** Nonfunctional
**Story points:** 5
**Priority:** Medium
**Planned:** Stretch
**Owner:** Balaraj (@balaraj74)
**SRS non-functional / constraints:** NFR-SEC9, NFR-Q5, NFR-P1, NFR-P3

### Acceptance criteria
- [ ] CSRF, escaping, parameter binding verified
- [ ] Line coverage >= 70%, screen render under 3s at P95

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'nonfunctional,priority:medium,SP-5,epic:Nonfunctional' 'Stretch' 'balaraj74' 5 'Stretch'
add_story '[US-29] Documentation, deviations log and demo video' '**Epic:** Documentation
**Story points:** 2
**Priority:** High
**Planned:** Sprint 2
**Owner:** Niveditha (@nnivedithaparmesh-cpu)
**SRS non-functional / constraints:** OR-6

### Acceptance criteria
- [ ] Deviations from SRS, SAD and Test Plan documented
- [ ] 1-minute and 2-minute sprint videos uploaded to repo

### Definition of done
- [ ] PR raised by the assignee and reviewed by a repo owner before merge
- [ ] Tests from docs/Test-Plan.md for the listed requirements pass
- [ ] Any deviation from SRS/SAD recorded in the deviations log' 'documentation,priority:high,SP-2,epic:Documentation' 'Sprint 2' 'nnivedithaparmesh-cpu' 2 'Sprint 2'
echo "Done. Open: https://github.com/orgs/$OWNER/projects/$PNUM"
