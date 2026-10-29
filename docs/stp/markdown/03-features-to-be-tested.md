# 3. Features to be Tested

Features mapped directly to SRS requirement IDs:

* **`SYS-F-001`:** Admin provisioning of student, faculty, and admin user accounts with temporary credentials.
* **`SYS-F-002`:** Mandatory password reset upon initial login using temporary credentials.
* **`SYS-F-003`:** Student and faculty profile contact details updates.
* **`SYS-F-004`:** Admin updates to user account status and role metadata.
* **`SYS-F-005`:** Course section creation with automatic rubric weight normalization to 100%.
* **`SYS-F-006`:** Student course self-enrollment capped at a maximum of 6 active courses.
* **`SYS-F-007`:** Class schedule creation and timetable publishing.
* **`SYS-F-008`:** Faculty course assignment and roster data isolation.
* **`SYS-F-009`:** Digitized binary roll-call attendance submission by faculty.
* **`SYS-F-010`:** Automated 48-hour modification freeze on attendance sessions post-start.
* **`SYS-F-011`:** Administrative attendance record override and audit logging.
* **`SYS-F-012`:** Student view of aggregate attendance percentages per course.
* **`SYS-F-013`:** Faculty rubric-based mark entry in `Draft` state.
* **`SYS-F-014`:** Faculty grade submission applying weighted rubric normalization.
* **`SYS-F-015`:** Administrative publication of final student course grades.
* **`SYS-F-016`:** Student regrade dispute filing transitioning grade state to `Under Review` (permitted only once per grade; a repeat request is rejected).
* **`SYS-F-017`:** Faculty dispute resolution and grade re-publication (the re-published grade is final).
* **`SYS-F-018`:** Consolidated student GPA calculation and dashboard rendering.
* **`SYS-F-019`:** Faculty class grade distribution analytics summary.
* **`SYS-F-020`:** Administrative export of institution-level performance metrics to CSV.
* **`SYS-NF-001`:** Response time $\le 800\text{ ms}$ for 95% of API requests under 500 active sessions.
* **`SYS-NF-002`:** Support for 200 concurrent attendance/grade submission transactions without database deadlock.
* **`SYS-NF-003`:** 99.0% system availability during active academic terms.
* **`SYS-NF-004`:** Responsive web interface (375px to 1920px) with $\le 3$ click roll-call navigation.
* **`SYS-NF-005`:** Modular 3-tier architecture maintaining $\ge 70\%$ automated test coverage.
