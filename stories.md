# Product Backlog & Sprint Allocation

**Project:** Student Record System

**Team Size:** 3 Developers (Tanmay T A, Uttam B S, Vibha Vasisht)

**Sprint Duration:** 2 Sprints (1 Week per Sprint)

**Total User Stories:** 15 Stories

**Total Committed Story Points:** 46 Points (Sprint 1: 23 pts | Sprint 2: 23 pts)

---

## Executive Summary

| Epic ID | Epic Name | Stories | Total Points | Sprint Allocation |
| --- | --- | --- | --- | --- |
| **EPIC-01** | Identity & Account Management | 4 | **9 pts** | Sprint 1 (9 pts) |
| **EPIC-02** | Course Offering, Enrollment & Scheduling | 3 | **9 pts** | Sprint 1 (9 pts) |
| **EPIC-03** | Attendance Engine & Automated Freeze Rules | 3 | **10 pts** | Sprint 1 (5 pts) / Sprint 2 (5 pts) |
| **EPIC-04** | Rubric Evaluation, Grading & Dispute Workflow | 3 | **13 pts** | Sprint 2 (13 pts) |
| **EPIC-05** | Academic Analytics & Security Infrastructure | 2 | **5 pts** | Sprint 2 (5 pts) |

---

## EPIC 1: Identity & Account Management (`EPIC-01`)

### US-01: Administrative User Provisioning & Credentials

* **Epic:** `EPIC-01: Identity & Account Management`
* **Sprint Allocation:** Sprint 1
* **Story Points:** 3
* **Assignee:** Tanmay T A

```markdown
### User Story
As an Administrator, I want to provision student, faculty, and admin user accounts with generated temporary credentials, so that new users can access the platform.

### Acceptance Criteria

- [ ] Admin UI provides a creation form capturing full name, email, role claim, and institutional ID.
- [ ] System generates a secure temporary password and displays it on-screen upon submission.
- [ ] User record is saved with `is_temporary_password = true`.
- [ ] Duplicate institutional IDs or email entries are rejected with a 409 conflict response.

### Requirement Traceability

- **SRS ID:** `SYS-F-001`
- **Test Case ID:** `TC-ACC-01`
```

---

### US-02: Mandatory Password Reset on Initial Login

* **Epic:** `EPIC-01: Identity & Account Management`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 2

* **Assignee:** Vibha Vasisht

```markdown
### User Story
As a New User, I want to be prompted to change my temporary password upon initial login, so that my account security is ensured.

### Acceptance Criteria

- [ ] Users logging in with temporary credentials are automatically redirected to the Password Reset view.
- [ ] System enforces password complexity rules before accepting submission.
- [ ] Password is hashed using bcrypt (work factor 12) before persisting to the database.
- [ ] Temporary credential flag is cleared and user is routed to their role dashboard.

### Requirement Traceability

- **SRS ID:** `SYS-F-002`, `PRJ-SR-002`
- **Test Case ID:** `TC-ACC-02`, `TC-SEC-02`
```

---

### US-03: Self-Service Profile Contact Details Update

* **Epic:** `EPIC-01: Identity & Account Management`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 2

* **Assignee:** Uttam B S

```markdown
### User Story
As a Student or Faculty Member, I want to update my personal contact details in my profile, so that institutional records remain up to date.

### Acceptance Criteria

- [ ] Profile page displays current contact information and assigned institutional ID.
- [ ] User can edit phone number, emergency contact, and personal email fields.
- [ ] System validates phone number and email formatting prior to saving.
- [ ] Read-only administrative fields (Institutional ID, role) cannot be modified by non-admin users.

### Requirement Traceability

- **SRS ID:** `SYS-F-003`
- **Test Case ID:** `TC-ACC-03`
```

---

### US-04: Admin Account Status & Role Metadata Management

* **Epic:** `EPIC-01: Identity & Account Management`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 2

* **Assignee:** Tanmay T A

```markdown
### User Story
As an Administrator, I want to modify user account status and role metadata, so that inactive accounts can be deactivated.

### Acceptance Criteria

- [ ] Admin interface provides user search and status toggle (Active / Inactive).
- [ ] Deactivating an account revokes active JWT sessions immediately.
- [ ] Account status updates write an entry to the administrative audit log.

### Requirement Traceability

- **SRS ID:** `SYS-F-004`
- **Test Case ID:** `TC-ACC-04`
```

---

## EPIC 2: Course Offering, Enrollment & Scheduling (`EPIC-02`)

### US-05: Course Offering Setup & Rubric Auto-Normalization

