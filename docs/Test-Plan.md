# Software Test Plan (STP)

## Blood Bank Management System

**Project:** Blood Bank Management System (BBMS)
**Version:** 1.0
**Authors:**

| SRN | Name | GitHub Handle | Testing Responsibility |
|---|---|---|---|
| PES1UG24CS560 | Balaraj R | balaraj74 | QA Lead. Plan, SF-1 and SF-2 test cases, integration tests. |
| PES1UG24CS567 | Dhanya K M | Dhanya-KM | Test Engineer. SF-3 and SF-4 test cases, data and inventory scenarios. |
| PES1UG24CS569 | G A Aadish | Sonuaadi0706 | Security validation and safety negative tests, system tests. |
| PES1UG24CS585 | Niveditha | nnivedithaparmesh-cpu | Test Engineer. SF-5 and SF-6 test cases, reporting and notification tests. |

**Organization:** SE-miniproject1
**Date:** 02 October 2026
**Status:** Draft. Restructured to the IEEE-style STP layout required for Deliverable 2. The detailed test cases from Deliverable 1 are retained unchanged in Appendix A.

---

## 1. Introduction

**Purpose.** This document defines the test plan for the Blood Bank Management System (BBMS) Release 1.0. It states the objectives, scope, strategy, environment, schedule, responsibilities and traceability for testing, so that every requirement in the SRS is verifiably covered.

**Scope.** Testing covers all six system features in the SRS (donor registration and eligibility, collection and screening, inventory, hospital request and issue, camps, and search, notification and reporting) together with the performance, safety, security and quality requirements in SRS Section 6. Third-party gateways and framework internals are excluded, as listed in Section 4.

**References.**

- `docs/SRS.md`, Software Requirements Specification, Version 1.0
- `docs/SAD.md`, Software Architecture and Design Specification, Version 1.0
- IEEE Std 829-2008, *Standard for Software and System Test Documentation*
- OWASP Application Security Verification Standard, Version 4.0

**Definitions.** BBMS (Blood Bank Management System), SRS (Software Requirements Specification), SAD (Software Architecture and Design Specification), RTM (Requirement Traceability Matrix), RBAC (Role-Based Access Control), TLS (Transport Layer Security), UT, IT, ST and SV (unit, integration, system and security-validation test case prefixes).

---

## 2. Test Items

- Donor registration and eligibility module (SF-1)
- Collection, screening and component separation module (SF-2)
- Inventory and stock module (SF-3)
- Hospital request and issue module (SF-4)
- Donation camp module (SF-5)
- Search, notification, reporting and administration module (SF-6)
- Authentication, RBAC and audit components shared by all modules
- Notification dispatcher and scheduled jobs

---

## 3. Features to be Tested

Features are mapped to SRS requirement identifiers.

| Feature | SRS Requirements | Priority |
|---|---|---|
| SF-1 Donor registration and eligibility screening | REQ-1 to REQ-8 | High |
| SF-2 Blood donation and collection management | REQ-9 to REQ-15 | High |
| SF-3 Blood inventory and stock management | REQ-16 to REQ-23 | High |
| SF-4 Hospital blood request and issue | REQ-24 to REQ-31 | High |
| SF-5 Donation camp and drive management | REQ-32 to REQ-37 | Medium |
| SF-6 Search, notification and reporting | REQ-38 to REQ-46 | Medium to High |

Nonfunctional requirements under test:

| Group | Requirements | Measure |
|---|---|---|
| Performance | NFR-P1, NFR-P2 | Screen render at most 3 seconds and availability search at most 2 seconds, 95th percentile |
| Safety | NFR-S1 to NFR-S4 | Untested, expired or wrong-group unit can never be issued. No double allocation |
| Security | NFR-SEC1 to NFR-SEC11 | See Section 5.1 |
| Quality | NFR-Q5, NFR-Q6, NFR-Q9 | At least 70 percent coverage, every requirement has a test, server-side validation |

---

## 4. Features Not to be Tested

- Laboratory instrument integration. Release 1.0 enters screening results manually (SRS ASM-2).
- Compatible-group substitution for issue. This stays a manual clinical decision (SRS BR-8).
- Internals of the third-party SMS gateway and SMTP relay. Only the BBMS side of the interface is tested, using stubs.
- Django, Gunicorn, Nginx and PostgreSQL internals, which are assumed tested by their maintainers.
- Barcode scanner device firmware. The scanner is treated as a keyboard.
- Billing, national registry integration and a native mobile application, all out of scope in SRS Section 1.3.

---

## 5. Test Approach / Strategy

**Levels.**

| Level | Prefix | Definition | Cases |
|---|---|---|---|
| Unit | UT | One function, validator or service method in isolation, collaborators stubbed | 48 |
| Integration | IT | Two or more components together, including the database and gateway stubs | 26 |
| System | ST | End-to-end scenarios through the user interface, including negative, security, concurrency and performance | 30 |
| Security validation | SV | Authentication, session, transport, storage, logging and fuzz checks (Section 5.1) | 8 |
| Acceptance | none | Faculty demonstration of the system tests against the SRS | by demonstration |

**Types.** Functional testing of every requirement, regression testing after each merged change, performance testing of the two bounded operations, safety negative testing (attempting every forbidden transition), usability testing of the staff and donor consoles, and security testing (Section 5.1).

**Entry criteria.** A stable build is deployed to the test environment, the deterministic seed data is loaded, test accounts exist for each role, and no blocker defect from the previous cycle remains open.

**Exit criteria.** All planned cases executed, no Critical or High defect open, at least 95 percent of cases passed, and unit test line coverage at least 70 percent (SRS NFR-Q5).

### 5.1 Security Validation

Security objectives in SRS Section 6.3 are SEC-OBJ-1 (confidentiality of donor and patient data) and SEC-OBJ-2 (integrity and non-repudiation of safety-critical transactions). Validation is organised around them.

