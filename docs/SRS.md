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



*Content pending — to be drafted by G A Aadish.*

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
