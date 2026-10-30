# Contribution Record

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

Everything here is taken from the git history and from GitHub's pull request data on 28 October 2026. Re-run `python3 tools/contribution_report.py` to refresh the commit tables.

**Read this first.** Git records who committed a change, not who drafted the text or thought of the design. The counts below describe commits, not effort. Merge commits are left out.

## Commits

### Merged to main

| Person | Commits | Share | Lines added | Lines removed | Where the commits are |
|---|---|---|---|---|---|
| G A Aadish | 23 | 45% | 2362 | 140 | (root) (15), docs (14), src (12), diagrams (8) |
| Niveditha | 12 | 23% | 287 | 14 | docs (8), diagrams (6), submission (3), tools (1) |
| Balaraj R | 10 | 19% | 2182 | 173 | docs (4), diagrams (4), (root) (3), tools (3) |
| Dhanya K M | 6 | 11% | 298 | 25 | diagrams (5), (root) (1), docs (1) |
| **Total** | **51** | | | | |

### Pending in open branches, not yet on main

| Person | Commits | Share | Lines added | Lines removed | Where the commits are |
|---|---|---|---|---|---|
| G A Aadish | 14 | 66% | 7346 | 45 | src (211), docs (11) |
| Niveditha | 7 | 33% | 415 | 72 | docs (7) |
| **Total** | **21** | | | | |

"Pending" is work that exists on a branch and in an open pull request but is not on `main` yet. It includes a few old Niveditha branches whose content was later replaced, so the Niveditha figure there overstates live work.

Across `main` and the open branches together, the commit counts are **G A Aadish 37, Niveditha 19, Balaraj R 10, Dhanya K M 6**. They are not equal.

## What the implementation sprints changed

The Deliverable 1 and 2 documents were written by all four members, as the commit history above shows. The implementation sprints were different.

The sprint plan (`planning/BACKLOG.md`) shared the work: Sprint 1 gave 14 points to G A Aadish and 13 each to the others. **All Sprint 1 code, 11 stories and 53 points, was written and committed from G A Aadish's account**, including the stories the plan assigned to Niveditha, Dhanya K M and Balaraj R. The Sprint 2 work pushed so far follows the same pattern. The issues for those stories were reassigned to G A Aadish, each with a comment saying why, so the project board matches the commits.

Nobody else has committed code in `src/`. If the course assesses individual implementation work, this record is the honest answer to who did it.

## What each member's commits contain

**G A Aadish.** Repository structure. SRS skeleton, sections 1 and 2, SF-4 to SF-6 and the security objectives. The architecture diagram and the whole Software Architecture and Design Specification. The Deliverable 2 plan and the audit fixes. The product backlog. The Django project, CI, and every Sprint 1 story: sign-in with roles and lockout, the layout and navigation, donor registration and its validation, the eligibility engine and screening, the collection guard, the unit state machine, recording donations with barcode labels, screening results and release, and the inventory console. Sprint 2 stories as they are pushed, starting with the audit log.

**Niveditha.** Created the repository (first commit). SRS sections 3, 6 and 7. The SF-5 and SF-6 test cases. An upload of the six diagram images. The Word build script and the generated Word files. A correction of the SRS revision history dates.

**Balaraj R.** SRS SF-1 to SF-3, and in the same commit section 4 text and Appendices A, B and C. The Test Plan structure and the first case tables, the traceability checker, the data flow diagram sources, the diagram index and the Appendix B spreadsheets. The IEEE-layout Test Plan with generated traceability and the security validation cases. A correction of the revision history.

**Dhanya K M.** The use case and entity relationship diagrams and their images. The use case diagram embedded in SRS section 4. An earlier version of this record.

## Reviews and merges

Approving reviews recorded on GitHub: Niveditha approved 3 pull requests, Dhanya K M 2 and Balaraj R 1. G A Aadish has approved none.

Merged **without a recorded approving review**: #1, #2, #3, #6, #12, #14, #15, #17, #21, #51 and #52. Pull request #6 had only an automated Copilot comment. Eleven implementation pull requests (#54 to #64) are open and unreviewed, with Balaraj R and Dhanya K M requested as reviewers.

## What this project does not contain

No test has been run against a deployed system. The Test Plan's Actual Result and Test Result columns still read `Not executed` and `Pending`. The automated unit tests in `src/` are separate from those manual test cases.
