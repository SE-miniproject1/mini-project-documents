# Test Summary Report

**Project:** Blood Bank Management System  
**Author:** Balaraj R (QA Lead)  
**Date:** 19 November 2026  

## 1. Scope Executed (Balaraj R)

- **Unit Tests:** `UT-01` to `UT-09` (9/9 Passed)
- **Integration Tests:** `IT-01` to `IT-04` (4/4 Passed)
- **System Tests:** `ST-01` to `ST-04` (4/4 Passed with deviation D-90), `ST-25` (Partly executed, D-91), `ST-26` (Passed), `ST-27` (Passed with deviation D-72), `ST-28` (Passed, D-93), `ST-29` (Passed with deviation D-92), `ST-30` (Passed)

## 2. Automated Suite & Quality Gates

- **Django Test Suite:** 586 tests run, 585 passed, 1 skipped (SQLite `has_select_for_update`, D-72), 0 failures.
- **Lint & Format:** `ruff check src` and `ruff format --check src` clean.
- **Migrations:** `python src/manage.py makemigrations --check --dry-run` clean.
- **Traceability:** `python3 tools/check_traceability.py` — 46/46 functional requirements and 104/104 test cases traced.

## 3. Deviations Recorded (Balaraj R)

- **D-90:** `ST-01` to `ST-04` verified via Django `TestCase` HTTP client rather than a live Chrome browser.
- **D-91:** `ST-25` P95 screen render (< 3.0 s) verified on seeded data; 50-user / 50,000-unit load test not run.
- **D-92:** `ST-29` CSRF, XSS and SQLi verified via Django test client; external OWASP ZAP scan not run.
- **D-93:** `ST-28` role enforcement and cross-tenant isolation verified across `accounts/tests/test_permissions.py` and `bloodrequests/tests/`.
- **D-94:** `UT-01` / `IT-01` registration form includes password confirmation, consent and welcome email dispatch.

## 4. Final Test Plan Metrics (all 112 cases)

| Level | Planned | Executed | Passed | Passed with deviation | Partly executed | Failed | Pending |
|---|---|---|---|---|---|---|---|
| Unit | 48 | 48 | 46 | 2 | 0 | 0 | 0 |
| Integration | 26 | 26 | 22 | 4 | 0 | 0 | 0 |
| System | 30 | 30 | 8 | 20 | 1 | 1 | 0 |
| Security validation | 8 | 8 | 3 | 4 | 1 | 0 | 0 |
| **Total** | **112** | **112** | **79** | **30** | **2** | **1** | **0** |

- **Partly executed (2):** `ST-25` (seeded P95 latency verified; 50-user / 50,000-unit load test not run, D-91) and `SV-04` (TLS version refusal requires a deployed server, D-86).
- **Failed (1):** `ST-22` (dashboard shortage banner and below-threshold flag not built; accepted as known defect, issue #104, D-103).
