# Branch Coverage Report

Prepared by Niveditha. Run date: 04-11-2026. Tool: coverage.py with `--branch`, driven by the Django test runner (`coverage run --branch manage.py test`), SQLite test database.

## 1. Result

| Measure | Value |
|---|---|
| Tests run | 577 |
| Passed | 576 |
| Skipped | 1 |
| Failed | 0 |
| Statements | 7,729 (7,616 covered, 98.5 percent) |
| Branches | 884 (831 covered, 53 missing) |
| Partial branches | 49 |
| **Branch coverage** | **94.0 percent** |

The Test Plan exit criterion (NFR-Q5) asks for at least 70 percent line coverage. Line coverage is 98.5 percent and branch coverage is 94.0 percent, so the criterion is met.

The one skipped test is `ConcurrentAllocationTests.test_only_one_of_two_simultaneous_allocations_wins`. SQLite has no `select_for_update`, so it runs only in the PostgreSQL pass of the CI (D-72). It is not one of the cases in this report.

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
