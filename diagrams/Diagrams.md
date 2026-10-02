# Analysis Models and Diagrams

Blood Bank Management System, SRS Section 4.

Each diagram is held as a Mermaid source file, which GitHub renders directly, and as an exported PNG for inclusion in the Word submission. Regenerate the images with the command in [../README.md](../README.md).

| Diagram | Source | Image |
|---|---|---|
| Use Case Diagram | [`use-case.mmd`](use-case.mmd) | [`use-case.png`](use-case.png) |
| Entity Relationship Diagram | [`er-diagram.mmd`](er-diagram.mmd) | [`er-diagram.png`](er-diagram.png) |
| Data Flow Diagram, Level 0 | [`dfd-level0.mmd`](dfd-level0.mmd) | [`dfd-level0.png`](dfd-level0.png) |
| Data Flow Diagram, Level 1, Sheet A | [`dfd-level1a-supply.mmd`](dfd-level1a-supply.mmd) | [`dfd-level1a-supply.png`](dfd-level1a-supply.png) |
| Data Flow Diagram, Level 1, Sheet B | [`dfd-level1b-demand.mmd`](dfd-level1b-demand.mmd) | [`dfd-level1b-demand.png`](dfd-level1b-demand.png) |
| System Architecture | [`architecture.mmd`](architecture.mmd) | [`architecture.png`](architecture.png) |

---

## Use Case Diagram

Actors and the use cases each may perform, grouped by system feature. SRS Section 4.

```mermaid
%% Blood Bank Management System - Use Case Diagram
%% SRS Section 4, Analysis Models
%% Use cases are grouped by the system feature (SF) that contains them.
flowchart TB
    DONOR([Donor])
    STAFF([Blood Bank Staff])
    HOSP([Hospital User])
    ADMIN([Administrator])
    SMS([SMS Gateway])
    MAIL([Email Gateway])

    subgraph SF1["SF-1 Donor and Eligibility"]
        direction LR
        UC1((Register<br/>as Donor))
        UC2((View Eligibility<br/>Status))
        UC4((Screen<br/>Donor))
    end

    subgraph SF2["SF-2 Collection and Screening"]
        direction LR
        UC5((Record<br/>Collection))
        UC6((Enter Test<br/>Results))
        UC7((Separate<br/>Components))
    end

    subgraph SF3["SF-3 Inventory"]
        direction LR
        UC8((Manage<br/>Inventory))
        UC9((Discard<br/>Unit))
    end

    subgraph SF4["SF-4 Request and Issue"]
        direction LR
        UC10((Raise Blood<br/>Request))
        UC11((Track<br/>Request))
        UC13((Approve or<br/>Reject Request))
        UC14((Allocate and<br/>Issue Units))
    end

    subgraph SF5["SF-5 Camps"]
        direction LR
        UC3((Enrol<br/>in Camp))
        UC15((Manage<br/>Camp))
    end

    subgraph SF6["SF-6 Search, Reporting and Admin"]
        direction LR
        UC12((Check<br/>Availability))
        UC16((Generate<br/>Reports))
        UC17((Manage Users<br/>and Roles))
        UC18((Configure<br/>Parameters))
        UC19((Send<br/>Notification))
    end

    DONOR --> UC1
    DONOR --> UC2
    DONOR --> UC3

    STAFF --> UC4
    STAFF --> UC5
    STAFF --> UC6
    STAFF --> UC7
    STAFF --> UC8
    STAFF --> UC9
    STAFF --> UC13
    STAFF --> UC14
    STAFF --> UC15
    STAFF --> UC16

    HOSP --> UC10
    HOSP --> UC11
    HOSP --> UC12
    HOSP --> UC16

    ADMIN --> UC8
    ADMIN --> UC15
    ADMIN --> UC16
    ADMIN --> UC17
    ADMIN --> UC18

    UC5 -.->|include| UC4
    UC14 -.->|include| UC8
    UC6 -.->|extend| UC9
    UC1 -.->|include| UC19
    UC3 -.->|include| UC19
    UC13 -.->|include| UC19

    UC19 --> SMS
    UC19 --> MAIL
```

## Entity Relationship Diagram

The fourteen persistent entities, their attributes and their cardinalities. Attribute detail is given in SRS Appendix B.

