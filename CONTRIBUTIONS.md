# Contribution Record

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

Everything here is taken from the git history and from GitHub's pull request data on 03 November 2026. Re-run `python3 tools/contribution_report.py` to refresh the commit tables.

**Read this first.** Git records who committed a change, not who drafted the text or thought of the design. The counts below describe commits, not effort. Merge commits are left out.

## Commits

### Merged to main

| Person | Commits | Share | Lines added | Lines removed | Where the commits are |
|---|---|---|---|---|---|
| G A Aadish | 50 | 63% | 16734 | 248 | src (359), docs (38), (root) (18), diagrams (8) |
| Niveditha | 13 | 16% | 369 | 14 | docs (8), diagrams (6), submission (3), src (1) |
| Balaraj R | 10 | 12% | 2182 | 173 | docs (4), diagrams (4), (root) (3), tools (3) |
| Dhanya K M | 6 | 7% | 298 | 25 | diagrams (5), (root) (1), docs (1) |
| **Total** | **79** | | | | |

### Pending in open branches, not yet on main

| Person | Commits | Share | Lines added | Lines removed | Where the commits are |
|---|---|---|---|---|---|
| Niveditha | 20 | 71% | 2144 | 258 | src (22), docs (17), (root) (3) |
| Dhanya K M | 5 | 17% | 489 | 3 | src (16), (root) (1) |
| Balaraj R | 2 | 7% | 298 | 0 | src (2) |
| G A Aadish | 1 | 3% | 130 | 18 | (root) (1), tools (1) |
| **Total** | **28** | | | | |

"Pending" counts every remote branch that is not on `main`. That includes the open pull requests #50, #77, #84, #85, #86, #89 and #90, and also old branches whose pull requests were closed, so it overstates live work. G A Aadish's pending commit is this record.

## What the implementation sprints changed

The Deliverable 1 and 2 documents were written by all four members, as the commit history shows. The implementation sprints were different.

The sprint plan (`planning/BACKLOG.md`) shared the work: Sprint 1 gave 14 points to G A Aadish and 13 each to the others. **All Sprint 1 code, 11 stories and 53 points, was committed from G A Aadish's account**, including the stories the plan assigned to the others. Those Sprint 1 issues were reassigned to G A Aadish, so the project board matches the commits.

**Sprint 2 code on `main` was also committed from G A Aadish's account**, with one exception: Niveditha committed the first admin models (`69336eb`). The Sprint 2 issues for US-16, US-18, US-22, US-26 and US-27 are still assigned to the members the plan named. Each of those issues has a comment linking the merged code, and the members were asked to check it.

From 02 November, G A Aadish used an AI coding assistant (Claude) for part of his work. On `main` that covers US-27 (`7891439`), US-24 (`28b1ba8`), the close-out notes in `planning/BACKLOG.md` (`7d26c9e` and later) and the refresh of this record. It also covers the fixes and additions pushed to other members' pull requests: the US-23 test fix (#89), the US-28 test fixes (#77) and the US-25 report screens (#86). These commits are authored by G A Aadish and counted under his name above, since the tables count by author.

Since 28 October the other members have also written code, in pull requests that are not merged yet:
- **Niveditha:** US-23 availability search (#89), US-14 inventory filters, transfer and discard (#90), and admin configuration (#84).
- **Dhanya K M:** US-25 report definitions (#86).
- **Balaraj R:** US-28 hardening tests (#77). Balaraj also opened a second set of pull requests for US-07, US-11, US-16, US-18, US-20 and US-27 (#76, #79 to #83). Those duplicated stories already merged and were closed.

## What each member's commits contain

**G A Aadish.** Repository structure. SRS skeleton, sections 1 and 2, SF-4 to SF-6 and the security objectives. The architecture diagram and the whole Software Architecture and Design Specification. The Deliverable 2 plan and the audit fixes. The product backlog. The Django project, CI, and every story on `main`: US-01 to US-13, US-15 to US-22, US-24, US-26 and US-27. The Sprint 1 demo video. The deviations log.

**Niveditha.** Created the repository (first commit). SRS sections 3, 6 and 7. The SF-5 and SF-6 test cases. An upload of the six diagram images. The Word build script and the generated Word files. A correction of the SRS revision history dates. The first admin models on `main`. Open: the deployment guide and the Sprint 2 demo video (#50, #85), and the work in #84, #89 and #90.

**Balaraj R.** SRS SF-1 to SF-3, and in the same commit section 4 text and Appendices A, B and C. The Test Plan structure and the first case tables, the traceability checker, the data flow diagram sources, the diagram index and the Appendix B spreadsheets. The IEEE-layout Test Plan with generated traceability and the security validation cases. A correction of the revision history. Open: #77.

**Dhanya K M.** The use case and entity relationship diagrams and their images. The use case diagram embedded in SRS section 4. An earlier version of this record. Open: #86.

## Reviews and merges

Approving reviews recorded on GitHub:
- **Balaraj R: 14.** Pull request #20, and 13 Sprint 1 and 2 implementation pull requests, from #54 to #74.
- **Dhanya K M: 6.** #13 and #19, plus four of Balaraj R's closed duplicates.
- **Niveditha: 3.** #11, #16 and #18.
- **G A Aadish: 0.**

The implementation stories were merged in a stack, each into the branch below it. Most stack pull requests were approved by Balaraj R when they merged into the branch below. On 02 November the stack reached `main` through #57, #61, #69, #70, #72, #73 and #75, and those pull requests had **no recorded approving review**. Neither did #87 (US-27), #88, #66 (demo video) or #91 (US-24). Among the earlier document pull requests, #1, #2, #6, #12, #14, #15, #17, #21, #51 and #52 were also merged without one. The working agreement asks for one approval from someone other than the author.

## What this project does not contain

No test has been run against a deployed system. The Test Plan's Actual Result and Test Result columns still read `Not executed` and `Pending`. The automated tests in `src/` (516 on `main`, run by CI on SQLite and PostgreSQL) are separate from those manual test cases.
