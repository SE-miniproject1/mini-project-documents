# Code Coverage Report

Measured on 17 November 2026 with `coverage run src/manage.py test src` followed by `coverage report` (line coverage, Python 3.14, SQLite).

## 1. Summary

| Measure | Statements | Missed | Coverage |
|---|---|---|---|
| Application code (tests excluded) | 3186 | 83 | **97%** |
| Everything under `src/` including the test files | 7544 | 109 | 99% |

The figure to quote is the first one. The second is higher because test files run every line of themselves. The CI gate (`fail_under = 70`) is met by a wide margin.

## 2. Coverage by app

| App | Statements | Missed | Coverage |
|---|---|---|---|
| accounts | 312 | 5 | 98% |
| audit | 131 | 3 | 98% |
| bbms | 95 | 12 | 87% |
| bloodrequests | 451 | 12 | 97% |
| camps | 212 | 7 | 97% |
| collection | 285 | 7 | 98% |
| core | 315 | 2 | 99% |
| donors | 444 | 9 | 98% |
| inventory | 439 | 11 | 97% |
| notifications | 246 | 11 | 96% |
| reports | 256 | 4 | 98% |

## 3. Modules below 100%

| Module | Statements | Missed | Coverage | Lines not run |
|---|---|---|---|---|
| notifications/admin.py | 15 | 4 | 73% | 15, 18, 21, 24 |
| donors/admin.py | 23 | 4 | 83% | 22, 30, 33, 36 |
| bbms/settings.py | 92 | 12 | 87% | 22, 29, 34, 41, 102, 200, 205-210 |
| donors/validators.py | 34 | 4 | 88% | 33-34, 47, 57 |
| accounts/backends.py | 22 | 2 | 91% | 13, 15 |
| inventory/services/actions.py | 36 | 3 | 92% | 16, 48-49 |
| audit/admin.py | 14 | 1 | 93% | 14 |
| bloodrequests/views.py | 105 | 7 | 93% | 41-42, 53, 149-150, 210-211 |
| notifications/management/commands/dispatch_notifications.py | 14 | 1 | 93% | 22 |
| core/models.py | 18 | 1 | 94% | 42 |
| notifications/sms.py | 32 | 2 | 94% | 27-28 |
| audit/models.py | 43 | 2 | 95% | 59-60 |
| bloodrequests/models.py | 62 | 3 | 95% | 67-68, 121 |
| camps/services.py | 86 | 4 | 95% | 127, 136-138 |
| collection/models.py | 41 | 2 | 95% | 26, 71 |
| inventory/forms.py | 42 | 2 | 95% | 29, 39 |
| camps/views.py | 57 | 2 | 96% | 55-56 |
| collection/services/screening.py | 77 | 3 | 96% | 104-106 |
| inventory/services/stock.py | 25 | 1 | 96% | 58 |
| notifications/dispatcher.py | 72 | 3 | 96% | 86-87, 130 |
| camps/models.py | 33 | 1 | 97% | 43 |
| collection/views.py | 60 | 2 | 97% | 39-41 |
| inventory/views.py | 89 | 3 | 97% | 142-143, 149 |
| notifications/models.py | 36 | 1 | 97% | 63 |
| reports/services/generator.py | 101 | 3 | 97% | 116-117, 246 |
| accounts/forms.py | 64 | 1 | 98% | 47 |
| accounts/lockout.py | 40 | 1 | 98% | 26 |
| bloodrequests/workflow.py | 52 | 1 | 98% | 97 |
| core/management/commands/seed_demo.py | 57 | 1 | 98% | 76 |
| inventory/services/separation.py | 47 | 1 | 98% | 24 |
| reports/views.py | 44 | 1 | 98% | 32 |
| accounts/views.py | 79 | 1 | 99% | 184 |
| bloodrequests/allocation.py | 121 | 1 | 99% | 128 |
| donors/models.py | 98 | 1 | 99% | 88 |
| inventory/models.py | 86 | 1 | 99% | 105 |

## 4. Reading the gaps

Each missed line is one the suite never reaches. None sits in the blood safety rules (`inventory/services/safety.py`, `donors/services/eligibility.py`, `collection/services/guard.py`) or in the status machine and audit store, which are all at 100% or within two lines of it.

- The lowest figures are in `admin.py` files (Django admin display helpers), `bbms/settings.py` (environment-dependent settings) and `notifications/sms.py` (the HTTP gateway, which tests replace with an in-memory outbox, D-78).
- One concurrency case is skipped on SQLite (D-72, D-101).
- One line is excluded with `# pragma: no cover`: the error handler at `inventory/services/separation.py` line 99, which cannot be reached from a Quarantined unit.

## 5. Method and limits

- Line coverage only. Branch coverage is a separate report.
- A covered line shows that a test ran it, not that the test checked its result.
- To repeat: `coverage erase && coverage run src/manage.py test src && coverage report --omit='*/tests/*'`.
