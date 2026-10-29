# System Features (Detailed Functional Requirements)

## Module 1: Account Provisioning & User Profile

| Req ID | Requirement Statement | Type | Priority | Source / Stakeholder | Acceptance Criteria / Test Ref | Comments / Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-001** | The system shall allow Administrators to provision user accounts with assigned roles (Student, Faculty, Admin) and display initial temporary login credentials on a dedicated confirmation screen upon creation within 2 seconds. | Functional | High | Admin | AC-SYS-F-001: Admin creates account; temporary credentials display on screen once. Test: TC-ACC-01 | Requires Admin RBAC privilege. |
| **SYS-F-002** | The system shall mandate users logging in with temporary credentials to update their account password before granting access to application features. | Functional | High | Security | AC-SYS-F-002: Login with temporary password forces redirect to password change screen. Test: TC-ACC-02 | Depends on SYS-F-001. |
| **SYS-F-003** | The system shall allow logged-in Students and Faculty to view and update their personal contact details (phone number, home address, emergency contact) at any time. | Functional | Medium | Student / Faculty | AC-SYS-F-003: Profile updates persist in database and display immediately upon saving. Test: TC-ACC-03 | Accessible by account owner. |
| **SYS-F-004** | The system shall allow Administrators to view user account metadata, reassign roles, or deactivate user accounts across the institution. | Functional | High | Admin | AC-SYS-F-004: Deactivated accounts are blocked from logging in within 1 second. Test: TC-ACC-04 | Admin privilege required. |

## Module 2: Course Setup, Self-Enrollment & Schedule Management

| Req ID | Requirement Statement | Type | Priority | Source / Stakeholder | Acceptance Criteria / Test Ref | Comments / Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-005** | The system shall allow Administrators to register course offerings, set section capacity limits, assign primary faculty, and set weighted rubric evaluation schemes with backend auto-normalization to 100%. | Functional | High | Admin / Faculty | AC-SYS-F-005: Course created with assigned faculty; raw rubric weights normalize to 100% automatically. Test: TC-CRS-01 | Baseline for grading. |
| **SYS-F-006** | The system shall allow Students to self-enroll in up to 6 active course sections during an open enrollment window set by the Administrator. | Functional | High | Student | AC-SYS-F-006: Student can enroll up to 6 courses; 7th attempt or full section attempt is rejected. Test: TC-CRS-02 | Requires active registration window. |
| **SYS-F-007** | The system shall allow Administrators to create class schedule sessions defining course section, date, start/end time, room, and assigned instructor. | Functional | High | Admin | AC-SYS-F-007: Created schedule populates calendar views for instructor and enrolled students. Test: TC-CRS-03 | Requires registered course sections. |
| **SYS-F-008** | The system shall restrict Faculty roster visibility and session access to only those course sections assigned to them by the Administrator. | Functional | High | Faculty | AC-SYS-F-008: Faculty dashboard displays only assigned sections; unauthorized access returns HTTP 403. Test: TC-CRS-04 | RBAC enforcement. |

## Module 3: Digitized Attendance Marking & Freeze Constraints

| Req ID | Requirement Statement | Type | Priority | Source / Stakeholder | Acceptance Criteria / Test Ref | Comments / Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-009** | The system shall allow Faculty to mark binary attendance (Present/Absent) for enrolled students during scheduled sessions assigned to them. | Functional | High | Faculty | AC-SYS-F-009: Attendance submission saves entries for enrolled students in valid assigned session. Test: TC-ATT-01 | Depends on SYS-F-007, SYS-F-008. |
| **SYS-F-010** | The system shall automatically lock attendance modification rights for Faculty exactly 48 hours after a session's scheduled start time. | Functional | High | Operations | AC-SYS-F-010: Faculty edit controls disable 48h post-session; backend rejects edits post-48h. Test: TC-ATT-02 | Automated timestamp validation. |
| **SYS-F-011** | The system shall allow Administrators to override and modify locked attendance records beyond the 48-hour window. | Functional | Medium | Admin | AC-SYS-F-011: Admin updates locked attendance record with administrative audit record. Test: TC-ATT-03 | Admin privilege required. |
| **SYS-F-012** | The system shall display aggregate and session-by-session attendance percentages to Students for all currently enrolled courses. | Functional | High | Student | AC-SYS-F-012: Attendance percentages update within 1s of Faculty submission. Test: TC-ATT-04 | Depends on SYS-F-009. |

## Module 4: Weighted Rubric Grading & Grade Lifecycle

| Req ID | Requirement Statement | Type | Priority | Source / Stakeholder | Acceptance Criteria / Test Ref | Comments / Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-013** | The system shall allow Faculty to record numeric marks against predefined rubric components for enrolled students, saving initial entries in `Draft` state. | Functional | High | Faculty | AC-SYS-F-013: Marks saved in `Draft` state remain hidden from student accounts. Test: TC-GRD-01 | Depends on SYS-F-005. |
| **SYS-F-014** | The system shall allow Faculty to submit draft grades, calculating total course scores based on normalized rubric weights and transitioning state to `Submitted`. | Functional | High | Faculty | AC-SYS-F-014: Total score calculates accurately; grade state transitions to `Submitted`. Test: TC-GRD-02 | Depends on SYS-F-013. |
| **SYS-F-015** | The system shall allow Administrators to publish `Submitted` grades, changing state to `Published` and rendering final grades visible on student dashboards. | Functional | High | Admin / Student | AC-SYS-F-015: Grade state updates to `Published`; grades display on student dashboard. Test: TC-GRD-03 | Admin approval step. |
| **SYS-F-016** | The system shall allow Students to submit regrade requests for `Published` grades, transitioning the grade state to `Under Review`. A grade may be disputed only once; once its dispute has been resolved and the grade re-published, further regrade requests for that grade shall be rejected. | Functional | Medium | Student | AC-SYS-F-016: Dispute text attaches; state updates to `Under Review` on Faculty/Admin view; a second regrade request for the same grade is rejected. Test: TC-GRD-04 | Student challenge workflow. |
| **SYS-F-017** | The system shall allow Faculty or Admin to resolve `Under Review` disputes by adjusting rubric marks and re-publishing the finalized grade. | Functional | Medium | Faculty / Admin | AC-SYS-F-017: Rubric marks recalculate; state transitions back to `Published`, which is final (the grade cannot be disputed again). Test: TC-GRD-05 | Resolution workflow. |

## Module 5: Analytics & Summary Reporting

| Req ID | Requirement Statement | Type | Priority | Source / Stakeholder | Acceptance Criteria / Test Ref | Comments / Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-F-018** | The system shall render a consolidated academic dashboard for Students summarizing overall GPA, individual course grades, and attendance rates within 800 ms. | Functional | High | Student | AC-SYS-F-018: Student dashboard loads current GPA, grades, and attendance within 800ms. Test: TC-REP-01 | Consolidated view. |
| **SYS-F-019** | The system shall generate class summary reports for Faculty displaying grade distributions and attendance averages per assigned section. | Functional | Medium | Faculty | AC-SYS-F-019: Class summary view displays section mean, median, and attendance rate. Test: TC-REP-02 | Faculty analytics. |
| **SYS-F-020** | The system shall allow Administrators to export institution-level summary metrics detailing total enrollments, unsubmitted grades, and attendance rates. | Functional | Medium | Admin | AC-SYS-F-020: Admin view generates institution metrics across active courses within 2s. Test: TC-REP-03 | Executive reporting. |
