# Unit Test Report

**Project:** Blood Bank Management System (`SE-miniproject1/mini-project-documents`)  
**Author:** Balaraj R (QA Lead)  
**Date:** 17 November 2026  

## 1. Environment & Command

- **OS / Runtime:** Linux x86_64, Python 3.12.14, Django 5.x (`BBMS_ENV=test`)
- **Database:** SQLite in-memory (`file:memorydb_default?mode=memory&cache=shared`)
- **Command:**
  ```bash
  export BBMS_ENV=test DJANGO_SECRET_KEY=local-test
  python src/manage.py test src --verbosity 2 > docs/test-reports/unit-test-output.txt 2>&1
  ```

## 2. Suite Summary

- **Total tests discovered:** 576
- **Passed:** 575
- **Failed / Errors:** 0
- **Skipped:** 1 — `bloodrequests.tests.test_safety.ConcurrentAllocationTests.test_only_one_of_two_simultaneous_allocations_wins` (`"Database doesn't support feature(s): has_select_for_update"`). SQLite does not support `SELECT ... FOR UPDATE` row locks; this test runs on PostgreSQL 16 in CI (see `docs/DEVIATIONS.md` D-72).
- **Raw log:** `docs/test-reports/unit-test-output.txt`

## 3. Unit Test Cases (UT-01 to UT-48)

> Note: `UT-01` to `UT-09` (Donor Registration & Eligibility) are executed and recorded below. `UT-10` to `UT-48` are owned by Aadish, Dhanya and Niveditha in their respective Deliverable 3 PRs and reflect their current status on `main`.

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
| UT-10 | Collection Entry | Pending | Not executed |
| UT-11 | Unit Identifier | Pending | Not executed |
| UT-12 | Unit State Machine | Pending | Not executed |
| UT-13 | Screening Panel | Pending | Not executed |
| UT-14 | Release Rule | Pending | Not executed |
| UT-15 | Reactive Handling | Pending | Not executed |
| UT-16 | Component Separation | Pending | Not executed |
| UT-17 | BloodUnit Entity | Pending | Not executed |
| UT-18 | Stock Aggregation | Pending | Not executed |
| UT-19 | Inventory Query | Pending | Not executed |
| UT-20 | Expiry Job | Pending | Not executed |
| UT-21 | Near-Expiry Alert | Pending | Not executed |
| UT-22 | Transfer | Pending | Not executed |
| UT-23 | Discard Workflow | Pending | Not executed |
| UT-24 | Audit Writer | Pending | Not executed |
| UT-25 | Request Creation | Pending | Not executed |
| UT-26 | Request Validator | Pending | Not executed |
| UT-27 | Queue Ordering | Pending | Not executed |
| UT-28 | Approval Workflow | Pending | Not executed |
| UT-29 | Allocation Rules | Pending | Not executed |
| UT-30 | Allocation Rules | Pending | Not executed |
| UT-31 | Issue Recording | Pending | Not executed |
| UT-32 | Fulfilment State | Pending | Not executed |
| UT-33 | Cancellation | Pending | Not executed |
| UT-34 | Camp Creation | Pending | Not executed |
| UT-35 | Camp Validator | Pending | Not executed |
| UT-36 | Camp Listing | Pending | Not executed |
| UT-37 | Enrolment Eligibility | Pending | Not executed |
| UT-38 | Camp Collection Link | Pending | Not executed |
| UT-39 | Camp Closure | Pending | Not executed |
| UT-40 | Availability Search | Passed | Passed with deviation: the counts-only logic is in the view, not a separate service function, so it is verified through the view (core/tests/test_availability.py). The hospital response carries only blood group, component and count. Staff are refused with 403 instead of receiving unit identifiers |
| UT-41 | Dispatcher | Pending | Not executed |
| UT-42 | Reminder Jobs | Pending | Not executed |
| UT-43 | Shortage Appeal | Pending | Not executed |
| UT-44 | Report Engine | Pending | Not executed |
| UT-45 | Export | Pending | Not executed |
| UT-46 | Data Scoping | Pending | Not executed |
| UT-47 | User Administration | Pending | Not executed |
| UT-48 | Configuration Store | Pending | Not executed |
