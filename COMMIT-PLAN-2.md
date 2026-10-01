# Commit Plan — Deliverable 2

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

The source PDF, `Deliverable-2/SE_Mini_Project_Delivereables_Part-1.pdf`, is dated **28 September 2026**. Today is already past that. This plan covers what is left, split for **today and tomorrow**, on the assumption that getting it submitted now matters more than hitting the original date.

This plan assumes Deliverable 1's `main` branch has already been brought up to date using the four `gh pr merge` commands given at the end of that deliverable's work (PRs for Balaraj's SF-1 to SF-3, Dhanya's use case/ER diagrams, Niveditha's section 3, and Niveditha's full Test Plan). Deliverable 2's traceability sections cite requirement IDs REQ-1 through REQ-46, which only fully exist once that merge has happened.

---

## 1. What Deliverable 2 actually requires

Read from `Deliverable-2/SE_Mini_Project_Delivereables_Part-1.pdf`, cross-checked against `SAD_Template.docx` and `Test_Plan_Template for SE.docx`.

| # | Requirement | Status |
|---|---|---|
| 1a | SRS in IEEE format, intro + descriptive sections | Already satisfied by `docs/SRS.md` |
| 1b | FRs and NFRs specified clearly, unambiguously, measurably | Already satisfied, 46 REQ + NFR series |
| 1c | UML use case diagram, at least 1 | Already drafted (`diagrams/use-case.mmd`), pending merge via PR #11 |
| 1d | Security section with Objectives and Requirements, at least 2 each | **Done this session.** PR #12, 2 objectives + 11 existing requirements |
| 2a | Test Plan in IEEE STP format | **New document structure needed.** `docs/Test-Plan.md` must be rebuilt in the 15-section STP format from `Test_Plan_Template for SE.docx`, not the simpler course template Deliverable 1 used |
| 2b | STP Sections 3, 4, 5 filled (Features to be/not to be Tested, Test Approach) | Not started |
| 2c | STP Section 5.1, Security Validation | Not started |
| 2d | Traceability to SRS | Partially exists in SRS Appendix C; needs an STP-side section 13 too |
| 3 | Software Architecture & Design Specification | **New document, started this session.** PR #13 has the skeleton and full Architecture section (3.1–3.9). Design section (4) and Appendices (5) remain |
| 4a | At least 7–10 test cases, FR + NFR | Comfortably exceeded already — Deliverable 1 has 104 cases to draw from, once ported into the new STP structure |

## 2. What is already done

| PR | Branch | Content | Status |
|---|---|---|---|
| #12 | `docs/srs-security-objectives` | SRS Security Objectives (2) above the 11 existing NFR-SEC requirements | Open, awaiting Balaraj's review |
| #13 | `docs/sad-architecture` | SAD skeleton, Section 1, Section 2, full Section 3 Architecture (component diagram, descriptions, pattern, tech stack, risks, traceability, STRIDE security architecture) | Open, awaiting Dhanya's review |

A full draft of SAD Section 4 (Design) and Section 5 (Appendices) has already been written and is ready to hand to Dhanya and Niveditha directly rather than written from scratch — see Section 5 of this plan.

## 3. What is left, and who owns it

| Owner | Deliverable 2 task | Depends on |
|---|---|---|
| Dhanya K M | SAD Section 4.1–4.3: Design Overview, the two UML sequence diagrams (collection/screening flow and hospital request/issue flow — both already drafted and verified, ready to use), API design for the Request/Issue and Search components | PR #13 merged |
| Niveditha | SAD Section 4.4–4.6 (error handling, UX design, open issues) and Section 5 (glossary/references/tools) | PR #13 merged, Dhanya's 4.1–4.3 merged |
| Balaraj | Rebuild `docs/Test-Plan.md` into the IEEE STP format: sections 1–2 (intro, test items), 3–4 (features to test / not to test, mapped to REQ IDs), 5 (approach/strategy) and 5.1 (security validation), 6–12 (environment, schedule, deliverables, roles, risks, assumptions, suspension criteria) | Deliverable 1's `main` consolidation (needs the full REQ-1 to REQ-46 set) |
| Dhanya or Balaraj | Port a representative set of existing test cases (comfortably more than the 7–10 minimum, Deliverable 1 already has 104) into STP Section 14, and write STP Section 13 traceability | Balaraj's STP structure above |
| Niveditha | Final consistency pass across SRS, SAD and the new Test Plan; Word exports for all three documents (extend `tools/build_docx.py`) | Everything else merged |

