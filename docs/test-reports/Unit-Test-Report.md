# Unit Test Report

**Project:** Blood Bank Management System (`SE-miniproject1/mini-project-documents`)  
**Author:** Balaraj R (QA Lead)  
**Date:** 19 November 2026  

## 1. Environment & Command

- **OS / Runtime:** Linux x86_64, Python 3.12.14, Django 5.2 (`BBMS_ENV=test`)
- **Database:** SQLite in-memory (`file:memorydb_default?mode=memory&cache=shared`)
- **Command:**
  ```bash
  export BBMS_ENV=test DJANGO_SECRET_KEY=local-test
  python src/manage.py test src --verbosity 2 > docs/test-reports/unit-test-output.txt 2>&1
  ```

## 2. Suite Summary

- **Total tests discovered:** 586
- **Passed:** 585
- **Failed / Errors:** 0
- **Skipped:** 1 — `bloodrequests.tests.test_safety.ConcurrentAllocationTests.test_only_one_of_two_simultaneous_allocations_wins` (`"Database doesn't support feature(s): has_select_for_update"`). SQLite does not support `SELECT ... FOR UPDATE` row locks; this test runs on PostgreSQL 16 in CI (see `docs/DEVIATIONS.md` D-72).
- **Raw log:** `docs/test-reports/unit-test-output.txt`

## 3. Unit Test Cases (UT-01 to UT-48)

> All 48 unit test cases (`UT-01` to `UT-48`) are executed and recorded from `main` (46 Passed, 2 Passed with deviation: `UT-19` and `UT-47`).

