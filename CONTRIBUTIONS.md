# Contribution Record

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

This record is built from the git history of `main` and the review data on GitHub. It states what the history shows. It does not claim more than that.

**Read this first.** Git records who committed a change, not who drafted the text. Large parts of the Deliverable 1 documents were assembled before they reached the repository and arrived in a small number of commits, so commit counts and the areas below are a record of commits, not a measure of effort. The counts are as of commit `4455144` on 04 October 2026, before the audit commits that rewrote this file.

## Commits on `main`

Non-merge commits only. Merge commits are counted separately.

| SRN | Name | GitHub | Role | Commits | Merge commits | Approving reviews given |
|---|---|---|---|---|---|---|
| PES1UG24CS569 | G A Aadish | @Sonuaadi0706 | Project Lead, Architect | 16 | 5 | 0 |
| PES1UG24CS585 | Niveditha | @nnivedithaparmesh-cpu | Interface Designer, Documentation Lead | 12 | 1 | 3 |
| PES1UG24CS560 | Balaraj R | @balaraj74 | Requirements Analyst, Test Lead | 10 | 5 | 1 |
| PES1UG24CS567 | Dhanya K M | @Dhanya-KM | System Analyst, Data Modeller | 6 | 3 | 2 |

The commit counts are not equal. They are 16, 12, 10 and 6 out of 44. Niveditha's 12 include the repository's first commit and one bulk upload of diagram images.

## What each member's commits contain

**G A Aadish.** Repository structure, `.gitignore` and first README. SRS skeleton, Section 1, Section 2, SF-4 to SF-6 (REQ-24 to REQ-46) and the security objectives in 6.3. The architecture diagram and the complete Software Architecture and Design Specification (`docs/SAD.md`), including the two sequence diagrams and their images. The Deliverable 2 plan and its update, and the README pointer.

**Niveditha.** Created the repository (first commit). SRS Section 6 and Section 7, and Section 3 (user interfaces, software and communications interfaces). The SF-5 and SF-6 test cases. An upload of the six diagram images. A revision to the Word build script and the generated Word files. The first correction of the SRS revision history dates.

**Balaraj R.** SRS SF-1 to SF-3 (REQ-1 to REQ-23). The same commit also carries SRS Section 4 text and Appendices A, B and C. The Test Plan structure and the first test case tables, which also contain the SF-3 to SF-6 case tables. The traceability checker. The data flow diagram sources, the diagram index, the Appendix B spreadsheets, the first Word build and `tools/build_docx.py`. The IEEE-layout restructure of the Test Plan with generated traceability and the eight security validation cases. A correction of the revision history.

**Dhanya K M.** The use case diagram and the entity relationship diagram (sources and images), and the architecture diagram image. The use case diagram embedded in SRS Section 4, with the use case summary. An earlier version of this file.

## Reviews and merges

Approving reviews recorded on GitHub: Niveditha approved #11, #16 and #18. Dhanya approved #13 and #19. Balaraj approved #20.

Pull requests merged **without a recorded approving review**: #1, #2, #3, #6 (only an automated Copilot comment), #12, #14, #15, #17, and the audit pull request that last revised this file. Earlier versions of this record said every pull request was reviewed. That was not true.

## What this project does not contain

There is no implementation. No test case has been executed. Every Actual Result and Test Result in the Test Plan reads `Not executed` and `Pending`.