* **Epic:** `EPIC-02: Course Offering, Enrollment & Scheduling`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 3

* **Assignee:** Tanmay T A

```markdown
### User Story
As an Administrator, I want to define course offerings and rubric schemes with backend auto-normalization, so that evaluation weights always sum to 100%.

### Acceptance Criteria

- [ ] Admin can register course offerings and set section seat capacities.
- [ ] User can define weighted evaluation components (Assignments, Exams, Projects).
- [ ] Backend automatically normalizes rubric component weights to sum to exactly 100.0% on save.

### Requirement Traceability

- **SRS ID:** `SYS-F-005`
- **Test Case ID:** `TC-CRS-01`
```

---

### US-06: Student Course Self-Enrollment & Capacity Cap Logic

* **Epic:** `EPIC-02: Course Offering, Enrollment & Scheduling`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 3

* **Assignee:** Uttam B S

```markdown
### User Story
As a Student, I want to self-enroll in available course sections up to a limit of 6 courses, so that I can construct my term schedule.

### Acceptance Criteria

- [ ] Course catalog displays open sections with real-time seat capacities.
- [ ] Student can select and enroll in available course sections.
- [ ] System blocks enrollment and displays an error if the student attempts to enroll in > 6 courses.
- [ ] Confirmed enrollments decrement available section capacity immediately.

### Requirement Traceability

- **SRS ID:** `SYS-F-006`
- **Test Case ID:** `TC-CRS-02`
```

---

### US-07: Class Schedule Creation & Faculty Roster Isolation

* **Epic:** `EPIC-02: Course Offering, Enrollment & Scheduling`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 3

* **Assignee:** Uttam B S

```markdown
### User Story
As an Administrator, I want to publish class timetables and restrict faculty roster visibility, so that privacy and scheduling rules are maintained.

### Acceptance Criteria

- [ ] Admin can assign day, time slot, and room location for registered course offerings.
- [ ] Student and faculty dashboards render weekly calendar views populated with scheduled sessions.
- [ ] Faculty members can only access student roster data for courses explicitly assigned to them.

### Requirement Traceability

- **SRS ID:** `SYS-F-007`, `SYS-F-008`
- **Test Case ID:** `TC-CRS-03`, `TC-CRS-04`
```

---

## EPIC 3: Attendance Engine & Automated Freeze Rules (`EPIC-03`)

### US-08: Digitized Binary Roll-Call & 48-Hour Automated Lock

* **Epic:** `EPIC-03: Attendance Engine & Automated Freeze Rules`

* **Sprint Allocation:** Sprint 1

* **Story Points:** 5

* **Assignee:** Vibha Vasisht

```markdown
### User Story
As a Faculty Member, I want to mark binary attendance (Present/Absent) for my course section, so that roll-call records are digitized immediately.

### Acceptance Criteria

- [ ] Roster displays enrolled students for the selected section.
- [ ] Faculty can toggle Present/Absent for each student.
- [ ] Save button persists records to DB and displays confirmation.
- [ ] Re-editing is blocked if the session start time is > 48 hours.

### Requirement Traceability

- **SRS ID:** `SYS-F-009`, `SYS-F-010`
- **Test Case ID:** `TC-ATT-01`, `TC-ATT-02`
```

---

### US-09: Administrative Attendance Override & Audit Logging

* **Epic:** `EPIC-03: Attendance Engine & Automated Freeze Rules`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 3

* **Assignee:** Uttam B S

```markdown
### User Story
As an Administrator, I want to override frozen attendance records with audit logging, so that legitimate attendance disputes can be rectified.

### Acceptance Criteria

- [ ] Admin user can edit attendance records even after the 48-hour freeze window.
- [ ] System requires entry of a mandatory justification reason prior to saving.
- [ ] Every override creates an immutable audit log entry capturing admin ID, old value, new value, and timestamp.

### Requirement Traceability

- **SRS ID:** `SYS-F-011`
- **Test Case ID:** `TC-ATT-03`
```

---

### US-10: Aggregate Attendance Dashboard Views

* **Epic:** `EPIC-03: Attendance Engine & Automated Freeze Rules`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 2

* **Assignee:** Uttam B S

```markdown
### User Story
As a Student, I want to view my aggregate attendance percentage per course, so that I can monitor my course attendance compliance.

### Acceptance Criteria

- [ ] Student dashboard displays attendance percentage per enrolled course.
- [ ] Course view breaks down total sessions held, sessions attended, and sessions missed.
- [ ] Visual alert indicator highlights courses where attendance drops below 75%.

### Requirement Traceability

- **SRS ID:** `SYS-F-012`
- **Test Case ID:** `TC-ATT-04`
```

