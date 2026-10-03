# Blood Bank Management System — Deliverable 1

Software Engineering Mini Project, PES University.
Organisation: [SE-miniproject1](https://github.com/SE-miniproject1) · Repository: [mini-project-documents](https://github.com/SE-miniproject1/mini-project-documents)

A web-based system that manages the full life cycle of donated blood, from donor registration and eligibility screening, through collection, screening tests, component separation and storage, to the fulfilment of blood requests raised by hospitals.

## Team

| SRN | Name | GitHub | Primary Responsibility |
|---|---|---|---|
| PES1UG24CS560 | Balaraj R | [@balaraj74](https://github.com/balaraj74) | Requirements Analyst, Test Lead |
| PES1UG24CS567 | Dhanya K M | [@Dhanya-KM](https://github.com/Dhanya-KM) | System Analyst, Data Modeller |
| PES1UG24CS569 | G A Aadish | [@Sonuaadi0706](https://github.com/Sonuaadi0706) | Project Lead, Architect |
| PES1UG24CS585 | Niveditha | [@nnivedithaparmesh-cpu](https://github.com/nnivedithaparmesh-cpu) | Interface Designer, Documentation Lead |

## What is in this deliverable

| Artefact | Location |
|---|---|
| Software Requirements Specification | [docs/SRS.md](docs/SRS.md) |
| Test Plan, 104 test cases | [docs/Test-Plan.md](docs/Test-Plan.md) |
| Analysis models, all six diagrams | [diagrams/Diagrams.md](diagrams/Diagrams.md) |
| Appendix B field layouts, spreadsheet form | [appendices/Appendix-B-Field-Layouts.csv](appendices/Appendix-B-Field-Layouts.csv) |
| Appendix B report requirements | [appendices/Appendix-B-Report-Requirements.csv](appendices/Appendix-B-Report-Requirements.csv) |
| Word documents for submission | [submission/](submission/) |
| Per-member contribution record | [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Commit sequence followed by the team | [COMMIT-PLAN.md](COMMIT-PLAN.md) |

## Document summary

The SRS follows the IEEE 830 structure given in the course template. It specifies **six system features** decomposed into **46 uniquely tagged functional requirements**, REQ-1 to REQ-46, together with nonfunctional requirements for performance, safety, security and quality.

| # | System Feature | Requirements |
|---|---|---|
| SF-1 | Donor Registration and Eligibility Screening | REQ-1 to REQ-8 |
| SF-2 | Blood Donation and Collection Management | REQ-9 to REQ-15 |
| SF-3 | Blood Inventory and Stock Management | REQ-16 to REQ-23 |
| SF-4 | Hospital Blood Request and Issue | REQ-24 to REQ-31 |
| SF-5 | Donation Camp and Drive Management | REQ-32 to REQ-37 |
| SF-6 | Search, Notification and Reporting | REQ-38 to REQ-46 |

The Test Plan carries **104 test cases**: 48 unit, 26 integration and 30 system. Every one of the 46 functional requirements is verified by at least one case, and the mapping is given in Appendix C of the SRS.

## Traceability

Appendix C of the SRS is the requirement traceability matrix. It maps each requirement to its architecture component, design element, code file and verifying test cases. The mapping is checked by a script that fails if any test identifier is referenced but not defined, or defined but never referenced.

```bash
python3 tools/check_traceability.py
```

## Rebuilding the Word submission copies

The Markdown files in `docs/` are the masters. The `.docx` files in `submission/` are generated from them, so edit the Markdown and rebuild rather than editing Word directly.

```bash
pip install -r tools/requirements.txt && python3 tools/build_docx.py
```

The build applies heading styles, repeating table headers, page numbering, landscape orientation for the wide test case tables, and embeds the six diagram images into SRS section 4.

## Regenerating the diagram images

Diagram sources are Mermaid. GitHub renders the `.mmd` files and the fenced blocks in `diagrams/Diagrams.md` directly, so the PNGs are needed only for the Word submission.

```bash
npm install @mermaid-js/mermaid-cli
for f in diagrams/*.mmd; do npx mmdc -i "$f" -o "${f%.mmd}.png" -b white -s 3; done
```

## Planned technology stack

Python 3.11 with Django 5.x, PostgreSQL 15, served by Gunicorn behind Nginx. Node.js with Express was evaluated and rejected for this release; the reasoning is recorded in SRS section 2.5 under constraint CON-1.

## Working agreement

The default branch is protected. All changes reach it through a pull request carrying at least one approving review from another team member. Branch names follow `docs/<area>` or `diagrams/<area>`.