```mermaid
%% Blood Bank Management System - Entity Relationship Diagram
%% SRS Section 4, attributes per Appendix B
erDiagram
    DONOR ||--o{ DONATION : "makes"
    DONOR ||--o{ CAMP_ENROLMENT : "enrols via"
    DONATION ||--|| BLOOD_UNIT : "produces"
    BLOOD_UNIT ||--o{ BLOOD_UNIT : "separates into"
    BLOOD_UNIT ||--o{ SCREENING_TEST : "is screened by"
    BLOOD_UNIT ||--o| ISSUE : "is issued as"
    HOSPITAL ||--o{ BLOOD_REQUEST : "raises"
    BLOOD_REQUEST ||--o{ ISSUE : "fulfilled by"
    CAMP ||--o{ CAMP_ENROLMENT : "has"
    CAMP ||--o{ DONATION : "hosts"
    USER_ACCOUNT ||--|| ROLE : "holds"
    USER_ACCOUNT ||--o{ AUDIT_LOG : "generates"
    HOSPITAL ||--o{ USER_ACCOUNT : "employs"
    DONOR ||--o| USER_ACCOUNT : "signs in as"
    NOTIFICATION }o--|| DONOR : "sent to"

    DONOR {
        string donor_id PK "DNR + 8 digits"
        string full_name
        date   date_of_birth
        string gender
        string blood_group
        string mobile_number UK
        string email UK
        string city
        string pin_code
        decimal weight_kg
        decimal haemoglobin
        date   last_donation_date
        date   next_eligible_date
        string eligibility_status
        string deferral_reason
        datetime consent_timestamp
    }

    DONATION {
        string donation_id PK
        string donor_id FK
        datetime collected_at
        int    volume_ml
        string bag_lot_number
        string collection_site
        string recorded_by
    }

    BLOOD_UNIT {
        string unit_id PK "BU + 10 digits"
        string donor_id FK
        string parent_unit_id FK
        string blood_group
        string component_type
        int    volume_ml
        date   collection_date
        date   expiry_date
        string storage_location
        string status
        string discard_reason
    }

    SCREENING_TEST {
        string test_id PK
        string unit_id FK
        string test_name
        string result "Reactive / Non-Reactive"
        date   tested_on
        string tested_by
    }

    HOSPITAL {
        string hospital_id PK
        string hospital_name
        string licence_number UK
        string city
        string contact_person
        string contact_number
        bool   is_active
    }

    BLOOD_REQUEST {
        string request_id PK "REQ + 8 digits"
        string hospital_id FK
        string blood_group
        string component_type
        int    quantity_requested
        int    quantity_issued
        string urgency
        datetime required_by
        string patient_reference
        string status
        string rejection_reason
        datetime raised_on
    }

    ISSUE {
        string issue_id PK
        string request_id FK
        string unit_id FK
        string issued_by
        datetime issued_at
    }

    CAMP {
        string camp_id PK
        string camp_name
        string venue_address
        date   camp_date
        time   start_time
        time   end_time
        string organiser_name
        int    target_units
        int    units_collected
        string status
    }

    CAMP_ENROLMENT {
        string enrolment_id PK
        string camp_id FK
        string donor_id FK
        datetime enrolled_at
        bool   attended
    }

    USER_ACCOUNT {
        string user_id PK
        string username UK
        string password_hash
        string role_id FK
        string hospital_id FK
        bool   is_active
        datetime last_login
    }

    ROLE {
        string role_id PK
        string role_name "Donor / Staff / Hospital / Admin"
    }

    NOTIFICATION {
        string notification_id PK
        string recipient_id
        string channel "SMS / Email"
        string message_body
        string dispatch_status
        int    retry_count
        datetime dispatched_at
    }

    AUDIT_LOG {
        string audit_id PK
        string entity_type
        string entity_id
        string previous_status
        string new_status
        string acting_user FK
        string reason
        datetime occurred_at
    }
```

## Data Flow Diagram, Level 0

The context diagram. The system as a single process with its six external entities.

