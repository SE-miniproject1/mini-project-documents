# Product Backlog: Blood Bank Management System

Source: `docs/SRS.md` v1.0 (46 functional requirements, NFRs, constraints). Points use the Fibonacci scale (2, 3, 5, 8).

## Sprint summary

| Sprint | Dates | Points | Balaraj | Dhanya | Aadish | Niveditha |
|---|---|---|---|---|---|---|
| Sprint 1 | 19-23 Oct | 53 | 13 | 13 | 14 | 13 |
| Sprint 2 | 26-30 Oct | 52 | 13 | 14 | 13 | 12 |
| Stretch | if capacity allows | 31 | 7 | 8 | 8 | 8 |

## Backlog

| ID | Story | Requirements | Pts | Pri | Sprint | Owner |
|---|---|---|---|---|---|---|
| US-01 | Project setup, CI and linting | CON-1, CON-3, CON-4 | 3 | High | Sprint 1 | Aadish |
| US-02 | Authentication, roles and access control | NFR-SEC1, NFR-SEC2, NFR-SEC3, NFR-SEC4, NFR-SEC5, NFR-SEC11 | 8 | High | Sprint 1 | Aadish |
| US-03 | Base layout and role-based navigation | UI-1, UI-2, UI-4 | 3 | High | Sprint 1 | Niveditha |
| US-04 | Donor registration and unique donor ID | REQ-1, REQ-2 | 5 | High | Sprint 1 | Dhanya |
| US-05 | Registration validation (duplicates and age) | REQ-3, REQ-4 | 3 | High | Sprint 1 | Dhanya |
| US-06 | Medical history and permanent deferral | REQ-5 | 3 | High | Sprint 2 | Dhanya |
| US-07 | Eligibility engine | REQ-6, NFR-Q4 | 5 | High | Sprint 1 | Balaraj |
| US-08 | Collection guard and next-eligible date | REQ-7, REQ-8, NFR-S5 | 3 | High | Sprint 1 | Aadish |
| US-09 | Record donation and unit ID with barcode | REQ-9, REQ-10 | 5 | High | Sprint 1 | Niveditha |
| US-10 | Unit state machine and quarantine | REQ-11, REQ-16, NFR-S7 | 5 | High | Sprint 1 | Dhanya |
| US-11 | Screening results, release and discard | REQ-12, REQ-13, REQ-14, NFR-S1 | 8 | High | Sprint 1 | Balaraj |
| US-12 | Audit log for status transitions | REQ-23, NFR-SEC10, SEC-OBJ-2 | 3 | High | Sprint 2 | Dhanya |
| US-13 | Inventory console: stock counts | REQ-17, NFR-P5 | 5 | High | Sprint 1 | Niveditha |
| US-14 | Inventory filters, transfer and manual discard | REQ-18, REQ-21, REQ-22 | 5 | Medium | Stretch | Niveditha |
| US-15 | Auto-expiry and near-expiry alerts | REQ-19, REQ-20, NFR-S2 | 5 | High | Sprint 2 | Aadish |
| US-16 | Component separation | REQ-15 | 5 | Medium | Sprint 2 | Balaraj |
| US-17 | Hospital raises blood request | REQ-24, REQ-25, BR-7 | 5 | High | Sprint 2 | Niveditha |
| US-18 | Request queue, approve and reject | REQ-26, REQ-27 | 5 | High | Sprint 2 | Balaraj |
| US-19 | Allocate, issue and fulfilment status | REQ-28, REQ-29, REQ-30, NFR-S3, NFR-S4 | 8 | High | Sprint 2 | Aadish |
| US-20 | Cancel request | REQ-31 | 2 | Medium | Stretch | Balaraj |
| US-21 | Camps: create, list and enrol | REQ-32, REQ-33, REQ-34, REQ-35 | 5 | Medium | Sprint 2 | Dhanya |
| US-22 | Camp collection link and closure | REQ-36, REQ-37 | 3 | Medium | Sprint 2 | Dhanya |
| US-23 | Availability search for hospitals | REQ-38, NFR-P2, NFR-SEC7 | 3 | High | Stretch | Niveditha |
| US-24 | Notifications: dispatcher, reminders, shortage appeal | REQ-39, REQ-40, REQ-41, NFR-P6 | 8 | Medium | Stretch | Aadish |
| US-25 | Reports, export and data scoping | REQ-42, REQ-43, REQ-44, NFR-P4, NFR-Q8 | 8 | Medium | Stretch | Dhanya |
| US-26 | Admin: users, hospitals and configuration | REQ-45, REQ-46, NFR-Q10 | 5 | High | Sprint 2 | Niveditha |
| US-27 | Safety rule tests and concurrency hardening | NFR-S1, NFR-S2, NFR-S3, NFR-S4 | 3 | High | Sprint 2 | Balaraj |
| US-28 | Security, quality and performance hardening | NFR-SEC9, NFR-Q5, NFR-P1, NFR-P3 | 5 | Medium | Stretch | Balaraj |
| US-29 | Documentation, deviations log and demo video | OR-6 | 2 | High | Sprint 2 | Niveditha |
