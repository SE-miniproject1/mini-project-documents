# Commit Plan — Deliverable 2

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

The source PDF, `SE_Mini_Project_Delivereables_Part-1.pdf`, is dated **28 September 2026**. That date has passed, so this plan fits everything that remains into **one working day, Friday 02 October 2026**.

---

## 1. What Deliverable 2 requires, and where it stands

| # | Requirement from the PDF | Where it lives | Status |
|---|---|---|---|
| 1a | SRS in IEEE format, intro and descriptive sections | `docs/SRS.md` | Done. Complete on PR #6 |
| 1b | FRs and NFRs, clear and measurable | `docs/SRS.md` sections 5 and 6 | Done. 46 REQ plus the NFR series |
| 1c | UML use case diagram, at least 1 | `diagrams/use-case.mmd` | Diagram merged. Embedding it in SRS section 4 is **task D2** below |
| 1d | Security objectives and requirements, at least 2 each | `docs/SRS.md` section 6.3 | Done. PR #12, 2 objectives and 11 requirements |
| 2a | Test Plan in IEEE STP format | `docs/Test-Plan.md` | Draft ready. Commit is **task D1** below |
| 2b | STP sections 3, 4 and 5 | Test Plan sections 3 to 5 | In the draft |
| 2c | STP section 5.1, security validation | Test Plan section 5.1 | In the draft, with 8 new cases SV-01 to SV-08 |
| 2d | Traceability with the SRS | Test Plan section 13, generated from SRS Appendix C | In the draft |
| 3 | Software Architecture and Design Specification | `docs/SAD.md` | **Done.** PR #13, sections 1 to 5 complete |
| 4 | At least 7 to 10 test cases, FR and NFR | Test Plan Appendix A and section 5.1 | 112 cases in the draft, far above the minimum |

## 2. What has been done

| PR | Branch | Content | State |
|---|---|---|---|
| #12 | `docs/srs-security-objectives` | Security objectives in SRS 6.3 | Open, needs a review |
| #13 | `docs/sad-architecture` | Complete SAD: architecture, two sequence diagrams, API design, error handling, UX, appendices | Open, approved by Dhanya for the architecture section |
| #14 | `docs/d2-commit-plan` | This plan | Open, needs a review |
| #15 | `docs/readme-d2-pointer` | README pointer to the new documents | Open, needs a review |
| #6 | `docs/balaraj-srs-testplan` | Balaraj's Deliverable 1 package: SF-1 to SF-3, Appendix C, tools, Test Plan, appendices | Open, mergeable, **must merge first** |

The SAD was written in full by Aadish, including the Design and Appendix sections originally planned for Dhanya and Niveditha, because the SAD is the architect's document and nothing else depended on those sections being split.

## 3. Merge order

Everything merges cleanly together. The order matters only because PR #6 carries most of Deliverable 1.

1. **#6** Balaraj's Deliverable 1 package
2. **#13** SAD
3. **#12** security objectives
4. **#14** this plan
5. **#15** README pointer, after #6
6. Close **#7** and **#10**. Their content is superseded by #6 and by direct commits already on `main`

## 4. Remaining work, one day

Each person commits only under their own name. The prepared drafts are in `Deliverable-2/handoff/<name>/` and should be read and adjusted, not pasted unread.

| Time | Owner | Task | Branch | Commit message |
|---|---|---|---|---|
| 09:30 | All | Review the open PRs. Balaraj reviews #12 and #14, Niveditha reviews #15 | | |
| 10:00 | Aadish | Merge in the order above | | |
| 10:30 | Balaraj | **D1.** Replace `docs/Test-Plan.md` with the IEEE STP layout from `handoff/balaraj/Test-Plan.md`. Run `python3 tools/check_traceability.py` and confirm it passes | `docs/test-plan-stp` | `docs(test-plan): restructure to IEEE STP layout with generated traceability` |
| 12:00 | Balaraj | Second commit for the security validation cases SV-01 to SV-08 and section 5.1 if split from the first | `docs/test-plan-stp` | `docs(test-plan): add security validation section and SV cases` |
| 10:30 | Dhanya | **D2.** Replace SRS section 4 with `handoff/dhanya/SRS-section4.md` so the use case diagram and use case summary appear in the SRS itself | `docs/srs-use-case-section` | `docs(srs): embed use case diagram and use case summary in section 4` |
| 12:00 | Dhanya | **D3.** Rewrite `CONTRIBUTIONS.md` from `git shortlog` and the real PR reviews. The version in PR #6 describes a planned history, not the actual one | `docs/contributions-actual` | `docs: record actual per-member contributions` |
| 11:00 | Niveditha | **D4.** Close #7 and #10 with a comment pointing at #6. Fix the SRS revision history dates to match when work really happened | `docs/revision-history-dates` | `docs(srs): correct revision history dates` |
| 14:00 | Niveditha | **D5.** After every content branch above has merged, replace `tools/build_docx.py` with `handoff/niveditha/build_docx.py`, run it, and commit the three regenerated `.docx` files | `build/submission-d2` | `build: generate Word versions of SRS, SAD and Test Plan` |
| 15:30 | Niveditha | Proofread the three documents against the PDF checklist in section 1 | | |
| 16:00 | Aadish | Final check. Run the traceability script, open each diagram on GitHub, confirm the `.docx` files match the Markdown, then submit | | |

Task D5 has to come last because it reads the Markdown masters. If anything merges after it, rerun the build.

## 5. Known issues to fix before submitting

- **CONTRIBUTIONS.md and the SRS revision history in PR #6 describe the original three-day plan.** Dates and commit counts there do not match what happened. D3 and D4 correct this.
- **Two Copilot comments on PR #6** (about REQ-4 and REQ-6) refer to an earlier revision and no longer match the text. Balaraj should confirm they no longer apply and resolve them.
- **No test has been executed.** Every Actual Result and Test Result stays `Not executed` and `Pending` until the system is built.

## 6. Working agreement

Same as Deliverable 1. One approving review from someone other than the author before merge, no squash merges, and nobody commits under another member's name.