| Case ID | Feature | Result | Actual Result / Evidence |
|---|---|---|---|
| UT-01 | Donor Registration | Passed | Passed in `donors/tests/test_registration.py` (`RegistrationFormTests.test_a_complete_valid_form_creates_one_donor_with_the_submitted_values`); form validates and persists one donor row (D-94). |
| UT-02 | Donor Identifier | Passed | Passed in `donors/tests/test_registration.py` (`DonorIdTests.test_a_thousand_identifiers_are_distinct_and_well_formed`); 1,000 generated IDs match `DNR` + 8 digits and are distinct. |
| UT-03 | Uniqueness Validator | Passed | Passed in `donors/tests/test_validation.py` (`DuplicateTests.test_a_duplicate_mobile_number_is_refused_with_the_srs_message`); duplicate mobile rejected with exact SRS message and row count unchanged. |
| UT-04 | Age Rule | Passed | Passed in `donors/tests/test_validation.py` (`AgeRuleTests.test_the_boundaries_are_inclusive_at_18_and_65`, `test_just_under_18_and_just_over_65_are_rejected`); 18, 40, 65 accepted; 17, 66 rejected. |
| UT-05 | Deferral Rules | Passed | Passed in `donors/tests/test_declarations.py` (`EngineWithDeclarationsTests.test_a_permanent_condition_defers_for_good_with_no_review_date`, `RegistrationDeclarationTests`); status set to Permanently Deferred with no review date. |
| UT-06 | Eligibility Engine | Passed | Passed in `donors/tests/test_eligibility.py` (`EngineTests.test_a_donor_who_meets_every_criterion_is_eligible`); returns Eligible with empty failure list. |
| UT-07 | Eligibility Engine | Passed | Passed in `donors/tests/test_eligibility.py` (`EngineTests.test_every_failing_criterion_is_reported_not_only_the_first`); returns Temporarily Deferred with all failing reasons listed. |
| UT-08 | Collection Guard | Passed | Passed in `collection/tests/test_guard.py` (`GuardTests.test_a_deferred_donor_is_refused_with_the_reason_and_review_date`) and `collection/tests/test_collect.py`; refused with reason/review date and no unit created. |
| UT-09 | Interval Calculator | Passed | Passed in `donors/tests/test_eligibility.py` (`NextEligibleDateTests.test_ninety_days_after_the_last_donation`); returns last donation date + 90 days. |
| UT-10 | Collection Entry | Passed | Passed: record_collection() creates one quarantined unit and sets the donor's last donation date (collection/tests/test_collect.py) |
| UT-11 | Unit Identifier | Passed | Passed: 1000 identifiers are distinct and match BU + 10 digits (inventory/tests/test_unit_model.py) |
| UT-12 | Unit State Machine | Passed | Passed: a new unit is Quarantined and a direct move to Issued is refused as an invalid transition (inventory/tests/test_unit_model.py) |
| UT-13 | Screening Panel | Passed | Passed: with Malaria missing, release is refused naming the test and the unit stays Quarantined (collection/tests/test_screening.py) |
| UT-14 | Release Rule | Passed | Passed: a complete non-reactive panel releases the unit to Available (collection/tests/test_screening.py) |
| UT-15 | Reactive Handling | Passed | Passed: one Reactive result discards the unit with reason Reactive Screening, the administrator alert is queued, and restoring the unit is refused (collection/tests/test_screening.py) |
| UT-16 | Component Separation | Passed | Passed: three linked child units with per-component expiry, parent closed (inventory/tests/test_separation.py) |
| UT-17 | BloodUnit Entity | Passed | Passed: every attribute is stored and returned unchanged, and a new unit is Quarantined, in quarantine storage, and cannot be created in any other status (inventory/tests/test_unit_model.py) |
| UT-18 | Stock Aggregation | Passed | Passed: only Available units are counted, every status is reported including empty ones, an expired unit is not counted even if still marked Available, and the row and column totals add up (inventory/tests/test_console.py) |
| UT-19 | Inventory Query | Passed with deviation | Passed with deviation: units matching every filter (group, component, location, status and expiry range) are listed and a unit matching fewer filters is not. The filtering is done by the console view and not by a separate inventory query function, so it is tested through the view, with A+ PRBC in FRIDGE-A1 instead of A+ FFP in FREEZER-B1 (inventory/tests/test_actions.py). See D-99 |
| UT-20 | Expiry Job | Passed | Passed: a unit past its expiry date becomes Expired and others are left alone, Quarantined and Reserved units expire too, Issued and Discarded units are not touched, a second run changes nothing, and each expiry is audited (inventory/tests/test_expiry.py) |
| UT-21 | Near-Expiry Alert | Passed | Passed: units inside the near-expiry window are listed soonest first, a unit expiring today is flagged, expired and non-Available units are not, and the window is configurable (inventory/tests/test_expiry.py) |
| UT-22 | Transfer | Passed | Passed: a transfer to FRIDGE-B2 changes the location and leaves the status Available, and the audit entry holds the previous and new location and the acting user (inventory/tests/test_actions.py) |
| UT-23 | Discard Workflow | Passed | Passed: a discard with no reason is refused, the retry with Breakage sets Discarded and stores the reason, and discarding an Issued unit is refused (inventory/tests/test_actions.py) |
| UT-24 | Audit Writer | Passed | Passed: each transition writes an entry with who, what, when and why, three transitions give three entries in order, a refused transition writes none, and edit, delete, bulk update and bulk delete of an entry are all refused (audit/tests/test_audit.py) |
| UT-25 | Request Creation | Passed | Passed: a valid request is created as Pending with a unique REQ identifier, identifiers are sequential and never reused, only users of an active hospital can raise one, and it is audited and staff are notified (bloodrequests/tests/test_raise_request.py) |
| UT-26 | Request Validator | Passed | Passed: quantity 0, -3, 51, a non-whole 1.5 and a required-by time in the past are each refused with the field named, and nothing is saved. 1.5 and one minute in the past were used in place of 2.5 and yesterday (bloodrequests/tests/test_raise_request.py) |
| UT-27 | Queue Ordering | Passed | Passed: the queue lists Emergency requests first and then orders by required-by time, and closed requests are left out unless asked for (bloodrequests/tests/test_queue.py) |
| UT-28 | Approval Workflow | Passed | Passed: a rejection with no reason or a reason outside the list is refused and the request stays Pending, and a valid reason sets Rejected, is stored and is emailed to the hospital (bloodrequests/tests/test_queue.py) |
| UT-29 | Allocation Rules | Passed | Passed: a unit of the wrong blood group is refused with the reason, nothing is reserved and the unit stays Available (bloodrequests/tests/test_allocation.py) |
| UT-30 | Allocation Rules | Passed | Passed: Quarantined, Expired, Reserved, Issued and Discarded units are each refused, a unit past its expiry date is refused even if marked Available, and two requests cannot hold one unit (bloodrequests/tests/test_allocation.py) |
| UT-31 | Issue Recording | Passed | Passed: allocation reserves the units, confirming the issue sets them to Issued, and the allocation record carries the issuing staff member, the Issued state and the issue time and links the request and its hospital (bloodrequests/tests/test_allocation.py) |
| UT-32 | Fulfilment State | Passed | Passed: issuing all requested units sets Fulfilled and issuing fewer sets Partially Fulfilled with the shortfall recorded, and the request stays open. Tested with 2 requested and 2 issued, then 2 requested and 1 issued, in place of 3 and 3, then 3 and 1 (bloodrequests/tests/test_allocation.py) |
| UT-33 | Cancellation | Passed | Passed: cancelling releases every reserved unit back to Available, a Pending request can be cancelled, and cancellation is barred once any unit is issued (bloodrequests/tests/test_allocation.py) |
| UT-34 | Camp Creation | Passed | Passed: `test_a_valid_camp_is_scheduled_with_a_unique_id_and_audited` creates a Scheduled camp with a unique CMP identifier, stores its details and writes an audit entry (`camps/tests/test_camps.py`). |
| UT-35 | Camp Validator | Passed | Passed: `test_today_is_allowed_but_the_past_is_not`, `test_end_time_must_be_after_start_time_and_target_positive` and the database time-rule test reject past dates, invalid time ranges and a zero target with the relevant field error (`camps/tests/test_camps.py`). |
| UT-36 | Camp Listing | Passed | Passed: `test_only_scheduled_future_camps_in_date_order` returns only future Scheduled camps in date order and excludes Completed, Cancelled and past camps (`camps/tests/test_camps.py`). |
| UT-37 | Enrolment Eligibility | Passed | Passed: the enrolment eligibility tests accept donors eligible by the camp date and refuse donors whose next eligible date is later, showing that date and creating no enrolment (`camps/tests/test_camps.py`). |
| UT-38 | Camp Collection Link | Passed | Passed: `test_a_unit_collected_at_a_camp_carries_the_camp_as_its_site` stores the camp identifier as both the unit and donation collection site; centre collections remain unchanged (`camps/tests/test_collection_link.py`). |
| UT-39 | Camp Closure | Passed | Passed: `test_closing_reports_actuals_against_target_and_blocks_more_collections` closes the camp with the actual collection count, records the audit reason and refuses another collection after closure (`camps/tests/test_collection_link.py`). |
| UT-40 | Availability Search | Passed | Passed with deviation: the counts-only logic is in the view, not a separate service function, so it is verified through the view (`core/tests/test_availability.py`). The hospital response carries only blood group, component and count. Staff are refused with 403 instead of receiving unit identifiers. |
| UT-41 | Dispatcher | Passed | Passed: `test_sms_is_tried_three_times_at_increasing_intervals_then_email` retries failed SMS delivery three times with increasing intervals and then queues email fallback (`notifications/tests/test_notifications.py`). |
| UT-42 | Reminder Jobs | Passed | Passed: `test_only_the_donor_eligible_today_is_reminded`, `test_a_missed_day_is_caught_up_but_old_dates_are_not` and camp reminder tests queue reminders only for due donors and camps within 24 hours, avoid old dates and prevent duplicate reminders (`notifications/tests/test_notifications.py`). |
| UT-43 | Shortage Appeal | Passed | Passed: shortage appeal tests identify O- stock below its configured threshold, notify only eligible O- donors, suppress repeats for 30 days and send no appeal when stock is sufficient (`notifications/tests/test_notifications.py`). |
| UT-44 | Report Engine | Passed | Passed: `test_every_report_returns_rows_in_its_column_order` checks all report titles, column order and row lengths; report generator tests also verify date-range validation and report contents (`reports/tests/test_generator.py`). |
| UT-45 | Export | Passed | Passed: CSV and PDF export tests verify provenance headers, column/data order, valid PDF output, CSV quoting and formula neutralisation (`reports/tests/test_export_csv.py`, `reports/tests/test_export_pdf.py`). |
| UT-46 | Data Scoping | Passed | Passed: `test_hospital_users_see_only_their_own_requests` confirms a hospital sees only its own requests while staff can see both hospitals' records (`reports/tests/test_generator.py`). |
| UT-47 | User Administration | Passed with deviation | Passed with deviation: a user holds a single role, so a second role cannot be assigned; a role change replaces it (D-102). Deactivation keeps the row (`accounts/tests/test_admin.py`). |
| UT-48 | Configuration Store | Passed | Passed: `test_an_override_applies_to_the_next_call` confirms saved administrator settings, including the 120-day donation interval and updated near-expiry and stock thresholds, are used by the configuration service; validation rejects an interval below 90 days (`core/tests/test_config.py`). |