---

## EPIC 4: Rubric Evaluation, Grading & Dispute Workflow (`EPIC-04`)

### US-11: Rubric Score Entry in Draft State

* **Epic:** `EPIC-04: Rubric Evaluation, Grading & Dispute Workflow`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 3

* **Assignee:** Tanmay T A

```markdown
### User Story
As a Faculty Member, I want to enter and edit numerical rubric component scores in a draft state, so that I can grade assignments progressively.

### Acceptance Criteria

- [ ] Interface renders configured rubric components for each enrolled student.
- [ ] Faculty can enter and save partial or complete numeric scores in `Draft` state.
- [ ] Students cannot view marks while the grade state remains `Draft`.

### Requirement Traceability

- **SRS ID:** `SYS-F-013`
- **Test Case ID:** `TC-GRD-01`
```

---

### US-12: Weighted Grade Submission & Administrative Publication

* **Epic:** `EPIC-04: Rubric Evaluation, Grading & Dispute Workflow`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 5

* **Assignee:** Tanmay T A

```markdown
### User Story
As a Faculty Member and Administrator, I want grades submitted with rubric weighting and published, so that official marks are released to students.

### Acceptance Criteria

- [ ] Submitting draft grades calculates weighted totals and transitions state to `Submitted`.
- [ ] Admin dashboard provides batch publication action for courses in `Submitted` state.
- [ ] Transitioning state to `Published` renders grades visible on student dashboards immediately.

### Requirement Traceability

- **SRS ID:** `SYS-F-014`, `SYS-F-015`
- **Test Case ID:** `TC-GRD-02`, `TC-GRD-03`
```

---

### US-13: Student Regrade Dispute Filing & Resolution

* **Epic:** `EPIC-04: Rubric Evaluation, Grading & Dispute Workflow`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 5

* **Assignee:** Vibha Vasisht

```markdown
### User Story
As a Student, I want to file a regrade dispute on a published grade, so that faculty can re-evaluate my score submission.

### Acceptance Criteria

- [ ] Dispute button is accessible next to published course grades on the student dashboard.
- [ ] Student must enter a required explanation/justification string prior to filing.
- [ ] Submitting the dispute transitions the grade state to `Under Review`.
- [ ] Faculty member receives notification indicator, re-evaluates score, and re-publishes updated grade.

### Requirement Traceability

- **SRS ID:** `SYS-F-016`, `SYS-F-017`
- **Test Case ID:** `TC-GRD-04`, `TC-GRD-05`
```

---

## EPIC 5: Academic Analytics & Security Infrastructure (`EPIC-05`)

### US-14: Consolidated GPA & Faculty Analytics Dashboards

* **Epic:** `EPIC-05: Academic Analytics & Security Infrastructure`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 3

* **Assignee:** Vibha Vasisht

```markdown
### User Story
As a Student or Faculty Member, I want to view term GPA summaries and class grade distributions, so that academic performance is transparent.

### Acceptance Criteria

- [ ] Student dashboard renders consolidated term GPA calculated from credit-weighted published grades.
- [ ] Faculty dashboard displays grade distribution charts (grade brackets A–F) per course section.
- [ ] Dashboard analytics queries execute and render in < 800 ms.

### Requirement Traceability

- **SRS ID:** `SYS-F-018`, `SYS-F-019`
- **Test Case ID:** `TC-REP-01`, `TC-REP-02`
```

---

### US-15: Admin Metrics CSV Export & Security Benchmark Suite

* **Epic:** `EPIC-05: Academic Analytics & Security Infrastructure`

* **Sprint Allocation:** Sprint 2

* **Story Points:** 2

* **Assignee:** Tanmay T A

```markdown
### User Story
As an Administrator, I want to export system metrics to CSV and ensure security compliance, so that performance and data privacy SLAs are met.

### Acceptance Criteria

- [ ] Admin dashboard provides a single-click button exporting system attendance and grade metrics to CSV.
- [ ] TLS 1.3 encryption, HTTP-only 48-hour JWT sessions, and parameterized ORM queries are enforced across all API endpoints.
- [ ] Automated concurrency test verifies 200 simultaneous submissions execute without DB deadlock.

### Requirement Traceability

- **SRS ID:** `SYS-F-020`, `SYS-NF-001` – `SYS-NF-005`, `PRJ-SR-001` – `PRJ-SR-005`
- **Test Case ID:** `TC-REP-03`, `TC-PERF-01`, `TC-PERF-02`, `TC-SEC-01` – `TC-SEC-05`
```