```mermaid
%% Blood Bank Management System - Data Flow Diagram, Level 0 (Context Diagram)
%% SRS Section 4
flowchart LR
    DONOR([Donor])
    STAFF([Blood Bank Staff])
    HOSP([Hospital User])
    ADMIN([Administrator])
    SMS([SMS Gateway])
    MAIL([Email Gateway])

    SYS[["0<br/>Blood Bank<br/>Management System"]]

    DONOR -->|"registration details,<br/>camp enrolment"| SYS
    SYS -->|"donor ID, eligibility status,<br/>camp confirmation"| DONOR

    STAFF -->|"screening values, collection data,<br/>test results, allocation decisions"| SYS
    SYS -->|"donor profile, unit IDs,<br/>stock levels, request queue"| STAFF

    HOSP -->|"blood request, cancellation,<br/>availability query"| SYS
    SYS -->|"request ID and status,<br/>available quantity, issue record"| HOSP

    ADMIN -->|"user and role changes,<br/>hospital registration, configuration"| SYS
    SYS -->|"audit log, all reports,<br/>reactive screening alert"| ADMIN

    SYS -->|"recipient number,<br/>message body"| SMS
    SMS -->|"delivery status"| SYS

    SYS -->|"recipient address,<br/>subject and body"| MAIL
    MAIL -->|"delivery status"| SYS

    DONOR ~~~ STAFF ~~~ HOSP ~~~ ADMIN
```

## Data Flow Diagram, Level 1, Sheet A

Processes 1.0 to 4.0. The path by which blood enters the system, from donor registration through to inventory.

```mermaid
%% Blood Bank Management System - Data Flow Diagram, Level 1 (Sheet A: Supply Side)
%% SRS Section 4. Processes 1.0 to 4.0, the path by which blood enters the system.
%% Sheet B covers processes 5.0 to 9.0.
flowchart TB
    DONOR([Donor])
    STAFF([Blood Bank Staff])
    ADMINA([Administrator])

    P1["1.0<br/>Register and<br/>Screen Donor"]
    P2["2.0<br/>Record<br/>Collection"]
    P3["3.0<br/>Test and<br/>Quarantine Unit"]
    P4["4.0<br/>Maintain<br/>Inventory"]

    D1[("D1  Donor Store")]
    D2[("D2  Unit Store")]
    D5[("D5  Audit Store")]

    TO_B(["To Sheet B<br/>6.0 Allocate and Issue"])
    TO_N(["To Sheet B<br/>9.0 Dispatch Notification"])
    FROM_C(["From Sheet B<br/>7.0 Manage Camp"])

    DONOR -->|"registration details"| P1
    P1 -->|"donor ID, eligibility status"| DONOR
    STAFF -->|"screening values"| P1
    P1 -->|"donor record"| D1
    D1 -->|"eligibility status"| P1

    D1 -->|"eligible donor"| P2
    STAFF -->|"collection data"| P2
    FROM_C -->|"camp as collection site"| P2
    P2 -->|"last donation date"| D1
    P2 -->|"new quarantined unit"| D2
    P2 -->|"unit ID and label"| STAFF

    STAFF -->|"test results"| P3
    D2 -->|"quarantined unit"| P3
    P3 -->|"released or discarded unit"| D2
    P3 -->|"reactive alert"| TO_N
    P3 -->|"status transition"| D5

    D2 -->|"unit records"| P4
    P4 -->|"expiry and transfer updates"| D2
    P4 -->|"stock levels"| STAFF
    P4 -->|"stock levels"| ADMINA
    P4 -->|"available units"| TO_B
    P4 -->|"near-expiry digest"| TO_N
    P4 -->|"status transition"| D5
```

## Data Flow Diagram, Level 1, Sheet B

Processes 5.0 to 9.0. The path by which blood leaves the system, with camp management, reporting and notification.