- **Authentication.** Password policy, lockout and session handling are exercised directly (SV-01, SV-02, SV-03).
- **Authorisation and isolation.** Vertical privilege (a donor reaching staff or admin URLs) and horizontal privilege (one hospital reading another hospital's records) are covered by the existing ST-28, IT-25 and IT-21.
- **Confidentiality.** Donor identity must never reach a hospital user in any screen, export or notification (ST-29, IT-08, IT-21).
- **Transport and storage.** TLS 1.2+ verification and credential storage are checked in SV-04 and SV-05.
- **Input handling.** Fuzzing of every free-text and numeric field with SQL, script and oversized payloads (SV-07, ST-29).
- **Non-repudiation.** Failed logins, authorisation failures and status transitions must appear in the audit log (SV-08, UT-24, IT-13).
- **Tooling.** An automated scanner is run against the test environment for the OWASP Top Ten classes (ST-29). Penetration testing of the authentication flow is limited to the cases above.

New security validation cases:

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| SV-01 | Authentication | Verify the password policy rejects weak and known-compromised passwords | Registration or password-change screen reachable | 1: Open the password change form<br>2: Submit each candidate password<br>3: Read the response | `short1!`, `longenoughbutnodigits!`, `Password123!` (on the compromised list), `Blood#Bank2026x` | The first three are rejected with a message naming the rule broken. The last is accepted | Not executed | Pending |
| SV-02 | Authentication | Verify the account locks for 15 minutes after 5 consecutive failed logins and the holder is emailed | Test staff account exists with a reachable mailbox | 1: Submit a wrong password 5 times<br>2: Submit the correct password immediately<br>3: Check the mailbox<br>4: Retry after 15 minutes | Wrong password x5, then the correct one | The sixth attempt is refused even with the correct password, a lockout email arrives, and login succeeds after 15 minutes | Not executed | Pending |
| SV-03 | Session management | Verify sessions expire after 30 minutes idle and are invalidated on logout and password change | Signed in as staff in two browsers | 1: Stay idle 31 minutes in browser A and reload<br>2: Log out in browser B and replay its old session cookie<br>3: Change password in A and reuse B's session | Captured session cookies | Idle session redirects to login. Replayed cookie after logout is refused. Other sessions end on password change | Not executed | Pending |
| SV-04 | Transport security | Verify HTTP redirects to HTTPS, weak TLS versions are refused and HSTS is sent | Test environment deployed behind the reverse proxy | 1: Request the site over plain HTTP<br>2: Attempt a TLS 1.0 and TLS 1.1 handshake<br>3: Inspect response headers | `http://` URL, a TLS scanner | HTTP gets a permanent redirect to HTTPS, TLS below 1.2 handshakes fail, `Strict-Transport-Security` header is present | Not executed | Pending |
| SV-05 | Credential storage | Verify only salted slow hashes are stored | Seeded database | 1: Query the user table's password column for 5 accounts<br>2: Compare two accounts given the same password | Two accounts with identical passwords | Values are salted hashes of a slow key derivation function, never plain text, and the two identical passwords produce different hashes | Not executed | Pending |
| SV-06 | Logging | Verify logs never contain passwords, session tokens or full medical histories | Application run through login, registration and screening | 1: Perform those flows at DEBUG and INFO level<br>2: Search the log output for the test values | Known test password, session id and a declared condition | None of the secret values appear in any log line | Not executed | Pending |
| SV-07 | Input handling | Verify fuzzed input never causes an unhandled error or data corruption | Staff console reachable | 1: Submit oversized, empty, unicode, negative, SQL and script payloads to every free-text and numeric field<br>2: Inspect responses and database | 10 000-character strings, `-1`, `' OR 1=1 --`, `<script>alert(1)</script>` | Every payload gets a field-level validation message or is stored as inert text. No stack trace, no 500, no script execution | Not executed | Pending |
| SV-08 | Audit | Verify failed logins and authorisation failures are written to the audit log with user, time and source | Audit log viewable by the administrator | 1: Fail a login as staff<br>2: Request an admin-only URL as a donor<br>3: Open the audit log as admin | Failed credentials, forbidden URL | Both events appear with the acting user, timestamp and source address | Not executed | Pending |

---

## 6. Test Environment

**Hardware.** Developer laptops and one test server with 4 virtual CPUs, 8 GB RAM and 100 GB storage. A USB or Bluetooth barcode scanner in keyboard mode for the collection screen.

**Software.** Python 3.11, Django 5.x, Gunicorn behind Nginx with TLS, PostgreSQL 15 (SQLite 3 for unit tests only), Google Chrome as the reference browser.

**Tools.** Django test runner with pytest and coverage.py (unit and integration), Selenium (UI automation), JMeter (load, NFR-P1 and NFR-P2), a TLS scanner and OWASP ZAP (security), Git and GitHub for defect tracking through issues.

**Test data.** A deterministic seed fixture with accounts for each role (`staff01`, `hosp01`, `admin01`, donor `DNR10000001`) and 50 000 unit records for the performance case.

---

## 7. Test Schedule

| Milestone | Date |
|---|---|
| Test case design (Deliverable 1) | Complete, 10 September 2026 |
| Restructure to STP layout and security validation cases (Deliverable 2) | 02 October 2026 |
| Environment setup | After the implementation milestone. Date to be confirmed by the team |
| Test execution | After environment setup. Date to be confirmed by the team |
| Acceptance demonstration | To be scheduled with the course faculty |

No test has been executed. Actual Result and Test Result columns stay `Not executed` and `Pending` until the system exists.

---

## 8. Test Deliverables

- Test Plan (this document)
- Test cases, manual and automated (Appendix A and Section 5.1)
- Test scripts and seed data
- Test execution logs
- Defect reports (GitHub issues)
- Test Summary Report

---

## 9. Roles and Responsibilities

| Role | Name | Responsibility |
|---|---|---|
| QA Lead | Balaraj R | Prepare the plan, coordinate execution, own the traceability matrix |
| Test Engineer | Dhanya K M | Design and execute inventory and request cases, log defects |
| Test Engineer | Niveditha | Design and execute camp, reporting and notification cases, log defects |
| Security and System Test | G A Aadish | Security validation, safety negative tests, architecture questions |
| Sign-off | Course faculty | Approve results and readiness |

---

## 10. Risks and Mitigation

| Risk | Mitigation |
|---|---|
| Implementation is late, leaving little time to execute 112 cases | Prioritise safety (ST-26, ST-27) and security (Section 5.1) cases first, then High-priority features |
| Concurrency case ST-27 is hard to reproduce reliably | Use a scripted two-session harness and repeat the case 50 times |
| Gateway outage blocks notification tests | Use stubs for the SMS gateway and SMTP relay |
| Performance results differ between laptops and the test server | Run NFR-P1 and NFR-P2 only on the test server |
| Team members cannot all attend execution sessions | Cases are owned per feature so execution can proceed independently |

---

## 11. Assumptions and Dependencies

- The system is implemented to the SRS and SAD before execution starts.
- Test accounts and the seed fixture are available before execution.
- SMS and email gateways are stubbed in the test environment.
- The SRS and the traceability in Section 13 are kept in step. Any change to a requirement updates both.

---

## 12. Suspension and Resumption Criteria

**Suspend testing if** the test environment is unavailable for more than 4 hours, the build is unstable enough to block more than 30 percent of planned cases, or a Critical safety defect is found (any path that issues an untested, expired or wrong-group unit).

**Resume testing when** blocking defects are fixed and verified, the environment is stable, and for a safety defect a regression run of ST-26 and ST-27 passes.

---

## 13. Test Case Management and Traceability

The RTM in SRS Appendix C maps each requirement to architecture, design and code references. The tables below are the test-side view of the same mapping. Detailed case descriptions are in Appendix A and Section 5.1.

### 13.1 Functional requirements

| Requirement | Summary | Unit / Integration Cases | System Cases |
|---|---|---|---|
| REQ-1 | Donor registration capturing personal, contact and medical details | UT-01, IT-01 | ST-01 |
| REQ-2 | Unique immutable donor identifier DNR + 8 digits | UT-02 | ST-01 |
| REQ-3 | Reject duplicate mobile number or email | UT-03, IT-01 | ST-02 |
| REQ-4 | Age between 18 and 65 validated from date of birth | UT-04 | ST-02 |
| REQ-5 | Record medical history and apply permanent deferral | UT-05, IT-02 | ST-03 |
| REQ-6 | Evaluate all eligibility criteria and report every failure | UT-06, UT-07, IT-02 | ST-03 |
| REQ-7 | Block collection against a non-eligible donor | UT-08, IT-03 | ST-04 |
| REQ-8 | Compute next eligible date and auto-clear deferral | UT-09, IT-04 | ST-04 |
| REQ-9 | Record donation event with site and staff | UT-10, IT-05 | ST-05 |
| REQ-10 | Unique immutable unit identifier BU + 10 digits with barcode | UT-11 | ST-05 |
| REQ-11 | New units created Quarantined and not issuable | UT-12, IT-06 | ST-06 |
| REQ-12 | Mandatory screening panel complete before release | UT-13, IT-07 | ST-06 |
| REQ-13 | Release to Available only when all results Non-Reactive | UT-14, IT-07 | ST-07 |
| REQ-14 | Discard on reactive result and alert administrator | UT-15, IT-08 | ST-07 |
| REQ-15 | Component separation with per-component expiry and linkage | UT-16, IT-09 | ST-08 |
| REQ-16 | Maintain full unit attribute set and status | UT-17 | ST-09 |
| REQ-17 | Stock counts by group and component refreshed within 5 seconds | UT-18, IT-10 | ST-09 |
| REQ-18 | Filter and search inventory on combined criteria | UT-19, IT-10 | ST-10 |
| REQ-19 | Auto-expire units and exclude from availability | UT-20, IT-11 | ST-10 |
| REQ-20 | Flag near-expiry units and send daily digest | UT-21, IT-11 | ST-11 |
| REQ-21 | Record inter-location transfer without status change | UT-22, IT-12 | ST-11 |
| REQ-22 | Require reason and confirmation for manual discard | UT-23, IT-12 | ST-12 |
| REQ-23 | Immutable audit record for every status transition | UT-24, IT-13 | ST-12 |
| REQ-24 | Hospital raises request with unique identifier | UT-25, IT-14 | ST-13 |
| REQ-25 | Reject non-positive quantity and past required-by date | UT-26 | ST-13 |
| REQ-26 | Queue ordered by urgency then required-by | UT-27, IT-15 | ST-14 |
| REQ-27 | Approve, reject or partially fulfil with reason | UT-28, IT-15 | ST-14 |
| REQ-28 | Allocate only matching, Available, unexpired units | UT-29, UT-30, IT-16 | ST-15 |
| REQ-29 | Reserve then issue, recording full issue detail | UT-31, IT-16 | ST-15 |
| REQ-30 | Set Fulfilled or Partially Fulfilled and record shortfall | UT-32, IT-17 | ST-16 |
| REQ-31 | Hospital cancels own request and reservations released | UT-33, IT-17 | ST-16 |
| REQ-32 | Create camp with venue, schedule, organiser and target | UT-34, IT-18 | ST-17 |
| REQ-33 | Reject past camp date and invalid time range | UT-35 | ST-17 |
| REQ-34 | Publish scheduled camps and permit donor enrolment | UT-36, IT-19 | ST-18 |
| REQ-35 | Refuse enrolment when donor not eligible on camp date | UT-37, IT-19 | ST-18 |
| REQ-36 | Record camp as collection site on collected units | UT-38, IT-20 | ST-19 |
| REQ-37 | Close camp, report actual against target, block further entry | UT-39, IT-20 | ST-19 |
| REQ-38 | Availability search returning counts without donor data | UT-40, IT-21 | ST-20 |
| REQ-39 | Asynchronous dispatch with retry and email fallback | UT-41, IT-22 | ST-21 |
| REQ-40 | Eligibility and camp reminder notifications | UT-42, IT-22 | ST-21 |
| REQ-41 | Shortage appeal with 30-day per-donor suppression | UT-43, IT-23 | ST-22 |
| REQ-42 | Generate the six specified reports over a date range | UT-44, IT-24 | ST-22 |
| REQ-43 | Export every report as PDF and CSV with provenance header | UT-45, IT-24 | ST-23 |
| REQ-44 | Scope every report and search to the user's authorisation | UT-46, IT-25 | ST-23 |
| REQ-45 | Administer users, roles and hospital registration | UT-47, IT-26 | ST-24 |
| REQ-46 | Configure operational parameters without code change | UT-48, IT-26 | ST-24 |

### 13.2 Nonfunctional requirements

| Requirement | Description | Verification Method | Test Cases |
|---|---|---|---|
| NFR-P1 | Screen render within 3 seconds at 50 concurrent users | Load test | ST-25 |
| NFR-P2 | Availability search within 2 seconds at 50,000 units | Load test | ST-25 |
| NFR-S1 | Untested unit can never be issued | Negative test | ST-26 |
| NFR-S2 | Expired unit can never be issued | Negative test | ST-26 |
| NFR-S3 | Group mismatch allocation prevented | Negative test | ST-27 |
| NFR-S4 | Concurrent double allocation prevented | Concurrency test | ST-27 |
| NFR-SEC5 | Server-side role enforcement on every request | Security test | ST-28 |
| NFR-SEC6 | Hospital and donor data isolation | Security test | ST-28 |
| NFR-SEC7 | Donor identity never exposed to hospital users | Security test | ST-29 |
| NFR-SEC9 | No OWASP Top Ten vulnerability classes present | Security scan and manual test | ST-29 |
| NFR-Q5 | Unit test line coverage at least 70 percent | Coverage report | ST-30 |
| NFR-Q6 | Every functional requirement covered by a test case | Traceability review | ST-30 |
| NFR-SEC1 | Authentication required for every non-public function | Security test | ST-28, SV-08 |
| NFR-SEC2 | Passwords stored only as salted slow hashes | Inspection test | SV-05 |
| NFR-SEC3 | Password policy and compromised-password rejection | Security test | SV-01 |
| NFR-SEC4 | Lockout after 5 failures for 15 minutes | Security test | SV-02 |
| NFR-SEC8 | TLS 1.2+ for all data in transit | Configuration scan | SV-04 |
| NFR-SEC10 | Audit record for auth events and config changes | Security test | SV-06, SV-08 |
| NFR-SEC11 | Session expiry and invalidation | Security test | SV-03 |
| NFR-Q9 | Server-side validation, no unhandled errors on bad input | Fuzz test | SV-07 |

---

## 14. Test Metrics and Reporting

**Planned coverage.**

| Level | Planned | Executed | Passed | Failed | Pending |
|---|---|---|---|---|---|
| Unit | 48 | 0 | 0 | 0 | 48 |
| Integration | 26 | 0 | 0 | 0 | 26 |
| System | 30 | 0 | 0 | 0 | 30 |
| Security validation | 8 | 0 | 0 | 0 | 8 |
| **Total** | **112** | **0** | **0** | **0** | **112** |

**Metrics collected.** Percentage of cases executed, percentage passed and failed, defect density, defect ageing and requirement coverage (currently 46 of 46 functional requirements and 20 nonfunctional requirements have at least one case).

**Reports.** Daily execution status during the execution window and a final Test Summary Report.

---

## 15. Approvals

| Role | Name | Signature / Date |
|---|---|---|
| QA Lead | Balaraj R | |
| Project Lead | G A Aadish | |
| Course faculty | | |

---

## Appendix A: Detailed Test Cases

### A.1 SF-1 Donor Registration and Eligibility Screening

Covers REQ-1 to REQ-8.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-01 | Donor Registration | Verify the registration form accepts a fully valid donor record and persists it | Donor model and form available | 1: Instantiate DonorRegistrationForm with a complete valid payload<br>2: Call is_valid()<br>3: Call save()<br>4: Query the donor table | Name: Ravi Kumar, DOB: 12-04-1998, Gender: Male, Group: O+, Mobile: 9880011223, Email: ravi.k@example.com, City: Bengaluru, PIN: 560085, Weight: 68 | is_valid() returns True and exactly one donor row is created with the submitted values | Not executed | Pending |
| UT-02 | Donor Identifier | Verify the donor identifier generator produces a unique DNR + 8 digit value | Identifier generator available | 1: Call generate_donor_id() 1000 times<br>2: Collect results into a set<br>3: Assert format and uniqueness | 1000 successive invocations | All 1000 values match the pattern DNR followed by 8 digits, and the set contains 1000 distinct values | Not executed | Pending |
| UT-03 | Uniqueness Validator | Verify registration is rejected when the mobile number already exists | A donor with mobile 9880011223 exists | 1: Submit a registration with the same mobile number<br>2: Inspect form errors<br>3: Count donor rows | Mobile: 9880011223, Email: different@example.com | Validation fails with "This mobile number is already registered. Please sign in or reset your password." and the donor row count is unchanged | Not executed | Pending |
| UT-04 | Age Rule | Verify the age boundary rule at, inside and outside the permitted range | Age validator available | 1: Call validate_age with each date of birth<br>2: Record the outcome for each | DOB giving ages 17, 18, 40, 65 and 66 on the test date | Ages 17 and 66 rejected with "Donors must be between 18 and 65 years of age." Ages 18, 40 and 65 accepted | Not executed | Pending |
| UT-05 | Deferral Rules | Verify a declared permanent deferral condition marks the donor permanently ineligible | Deferral condition list configured | 1: Register a donor declaring a permanent deferral condition<br>2: Read the eligibility status field | Declared condition: HIV positive | Eligibility status is set to Permanently Deferred and no review date is set | Not executed | Pending |
| UT-06 | Eligibility Engine | Verify a donor meeting every criterion is reported Eligible | Eligibility service available | 1: Build a donor meeting all five criteria<br>2: Call evaluate_eligibility()<br>3: Read status and failure list | Age 30, weight 62 kg, Hb 13.8, BP 118/78, last donation 120 days ago | Status is Eligible and the failure list is empty | Not executed | Pending |
| UT-07 | Eligibility Engine | Verify every failing criterion is reported, not only the first | Eligibility service available | 1: Build a donor failing three criteria simultaneously<br>2: Call evaluate_eligibility()<br>3: Read the failure list | Weight 45 kg, Hb 10.2, last donation 30 days ago | Status is Temporarily Deferred and the failure list contains all three reasons: underweight, low haemoglobin and interval not elapsed | Not executed | Pending |
| UT-08 | Collection Guard | Verify a collection cannot be recorded against a deferred donor | A donor with status Temporarily Deferred exists | 1: Call record_collection() for that donor<br>2: Inspect the raised exception<br>3: Count unit rows | Donor DNR10000042, status Temporarily Deferred, reason Low haemoglobin | The call is refused, the deferral reason and review date are returned, and no blood unit row is created | Not executed | Pending |
| UT-09 | Interval Calculator | Verify the next eligible date is last donation date plus the configured interval | Interval configured at 90 days | 1: Set last donation date<br>2: Call next_eligible_date()<br>3: Compare with expected | Last donation 01-06-2026, interval 90 days | Returns 30-08-2026 | Not executed | Pending |
| IT-01 | Registration to Database | Verify end-to-end registration writes donor, consent and audit rows in one transaction | Empty donor table, database reachable | 1: POST a valid registration to the registration endpoint<br>2: Query donor, consent and audit tables<br>3: Repeat with a duplicate mobile and re-query | Valid payload, then a duplicate-mobile payload | First POST creates one donor row, one consent row and one audit row. Second POST creates no rows in any of the three tables | Not executed | Pending |
| IT-02 | Screening to Eligibility | Verify screening values entered by staff update donor eligibility in the database | Staff signed in, donor DNR10000001 exists and is Eligible | 1: Open the screening screen for the donor<br>2: Enter haemoglobin 11.0<br>3: Save<br>4: Reload the donor record | Haemoglobin: 11.0 g/dL | Donor status changes to Temporarily Deferred, reason is Low haemoglobin, and a review date is set | Not executed | Pending |
| IT-03 | Eligibility to Collection | Verify the collection screen refuses to open for a deferred donor | Donor DNR10000042 is Temporarily Deferred | 1: Search the donor on the staff console<br>2: Attempt to start a collection | Donor DNR10000042 | The Start Collection control is disabled and the deferral reason is displayed beside it | Not executed | Pending |
| IT-04 | Deferral Expiry | Verify a temporary deferral clears automatically once the review date has passed | Donor deferred with a review date of yesterday | 1: Run the nightly eligibility evaluation job<br>2: Reload the donor record | Review date set to the previous day | Donor status returns to Eligible and the deferral reason is cleared | Not executed | Pending |
| ST-01 | Donor Portal | Verify a member of the public can self-register and receives a donor identifier | Chrome available, application reachable | 1: Navigate to the application URL<br>2: Click Register as Donor<br>3: Complete every mandatory field<br>4: Tick the consent checkbox<br>5: Click Submit | Name: Meena Rao, DOB: 03-09-2000, Group: B+, Mobile: 9845567788, Email: meena.rao@example.com, PIN: 560076, Weight: 55 | A confirmation screen displays "Registration successful" and a donor identifier in DNR + 8 digit format. A welcome email is received | Not executed | Pending |
| ST-02 | Donor Portal | Verify invalid registration inputs are rejected with field-level messages | Application reachable | 1: Navigate to the registration screen<br>2: Enter a date of birth giving age 16<br>3: Enter an already registered mobile number<br>4: Enter a 5-digit PIN code<br>5: Click Submit | DOB: 01-01-2010, Mobile: 9880011223, PIN: 56008 | Submission is refused. Three errors appear adjacent to their fields, each naming the field and the corrective action, and a summary banner lists all three. No account is created | Not executed | Pending |
| ST-03 | Staff Console | Verify screening a donor who fails multiple criteria shows every reason | Staff signed in as staff01 | 1: Search donor DNR10000003<br>2: Open Screening<br>3: Enter weight 46 and haemoglobin 10.5<br>4: Click Evaluate | Weight: 46 kg, Haemoglobin: 10.5 g/dL | The screen shows Temporarily Deferred and lists both the underweight and low haemoglobin reasons, with a review date | Not executed | Pending |
| ST-04 | Donor Portal | Verify the donor dashboard shows the correct next eligible date after a donation | Donor DNR10000001 donated 10 days ago | 1: Sign in as the donor<br>2: Open the dashboard<br>3: Read the eligibility panel | Donor DNR10000001 | The dashboard shows Not Eligible, the next eligible date as the donation date plus 90 days, and the number of days remaining | Not executed | Pending |

### A.2 SF-2 Blood Donation and Collection Management

Covers REQ-9 to REQ-15.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-10 | Collection Entry | Verify a valid collection creates a unit and updates the donor's last donation date | Eligible donor exists | 1: Call record_collection() with a valid payload<br>2: Read the created unit<br>3: Read the donor record | Donor DNR10000001, volume 450 ml, bag lot BG-2026-0417, site Centre | One unit row is created and the donor's last donation date is set to the collection date | Not executed | Pending |
| UT-11 | Unit Identifier | Verify the unit identifier generator produces a unique BU + 10 digit value | Identifier generator available | 1: Call generate_unit_id() 1000 times<br>2: Assert format and uniqueness | 1000 successive invocations | All values match BU followed by 10 digits and all 1000 are distinct | Not executed | Pending |
| UT-12 | Unit State Machine | Verify a newly created unit is Quarantined and cannot be issued | Unit state machine available | 1: Create a unit<br>2: Read its status<br>3: Attempt to transition it directly to Issued | Newly created unit | Initial status is Quarantined and the direct transition to Issued is refused as an invalid transition | Not executed | Pending |
| UT-13 | Screening Panel | Verify a unit with an incomplete panel cannot be released | Unit in Quarantined status | 1: Record four of the five mandatory tests as Non-Reactive<br>2: Call release_unit()<br>3: Read the unit status | HIV, HBV, HCV and Syphilis recorded, Malaria omitted | Release is refused with a message naming Malaria as the missing test, and the unit remains Quarantined | Not executed | Pending |
| UT-14 | Release Rule | Verify a unit with a complete non-reactive panel moves to Available | Unit in Quarantined status | 1: Record all five mandatory tests as Non-Reactive<br>2: Call release_unit()<br>3: Read the unit status | All five tests Non-Reactive | The unit status becomes Available | Not executed | Pending |
| UT-15 | Reactive Handling | Verify a single reactive result discards the unit permanently | Unit in Quarantined status | 1: Record four tests Non-Reactive and HCV Reactive<br>2: Call release_unit()<br>3: Attempt to move the unit back to Available | HCV: Reactive, remaining four Non-Reactive | The unit becomes Discarded with reason Reactive Screening, an administrator alert is queued, and the attempt to restore it to Available is refused | Not executed | Pending |
| UT-16 | Component Separation | Verify separation creates linked child units with correct per-component expiry | An Available whole blood unit collected on 01-09-2026 exists | 1: Call separate_components() for PRBC, FFP and Platelets<br>2: Read the three child units<br>3: Read the parent unit | Parent BU1000000001, collection date 01-09-2026 | Three child units are created, each linked to the parent and the donor, with expiry dates of 13-10-2026 for PRBC, 01-09-2027 for FFP and 06-09-2026 for Platelets. The parent unit is closed and cannot be issued | Not executed | Pending |
| IT-05 | Collection to Inventory | Verify a collection recorded on screen appears in the inventory console | Staff signed in, eligible donor available | 1: Record a collection through the staff console<br>2: Open the inventory console<br>3: Filter on Quarantined | Donor DNR10000005, volume 450 ml | The new unit appears in the Quarantined list with the correct group, volume and expiry date, and is absent from the Available count | Not executed | Pending |
| IT-06 | Quarantine Enforcement | Verify a Quarantined unit is invisible to availability search and allocation | A Quarantined unit of group A+ exists | 1: Run an availability search for A+ whole blood<br>2: Attempt to allocate the Quarantined unit to a request | Group A+, component Whole Blood | The Quarantined unit is not counted in the search result and the allocation attempt is refused | Not executed | Pending |
| IT-07 | Screening to Inventory | Verify entering a full non-reactive panel moves the unit into Available stock | A Quarantined unit exists, staff signed in | 1: Open Test Result Entry for the unit<br>2: Record all five tests Non-Reactive<br>3: Save<br>4: Refresh the inventory console | All five tests Non-Reactive | The unit moves to Available and the Available count for its group and component increases by one | Not executed | Pending |
| IT-08 | Reactive Alert | Verify a reactive result discards the unit and notifies only the administrator | A Quarantined unit exists, staff and admin accounts available | 1: Record HIV as Reactive and save<br>2: Check the unit status<br>3: Check the administrator notification inbox<br>4: Sign in as a hospital user and search availability | HIV: Reactive | The unit is Discarded, the administrator receives an alert naming the donor, the hospital availability search does not reflect the unit, and no hospital user can see the donor identity | Not executed | Pending |
| IT-09 | Separation Persistence | Verify component separation persists parent and child linkage across a reload | An Available whole blood unit exists | 1: Separate the unit into three components through the staff console<br>2: Reload the application<br>3: Open each child unit and read its parent link | Parent unit BU1000000007 | Each child unit displays the correct parent identifier and the same donor identifier as the parent, and the parent shows all three children | Not executed | Pending |
| ST-05 | Staff Console | Verify staff can record a complete collection end to end | Staff signed in, eligible donor present | 1: Search donor DNR10000001<br>2: Click Start Collection<br>3: Enter volume, bag lot and site<br>4: Click Save<br>5: Read the confirmation | Volume: 450 ml, Bag lot: BG-2026-0417, Site: Centre | A confirmation displays the new unit identifier in BU + 10 digit format, the unit status as Quarantined, and the computed expiry date | Not executed | Pending |
| ST-06 | Staff Console | Verify an incompletely tested unit cannot be released | A Quarantined unit exists, staff signed in | 1: Open Test Result Entry for the unit<br>2: Record four tests, leave Malaria blank<br>3: Click Release to Inventory | Four results entered, Malaria blank | The release is refused with a message naming the missing test. The unit remains Quarantined and does not appear in Available stock | Not executed | Pending |
| ST-07 | Staff Console | Verify a reactive screening result removes the unit from circulation permanently | A Quarantined unit exists, staff signed in | 1: Record Hepatitis B as Reactive<br>2: Save<br>3: Attempt to allocate the unit to a request<br>4: Sign in as admin and check alerts | Hepatitis B: Reactive | The unit shows Discarded with reason Reactive Screening, allocation is impossible because the unit is not offered, and the administrator sees a confidential alert | Not executed | Pending |
| ST-08 | Staff Console | Verify component separation through the interface produces three usable child units | An Available whole blood unit exists, staff signed in | 1: Open the unit<br>2: Click Separate Components<br>3: Select PRBC, FFP and Platelets<br>4: Confirm<br>5: Open the inventory console | Parent unit collected 01-09-2026 | Three child units appear as Available with distinct identifiers and distinct expiry dates, and the parent no longer appears in issuable stock | Not executed | Pending |

### A.3 SF-3 Blood Inventory and Stock Management

Covers REQ-16 to REQ-23.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-17 | BloodUnit Entity | Verify the unit entity persists every required attribute | Unit model available | 1: Create a unit populating all mandatory attributes<br>2: Reload it from the database<br>3: Compare each field | Group O+, PRBC, 350 ml, location FRIDGE-A2, lot BG-2026-0418 | Every attribute in the Appendix B.2 layout is stored and returned unchanged, and status defaults to Quarantined | Not executed | Pending |
| UT-18 | Stock Aggregation | Verify stock counts group correctly and exclude non-issuable statuses | Units exist in mixed statuses | 1: Seed 5 Available, 2 Reserved, 3 Quarantined and 1 Expired unit of O+ PRBC<br>2: Call get_stock_summary()<br>3: Read the O+ PRBC row | 11 units of O+ PRBC across four statuses | Available count is 5, Reserved is 2, Quarantined is 3, Expired is 1, and the issuable count is 5 | Not executed | Pending |
| UT-19 | Inventory Query | Verify combined filters return only the intersecting set | Mixed inventory seeded | 1: Call the inventory query with group, component, location and status filters together<br>2: Inspect the returned set | Group A+, component FFP, location FREEZER-B1, status Available | Only units matching all four filters are returned. Units matching three of four are excluded | Not executed | Pending |
| UT-20 | Expiry Job | Verify units past their expiry date transition to Expired | Units seeded with past, today and future expiry | 1: Run the expiry evaluation job<br>2: Read the status of each seeded unit | Expiry dates of yesterday, today and tomorrow | The unit expiring yesterday becomes Expired. The units expiring today and tomorrow remain Available | Not executed | Pending |
| UT-21 | Near-Expiry Alert | Verify the near-expiry window flags the correct units | Near-expiry window configured at 7 days | 1: Seed units expiring in 3, 7, 8 and 40 days<br>2: Call get_near_expiry_units()<br>3: Inspect the result | Expiry in 3, 7, 8 and 40 days | Units expiring in 3 and 7 days are returned. Units expiring in 8 and 40 days are not | Not executed | Pending |
| UT-22 | Transfer | Verify a location transfer changes location but not status | An Available unit in FRIDGE-A1 exists | 1: Call transfer_unit() to FRIDGE-B2<br>2: Read the unit location and status<br>3: Read the audit record | Source FRIDGE-A1, destination FRIDGE-B2 | Location becomes FRIDGE-B2, status remains Available, and an audit record captures both locations, the timestamp and the acting user | Not executed | Pending |
| UT-23 | Discard Workflow | Verify a discard requires a reason and refuses an Issued unit | One Available and one Issued unit exist | 1: Call discard_unit() on the Available unit with no reason<br>2: Retry with reason Breakage<br>3: Call discard_unit() on the Issued unit with a reason | Reasons: none, then Breakage | The first call is refused for a missing reason. The second succeeds and sets status Discarded. The third is refused because an Issued unit cannot be discarded | Not executed | Pending |
| UT-24 | Audit Writer | Verify every status transition writes an immutable audit record | Audit writer available | 1: Move a unit through Quarantined to Available to Reserved to Issued<br>2: Read the audit records for the unit<br>3: Attempt to update and then delete an audit record | One unit, three transitions | Three audit records exist carrying previous status, new status, timestamp and acting user. Both the update and the delete attempts are refused | Not executed | Pending |
| IT-10 | Inventory Console | Verify a committed inventory change is reflected on the console within 5 seconds | Staff signed in, inventory console open | 1: Note the Available count for B+ PRBC<br>2: In a second session release a B+ PRBC unit to Available<br>3: Refresh the console and time the update | One B+ PRBC unit released | The Available count for B+ PRBC increases by one and the change is visible within 5 seconds, satisfying NFR-P5 | Not executed | Pending |
| IT-11 | Expiry and Digest | Verify the expiry job updates stock and produces the near-expiry digest | Units seeded across expiry boundaries, staff email configured | 1: Run the nightly expiry job<br>2: Refresh the inventory console<br>3: Check the staff mailbox | Units expiring yesterday, in 5 days and in 30 days | Expired units are removed from Available counts, near-expiry units are flagged on the console, and a single digest email listing the near-expiry units is received | Not executed | Pending |
| IT-12 | Transfer and Discard Audit | Verify transfer and discard actions performed on screen persist audit trails | Staff signed in, an Available unit exists | 1: Transfer the unit to another location<br>2: Discard the unit with reason Temperature Excursion and confirm<br>3: Open the unit history tab | Destination FREEZER-C1, reason Temperature Excursion | The history tab lists both events in order with timestamps, the acting user and the discard reason | Not executed | Pending |
| IT-13 | Audit Immutability | Verify audit records survive an attempt to alter them through the application | Audit records exist | 1: Attempt to edit an audit record through every available application route<br>2: Attempt to delete it<br>3: Re-read the record | An existing audit record for a unit transition | No application route permits edit or delete, and the record is returned unchanged | Not executed | Pending |
| ST-09 | Inventory Console | Verify the console displays accurate stock grouped by group and component | Staff signed in, seeded inventory | 1: Open the inventory console<br>2: Read the summary grid<br>3: Cross-check three cells against a direct database count | Seeded inventory of 120 units | The grid shows counts by blood group and component type, and all three cross-checked cells match the database exactly | Not executed | Pending |
| ST-10 | Inventory Console | Verify filtering and the exclusion of expired stock from issuable results | Staff signed in, expired and valid units present | 1: Filter on group AB-, component Platelets, status Available<br>2: Note the result set<br>3: Confirm no expired unit appears | Group AB-, component Platelets | Only Available, unexpired AB- Platelet units are listed. No Expired unit appears anywhere in the result | Not executed | Pending |
| ST-11 | Inventory Console | Verify near-expiry flagging and location transfer through the interface | Staff signed in, a unit expiring in 4 days exists | 1: Open the console and locate the unit<br>2: Confirm it carries the near-expiry flag<br>3: Transfer it to FRIDGE-D1<br>4: Re-open the unit | Unit expiring in 4 days | The unit is visibly flagged as near expiry, the transfer succeeds, and after transfer the location is FRIDGE-D1 with the status and flag unchanged | Not executed | Pending |
| ST-12 | Inventory Console | Verify the discard workflow enforces confirmation and audit | Staff signed in, an Available unit exists | 1: Click Discard on the unit<br>2: Attempt to confirm without selecting a reason<br>3: Select reason Breakage<br>4: Read the confirmation dialog text<br>5: Confirm<br>6: Open the audit log | Reason: Breakage | The confirmation is blocked until a reason is chosen. The dialog names the specific unit identifier. After confirmation the unit is Discarded and the audit log records the user, timestamp and reason | Not executed | Pending |

### A.4 SF-4 Hospital Blood Request and Issue

Covers REQ-24 to REQ-31.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-25 | Request Creation | Verify a valid request is created with a unique identifier | Request service available | 1: Call create_request() with a valid payload<br>2: Read the created request<br>3: Assert the identifier format | Hospital HOSP000001, group O-, PRBC, quantity 3, Emergency, required by tomorrow 09:00, patient ref PT-9931 | A request is created in Pending status with an identifier matching REQ followed by 8 digits | Not executed | Pending |
| UT-26 | Request Validator | Verify invalid quantity and past required-by date are rejected | Request validator available | 1: Submit quantity 0<br>2: Submit quantity -2<br>3: Submit quantity 2.5<br>4: Submit a required-by date of yesterday | Quantities 0, -2 and 2.5, required-by yesterday | All four submissions are rejected. Each error message names the offending field and states the correction required | Not executed | Pending |
| UT-27 | Queue Ordering | Verify the queue orders Emergency first then by required-by ascending | Requests seeded with mixed urgency | 1: Seed a Routine request due in 1 hour, an Urgent due in 6 hours and two Emergency requests due in 4 and 8 hours<br>2: Call get_request_queue()<br>3: Read the order | Four requests of mixed urgency and due time | Order is the Emergency due in 4 hours, the Emergency due in 8 hours, then the Urgent, then the Routine. Urgency dominates the due time | Not executed | Pending |
| UT-28 | Approval Workflow | Verify rejection requires a reason and records it | A Pending request exists | 1: Call reject_request() with no reason<br>2: Retry with reason Insufficient Stock<br>3: Read the request | Reasons: none, then Insufficient Stock | The first call is refused for a missing reason. The second sets status Rejected and stores the reason for communication to the hospital | Not executed | Pending |
| UT-29 | Allocation Rules | Verify allocation refuses a blood group mismatch | An Approved A+ request and an O+ Available unit exist | 1: Call allocate_unit() pairing the O+ unit with the A+ request<br>2: Inspect the refusal<br>3: Read the unit status | Request group A+, unit group O+ | Allocation is refused with a group mismatch message, satisfying NFR-S3, and the unit remains Available | Not executed | Pending |
| UT-30 | Allocation Rules | Verify allocation refuses Quarantined, Expired and already Reserved units | An Approved request and units in three unsuitable states exist | 1: Attempt to allocate a Quarantined unit<br>2: Attempt to allocate an Expired unit<br>3: Attempt to allocate a unit already Reserved to another request | Three units of the correct group in unsuitable states | All three allocation attempts are refused, each naming the disqualifying condition. No unit changes status | Not executed | Pending |
| UT-31 | Issue Recording | Verify reservation then issue records complete issue detail | An Approved request and a matching Available unit exist | 1: Allocate the unit and read its status<br>2: Confirm the issue<br>3: Read the unit status and the issue record | Request REQ10000004, unit BU1000000031 | Status is Reserved after allocation and Issued after confirmation. The issue record carries the request identifier, unit identifier, issuing staff member, receiving hospital and timestamp | Not executed | Pending |
| UT-32 | Fulfilment State | Verify Fulfilled and Partially Fulfilled are set correctly with shortfall | Approved requests for quantity 3 exist | 1: Issue 3 units against the first request and read its status<br>2: Issue 1 unit against the second request and read its status and shortfall | Quantity requested 3, issued 3 then 1 | The first request becomes Fulfilled. The second becomes Partially Fulfilled with a recorded shortfall of 2 and remains open | Not executed | Pending |
| UT-33 | Cancellation | Verify cancellation releases reservations and is barred after issue | One Approved request with reserved units and one with issued units exist | 1: Cancel the request with reserved units and read the unit statuses<br>2: Attempt to cancel the request with issued units | Two requests in differing states | The first cancellation succeeds and every reserved unit returns to Available. The second is refused because units have been issued | Not executed | Pending |
| IT-14 | Request to Queue | Verify a request raised by a hospital appears in the staff queue | Hospital user hosp01 and staff01 both available | 1: Sign in as hosp01 and raise an Emergency request<br>2: Sign in as staff01 in a second session<br>3: Open the request queue | Group O-, PRBC, quantity 2, Emergency | The request appears in the staff queue at the head of the list, visually distinguished as Emergency, carrying the hospital name and required-by time | Not executed | Pending |
| IT-15 | Approval and Notification | Verify approval and rejection reach the requesting hospital | A Pending request from hosp01 exists | 1: Approve a request as staff and check the hospital tracker<br>2: Reject a second request with reason Insufficient Stock and check the tracker and mailbox | Two Pending requests | The approved request shows Approved on the hospital tracker. The rejected one shows Rejected with the reason visible, and a notification stating the reason is received | Not executed | Pending |
| IT-16 | Allocation to Inventory | Verify allocation and issue update inventory counts atomically | An Approved request and 5 Available matching units exist | 1: Note the Available count<br>2: Allocate 2 units<br>3: Re-read the counts<br>4: Confirm the issue<br>5: Re-read the counts | 5 Available units, allocate 2 | After allocation Available falls by 2 and Reserved rises by 2. After issue Reserved falls by 2 and Issued rises by 2. The total unit count never changes | Not executed | Pending |
| IT-17 | Partial Fulfilment and Cancellation | Verify partial fulfilment keeps a request open and cancellation restores stock | An Approved request for 4 units with only 2 Available exists | 1: Issue the 2 available units<br>2: Read the request status and shortfall<br>3: Cancel the remainder<br>4: Read the inventory | Requested 4, available 2 | The request shows Partially Fulfilled with a shortfall of 2 and remains open. Cancelling the remainder closes it without altering the 2 already Issued units | Not executed | Pending |
| ST-13 | Hospital Portal | Verify a hospital user can raise a request end to end | Signed in as hosp01 | 1: Open Raise Request<br>2: Select group O-, component PRBC, quantity 2<br>3: Set urgency Emergency and required-by tomorrow 09:00<br>4: Enter patient reference PT-9931<br>5: Submit | Group O-, PRBC, quantity 2, Emergency, PT-9931 | A confirmation displays a request identifier in REQ + 8 digit format and status Pending. The request appears in the hospital's own tracker | Not executed | Pending |
| ST-14 | Staff Console | Verify the staff queue prioritises Emergency requests and supports rejection | Multiple Pending requests of mixed urgency exist, staff signed in | 1: Open the request queue<br>2: Verify the ordering<br>3: Reject the lowest priority request with reason Insufficient Stock<br>4: Sign in as the requesting hospital and check | Four requests of mixed urgency | Emergency requests appear first and are visually distinguished. The rejection succeeds and the hospital sees Rejected with the stated reason | Not executed | Pending |
| ST-15 | Staff Console | Verify units are issued only when group, status and expiry all match | An Approved A+ request exists with mixed candidate units | 1: Open the issue screen for the request<br>2: Inspect the offered unit list<br>3: Issue two offered units<br>4: Check inventory and the hospital tracker | A+ request, candidate units of A+, O+, expired A+ and Quarantined A+ | Only Available, unexpired A+ units are offered. The O+, expired and Quarantined units are not selectable. After issue the units show Issued and the hospital tracker updates | Not executed | Pending |
| ST-16 | Hospital Portal | Verify partial fulfilment display and cancellation behaviour for a hospital user | A Partially Fulfilled request and a Pending request exist for hosp01 | 1: Open the tracker and read the partial request<br>2: Cancel the Pending request<br>3: Attempt to cancel the partially fulfilled request | Two requests in differing states | The partial request shows the issued quantity and the outstanding shortfall. The Pending request cancels successfully. The partially fulfilled request cannot be cancelled because units have been issued | Not executed | Pending |

### A.5 SF-5 Donation Camp and Drive Management

Covers REQ-32 to REQ-37.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-34 | Camp Creation | Verify a valid camp is created in Scheduled status | Camp service available | 1: Call create_camp() with a valid payload<br>2: Read the created camp<br>3: Assert the status | Name: PESU Blood Drive, venue: PESU RR Campus, date: 15-10-2026, 09:00 to 16:00, organiser: NSS PESU, target 150 | The camp is created in Scheduled status with all supplied attributes stored and a camp identifier assigned | Not executed | Pending |
| UT-35 | Camp Validator | Verify a past date and an invalid time range are rejected | Camp validator available | 1: Submit a camp dated yesterday<br>2: Submit a camp with end time earlier than start time<br>3: Submit a camp with end time equal to start time | Date yesterday; 16:00 to 09:00; 09:00 to 09:00 | All three are rejected. The date error names the camp date field and the two time errors name the end time field | Not executed | Pending |
| UT-36 | Camp Listing | Verify only Scheduled camps are published, ordered by date ascending | Camps seeded in three statuses | 1: Seed Scheduled camps on 20-10 and 05-10, one Completed and one Cancelled camp<br>2: Call get_published_camps()<br>3: Read the result | Four camps across three statuses | Only the two Scheduled camps are returned, ordered 05-10 then 20-10. The Completed and Cancelled camps are excluded | Not executed | Pending |
| UT-37 | Enrolment Eligibility | Verify enrolment is refused when the donor is not eligible on the camp date | A donor whose next eligible date is after the camp date exists | 1: Call enrol_donor() for that donor and camp<br>2: Inspect the refusal message<br>3: Repeat for a donor eligible before the camp date | Camp date 15-10-2026, donor next eligible 01-11-2026, second donor next eligible 01-10-2026 | The first enrolment is refused and the message states the donor's next eligible date of 01-11-2026. The second enrolment succeeds | Not executed | Pending |
| UT-38 | Camp Collection Link | Verify a unit collected at a camp records the camp as its collection site | A Scheduled camp and an eligible donor exist | 1: Record a collection with the camp as the site<br>2: Read the created unit<br>3: Query units by camp | Camp CMP0000002 | The unit's collection site is the camp identifier, and the unit is returned when querying units by that camp | Not executed | Pending |
| UT-39 | Camp Closure | Verify closing a camp computes actuals and blocks further collections | A Scheduled camp with 87 collections exists | 1: Call close_camp()<br>2: Read the camp status and units collected<br>3: Attempt to record a further collection against the camp | Camp with target 150 and 87 units collected | The camp becomes Completed with units collected 87 against a target of 150. The further collection is refused because the camp is Completed | Not executed | Pending |
| IT-18 | Camp Creation to Listing | Verify a camp created by staff appears on the donor portal listing | Staff and donor accounts available | 1: Create a camp as staff<br>2: Sign in as a donor in a second session<br>3: Open the camp listing | Camp dated 15-10-2026 | The new camp appears in the donor's camp listing with its name, venue, date and timings | Not executed | Pending |
| IT-19 | Enrolment Flow | Verify eligible and ineligible donors receive the correct enrolment outcome | Two donors of differing eligibility, one Scheduled camp | 1: Sign in as the eligible donor and enrol<br>2: Check the confirmation and mailbox<br>3: Sign in as the ineligible donor and attempt to enrol | Camp date 15-10-2026 | The eligible donor is enrolled and receives a confirmation notification. The ineligible donor is refused and shown their next eligible date. The camp enrolment count rises by exactly one | Not executed | Pending |
| IT-20 | Camp Collection to Inventory | Verify camp collections reconcile into central inventory and closure locks the camp | An active camp with enrolled donors, staff signed in | 1: Record three collections against the camp<br>2: Open the inventory console<br>3: Close the camp<br>4: Attempt a fourth collection against the camp | Three collections at camp CMP0000002 | All three units appear in central inventory as Quarantined with the camp as collection site. After closure the camp reports 3 units and the fourth collection is refused | Not executed | Pending |
| ST-17 | Camp Management | Verify staff can schedule a camp and invalid schedules are refused | Staff signed in | 1: Open Camp Management and click New Camp<br>2: Enter a date in the past and submit<br>3: Correct the date but set end time before start time and submit<br>4: Correct both and submit | Past date, then 16:00 to 09:00, then 15-10-2026 09:00 to 16:00 | The first two submissions are refused with field-level messages. The third succeeds and the camp appears in the camp list as Scheduled | Not executed | Pending |
| ST-18 | Donor Portal | Verify a donor can browse and enrol in an upcoming camp | Donor signed in, a Scheduled camp exists | 1: Open Upcoming Camps<br>2: Confirm camps are ordered by date<br>3: Click Enrol on the nearest camp<br>4: Read the confirmation<br>5: Return to the listing | Camp on 15-10-2026 | Camps are listed in ascending date order. Enrolment succeeds with an on-screen confirmation, and the camp then shows the donor as enrolled | Not executed | Pending |
| ST-19 | Camp Management | Verify camp performance is reported correctly on closure | An active camp with recorded collections, staff signed in | 1: Record collections at the camp<br>2: Click Close Camp and confirm<br>3: Read the camp summary<br>4: Open the Camp Performance Report | Target 150, 87 units collected | The camp shows Completed, 87 units collected against a target of 150, and the report shows an achievement of 58 percent | Not executed | Pending |

### A.6 SF-6 Search, Notification and Reporting

Covers REQ-38 to REQ-46.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| UT-40 | Availability Search | Verify the search returns counts only and never donor data | Search service available, inventory seeded | 1: Call availability_search() as a hospital user role<br>2: Inspect every field of the response<br>3: Repeat as a staff role | Group A+, component PRBC | The hospital response carries counts by group and component and contains no unit identifier, donor identifier or donor personal field. The staff response may carry unit identifiers | Not executed | Pending |
| UT-41 | Dispatcher | Verify SMS failure retries three times then falls back to email | Notification dispatcher available, SMS gateway stubbed to fail | 1: Dispatch a notification with the SMS gateway failing<br>2: Count gateway invocations<br>3: Read the notification record and the email queue | One notification, SMS gateway always failing | The gateway is invoked three times at increasing intervals. The notification record shows the SMS failure and an email is queued as fallback | Not executed | Pending |
| UT-42 | Reminder Jobs | Verify eligibility and camp reminders fire at the right time | Donors seeded across reminder boundaries | 1: Seed a donor becoming eligible today and one eligible in 5 days<br>2: Seed enrolments for camps in 24 hours and in 5 days<br>3: Run the reminder job<br>4: Inspect the notification queue | Two donors, two camp enrolments | An eligibility reminder is queued only for the donor eligible today. A camp reminder is queued only for the camp in 24 hours | Not executed | Pending |
| UT-43 | Shortage Appeal | Verify the shortage appeal fires below threshold and suppresses repeats within 30 days | Threshold for O- configured at 10 units | 1: Reduce O- Available stock to 8 and run the appeal job<br>2: Run the job again the next day<br>3: Advance the clock 31 days and run again | O- stock 8, threshold 10 | The first run queues an appeal to eligible O- donors. The second run queues nothing because of the 30-day suppression. The third run queues an appeal again | Not executed | Pending |
| UT-44 | Report Engine | Verify each of the six reports is generated over the selected date range | Report engine available, data seeded across dates | 1: Generate each of the six reports for 01-09-2026 to 30-09-2026<br>2: Inspect the columns of each<br>3: Confirm no record outside the range is included | Date range 01-09-2026 to 30-09-2026 | All six reports generate. Each carries exactly the columns specified in Appendix B.7, and no record dated outside the range appears in any report | Not executed | Pending |
| UT-45 | Export | Verify PDF and CSV export carry the required provenance header | A generated report available | 1: Export the Inventory Status Report as PDF<br>2: Export the same report as CSV<br>3: Inspect the header of each artefact | Inventory Status Report | Both artefacts carry the report name, the selected date range, the generating user and the generation timestamp. The CSV conforms to RFC 4180 | Not executed | Pending |
| UT-46 | Data Scoping | Verify report data is scoped to the requesting user's authorisation | Requests exist for two different hospitals | 1: Generate the Request and Issue Report as hosp01<br>2: Generate the same report as hosp02<br>3: Generate it as staff01 | Requests belonging to Apollo and to Fortis | hosp01 sees only Apollo records, hosp02 sees only Fortis records, and staff01 sees both. No hospital user sees another hospital's data | Not executed | Pending |
| UT-47 | User Administration | Verify accounts are deactivated rather than deleted and carry exactly one role | Admin service available | 1: Create a user and assign the Staff role<br>2: Attempt to assign a second role<br>3: Deactivate the user<br>4: Query the user table | New user account | The second role assignment is refused. Deactivation sets the account inactive but the row remains present, satisfying CON-6 | Not executed | Pending |
| UT-48 | Configuration Store | Verify configuration changes take effect without a restart | Configuration service available | 1: Read the current minimum donation interval<br>2: Change it to 120 days through the configuration service<br>3: Evaluate a donor whose last donation was 100 days ago<br>4: Attempt to set the interval to 60 days | Interval changed from 90 to 120, then attempted 60 | The donor is reported ineligible under the new 120-day interval with no restart. The attempt to set 60 days is refused because BR-2 forbids a value below 90 | Not executed | Pending |
| IT-21 | Search Isolation | Verify the availability search exposes no donor data through any interface | Hospital user signed in, inventory seeded | 1: Run an availability search on the hospital portal<br>2: Inspect the rendered page<br>3: Inspect the underlying network response payload | Group A+, component PRBC | Neither the rendered page nor the network payload contains a unit identifier, a donor identifier or any donor personal field. Only counts are present | Not executed | Pending |
| IT-22 | Notification Delivery | Verify notifications are dispatched asynchronously without blocking the transaction | Gateways configured, notification triggers available | 1: Trigger a notification-producing transaction with the SMS gateway artificially delayed<br>2: Time the user-visible transaction<br>3: Confirm the transaction committed<br>4: Check the notification queue | SMS gateway delayed by 20 seconds | The user transaction completes and commits without waiting for the gateway. The notification is enqueued within 1 second, satisfying NFR-P6 | Not executed | Pending |
| IT-23 | Shortage Appeal Delivery | Verify a shortage appeal reaches only eligible donors of the affected group | Donors of several groups and eligibility states seeded | 1: Drive O- stock below threshold<br>2: Run the appeal job<br>3: Inspect the recipient list | O- stock below threshold | Only donors of group O- whose status is Eligible receive the appeal. Deferred O- donors and donors of other groups receive nothing | Not executed | Pending |
| IT-24 | Report Generation and Export | Verify reports generated on screen export correctly as PDF and CSV | Staff signed in, data seeded | 1: Generate the Collection Report for a 30-day range<br>2: Compare the on-screen row count against a direct database count<br>3: Export as PDF and open it<br>4: Export as CSV and open it in a spreadsheet | 30-day range | The on-screen count matches the database. The PDF opens and is legible. The CSV opens with correct column alignment and no malformed rows | Not executed | Pending |
| IT-25 | Cross-Role Authorisation | Verify a user cannot reach another role's functions by direct URL | Accounts for all four roles available | 1: Sign in as a donor and request a staff-only URL directly<br>2: Sign in as a hospital user and request an admin-only URL<br>3: Sign in as staff and request an admin-only URL | Direct URL entry for each case | All three requests are refused with an authorisation error. No protected data is returned in any response body, satisfying NFR-SEC5 | Not executed | Pending |
| IT-26 | Administration and Configuration | Verify administrator changes to users and configuration take effect immediately | Admin signed in | 1: Create a staff user and sign in as that user in a second session<br>2: As admin, change the near-expiry window from 7 to 14 days<br>3: Refresh the staff inventory console | Near-expiry window 7 then 14 days | The new user signs in successfully with staff permissions. After the configuration change the console flags units expiring within 14 days, with no restart | Not executed | Pending |
| ST-20 | Hospital Portal | Verify a hospital user can check availability before raising a request | Signed in as hosp01, inventory seeded | 1: Open Check Availability<br>2: Select group B+ and component PRBC<br>3: Read the result | Group B+, PRBC | The available quantity is displayed. No unit identifier and no donor information appear anywhere on the screen | Not executed | Pending |
| ST-21 | Notifications | Verify a donor receives eligibility and camp reminder notifications | A donor becoming eligible today and enrolled in a camp tomorrow | 1: Run the reminder job<br>2: Check the donor's email and SMS<br>3: Read the message content | Donor DNR10000001 | The donor receives an eligibility notification and a camp reminder. Both name the donor and carry the relevant date. Neither contains another donor's data | Not executed | Pending |
| ST-22 | Reporting | Verify shortage appeal and report generation through the interface | Admin signed in, O- stock below threshold | 1: Confirm the shortage banner on the dashboard<br>2: Open Reports and generate the Inventory Status Report<br>3: Read the O- row | O- stock 8, threshold 10 | The dashboard shows a shortage banner for O-. The report shows the O- available count as 8 and flags it as below threshold | Not executed | Pending |
| ST-23 | Reporting | Verify report export and hospital data scoping through the interface | Signed in as hosp01, then as hosp02 | 1: As hosp01 generate and export the Request and Issue Report as CSV<br>2: Open the CSV<br>3: Repeat as hosp02 and compare the two files | Requests for two hospitals | Each CSV contains only the signing-in hospital's records, and each carries the provenance header. Neither file contains the other hospital's data | Not executed | Pending |
| ST-24 | Administration | Verify an administrator can manage users, hospitals and configuration | Signed in as admin01 | 1: Register a new hospital<br>2: Create a hospital user linked to it<br>3: Sign in as that user and raise a request<br>4: As admin, deactivate the hospital<br>5: Attempt to raise another request as that user | New hospital: City Care Hospital, licence LIC-2026-3391 | The hospital and user are created and the first request succeeds. After deactivation the second request is refused, satisfying BR-7 | Not executed | Pending |

### A.7 Nonfunctional, Safety and Security System Tests

These cases verify the nonfunctional requirements traced in Appendix C.1 of the SRS.

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST-25 | Performance | Verify screen render and search response under concurrent load | Load tool configured, 50,000 units seeded | 1: Drive 50 concurrent virtual users through the staff console<br>2: Record the 95th percentile render time<br>3: Run 500 availability searches and record the 95th percentile | 50 concurrent users, 50,000 unit records | The 95th percentile screen render is at most 3 seconds per NFR-P1 and the 95th percentile availability search is at most 2 seconds per NFR-P2 | Not executed | Pending |
| ST-26 | Safety | Verify an untested and an expired unit can never be issued through any route | An Approved request, one Quarantined unit and one Expired unit of the matching group | 1: Attempt to issue the Quarantined unit through the interface<br>2: Attempt the same by direct URL manipulation<br>3: Repeat both for the Expired unit | Quarantined and Expired units of the requested group | Neither unit is offered in the interface, and both direct attempts are refused server-side. Both units retain their original status, satisfying NFR-S1 and NFR-S2 | Not executed | Pending |
| ST-27 | Safety | Verify group mismatch and concurrent double allocation are both prevented | An A+ request, an O+ unit, and one A+ unit contended by two sessions | 1: Attempt to allocate the O+ unit to the A+ request<br>2: In two sessions simultaneously allocate the same A+ unit to two different requests | One shared A+ unit, two concurrent sessions | The group mismatch is refused per NFR-S3. Exactly one of the two concurrent allocations succeeds and the other is refused, with the unit reserved to exactly one request per NFR-S4 | Not executed | Pending |
| ST-28 | Security | Verify server-side role enforcement and tenant data isolation | Accounts for all four roles, data for two hospitals | 1: For each role, request every function outside that role by direct URL<br>2: As hosp01, attempt to open a hosp02 request by its identifier<br>3: As a donor, attempt to open another donor's profile | Cross-role and cross-tenant direct access attempts | Every attempt is refused server-side with an authorisation error. No protected data appears in any response body. Each refusal is written to the audit log per NFR-SEC10 | Not executed | Pending |
| ST-29 | Security | Verify donor confidentiality and absence of common vulnerability classes | Hospital user signed in, security scanner available | 1: Traverse every hospital-accessible screen, export and notification and search for donor fields<br>2: Submit SQL metacharacters and script payloads into every free-text field<br>3: Replay a state-changing request without a CSRF token<br>4: Run the security scanner | Payloads: `' OR 1=1 --` and `<script>alert(1)</script>` | No donor identity is exposed anywhere per NFR-SEC7. Injected payloads are stored and rendered as inert text with no query error and no script execution. The token-less request is refused. The scanner reports no OWASP Top Ten finding per NFR-SEC9 | Not executed | Pending |
| ST-30 | Quality | Verify test coverage and complete requirement traceability | Full suite executable, SRS Appendix C available | 1: Run the full automated suite with coverage measurement<br>2: Read the line coverage figure<br>3: Cross-check every REQ tag in SRS Appendix C against this document | REQ-1 to REQ-46 | Line coverage is at least 70 percent per NFR-Q5. Every one of the 46 functional requirements maps to at least one test case present in this document, per NFR-Q6 | Not executed | Pending |

---

**End of Software Test Plan, Version 1.0**
