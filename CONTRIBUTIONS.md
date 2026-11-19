# Contribution Record

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

Everything here is taken from the git history and from GitHub's pull request data on 19 November 2026. Re-run `python3 tools/contribution_report.py` to refresh the commit tables.

**Read this first.** Git records who committed a change, not who drafted the text or thought of the design. The counts below describe commits, not effort. Merge commits are left out.

## Commits

### Merged to main

| Person | Commits | Share | Lines added | Lines removed | Where the commits are |
|---|---|---|---|---|---|
| G A Aadish | 64 | 47% | 18106 | 361 | src (379), docs (45), (root) (25), planning (8) |
| Niveditha | 42 | 31% | 1849 | 382 | docs (34), src (29), diagrams (6), (root) (4) |
| Balaraj R | 14 | 10% | 4415 | 204 | docs (9), diagrams (4), submission (3), (root) (3) |
| Dhanya K M | 14 | 10% | 913 | 61 | src (17), docs (5), diagrams (5), (root) (2) |
| **Total** | **134** | | | | |

### Pending in open branches, not yet on main

Apart from the pull request that adds this record, none is open. The script still counts 18 commits on old remote branches whose pull requests were closed or superseded (16 by Niveditha, 1 by Balaraj R) and G A Aadish's commit of this record. None of it is live work.

## What the implementation sprints changed

The Deliverable 1 and 2 documents were written by all four members, as the commit history shows. The implementation sprints were different.

The sprint plan (`planning/BACKLOG.md`) shared the work: Sprint 1 gave 14 points to G A Aadish and 13 each to the others. **All Sprint 1 code, 11 stories and 53 points, was committed from G A Aadish's account**, including the stories the plan assigned to the others. Those Sprint 1 issues were reassigned to G A Aadish, so the project board matches the commits.

**Sprint 2 code on `main` was also committed from G A Aadish's account**, with one exception: Niveditha committed the first admin models (`69336eb`). The Sprint 2 issues for US-16, US-18, US-22, US-26 and US-27 are still assigned to the members the plan named. Each of those issues has a comment linking the merged code, and the members were asked to check it.

From 02 November, G A Aadish used an AI coding assistant (Claude) for part of his work, including his Deliverable 3 work (see below). On `main` that covers US-27 (`7891439`), US-24 (`28b1ba8`), the close-out notes in `planning/BACKLOG.md` (`7d26c9e` and later) and the refresh of this record. It also covers the fixes and additions pushed to other members' pull requests: the US-23 test fix (#89), the US-28 test fixes (#77) and the US-25 report screens (#86). These commits are authored by G A Aadish and counted under his name above, since the tables count by author.

