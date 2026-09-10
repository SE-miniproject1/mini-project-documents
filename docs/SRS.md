# Software Requirements Specification

## for Blood Bank Management System

**Version 0.1 draft**

**Prepared by**

| SRN | Name | GitHub Handle | Role |
|---|---|---|---|
| PES1UG24CS560 | Balaraj R | balaraj74 | Requirements Analyst / Test Lead |
| PES1UG24CS567 | Dhanya K M | Dhanya-KM | System Analyst / Data Modeller |
| PES1UG24CS569 | G A Aadish | Sonuaadi0706 | Project Lead / Architect |
| PES1UG24CS585 | Niveditha | nnivedithaparmesh-cpu | Interface Designer / Documentation Lead |

**Organization:** SE-miniproject1
**Course:** Software Engineering — Mini Project
**Date Created:** 08 September 2026


---


## Table of Contents

- [Revision History](#revision-history)
- [1. Introduction](#1-introduction)
  - [1.1 Purpose](#11-purpose)
  - [1.2 Intended Audience and Reading Suggestions](#12-intended-audience-and-reading-suggestions)
  - [1.3 Product Scope](#13-product-scope)
  - [1.4 References](#14-references)
- [2. Overall Description](#2-overall-description)
  - [2.1 Product Perspective](#21-product-perspective)
  - [2.2 Product Functions](#22-product-functions)
  - [2.3 User Classes and Characteristics](#23-user-classes-and-characteristics)
  - [2.4 Operating Environment](#24-operating-environment)
  - [2.5 Design and Implementation Constraints](#25-design-and-implementation-constraints)
  - [2.6 Assumptions and Dependencies](#26-assumptions-and-dependencies)
- [3. External Interface Requirements](#3-external-interface-requirements)
  - [3.1 User Interfaces](#31-user-interfaces)
  - [3.2 Software Interfaces](#32-software-interfaces)
  - [3.3 Communications Interfaces](#33-communications-interfaces)
  - [3.4 Hardware Interfaces](#34-hardware-interfaces)
- [4. Analysis Models](#4-analysis-models)
- [5. System Features](#5-system-features)
  - [5.1 Donor Registration and Eligibility Screening](#51-donor-registration-and-eligibility-screening)
  - [5.2 Blood Donation and Collection Management](#52-blood-donation-and-collection-management)
  - [5.3 Blood Inventory and Stock Management](#53-blood-inventory-and-stock-management)
  - [5.4 Hospital Blood Request and Issue](#54-hospital-blood-request-and-issue)
  - [5.5 Donation Camp and Drive Management](#55-donation-camp-and-drive-management)
  - [5.6 Search, Notification and Reporting](#56-search-notification-and-reporting)
- [6. Other Nonfunctional Requirements](#6-other-nonfunctional-requirements)
  - [6.1 Performance Requirements](#61-performance-requirements)
  - [6.2 Safety Requirements](#62-safety-requirements)
  - [6.3 Security Requirements](#63-security-requirements)
  - [6.4 Software Quality Attributes](#64-software-quality-attributes)
  - [6.5 Business Rules and Domain Requirements](#65-business-rules-and-domain-requirements)
- [7. Other Requirements](#7-other-requirements)
- [Appendix A: Glossary](#appendix-a-glossary)
- [Appendix B: Field Layouts](#appendix-b-field-layouts)
- [Appendix C: Requirement Traceability Matrix](#appendix-c-requirement-traceability-matrix)


---

## Revision History

| Name | Date | Reason For Changes | Version |
|---|---|---|---|
| G A Aadish | 08 Sep 2026 | Initial document skeleton, Section 1 Introduction and Section 2 Overall Description drafted. | 0.1 |

---


## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification describes the software requirements for the **Blood Bank Management System (BBMS), Release 1.0**. The BBMS is a web-based application that manages the full life cycle of donated blood, from the registration and eligibility screening of a donor, through collection, testing, component separation and storage, to the fulfilment of blood requests raised by hospitals.

This document covers the complete system as scoped for Release 1.0. It specifies the behaviour of all six functional subsystems, the external interfaces exposed to users and to other software, and the nonfunctional characteristics the system must exhibit. No part of the system is deferred to a separate SRS.

The document does not describe the internal design, database schema implementation, or user interface visual styling. Those are addressed in the Design Document and are outside the scope of this specification.

### 1.2 Intended Audience and Reading Suggestions

This SRS is written for the following readers.

| Reader | Interest | Suggested Reading Order |
|---|---|---|
| Course Faculty and Evaluators | Completeness, consistency and verifiability of the requirements | Section 1, Section 2, Section 5, Appendix C |
| Development Team | What to build and against what constraints | Section 2.4 to 2.6, Section 3, Section 4, Section 5 |
| Test Team | What to verify and how success is judged | Section 5, Section 6, Appendix C, and the companion Test Plan |
| Blood Bank Staff and Domain Reviewers | Whether the described behaviour matches real blood bank practice | Section 1.3, Section 2.2, Section 2.3, Section 6.5 |
| Hospital Users | How requests are raised and fulfilled | Section 5.4, Section 5.6, Section 3.1 |

The remainder of this SRS is organised as follows. Section 2 gives the overall product context, its major functions and its users. Section 3 defines the interfaces to users, to other software and over the network. Section 4 presents the analysis models. Section 5 carries the detailed functional requirements grouped by system feature, each requirement uniquely tagged. Section 6 states the nonfunctional requirements. Section 7 covers remaining requirements. The appendices provide a glossary, field layouts and the requirement traceability matrix.

Readers new to the project should read Section 1 and Section 2 first, then move to Section 5 for detail.

### 1.3 Product Scope

The Blood Bank Management System replaces the paper registers and disconnected spreadsheets that a mid-sized blood bank currently uses to track donors, stock and hospital demand. Its purpose is to make the location, quantity and expiry status of every blood unit visible in real time, and to make the matching of a hospital request against available stock a controlled, auditable operation rather than a phone call.

The benefits and objectives of the product are as follows.

- **Reduce wastage from expiry.** Blood components have short shelf lives. By tracking expiry per unit and surfacing units nearing expiry, the system aims to cut expiry-driven wastage.
- **Reduce time to fulfil an emergency request.** A hospital raising an urgent request should see candidate units immediately rather than waiting on manual stock checks.
- **Enforce donor safety rules automatically.** The mandatory interval between donations, minimum age, minimum weight and haemoglobin thresholds are checked by the system rather than remembered by staff.
- **Provide an audit trail.** Every unit can be traced from the donor who gave it to the hospital that received it, which is a regulatory expectation in blood banking.
- **Improve donor retention.** Donors are notified when they become eligible again and when their blood group is in short supply.

The following are explicitly **out of scope** for Release 1.0: laboratory instrument integration, financial billing and payment processing, integration with national blood registries, and a native mobile application. These may be considered in later releases.

### 1.4 References

1. IEEE Std 830-1998, *IEEE Recommended Practice for Software Requirements Specifications*, Institute of Electrical and Electronics Engineers, 1998.
2. *SRS-Template.docx*, Software Engineering course template, PES University, 2026. Supplied with the course material and used as the structural basis of this document.
3. *Test-Plan-Details.docx*, Software Engineering course template, PES University, 2026. Defines the test case template referenced in Appendix C.
4. National Blood Transfusion Council, *Standards for Blood Banks and Blood Transfusion Services*, Ministry of Health and Family Welfare, Government of India. Source of the donor eligibility and component shelf-life rules stated in Section 6.5.
5. Django Software Foundation, *Django Documentation, Version 5.x*. Available at https://docs.djangoproject.com/
6. OWASP Foundation, *OWASP Application Security Verification Standard, Version 4.0*. Basis of the security requirements in Section 6.3.
7. Project repository: https://github.com/SE-miniproject1/mini-project-documents


---


## 2. Overall Description

### 2.1 Product Perspective

The Blood Bank Management System is a **new, self-contained product**. It is not a member of an existing product family and it does not replace a specific existing software system. It replaces a manual, register-based process.

The system is a three-tier web application. A browser-based presentation tier serves four distinct user classes. An application tier holds the business logic, including the eligibility rules, the inventory allocation logic and the request approval workflow. A data tier holds the persistent records for donors, units, requests, camps and users.

The system has three external touch points. It sends outbound email and SMS through third-party gateways. It accepts no inbound automated traffic in Release 1.0. It exports reports as PDF and CSV files for offline use.

```
                 +-------------------------------------------+
                 |            Presentation Tier              |
                 |   Donor Portal | Staff Console |          |
                 |   Hospital Portal | Admin Console         |
                 +---------------------+---------------------+
                                       | HTTPS
                 +---------------------v---------------------+
                 |            Application Tier               |
                 |  Donor Mgmt | Collection | Inventory |    |
                 |  Request Mgmt | Camp Mgmt | Reporting     |
                 |  Auth & RBAC  | Notification Dispatcher   |
                 +------+--------------------+---------------+
                        |                    |
             +----------v--------+   +-------v-----------------+
             |    Data Tier      |   |  External Gateways      |
             |  Relational DB    |   |  Email SMTP | SMS API   |
             +-------------------+   +-------------------------+
```

A rendered version of this diagram is provided in `diagrams/architecture.mmd`, with an exported image at `diagrams/architecture.png`.

### 2.2 Product Functions

The major functions the product must perform are summarised below. Each maps to a system feature detailed in Section 5.

- **Donor management.** Register a donor, capture medical and contact details, screen the donor against eligibility rules, and maintain donation history.
- **Collection management.** Record a donation event, generate a uniquely identified blood unit, record screening test outcomes, and separate whole blood into components.
- **Inventory management.** Track every unit by blood group, component type, storage location, status and expiry date. Flag units nearing expiry and quarantine units that fail screening.
- **Request management.** Allow a registered hospital to raise a blood request, allow staff to approve, reject or partially fulfil it, and record the issue of specific units against it.
- **Camp management.** Schedule donation camps, register donors for a camp, and reconcile collections made at a camp back into central inventory.
- **Search, notification and reporting.** Search availability by group, component and location. Notify donors and hospitals of relevant events. Generate operational and statutory reports.

### 2.3 User Classes and Characteristics

Four user classes are anticipated.

**UC-1 Donor.** A member of the public who registers to donate blood. Low technical expertise is assumed. Uses the system infrequently, perhaps three or four times a year. Accesses only their own profile, donation history, camp listings and eligibility status. This is the largest class by headcount and an important class to satisfy, because a poor donor experience directly reduces the blood supply. Interfaces for this class must be usable on a mobile browser without training.

**UC-2 Blood Bank Staff.** Technicians and counsellors employed by the blood bank. Moderate technical expertise. Uses the system continuously through the working day and is the heaviest user by transaction volume. Performs screening, records collections, manages inventory and processes hospital requests. This is the **most important user class**, because the correctness and speed of their workflows determines whether the system delivers its objectives. Requires dense, keyboard-efficient screens rather than simplified ones.

**UC-3 Hospital User.** An authorised representative of a registered hospital, typically a blood bank liaison or a duty doctor. Moderate technical expertise, often working under time pressure in emergencies. Raises requests, tracks their status and views issue history for their own hospital only. Cannot see donor identities.

**UC-4 Administrator.** A blood bank manager or system administrator. High technical expertise. Uses the system daily but for a small set of functions. Manages user accounts and roles, registers hospitals, configures eligibility and expiry parameters, and views all reports and audit logs. Smallest class by headcount, highest privilege level.

Requirements REQ-40 through REQ-46 in Section 5.6 pertain principally to UC-4. Requirements REQ-24 through REQ-31 pertain principally to UC-3.

### 2.4 Operating Environment

**OE-1 Server environment.** The application runs on a 64-bit Linux server, Ubuntu 22.04 LTS or later.

**OE-2 Application platform.** Python 3.11 or later with the Django 5.x web framework, served by Gunicorn behind an Nginx reverse proxy.

**OE-3 Database.** PostgreSQL 15 or later. SQLite 3 is permitted for local development and for the automated test suite only.

**OE-4 Client environment.** The system must operate correctly on the current and immediately preceding major versions of Google Chrome, Mozilla Firefox, Microsoft Edge and Apple Safari, on Windows 10 or later, macOS 13 or later, Android 10 or later and iOS 15 or later.

**OE-5 Screen sizes.** The interface must render usably from a 360-pixel-wide mobile viewport up to a 1920-pixel-wide desktop viewport.

**OE-6 Coexistence.** The system must coexist with the blood bank's existing office productivity software and must not require any client-side installation beyond a standards-compliant browser.

### 2.5 Design and Implementation Constraints

**CON-1 Technology stack.** The implementation shall use Python with the Django framework and the Django ORM. Node.js with Express was evaluated as an alternative and rejected for Release 1.0, because Django's built-in authentication, role and administrative scaffolding materially reduce the work needed for the access-control requirements in Section 6.3. Any move to Node.js would require a re-baseline of this SRS.

**CON-2 Database access.** All persistent access shall go through the Django ORM. Raw SQL is permitted only where a query cannot be expressed through the ORM, and every such instance must use parameter binding.

**CON-3 Coding standards.** Python code shall conform to PEP 8. JavaScript, where used for client-side interactivity, shall conform to the Airbnb style guide. All code shall pass the project linters before merge.

**CON-4 Version control.** All work products, including this document, shall be maintained in the Git repository named in Section 1.4. Direct commits to the default branch are prohibited; changes shall be merged through pull requests with at least one peer review.

**CON-5 Regulatory constraint.** Donor identity shall never be disclosed to hospital users. This is a privacy requirement of blood banking practice and constrains the design of the request and issue screens.

**CON-6 Data retention.** Donor records and unit traceability records shall be retained for a minimum of five years and shall not be hard-deleted by any application function.

**CON-7 Time and team constraint.** The project is delivered by a four-member student team within a single academic semester. This constrains Release 1.0 to the scope stated in Section 1.3 and rules out the out-of-scope items listed there.

**CON-8 Offline operation.** The system is not required to operate without network connectivity. No offline mode shall be assumed by any requirement.

### 2.6 Assumptions and Dependencies

**ASM-1** It is assumed that the blood bank has reliable broadband connectivity during working hours. The performance requirements in Section 6.1 are stated on that assumption.

**ASM-2** It is assumed that screening test results are entered manually by a technician. No laboratory instrument produces machine-readable output for this release. If instrument integration becomes available, REQ-12 and REQ-13 will need revision.

**ASM-3** It is assumed that each hospital nominates and vouches for its own authorised users. The system does not independently verify that a hospital user is a licensed medical practitioner.

**ASM-4** It is assumed that donors provide accurate self-reported medical history. The system records declarations but cannot validate them.

**ASM-5** It is assumed that the component shelf-life values in Section 6.5 remain as stated. These are configurable, so a change in regulation is absorbed by configuration and not by code change.

**DEP-1** The system depends on a third-party SMS gateway for donor notifications. If the gateway is unavailable, notification requirements degrade to email only, as stated in REQ-39.

**DEP-2** The system depends on an SMTP relay for email notification and for password reset.

**DEP-3** The system depends on the Django framework and its security patch stream. A critical framework vulnerability may force an unplanned upgrade.

**DEP-4** The system reuses no components from other projects. All application code is written for this project.


---

## 3. External Interface Requirements

*Content pending — to be drafted by Niveditha.*

---

## 4. Analysis Models

*Content pending — to be drafted by Dhanya K M.*

---

## 5. System Features

The functional requirements are organised by system feature, which are the major services the product provides. Six features are specified. Each requirement carries a unique tag of the form `REQ-n` and is traced in Appendix C.

Priority is stated as High, Medium or Low, supported by component ratings for benefit, penalty, cost and risk, each on a scale of 1 to 9.

*Content pending — SF-1 to SF-3 to be drafted by Balaraj R.*

### 5.4 Hospital Blood Request and Issue

#### 5.4.1 Description and Priority

This feature allows a registered hospital to raise a request for blood, allows staff to review and act on that request, and records the issue of specific units against it. It is the demand side of the system and the feature that most directly affects patient outcomes in an emergency.

**Priority: High.** Benefit 9, Penalty 9, Cost 6, Risk 6.

#### 5.4.2 Stimulus/Response Sequences

**Sequence 1, raise a request.** A hospital user submits a request specifying blood group, component, quantity, urgency and required-by date and time, together with a patient reference that is not a patient name. The system validates the input, creates the request in Pending status, assigns a request identifier, and notifies blood bank staff. Emergency requests are placed at the head of the queue.

**Sequence 2, insufficient stock.** The hospital requests a quantity exceeding available stock of that group and component. The system accepts the request but displays the currently available quantity, and staff may later fulfil it partially.

**Sequence 3, approve and issue.** Staff open a Pending request, review it, and approve it. The system moves the request to Approved. Staff then allocate specific units. The system reserves each allocated unit, and on confirmation of issue moves each unit to Issued, moves the request to Fulfilled, and notifies the hospital.

**Sequence 4, partial fulfilment.** Staff allocate fewer units than requested. The system moves the request to Partially Fulfilled, records the shortfall, and keeps the request open for further allocation.

**Sequence 5, rejection.** Staff reject a request with a stated reason. The system moves the request to Rejected, releases any reservation, and notifies the hospital with the reason.

**Sequence 6, cancellation.** A hospital user cancels a request that has not yet been issued. The system releases any reserved units back to Available and moves the request to Cancelled.

#### 5.4.3 Functional Requirements

**REQ-24:** The system shall permit an authenticated hospital user to raise a blood request capturing blood group, component type, quantity of units, urgency drawn from Routine, Urgent and Emergency, required-by date and time, and a patient reference code. The system shall assign a unique, immutable request identifier of the form `REQ` followed by eight digits.

**REQ-25:** The system shall reject a request for a quantity that is not a positive integer, and shall reject a required-by date and time that lies in the past, with a message naming the field in error.

**REQ-26:** The system shall order the staff request queue by urgency, with Emergency first, then by required-by date and time ascending, and shall visually distinguish Emergency requests.

**REQ-27:** The system shall permit staff to approve, reject or partially fulfil a Pending request. A rejection shall require a reason drawn from a configured list, and that reason shall be communicated to the requesting hospital.

**REQ-28:** The system shall permit staff to allocate specific Available units of the requested blood group and component to an approved request. The system shall reject any attempt to allocate a unit that is not Available, whose blood group does not match the request, or which has expired.

**REQ-29:** The system shall move an allocated unit to Reserved on allocation and to Issued on confirmation of issue, and shall record against each issue the request identifier, unit identifier, issuing staff member, receiving hospital and timestamp.

**REQ-30:** The system shall set a request to Fulfilled when the issued quantity equals the requested quantity, to Partially Fulfilled when it is greater than zero but less than the requested quantity, and shall record the outstanding shortfall in the latter case.

**REQ-31:** The system shall permit a hospital user to cancel their own request while it is in Pending or Approved status, shall release any Reserved units back to Available, and shall prohibit cancellation once any unit has been Issued against the request.

### 5.5 Donation Camp and Drive Management

#### 5.5.1 Description and Priority

This feature schedules and manages blood donation camps held away from the blood bank premises, handles donor enrolment for those camps, and reconciles the units collected at a camp into central inventory. Camps are the principal source of supply for most blood banks, so the feature carries real operational benefit, though the system remains usable without it.

**Priority: Medium.** Benefit 7, Penalty 5, Cost 5, Risk 3.

#### 5.5.2 Stimulus/Response Sequences

**Sequence 1, schedule a camp.** Staff create a camp specifying name, venue, date, start and end times, organiser and target unit count. The system validates that the date is in the future and creates the camp in Scheduled status.

**Sequence 2, donor enrols.** A donor browses upcoming camps and enrols in one. The system verifies that the donor will be eligible on the camp date, records the enrolment and sends a confirmation.

**Sequence 3, ineligible enrolment.** A donor whose next eligible date falls after the camp date attempts to enrol. The system refuses the enrolment and displays the date on which the donor becomes eligible.

**Sequence 4, camp day collection.** Staff record collections against the camp. Each unit created carries the camp as its collection site.

**Sequence 5, close a camp.** Staff close the camp. The system moves it to Completed, computes actual units collected against the target, and prevents further collections being recorded against it.

#### 5.5.3 Functional Requirements

**REQ-32:** The system shall permit staff and administrators to create a donation camp capturing camp name, venue address, camp date, start and end time, organiser name and contact, and target number of units.

**REQ-33:** The system shall reject the creation of a camp whose date is earlier than the current date, and shall reject an end time that is not later than the start time.

**REQ-34:** The system shall publish all camps in Scheduled status to the donor camp listing, ordered by camp date ascending, and shall permit a donor to enrol in a listed camp.

**REQ-35:** The system shall refuse a camp enrolment where the donor's next eligible donation date falls after the camp date, and shall display the donor's next eligible date in the refusal message.

**REQ-36:** The system shall record the camp identifier as the collection site on every unit collected at that camp, so that units remain traceable to the camp at which they were collected.

**REQ-37:** The system shall permit staff to close a camp, shall move it to Completed status, shall report actual units collected against the target, and shall reject any collection recorded against a Completed camp.

### 5.6 Search, Notification and Reporting

#### 5.6.1 Description and Priority

This feature provides availability search across the inventory, dispatches notifications to donors, hospitals and staff, and generates the operational and statutory reports the blood bank must produce. It also carries the administrative functions for users, roles and system configuration.

**Priority: Medium to High.** Benefit 8, Penalty 6, Cost 5, Risk 3.

#### 5.6.2 Stimulus/Response Sequences

**Sequence 1, availability search.** A hospital user searches for a blood group and component. The system returns the available quantity without revealing individual unit identifiers or donor identities.

**Sequence 2, eligibility notification.** A donor reaches their next eligible date. The system sends a notification inviting them to donate.

**Sequence 3, shortage appeal.** Stock of a blood group falls below its configured minimum threshold. The system notifies eligible donors of that group.

**Sequence 4, generate a report.** A user selects a report and a date range. The system generates it, displays it on screen, and offers PDF and CSV export.

**Sequence 5, gateway failure.** The SMS gateway is unreachable. The system records the failure, retries per the configured policy, and falls back to email.

**Sequence 6, user administration.** An administrator creates a user account, assigns a role and, for a hospital user, links the account to a registered hospital.

#### 5.6.3 Functional Requirements

**REQ-38:** The system shall provide an availability search returning the count of Available units by blood group and component type. When invoked by a hospital user the response shall carry counts only, and shall not disclose unit identifiers, donor identifiers or any donor personal data.

**REQ-39:** The system shall dispatch notifications by SMS and email. Dispatch shall be asynchronous and shall not block or roll back the originating transaction. A failed SMS dispatch shall be retried up to three times at increasing intervals, and on final failure the system shall fall back to email and record the failure against the notification record.

**REQ-40:** The system shall notify a donor when their next eligible donation date is reached, and shall notify enrolled donors 24 hours before a camp in which they are enrolled.

**REQ-41:** The system shall notify eligible donors of a given blood group when Available stock of that group falls below its configured minimum threshold, and shall not send more than one such appeal to the same donor within any 30-day period.

**REQ-42:** The system shall generate the following reports over a user-selected date range: Donor Registration Report, Blood Collection Report, Inventory Status Report, Near-Expiry and Expiry Report, Hospital Request and Issue Report, and Camp Performance Report. The field composition of each is specified in Appendix B.

**REQ-43:** The system shall permit every generated report to be exported as PDF and as CSV, and shall include in the exported artefact the report name, the selected date range, the generating user and the generation timestamp.

**REQ-44:** The system shall restrict every report and search result to the data the requesting user is authorised to see. A hospital user shall see only requests and issues belonging to their own hospital.

**REQ-45:** The system shall permit an administrator to create, modify and deactivate user accounts, to assign exactly one role from Donor, Staff, Hospital User and Administrator to each account, and to register hospitals with name, address, licence number and contact details. Accounts shall be deactivated rather than deleted, in accordance with CON-6.

**REQ-46:** The system shall permit an administrator to configure the minimum donation interval, the donor age bounds, the minimum weight, the minimum haemoglobin, the component shelf lives, the near-expiry window and the per-group minimum stock thresholds, without requiring a code change or a restart.

---
### 6.1 Performance Requirements

**NFR-P1:** Any screen that does not generate a report shall render completely within 3 seconds at the 95th percentile, measured at the server under a load of 50 concurrent users. This bound exists because blood bank staff perform high-volume repetitive entry, and a slower response measurably reduces throughput during peak collection hours.

**NFR-P2:** The availability search specified in REQ-38 shall return within 2 seconds at the 95th percentile for an inventory of up to 50,000 unit records. Emergency requests depend on this search, so it is bounded more tightly than general screens.

**NFR-P3:** The system shall support at least 50 concurrent authenticated users and at least 200 registered hospital accounts without breaching NFR-P1.

**NFR-P4:** A report covering a 12-month range shall be generated and made available for download within 30 seconds. Reporting is a background activity and is permitted a looser bound than interactive screens.

**NFR-P5:** An inventory change committed by one user shall be visible to all other users within 5 seconds, satisfying REQ-17. This bound prevents two staff members allocating the same unit to different requests.

**NFR-P6:** Notification dispatch shall be enqueued within 1 second of the triggering transaction committing. Actual delivery time is governed by the external gateway and is outside the system's control.

**NFR-P7:** The database shall sustain the stated response times with up to 200,000 donor records, 500,000 unit records and 100,000 request records.
### 6.2 Safety Requirements

**NFR-S1:** The system shall make it impossible, through any application function, to issue a blood unit that has not completed the mandatory screening panel with all results Non-Reactive. This is the single most safety-critical constraint in the system, because an infected unit reaching a patient could cause death.

**NFR-S2:** The system shall make it impossible to issue a unit whose expiry date has passed.

**NFR-S3:** The system shall prevent the allocation of a unit whose blood group does not match the blood group on the request. Group mismatch in transfusion can cause a fatal haemolytic reaction.

**NFR-S4:** The system shall prevent the same unit being allocated to more than one request concurrently, by reserving the unit atomically at the point of allocation.

**NFR-S5:** The system shall enforce the donor deferral rules in REQ-6 and REQ-7 so that a donor cannot be bled more frequently than the configured interval, protecting the donor from iron depletion.

**NFR-S6:** Every unit shall remain traceable in both directions, from donor to recipient hospital and from recipient hospital back to donor, for the retention period stated in CON-6, so that a transfusion-transmitted infection can be investigated.

**NFR-S7:** Where the system cannot determine that an operation is safe, it shall refuse the operation rather than permit it. Ambiguity resolves to refusal.
### 6.3 Security Requirements

**NFR-SEC1:** The system shall authenticate every user by username and password before granting access to any function other than public camp listings and the registration and login screens.

**NFR-SEC2:** Passwords shall be stored only as salted hashes produced by a deliberately slow key derivation function. Plain text and reversibly encrypted passwords are prohibited.

**NFR-SEC3:** The system shall enforce a password policy of at least 10 characters including at least one letter, one digit and one special character, and shall reject passwords appearing in a known-compromised password list.

**NFR-SEC4:** The system shall lock an account for 15 minutes after 5 consecutive failed authentication attempts, and shall notify the account holder by email.

**NFR-SEC5:** The system shall enforce role-based access control so that every function and every data record is accessible only to the roles authorised for it. Authorisation shall be checked on the server for every request, and shall never rely on the client hiding a control.

**NFR-SEC6:** A hospital user shall be able to access only records belonging to their own hospital. A donor shall be able to access only their own records.

**NFR-SEC7:** Donor identity shall never be disclosed to any hospital user, in any screen, report, export or notification, in accordance with CON-5.

**NFR-SEC8:** All data in transit shall be protected by TLS 1.2 or higher, as stated in CI-1.

**NFR-SEC9:** The system shall be free of the OWASP Top Ten vulnerability classes. In particular, all database access shall use parameter binding, all user-supplied content shall be contextually escaped on output, and all state-changing requests shall carry a CSRF token.

**NFR-SEC10:** The system shall write an audit record for every authentication event, every authorisation failure, every unit status transition and every configuration change, carrying the acting user, the timestamp and the source address.

**NFR-SEC11:** Sessions shall expire after 30 minutes of inactivity and shall be invalidated on logout and on password change.

### 6.4 Software Quality Attributes

**NFR-Q1 Usability.** A blood bank staff member shall be able to complete a routine collection entry in no more than 8 interactions after the donor is located. A donor with no training shall be able to complete registration without assistance. Where ease of use and ease of learning conflict for the staff console, **ease of use is preferred**, because staff are trained once and then use the system continuously. For the donor portal the preference is reversed and **ease of learning is preferred**, because donors use the system rarely.

**NFR-Q2 Availability.** The system shall be available at least 99 percent of the time during the blood bank's operating hours, excluding scheduled maintenance announced at least 48 hours in advance.

**NFR-Q3 Reliability.** The mean time between failures shall exceed 720 hours of operation. No failure shall leave a unit in an inconsistent status, because every status transition is performed within a database transaction.

**NFR-Q4 Correctness.** All eligibility, expiry and allocation calculations shall be exact. There is no tolerance for approximation in any safety-related computation.

**NFR-Q5 Maintainability.** Automated unit test line coverage shall be at least 70 percent. Every module shall carry a docstring stating its responsibility. Cyclomatic complexity of any single function shall not exceed 10.

**NFR-Q6 Testability.** Every functional requirement in Section 5 shall be verifiable by at least one test case, and this shall be demonstrated in Appendix C. The system shall support seeding of a deterministic test data set.

**NFR-Q7 Portability.** The application shall run on any Linux distribution providing the platform versions in Section 2.4 and shall not depend on any operating system feature outside the Python standard library and declared dependencies.

**NFR-Q8 Interoperability.** All report exports shall be produced in PDF and in RFC 4180 conformant CSV, so that they can be consumed by standard office software.

**NFR-Q9 Robustness.** The system shall validate every input on the server irrespective of client-side validation, and shall respond to invalid input with a corrective message rather than an unhandled error.

**NFR-Q10 Flexibility.** The parameters listed in REQ-46 shall be changeable through configuration without code modification, so that a change in regulation is absorbed operationally.
---
### 6.5 Business Rules and Domain Requirements

**BR-1** Only a donor whose current eligibility status is Eligible may donate. Staff cannot override this rule.

**BR-2** The minimum interval between two whole blood donations by the same donor is 90 days. This value is configurable per REQ-46 but shall not be configurable below 90 days.

**BR-3** A donor must be at least 18 and at most 65 years of age, weigh at least 50 kilograms and have a haemoglobin level of at least 12.5 grams per decilitre.

**BR-4** Component shelf lives, measured from the collection date, are as follows. These are domain requirements derived from transfusion medicine practice.

| Component | Shelf Life | Storage Temperature |
|---|---|---|
| Whole Blood | 35 days | 2 to 6 degrees Celsius |
| Packed Red Blood Cells | 42 days | 2 to 6 degrees Celsius |
| Fresh Frozen Plasma | 365 days | minus 30 degrees Celsius or below |
| Platelet Concentrate | 5 days | 20 to 24 degrees Celsius with agitation |
| Cryoprecipitate | 365 days | minus 30 degrees Celsius or below |

**BR-5** Every unit must complete the mandatory screening panel of HIV, Hepatitis B, Hepatitis C, Syphilis and Malaria. A unit reactive to any of these is discarded and can never be issued.

**BR-6** Only blood bank staff may record a collection or issue a unit. Only an administrator may alter configuration, register a hospital or change a user's role.

**BR-7** Only a hospital user linked to a registered, active hospital may raise a blood request.

**BR-8** Blood group compatibility for issue in Release 1.0 is exact match only. Compatible-group substitution, such as issuing O negative to any recipient, is a manual clinical decision and is not automated by the system.

**BR-9** Donor identity is confidential. It is visible to blood bank staff and administrators only, never to hospital users.

**BR-10** No donor record, unit record, request record or audit record may be permanently deleted. Records are deactivated or superseded, never removed.
## 7. Other Requirements

**OR-1 Database requirements.** The schema shall be normalised to at least third normal form. Every table shall carry a surrogate primary key, a creation timestamp and a last-modified timestamp. Foreign key constraints shall be enforced at the database level and shall not rely solely on application logic. All schema changes shall be applied through versioned migration files held in source control.

**OR-2 Backup and recovery.** The database shall be backed up daily with a retention of 30 days. The recovery point objective is 24 hours and the recovery time objective is 4 hours. A restore shall be tested at least once before release.

**OR-3 Internationalisation.** All user-facing text shall be held in externalised message files rather than embedded in code, so that a future release can add a second language. Release 1.0 ships English only. All timestamps shall be stored in UTC and displayed in the Asia/Kolkata timezone. Dates shall be displayed as DD-MM-YYYY.

**OR-4 Legal and regulatory.** Donor personal data and medical data shall be processed only for the purposes stated in this SRS. The registration screen shall obtain the donor's explicit consent to the storage and processing of their data, and that consent shall be recorded with a timestamp.

**OR-5 Reuse objectives.** The authentication, role-based access control and notification dispatch modules shall be written without dependency on blood-bank-specific domain logic, so that they can be reused in future projects.

**OR-6 Documentation.** The delivered system shall be accompanied by a user manual per user class, an installation and deployment guide, and API documentation generated from source docstrings.

**OR-7 Logging.** The application shall write structured logs at INFO level for business events and at ERROR level for failures. Logs shall never contain passwords, session tokens or full donor medical histories.

**OR-8 Environment separation.** Development, test and production environments shall be separate. Production data shall never be copied to a development environment without anonymisation of donor personal data.

## Appendix A: Glossary

*Content pending — to be drafted by Dhanya K M.*

---

## Appendix B: Field Layouts

*Content pending — to be drafted by Dhanya K M.*

---

## Appendix C: Requirement Traceability Matrix

*Content pending — to be drafted by Balaraj R.*

---

*Draft in progress — Deliverable 1, Blood Bank Management System. Not yet complete or reviewed.*
