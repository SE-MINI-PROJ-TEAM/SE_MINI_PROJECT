# 13. Test Case Management & Traceability

Requirements Traceability Matrix (RTM) maps SRS requirement IDs to corresponding test cases and test suites:

| SRS Requirement ID | Requirement Summary | Test Case ID | Test Suite |
| :--- | :--- | :--- | :--- |
| **SYS-F-001** | Account provisioning & credential display | `TC-ACC-01` | `TS-AUTH` |
| **SYS-F-002** | Mandate password reset on initial login | `TC-ACC-02` | `TS-AUTH` |
| **SYS-F-003** | Personal contact details update | `TC-ACC-03` | `TS-AUTH` |
| **SYS-F-004** | Admin account metadata/status update | `TC-ACC-04` | `TS-AUTH` |
| **SYS-F-005** | Course setup & rubric weight auto-norm | `TC-CRS-01` | `TS-CRS` |
| **SYS-F-006** | Student self-enrollment (max 6 courses) | `TC-CRS-02` | `TS-CRS` |
| **SYS-F-007** | Class schedule creation & publishing | `TC-CRS-03` | `TS-CRS` |
| **SYS-F-008** | Restrict faculty roster visibility | `TC-CRS-04` | `TS-CRS` |
| **SYS-F-009** | Digitized binary roll-call submission | `TC-ATT-01` | `TS-ATT` |
| **SYS-F-010** | 48-hour automated attendance freeze | `TC-ATT-02` | `TS-ATT` |
| **SYS-F-011** | Administrative attendance override | `TC-ATT-03` | `TS-ATT` |
| **SYS-F-012** | Student aggregate attendance view | `TC-ATT-04` | `TS-ATT` |
| **SYS-F-013** | Rubric score entry in `Draft` state | `TC-GRD-01` | `TS-GRD` |
| **SYS-F-014** | Submit draft grades with rubric weight | `TC-GRD-02` | `TS-GRD` |
| **SYS-F-015** | Admin grade publication | `TC-GRD-03` | `TS-GRD` |
| **SYS-F-016** | Student regrade request (`Under Review`, once per grade)| `TC-GRD-04` | `TS-GRD` |
| **SYS-F-017** | Resolve regrade dispute and re-publish | `TC-GRD-05` | `TS-GRD` |
| **SYS-F-018** | Student consolidated GPA dashboard | `TC-REP-01` | `TS-PERF` |
| **SYS-F-019** | Faculty class summary analytics | `TC-REP-02` | `TS-PERF` |
| **SYS-F-020** | Admin institution metrics export | `TC-REP-03` | `TS-PERF` |
| **SYS-NF-001**| Latency $\le 800\text{ ms}$ at 95th percentile | `TC-PERF-01` | `TS-PERF` |
| **SYS-NF-002**| 200 concurrent submission transactions | `TC-PERF-02` | `TS-PERF` |
| **SYS-NF-003**| 99.0% operational availability | `TC-OPS-01` | `TS-PERF` |
| **SYS-NF-004**| Responsive UI & $\le 3$ click roll-call | `TC-UX-01` | `TS-AUTH` |
| **SYS-NF-005**| 3-tier separation & $\ge 70\%$ test coverage| `TC-QUAL-01` | `TS-AUTH` |
| **PRJ-SR-001**| Mandatory TLS 1.3 transit encryption | `TC-SEC-01` | `TS-SEC` |
| **PRJ-SR-002**| Bcrypt password hashing (factor 12) | `TC-SEC-02` | `TS-SEC` |
| **PRJ-SR-003**| 48-hour HTTP-only JWT sessions | `TC-SEC-03` | `TS-SEC` |
| **PRJ-SR-004**| Endpoint RBAC middleware check | `TC-SEC-04` | `TS-SEC` |
| **PRJ-SR-005**| Parameterized ORM queries (SQLi/XSS) | `TC-SEC-05` | `TS-SEC` |