From 28 October the other members also wrote code, all of it now merged:
- **Niveditha:** US-23 availability search (#89), US-14 inventory filters, transfer and discard (#90), the deployment guide and Sprint 2 video (#50). Her admin configuration pull request (#84) was closed because it clashed with the existing user model.
- **Dhanya K M:** US-25 report definitions (#86), and a search fix found during testing (`31a46f0`, NUL characters crashed PostgreSQL).
- **Balaraj R:** US-28 hardening tests (#77). His second set of pull requests for US-07, US-11, US-16, US-18, US-20 and US-27 (#76, #79 to #83) duplicated stories already merged and was closed.

## Deliverable 3: testing and reports

Each member ran the Test Plan cases for their own features, recorded the results, and wrote one report. All 112 cases now have a result: 79 Passed, 30 Passed with deviation, 2 Partly executed (SV-04, ST-25) and 1 Failed (ST-22, the dashboard shortage banner is not built).

| Member | Cases | Report | Pull request | Approved by |
|---|---|---|---|---|
| G A Aadish | 24: collection (UT-10 to UT-16, IT-05 to IT-09, ST-05 to ST-08) and security (SV-01 to SV-08) | System Validation Report, branch coverage setting, the Deliverable 3 plan | #98 | Balaraj R |
| Balaraj R | 23: donor registration (UT-01 to UT-09, IT-01 to IT-04, ST-01 to ST-04) and nonfunctional (ST-25 to ST-30) | Unit Test Report, Test Summary Report, Word copy | #101 | Dhanya K M |
| Dhanya K M | 33: inventory (UT-17 to UT-24, IT-10 to IT-13, ST-09 to ST-12) and requests (UT-25 to UT-33, IT-14 to IT-17, ST-13 to ST-16) | Code Coverage Report | #100 | Balaraj R |
| Niveditha | 32: camps (UT-34 to UT-39, IT-18 to IT-20, ST-17 to ST-19) and search, notifications and reports (UT-40 to UT-48, IT-21 to IT-26, ST-20 to ST-24) | Branch Coverage Report | #99 | G A Aadish |

G A Aadish's Deliverable 3 work used Claude: the new security tests, the result entries, the report generator, the two reviews of #99, and the merge of `main` into #99 that kept both members' deviation rows. G A Aadish merged #99 and #101 after they were approved.

## What each member's commits contain

**G A Aadish.** Repository structure. SRS skeleton, sections 1 and 2, SF-4 to SF-6 and the security objectives. The architecture diagram and the whole Software Architecture and Design Specification. The Deliverable 2 plan and the audit fixes. The product backlog. The Django project, CI, and every story on `main`: US-01 to US-13, US-15 to US-22, US-24, US-26 and US-27. The Sprint 1 demo video. The deviations log. The Deliverable 3 collection and security cases and the System Validation Report (#98).

**Niveditha.** Created the repository (first commit). SRS sections 3, 6 and 7. The SF-5 and SF-6 test cases. An upload of the six diagram images. The Word build script and the generated Word files. A correction of the SRS revision history dates. The first admin models on `main`. The deployment guide and Sprint 2 demo video (#50), US-23 (#89) and US-14 (#90). The Deliverable 3 camp, search, notification and report cases and the Branch Coverage Report (#99).

**Balaraj R.** SRS SF-1 to SF-3, and in the same commit section 4 text and Appendices A, B and C. The Test Plan structure and the first case tables, the traceability checker, the data flow diagram sources, the diagram index and the Appendix B spreadsheets. The IEEE-layout Test Plan with generated traceability and the security validation cases. A correction of the revision history. US-28 hardening tests (#77). The Deliverable 3 donor registration and nonfunctional cases, the Unit Test and Test Summary reports and the Word copy (#101).

**Dhanya K M.** The use case and entity relationship diagrams and their images. The use case diagram embedded in SRS section 4. An earlier version of this record. US-25 report definitions (#86). The Deliverable 3 inventory and request cases, the US-14 test tags and the Code Coverage Report (#100).

## Reviews and merges

Approving reviews recorded on GitHub:
- **Balaraj R: 16.** #20, 13 Sprint 1 and 2 implementation pull requests from #54 to #74, and #98 and #100 in Deliverable 3.
- **Dhanya K M: 7.** #13 and #19, four of Balaraj R's closed duplicates, and #101.
- **Niveditha: 3.** #11, #16 and #18.
- **G A Aadish: 2.** #94 and #99.

The implementation stories were merged in a stack, each into the branch below it. Most stack pull requests were approved by Balaraj R when they merged into the branch below. On 02 November the stack reached `main` through #57, #61, #69, #70, #72, #73 and #75, and those pull requests had **no recorded approving review**. Neither did #87 (US-27), #88, #66 (demo video) or #91 (US-24). Among the earlier document pull requests, #1, #2, #6, #12, #14, #15, #17, #21, #51 and #52 were also merged without one. The working agreement asks for one approval from someone other than the author.

## What this project does not contain

No test has been run against a deployed system. Every Test Plan case was verified through Django's test client and services, as the deviations D-84 to D-107 record. Steps that need a server behind Nginx, a TLS or OWASP scanner, a load test or a browser session were not run. The automated suite has 586 tests on `main`, run by CI on SQLite and PostgreSQL 16.
