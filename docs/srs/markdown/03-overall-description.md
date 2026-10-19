# Overall Description

## Product Perspective
The Academic Management & Record System is an independent, responsive web service designed to replace paper-based academic tracking across a higher education institution of approximately 10,000 students and staff. It operates in a standard 3-tier web architecture consisting of a modern single-page client interface, a RESTful API application server with middleware role-based access control, and a relational SQL database store.

## Major Product Functions
* **Account Provisioning & Profile Management:** Administrative creation of Student, Faculty, and Admin accounts; mandatory password changes upon first login; self-service contact detail updates.
* **Course Offering & Self-Enrollment:** Administrative course registration, assignment of primary faculty, setting evaluation rubrics (with backend auto-normalization to 100%), and student self-enrollment (capped at 6 courses per term).
* **Schedule & Roll-Call Attendance:** Class schedule publishing; digitized instructor roll-call; 48-hour automated attendance freeze; administrative override capability.
* **Weighted Rubric Grading Workflow:** Faculty mark entry against weighted components; transition through state lifecycle (`Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Published`); student regrade request dispute workflow (`Under Review`).
* **Academic Dashboards:** Real-time student GPA and attendance metrics; class grade distribution summaries; administrative institution-level reporting.

## User Roles and Characteristics

| Role | Characteristics & Responsibilities |
| :--- | :--- |
| **Student** | Enrolls in up to 6 active courses during registration windows; views session-by-session attendance and grade distributions; submits regrade dispute requests; updates personal contact information. |
| **Faculty** | Conducts class roll-calls for assigned sessions; updates attendance within 48 hours; inputs rubric marks; submits draft grades for administrative review; resolves student regrade requests. |
| **Administrator** | Provisions user accounts; creates courses and schedule sessions; sets evaluation rubrics; publishes finalized grades; executes administrative attendance overrides; manages account operational states. |

## Operating Environment
* **Server Environment:** Linux container execution environment (Docker) running Python application services and MySQL relational database.
* **Client Environment:** Responsive web browser (Google Chrome, Mozilla Firefox, Apple Safari, Microsoft Edge) operating on devices with screen widths from 375px to 1920px.
* **Network Infrastructure:** Standard institutional WAN/LAN with mandatory HTTPS (TLS 1.3) traffic routing.

## Constraints
* **Agile Sprint Scope:** Implementation is bounded by 2 one-week-long Agile sprints delivered by a 3-student engineering team.
* **Zero Mail Automation:** External SMTP server setup is excluded; temporary credentials must be rendered directly on administrative confirmation UI views.
* **Hard 48-Hour Attendance Freeze:** Faculty attendance edit permissions are strictly revoked 48 hours post-session by automated backend time checks.
* **Course Limits:** Student enrollment is capped at a strict upper limit of 6 courses per academic term.
