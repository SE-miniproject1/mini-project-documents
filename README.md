# Blood Bank Management System — Deliverables 1 and 2

Software Engineering Mini Project, PES University.
Organisation: [SE-miniproject1](https://github.com/SE-miniproject1) · Repository: [mini-project-documents](https://github.com/SE-miniproject1/mini-project-documents)

A web-based system that manages the full life cycle of donated blood, from donor registration and eligibility screening, through collection, screening tests, component separation and storage, to the fulfilment of blood requests raised by hospitals.

## Documents

| Document | File | Deliverable |
|---|---|---|
| Software Requirements Specification | [docs/SRS.md](docs/SRS.md) | 1, extended for 2 with security objectives and an embedded use case diagram |
| Software Test Plan, IEEE layout | [docs/Test-Plan.md](docs/Test-Plan.md) | 1, restructured for 2 |
| Software Architecture and Design Specification | [docs/SAD.md](docs/SAD.md) | 2 |
| Word copies for submission | [submission/](submission/) | 1 and 2 |

Plans and records: [COMMIT-PLAN-2.md](COMMIT-PLAN-2.md) for the Deliverable 2 schedule and [CONTRIBUTIONS.md](CONTRIBUTIONS.md) for what the git history shows about who did what.

## Team

| SRN | Name | GitHub | Primary Responsibility |
|---|---|---|---|
| PES1UG24CS560 | Balaraj R | [@balaraj74](https://github.com/balaraj74) | Requirements Analyst, Test Lead |
| PES1UG24CS567 | Dhanya K M | [@Dhanya-KM](https://github.com/Dhanya-KM) | System Analyst, Data Modeller |
| PES1UG24CS569 | G A Aadish | [@Sonuaadi0706](https://github.com/Sonuaadi0706) | Project Lead, Architect |
| PES1UG24CS585 | Niveditha | [@nnivedithaparmesh-cpu](https://github.com/nnivedithaparmesh-cpu) | Interface Designer, Documentation Lead |

## What is in the repository

| Artefact | Location |
|---|---|
| Requirements, 46 functional and the NFR series | [docs/SRS.md](docs/SRS.md) |
| Test Plan, 112 test cases | [docs/Test-Plan.md](docs/Test-Plan.md) |
| Architecture and design, with two sequence diagrams | [docs/SAD.md](docs/SAD.md) |
| All eight diagrams, Mermaid source and PNG | [diagrams/Diagrams.md](diagrams/Diagrams.md) |
| Appendix B field layouts and report requirements, spreadsheet form | [appendices/](appendices/) |
| Build and traceability scripts | [tools/](tools/) |
| Contribution record | [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |

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

The Test Plan carries **112 test cases**: 48 unit, 26 integration, 30 system and 8 security validation. Every one of the 46 functional requirements is verified by at least one case, and the mapping is given in Appendix C of the SRS and in section 13 of the Test Plan. No test has been executed, because the system has not been implemented. Every result column reads `Not executed` and `Pending`.

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

The build applies heading styles, repeating table headers, page numbering, landscape orientation for the wide test case tables, and embeds the diagram images into the SRS and the SAD.

## Regenerating the diagram images

Diagram sources are Mermaid. GitHub renders the `.mmd` files and the fenced blocks in `diagrams/Diagrams.md` directly, so the PNGs are needed only for the Word submission.

```bash
npm install @mermaid-js/mermaid-cli
for f in diagrams/*.mmd; do npx mmdc -i "$f" -o "${f%.mmd}.png" -b white -s 3; done
```

## Planned technology stack

Python 3.11 with Django 5.x, PostgreSQL 15, served by Gunicorn behind Nginx. Node.js with Express was evaluated and rejected for this release; the reasoning is recorded in SRS section 2.5 under constraint CON-1.

## Working agreement

Changes reach `main` through a pull request, with a reviewer requested on each. Not every pull request received a recorded approval, and `CONTRIBUTIONS.md` lists which did not. Branch names follow `docs/<area>`, `diagrams/<area>` or `build/<area>`.
