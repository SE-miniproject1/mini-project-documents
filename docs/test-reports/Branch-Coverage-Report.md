# Branch Coverage Report

Prepared by Niveditha. Coverage figures verified on 18-11-2026 against commit `25cac0340d0cfb5ebcb6d0abbbc55bdcf88c9368`. Tool: coverage.py with branch measurement, driven by the Django test runner on the SQLite test database.

**Commands:**
```bash
export BBMS_ENV=test DJANGO_SECRET_KEY=local-test
coverage run --branch src/manage.py test src
coverage report --show-missing > docs/test-reports/branch-coverage-summary.txt
```

## 1. Result

| Measure | Value |
|---|---|
| Tests run | 586 |
| Passed | 585 |
| Skipped | 1 |
| Failed | 0 |
| Statements | 7,692 |
| Branches | 890 (837 covered, 53 missing) |
| Partial branches | 47 |
| **Branch coverage** | **94.0 percent** |

The Test Plan exit criterion (NFR-Q5) asks for at least 70 percent line coverage. Line coverage is 98.5 percent and branch coverage is 94.0 percent, so the criterion is met.

The one skipped test is `ConcurrentAllocationTests.test_only_one_of_two_simultaneous_allocations_wins`. SQLite has no `select_for_update`, so it runs only in the PostgreSQL pass of the CI (D-72). It is not one of the cases in this report.

## 2. Scope

The figures above are for the whole project. The line and branch totals reflect the 18-11-2026 run identified above. The modules covered by the cases run for this report (UT-34 to UT-48, IT-18 to IT-26, ST-17 to ST-24) are camps, notifications, reports, accounts and core. For those five packages, excluding tests and migrations: 1,362 statements, 29 not run, 270 branches, 17 partial branches, 97 percent combined coverage.

## 3. Cases tagged for this report

Tests carry their case IDs in the docstring, so the traceability check finds them.

| Case | Test |
|---|---|
| UT-47 | `accounts/tests/test_admin.py`: deactivation keeps the record; a role change replaces the role |
| UT-48 | `core/tests/test_config.py`: an override applies to the next call; the 90-day floor |
| IT-20 | `camps/tests/test_it20_camp_to_inventory.py` (new), plus `camps/tests/test_collection_link.py` |
| IT-26 | `accounts/tests/test_admin.py`, `core/tests/test_config.py` |
| ST-22 | no test: the dashboard banner and the below-threshold flag are not built (D-103) |
| ST-24 | `accounts/tests/test_admin.py` (hospital registration and deactivation), `bloodrequests/tests/test_raise_request.py` (inactive hospital refused) |
| UT-40, IT-21, ST-20 | `core/tests/test_availability.py` |

## 4. Files below 100 percent in the five packages

| File | Missing | Why it is not covered |
|---|---|---|
| `accounts/backends.py` | 13, 15 | Login by `kwargs`, or with no username or password. The login form always supplies both, so only a direct call reaches these. |
| `accounts/forms.py` | 47, 75->77 | Editing a donor-role account, and saving the form with `commit=False`. Neither is used by any screen. |
| `accounts/lockout.py` | 26 | `minutes_remaining` returns 0 for an unlocked account. It is only called for locked accounts. |
| `accounts/views.py` | 96->113, 184 | Showing the user-edit form again after invalid input, and the hospital edit form on a GET. |
| `camps/models.py` | 43 | `__str__` of a camp, used only in the admin site. |
| `camps/services.py` | 127, 136-138 | Enrolment confirmation for a donor with no email, and a mail failure. Per D-67 the enrolment stands, and this needs a mail server error to trigger. |
| `camps/views.py` | 30->37, 55-56, 80->91 | A GET to the enrol URL, a camp refused by the service after the form accepted it, and a GET to the close URL. |
| `notifications/admin.py` | 15, 18, 21, 24 | Read-only admin permission methods. |
| `notifications/dispatcher.py` | 86-87, 130 | SMS failure for a donor with no email, and a notification taken by another worker first (needs two workers). |
| `notifications/management/commands/dispatch_notifications.py` | 22 | The `--loop` sleep. A test that looped would never finish. |
| `notifications/models.py` | 63 | `__str__` of a notification. |
| `notifications/sms.py` | 27-28 | The development backend that only logs. Tests use the in-memory outbox (D-78). |
| `reports/services/generator.py` | 116-117, 246 | Expired units in the Inventory Status Report, and a missing start or end date. |
| `reports/views.py` | 32 | A report name that does not exist (404). |
| `core/models.py` | 42 | `__str__` of a configuration value. |
| `core/management/commands/seed_demo.py` | 76 | A demo donor who is not eligible is skipped. |

All other files in the five packages are at 100 percent.

## 5. Assessment

Most gaps are string methods, admin settings, the development SMS backend, a loop that never exits, and failure paths that need a real mail or SMS server or two concurrent workers. None carries business logic for the cases in this report.

One gap is real logic and is recommended as a follow-up: `reports/services/generator.py` lines 116-117, the expired-unit rows of the Inventory Status Report. No test creates an expired unit for that report. It is related to the open ST-22 deviation (D-103).

The remaining 53 missing branches in the whole-project figure include code in other packages (inventory, donors, collection, bloodrequests) whose cases belong to other team members.
