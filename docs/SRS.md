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

*Content pending — to be drafted by Balaraj R and G A Aadish.*

---

## 6. Other Nonfunctional Requirements

*Content pending — to be drafted by Niveditha.*

---

## 7. Other Requirements

*Content pending — to be drafted by Niveditha.*

---

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
