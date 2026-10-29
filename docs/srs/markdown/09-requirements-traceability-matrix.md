# Requirements Traceability Matrix (RTM)

| Req ID | Requirement Summary | Design Spec Ref | Target Module | Test Case Ref | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-001** | Provision user accounts & display credentials | DS-ACC-01 | Account Module | TC-ACC-01 | Verified |
| **SYS-F-002** | Mandate password update on first login | DS-ACC-02 | Auth Module | TC-ACC-02 | Verified |
| **SYS-F-003** | Update personal contact details | DS-ACC-03 | Profile Module | TC-ACC-03 | Verified |
| **SYS-F-004** | Manage account metadata and status | DS-ACC-04 | Admin Module | TC-ACC-04 | Verified |
| **SYS-F-005** | Register course & set rubric scheme | DS-CRS-01 | Course Module | TC-CRS-01 | Verified |
| **SYS-F-006** | Student self-enrollment (max 6 courses) | DS-CRS-02 | Enrollment Module | TC-CRS-02 | Verified |
| **SYS-F-007** | Create and publish class schedules | DS-CRS-03 | Schedule Module | TC-CRS-03 | Verified |
| **SYS-F-008** | Restrict faculty roster visibility | DS-CRS-04 | RBAC / Course | TC-CRS-04 | Verified |
| **SYS-F-009** | Digitized binary roll-call attendance | DS-ATT-01 | Attendance Module | TC-ATT-01 | Verified |
| **SYS-F-010** | 48-hour automated attendance freeze | DS-ATT-02 | Attendance Module | TC-ATT-02 | Verified |
| **SYS-F-011** | Administrative attendance override | DS-ATT-03 | Admin / Attendance | TC-ATT-03 | Verified |
| **SYS-F-012** | Student attendance dashboard view | DS-ATT-04 | Dashboard Module | TC-ATT-04 | Verified |
| **SYS-F-013** | Record rubric marks in `Draft` state | DS-GRD-01 | Grading Module | TC-GRD-01 | Verified |
| **SYS-F-014** | Submit draft grades with weight total | DS-GRD-02 | Grading Module | TC-GRD-02 | Verified |
| **SYS-F-015** | Publish final grades to students | DS-GRD-03 | Admin / Grading | TC-GRD-03 | Verified |
| **SYS-F-016** | Submit regrade dispute (`Under Review`) | DS-GRD-04 | Dispute Module | TC-GRD-04 | Verified |
| **SYS-F-017** | Resolve dispute and re-publish grade | DS-GRD-05 | Grading Module | TC-GRD-05 | Verified |
| **SYS-F-018** | Student consolidated GPA dashboard | DS-REP-01 | Dashboard Module | TC-REP-01 | Verified |
| **SYS-F-019** | Faculty class summary analytics | DS-REP-02 | Analytics Module | TC-REP-02 | Verified |
| **SYS-F-020** | Admin institution-level metrics export | DS-REP-03 | Analytics Module | TC-REP-03 | Verified |
| **SYS-NF-001** | Latency $< 800\text{ ms}$ at 95th percentile | DS-PERF-01 | System-wide | TC-PERF-01 | Verified |
| **SYS-NF-002** | 200 concurrent transaction capability | DS-PERF-02 | Database Layer | TC-PERF-02 | Verified |
| **SYS-NF-003** | 99.0% operational availability | DS-OPS-01 | Infrastructure | TC-OPS-01 | Waived |
| **SYS-NF-004** | Responsive UI (375px-1920px, $\le 3$ clicks)| DS-UX-01 | Web Presentation | TC-UX-01 | Verified |
| **SYS-NF-005** | 3-tier architecture & $\ge 70\%$ test cover | DS-QUAL-01 | Architecture | TC-QUAL-01 | Verified |
| **PRJ-SO-001** | Data isolation and RBAC objective | DS-SEC-01 | System-wide | TC-SEC-04 | Verified |
| **PRJ-SO-002** | Workflow state integrity objective | DS-SEC-02 | Core Business Rules | TC-ATT-02, TC-GRD-03 | Verified |
| **PRJ-SR-001** | Mandatory TLS 1.3 encryption | DS-SEC-03 | Network Layer | TC-SEC-01 | Verified |
| **PRJ-SR-002** | Bcrypt password hashing (factor 12) | DS-SEC-04 | Auth Module | TC-SEC-02 | Verified |
| **PRJ-SR-003** | 48-hour HTTP-only JWT sessions | DS-SEC-05 | Auth Middleware | TC-SEC-03 | Verified |
| **PRJ-SR-004** | Endpoint RBAC enforcement middleware | DS-SEC-06 | API Middleware | TC-SEC-04 | Verified |
| **PRJ-SR-005** | ORM parameterization (SQLi/XSS prevention)| DS-SEC-07 | Data Access Layer | TC-SEC-05 | Verified |
