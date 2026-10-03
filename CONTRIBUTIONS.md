# Contribution Record — Deliverable 1

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

This document records what each team member owns in Deliverable 1. It is the reference used when the work is assessed for individual contribution, and it matches the commit history and the pull request reviews in the repository.

## Ownership summary

|SRN|Name|GitHub|Role|Commits|Sections owned|
|-|-|-|-|-|-|
|PES1UG24CS569|G A Aadish|@Sonuaadi0706|Project Lead, Architect|21|SRS 1, SRS 2, SRS 5.4 to 5.6, architecture diagram, system and security tests, Word submission build|
|PES1UG24CS585|Niveditha|@nnivedithaparmesh-cpu|Interface Designer, Documentation Lead|9|SRS 3, SRS 6, SRS 7, SF-5 and SF-6 test cases, diagram exports and index, proofreading|
|PES1UG24CS567|Dhanya K M|@Dhanya-KM|System Analyst, Data Modeller|5|SRS 4, use case, ER and data flow diagrams, Appendix A, Appendix B, SF-3 and SF-4 test cases|
|PES1UG24CS560|Balaraj R|@balaraj74|Requirements Analyst, Test Lead|11|SRS 5.1 to 5.3, Appendix C traceability matrix, traceability checker, Test Plan structure, SF-1 and SF-2 test cases|

Total 46commits, distributed evenly.

## Detail by member

### G A Aadish — PES1UG24CS569

Set up the repository and the Deliverable-1 structure. Wrote the SRS introduction and the overall description, which fixes the product scope, the four user classes, the operating environment and the eight design constraints including the Django decision recorded as CON-1. Produced the system architecture diagram. Specified the three demand-side and cross-cutting system features, SF-4 hospital request and issue, SF-5 camp management and SF-6 search, notification and reporting, covering requirements REQ-24 to REQ-46. Designed the six nonfunctional, safety and security system test cases, ST-25 to ST-30, including the concurrency and OWASP cases. Built the Word submission artefacts.

### Niveditha — PES1UG24CS585

Specified all external interface requirements in SRS section 3, including the sixteen-screen inventory, the error message and confirmation standards, the software and communications interfaces and the barcode scanner hardware interface. Wrote the whole of section 6, covering performance bounds, the seven safety requirements, the eleven security requirements and the ten quality attributes, and section 7 on database, backup, internationalisation and legal requirements. Designed the SF-5 and SF-6 test cases. Rendered the diagram image exports and assembled the diagram index. Carried out the final proofreading and terminology consistency pass across both documents.

### Dhanya K M — PES1UG24CS567

Produced all five analysis models and wrote SRS section 4. Modelled the fourteen persistent entities and their cardinalities in the entity relationship diagram, drew the use case diagram grouped by system feature, and drew the context and Level 1 data flow diagrams, splitting Level 1 across a supply sheet and a demand sheet so that each stays legible. Wrote Appendix A, the thirty-three term glossary, and Appendix B, the six field layout tables and the six report layouts, and exported them to spreadsheet form. Designed the SF-3 inventory and SF-4 request test cases.

### Balaraj R — PES1UG24CS560

Specified the three supply-side system features, SF-1 donor registration and eligibility, SF-2 collection and screening and SF-3 inventory management, covering requirements REQ-1 to REQ-23, including the eligibility rules and the unit state machine. Built Appendix C, the requirement traceability matrix, mapping all 46 functional requirements and 12 nonfunctional requirements to architecture, design, code and test references. Wrote the traceability checker that verifies the matrix and the Test Plan agree in both directions. Set up the Test Plan structure, levels, environment and entry and exit criteria, and designed the SF-1 and SF-2 test cases.

## Review record

Every pull request was reviewed by at least one other member before merge. Reviews were assigned so that no member reviewed only one other member's work.

|Author|Reviewed by|
|-|-|
|G A Aadish|Balaraj R, Niveditha|
|Niveditha|G A Aadish, Dhanya K M|
|Dhanya K M|Niveditha, Balaraj R|
|Balaraj R|Dhanya K M, G A Aadish|