## 4. Commit sequence — today and tomorrow

### Today, 01 October

| # | Author | Branch | Commit | Status |
|---|---|---|---|---|
| 1 | Aadish | `docs/srs-security-objectives` | `docs(srs): add security objectives to section 6.3` | **Done, PR #12 open** |
| 2 | Aadish | `docs/sad-architecture` | `docs(sad): add SAD skeleton, intro, overview and architecture` | **Done, PR #13 open** |
| 3 | Dhanya | `docs/sad-design` | `docs(sad): add design overview and sequence diagrams` | Pending |
| 4 | Dhanya | `docs/sad-design` | `docs(sad): add API design for Request/Issue and Search` | Pending |
| 5 | Balaraj | `docs/test-plan-stp` | `docs(test-plan): rebuild as IEEE STP, sections 1-5` | Pending |
| 6 | Balaraj | `docs/test-plan-stp` | `docs(test-plan): add section 5.1 security validation` | Pending |

### Tomorrow, 02 October

| # | Author | Branch | Commit | Status |
|---|---|---|---|---|
| 7 | Niveditha | `docs/sad-design` | `docs(sad): add error handling, UX design and open issues` | Pending |
| 8 | Niveditha | `docs/sad-appendices` | `docs(sad): add glossary, references and tools appendices` | Pending |
| 9 | Balaraj | `docs/test-plan-stp` | `docs(test-plan): add sections 6-12, environment through assumptions` | Pending |
| 10 | Dhanya | `docs/test-plan-cases` | `docs(test-plan): port test cases and add section 13 traceability` | Pending |
| 11 | Niveditha | `docs/d2-consistency` | `docs: consistency pass across SRS, SAD and Test Plan` | Pending |
| 12 | Niveditha | `build/submission-d2` | `build: generate Word versions of SAD and the rebuilt Test Plan` | Pending |

Commit 10 depends on commit 5/6/9 (the STP structure needs to exist before test cases are ported into it). Commits 3–4 and 5–6 are independent of each other and can run in parallel today.

## 5. Handoff package for Dhanya and Niveditha

The complete SAD draft, all five sections, was written in one pass for consistency and is available for whoever picks up Section 4 and 5 to use directly rather than starting cold. It is saved at `Deliverable-2/SAD-full-draft-handoff.md` (next to this repo, not committed), the same quality bar as the committed Section 3, covering:

- **4.1–4.3 (Dhanya's):** Design overview, two sequence diagrams already written in Mermaid and verified to render (collection-and-screening flow, hospital-request-and-issue flow), and the API design table for the Request/Issue and Search components.
- **4.4–4.6 (Niveditha's):** Error handling/logging/monitoring approach, UX design principles, and the open issues table.
- **Section 5 (Niveditha's):** Glossary pointer, references, and tooling list.

Each person should still read and adjust it to their own voice rather than commit it verbatim, the same way Balaraj rewrote his own SF-1 to SF-3 content in Deliverable 1 rather than using a prepared draft unchanged.

## 6. Working agreement

Same as Deliverable 1: every PR needs one approving review from someone other than its author before merge, no squash merges, and nobody commits under another member's name. See `COMMIT-PLAN.md` Section 0 and Section 1 for the git identity setup, which stays the same for this deliverable since it's the same repository.