```mermaid
%% Blood Bank Management System - Data Flow Diagram, Level 1 (Sheet B: Demand, Camps and Reporting)
%% SRS Section 4. Processes 5.0 to 9.0, the path by which blood leaves the system,
%% together with camp management, reporting and notification.
%% Sheet A covers processes 1.0 to 4.0.
flowchart TB
    HOSP([Hospital User])
    STAFFB([Blood Bank Staff])
    ADMIN([Administrator])
    DONORB([Donor])
    GATEWAY([SMS / Email Gateways])

    P5["5.0<br/>Receive and<br/>Approve Request"]
    P6["6.0<br/>Allocate and<br/>Issue Units"]
    P7["7.0<br/>Manage<br/>Camp"]
    P8["8.0<br/>Generate<br/>Report"]
    P9["9.0<br/>Dispatch<br/>Notification"]

    D2B[("D2  Unit Store")]
    D3[("D3  Request Store")]
    D4[("D4  Camp Store")]
    D5B[("D5  Audit Store")]

    FROM_A(["From Sheet A<br/>4.0 Maintain Inventory"])
    TO_A(["To Sheet A<br/>2.0 Record Collection"])
    ALERTS(["From Sheet A<br/>3.0 and 4.0 alerts"])
    STORES_A(["From Sheet A<br/>D1 Donor Store"])

    HOSP -->|"blood request, cancellation"| P5
    STAFFB -->|"approval or rejection"| P5
    P5 -->|"request record"| D3
    D3 -->|"request queue"| P5
    P5 -->|"queue and decisions"| STAFFB
    P5 -->|"approval or rejection"| P9

    P5 -->|"approved request"| P6
    STAFFB -->|"allocation decision"| P6
    FROM_A -->|"available units"| P6
    P6 -->|"reserved then issued unit"| D2B
    P6 -->|"issue record and fulfilment status"| D3
    P6 -->|"status transition"| D5B
    P6 -->|"issue confirmation"| P9

    STAFFB -->|"camp details"| P7
    ADMIN -->|"camp details"| P7
    P7 -->|"camp and enrolment records"| D4
    D4 -->|"camp listing"| P7
    P7 -->|"camp listing and confirmation"| DONORB
    P7 -->|"camp site"| TO_A
    P7 -->|"camp reminder"| P9

    STORES_A -->|"donor data"| P8
    D2B -->|"unit data"| P8
    D3 -->|"request data"| P8
    D4 -->|"camp data"| P8
    D5B -->|"audit records"| P8
    P8 -->|"reports and exports"| STAFFB
    P8 -->|"scoped reports"| HOSP
    P8 -->|"all reports and audit"| ADMIN

    ALERTS -->|"reactive alert, near-expiry digest"| P9
    P9 -->|"message"| GATEWAY
    GATEWAY -->|"delivery status"| P9
    P9 -->|"notification"| DONORB
    P9 -->|"notification"| HOSP
    P9 -->|"confidential alert"| ADMIN
```

## System Architecture

Tier decomposition, domain services and external gateways. SRS Section 2.1.

```mermaid
%% Blood Bank Management System - System Architecture
%% SRS Section 2.1, Product Perspective
flowchart TB
    subgraph CLIENT["Presentation Tier — Browser"]
        direction LR
        C1["Donor Portal"]
        C2["Staff Console"]
        C3["Hospital Portal"]
        C4["Admin Console"]
    end

    LB["Nginx Reverse Proxy<br/>TLS 1.2+ termination, HSTS"]

    subgraph APP["Application Tier — Django 5.x on Gunicorn"]
        direction TB
        SEC["Authentication and RBAC<br/>session, CSRF, permissions"]
        subgraph DOMAIN["Domain Services"]
            direction LR
            M1["Donor<br/>Management"]
            M2["Collection and<br/>Screening"]
            M3["Inventory<br/>Management"]
            M4["Request and<br/>Issue"]
            M5["Camp<br/>Management"]
            M6["Search and<br/>Reporting"]
        end
        NOTIF["Notification Dispatcher<br/>async, retry, email fallback"]
        JOBS["Scheduled Jobs<br/>expiry, reminders, shortage appeal"]
        AUD["Audit Writer<br/>append-only"]
    end

    subgraph DATA["Data Tier"]
        direction LR
        DB[("PostgreSQL 15<br/>donors, units, requests,<br/>camps, users, audit")]
        FILES[("Report Artefacts<br/>PDF and CSV")]
    end

    subgraph EXT["External Gateways"]
        direction LR
        SMSG["SMS Gateway<br/>HTTPS REST"]
        SMTP["SMTP Relay<br/>STARTTLS :587"]
    end

    SCAN["Barcode Scanner<br/>keyboard-wedge"]

    C1 -->|HTTPS| LB
    C2 -->|HTTPS| LB
    C3 -->|HTTPS| LB
    C4 -->|HTTPS| LB
    SCAN -.->|unit ID keystrokes| C2

    LB --> SEC
    SEC --> DOMAIN
    DOMAIN --> AUD
    DOMAIN --> NOTIF
    JOBS --> DOMAIN

    DOMAIN -->|Django ORM| DB
    AUD -->|append only| DB
    M6 --> FILES

    NOTIF --> SMSG
    NOTIF --> SMTP
```
