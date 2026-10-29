# UAT results

| Field | Value |
| --- | --- |
| Application version / commit | 897e172 + uncommitted working tree; Docker images built from this working tree |
| Test environment | Docker (`docker-compose.qa.yml`): MySQL 8 + gunicorn API + nginx (HTTP, TLS 1.3 on 443) + headless Chromium 1280x720, Asia/Kolkata, freshly seeded database |
| Tester(s) | Tanmay T A, Uttam B S, Vibha Vasisht |
| Date(s) | 2026-10-28 17:27 UTC |

Result values: `PASS` · `FAIL` · `BLOCKED` (leave empty if not yet executed).

## Acceptance criteria

| ID | Acceptance criterion | Result | Defect # | Comment |
| --- | --- | --- | --- | --- |
| US-01.1 | Admin UI provides a creation form capturing full name, email, role claim, and institutional ID. | PASS |  | Form shows Full name, Email, Institutional ID and a Role selector offering Student / Faculty / Admin. |
| US-01.2 | System generates a secure temporary password and displays it on-screen upon submission. | PASS |  | Confirmation screen shows a 12-character password mixing upper/lower case, digits and symbols, with a warning that it is shown only once. |
| US-01.3 | User record is saved with `is_temporary_password = true`. | PASS |  | User list marks the account "Temp password"; a direct database query returns is_temporary_password = 1. |
| US-01.4 | Duplicate institutional IDs or email entries are rejected with a 409 conflict response. | PASS |  | Duplicate email -> HTTP 409 DUPLICATE_EMAIL; duplicate ID -> HTTP 409 DUPLICATE_INSTITUTIONAL_ID; the form shows the error next to the field. |
| US-02.1 | Users logging in with temporary credentials are automatically redirected to the Password Reset view. | PASS |  | After signing in with the temporary password the user lands on "Set a new password"; navigating to /catalog bounces back to it. |
| US-02.2 | System enforces password complexity rules before accepting submission. | PASS |  | "abc" meets 1 of 5 rules, so the button stays disabled; the server independently rejects it with 400 WEAK_PASSWORD and lists 4 unmet rules. |
| US-02.3 | Password is hashed using bcrypt (work factor 12) before persisting to the database. | PASS |  | Database value begins "$2b$12$" (bcrypt, cost 12) and is 60 characters; the plain password is not stored. |
| US-02.4 | Temporary credential flag is cleared and user is routed to their role dashboard. | PASS |  | After the reset the student dashboard is shown; the database flag is 0 and the API reports must_change_password = false. |
| US-03.1 | Profile page displays current contact information and assigned institutional ID. | PASS |  | Profile lists institutional ID UAT0001, institutional email and the editable contact fields. |
| US-03.2 | User can edit phone number, emergency contact, and personal email fields. | PASS |  | Saved with a confirmation toast; after a full page reload all three values are still there. |
| US-03.3 | System validates phone number and email formatting prior to saving. | PASS |  | Invalid phone and email show inline errors and nothing is saved; the server also answers 400 VALIDATION_FAILED. |
| US-03.4 | Read-only administrative fields (Institutional ID, role) cannot be modified by non-admin users. | PASS |  | The UI shows these fields as locked text. A forged API request is refused with 403 READ_ONLY_FIELD and the role / ID are unchanged. |
| US-04.1 | Admin interface provides user search and status toggle (Active / Inactive). | PASS |  | Searching by email narrows the list to one user whose Active switch is on. |
| US-04.2 | Deactivating an account revokes active JWT sessions immediately. | PASS |  | A student signed in elsewhere was sent to the sign-in page with "account deactivated" on their very next request, and signing in again returns 403. |
| US-04.3 | Account status updates write an entry to the administrative audit log. | PASS |  | Audit log row: "User status changed" by ADM001 for PES1UG24CS009, old = Active, new = Inactive, with a timestamp. |
| US-05.1 | Admin can register course offerings and set section seat capacities. | PASS |  | Course UAT101 created with capacity 3 and assigned faculty FAC050; the list shows 0 / 3 seats filled. |
| US-05.2 | User can define weighted evaluation components (Assignments, Exams, Projects). | PASS |  | Saved rubric has three components in the categories Assignments, Exams and Projects. |
| US-05.3 | Backend automatically normalizes rubric component weights to sum to exactly 100.0% on save. | PASS |  | Raw weights 1 : 1 : 1 were saved as 33.34 + 33.33 + 33.33 = 100.00 exactly (the extra cent goes to the largest remainder). |
| US-06.1 | Course catalog displays open sections with real-time seat capacities. | PASS |  | UAT101 card shows "3 of 3 seats open"; the header shows this student is enrolled in 4 of 6 courses. |
| US-06.2 | Student can select and enroll in available course sections. | PASS |  | Enrollment succeeded with a confirmation toast and the card now shows an "Enrolled" badge. |
| US-06.3 | System blocks enrollment and displays an error if the student attempts to enroll in > 6 courses. | PASS |  | A student already on 6 courses sees the error "You can enroll in at most 6 courses per term"; a direct API call returns 409 ENROLLMENT_LIMIT_REACHED. |
| US-06.4 | Confirmed enrollments decrement available section capacity immediately. | PASS |  | After the enrollment the section shows "2 of 3 seats open" and the student counter moved from 4 / 6 to 5 / 6. |
| US-07.1 | Admin can assign day, time slot, and room location for registered course offerings. | PASS |  | Published UAT101 for 2026-10-29 10:00-11:00 in room UAT-R1; it appears in the scheduled-sessions table. |
| US-07.2 | Student and faculty dashboards render weekly calendar views populated with scheduled sessions. | PASS |  | The enrolled student sees UAT101 (room UAT-R1) in the dashboard "This week" card and in the weekly calendar page; the assigned faculty member sees it on their dashboard. |
| US-07.3 | Faculty members can only access student roster data for courses explicitly assigned to them. | PASS |  | "My sections" lists exactly the 3 sections assigned to faculty001; the roster of a section taught by someone else returns 403 NOT_ASSIGNED with no student data. |
| US-08.1 | Roster displays enrolled students for the selected section. | PASS |  | The roll-call opened from the dashboard widget lists 50 enrolled students with their institutional IDs. |
| US-08.2 | Faculty can toggle Present/Absent for each student. | PASS |  | Rows 2 and 5 were switched to Absent (highlighted red); the others remain Present. |
| US-08.3 | Save button persists records to DB and displays confirmation. | PASS |  | Toast "Attendance recorded for N students"; after a full reload the two Absent marks are still stored. |
| US-08.4 | Re-editing is blocked if the session start time is > 48 hours. | PASS |  | A frozen session opens read-only with a banner, the toggles are disabled and there is no Save button; bypassing the UI with a direct API call returns 403 ATTENDANCE_FROZEN. |
| US-09.1 | Admin user can edit attendance records even after the 48-hour freeze window. | PASS |  | A frozen session (faculty cannot edit) was corrected by the admin: first student Present -> Absent. |
| US-09.2 | System requires entry of a mandatory justification reason prior to saving. | PASS |  | Applying without a reason is refused in the UI ("a justification of at least 5 characters is required") and by the API (400); nothing was changed. |
| US-09.3 | Every override creates an immutable audit log entry capturing admin ID, old value, new value, and timestamp. | PASS |  | Entry shows admin ADM001, old value "Present", new value "Absent", the reason and a timestamp. There is no edit or delete endpoint (PUT/PATCH/DELETE -> 404/405) and the ORM rejects updates to audit rows. |
| US-10.1 | Student dashboard displays attendance percentage per enrolled course. | PASS |  | The Attendance card lists 5 enrolled courses; the 4 that have held sessions each show a percentage and a progress bar (the course joined moments ago has no session yet and shows 0 attended / 0 missed / 0 held). |
| US-10.2 | Course view breaks down total sessions held, sessions attended, and sessions missed. | PASS |  | CS102: 12 sessions held = 6 attended + 6 missed, with a per-session table. |
| US-10.3 | Visual alert indicator highlights courses where attendance drops below 75%. | PASS |  | Only CS102 (below 75%) carries the red "Below 75%" badge, plus a page-level warning; the other courses are not flagged. |
| US-11.1 | Interface renders configured rubric components for each enrolled student. | PASS |  | CS103 sheet: one column per rubric component (Assignments 10%, Capstone Project 40%, Final Exam 50%) for each of the enrolled students. |
| US-11.2 | Faculty can enter and save partial or complete numeric scores in `Draft` state. | PASS |  | One student saved with a single score, another with all three; after a reload both persist and show state "Draft". |
| US-11.3 | Students cannot view marks while the grade state remains `Draft`. | PASS |  | student001 has Draft marks in CS103 but sees only "Pending - marks will appear here once published"; no numbers are shown. |
| US-12.1 | Submitting draft grades calculates weighted totals and transitions state to `Submitted`. | PASS |  | 80 / 90 / 70 with weights 10 / 40 / 50 gives a weighted total of 79.00 (8 + 36 + 35); the row moved to "Submitted" and its inputs are locked. |
| US-12.2 | Admin dashboard provides batch publication action for courses in `Submitted` state. | PASS |  | The publication queue listed CS103 (and the other submitted course); the batch action published it and it left the queue. |
| US-12.3 | Transitioning state to `Published` renders grades visible on student dashboards immediately. | PASS |  | Immediately after publication student001 sees CS103 as Published with total 79.00 and letter C. |
| US-13.1 | Dispute button is accessible next to published course grades on the student dashboard. | PASS |  | The Dispute button sits in the CS103 row next to the published grade. |
| US-13.2 | Student must enter a required explanation/justification string prior to filing. | PASS |  | Submitting with an empty explanation shows "Please explain your request in at least 10 characters" and the grade stays Published. |
| US-13.3 | Submitting the dispute transitions the grade state to `Under Review`. | PASS |  | With an explanation the request is filed; CS103 shows "Under Review" and the Dispute button disappears. |
| US-13.4 | Faculty member receives notification indicator, re-evaluates score, and re-publishes updated grade. | PASS |  | Faculty saw the red notification badge, re-scored the first component (80 -> 95) and re-published. The student sees Published, total 79.00 -> 80.50 (letter B), the faculty note, and the "Regrade used" badge: a second dispute is no longer possible. |
| US-14.1 | Student dashboard renders consolidated term GPA calculated from credit-weighted published grades. | PASS |  | Displayed GPA 9.14 / 10 equals sum(grade points x credits) / sum(credits) = 9.14 over 7 credits of published grades (A=10, B=8, C=6, D=4, F=0). |
| US-14.2 | Faculty dashboard displays grade distribution charts (grade brackets A–F) per course section. | PASS |  | Three sections, each with an A / B / C / D / F histogram plus mean, median, graded count and attendance rate. |
| US-14.3 | Dashboard analytics queries execute and render in < 800 ms. | PASS |  | Server-side query time reported on screen: student GPA 1.8 ms, faculty analytics 6.2 ms (limit 800 ms); the load test measured p95 = 30 ms at 500 sessions. |
| US-15.1 | Admin dashboard provides a single-click button exporting system attendance and grade metrics to CSV. | PASS |  | One click downloaded system-metrics-20261028-172743.csv with 51 course rows plus a TOTAL row, containing attendance rates and grade-state counts. |
| US-15.2 | TLS 1.3 encryption, HTTP-only 48-hour JWT sessions, and parameterized ORM queries are enforced across all API endpoints. | PASS |  | Handshake with a TLS 1.2-only client is refused (C0ACA61FFC7A0000:error:0A00042E:SSL routines:ssl3_read_bytes:tlsv1 alert protocol version:../deps/openssl/openssl/ssl/record/rec_layer_s3.c:918:SSL alert number 70 ); TLS 1.3 connects (TLSv1.3). Over HTTPS the login cookie is HttpOnly + Secure + SameSite=Lax with a 48 h lifetime, HSTS is sent, and the token is not in the response body. A SQL-injection payload in a search returns 0 rows and the users table is intact (parameterised ORM queries). |
| US-15.3 | Automated concurrency test verifies 200 simultaneous submissions execute without DB deadlock. | PASS |  | Evidence from the k6 run of 2026-10-28T17:13:41.217Z: 200 simultaneous attendance + grade submissions across 12 server processes -> 200 accepted, 0 failed, 0 HTTP errors (also covered by the PyTest concurrency test). |

## Exploratory sessions

Time-boxed (15 min each). Write down anything surprising, even if it is not a defect.

| Charter | Tester | Findings / defects |
| --- | --- | --- |
| Try to break the grade lifecycle as a **student** (skip states, dispute twice, read other students' marks) | Tanmay T A | Edit marks / publish / submit / self-resolve / list users all returned 403; a second dispute returned 409 ALREADY_DISPUTED; another student's enrollment returned 404; /grades/mine exposes only the caller's data. No weakness found. |
| Try to see or change **another faculty member's** sections, rosters and marks | Uttam B S | Grade sheet, save marks, submit and roster of a foreign section all returned 403; the dispute list only contains the faculty member's own courses (CS103, CS101). No weakness found. |
| Use the whole app with the **keyboard only** (no mouse), then at **375 px** width | Vibha Vasisht | Signed in and reached the content using only the keyboard (skip link works: focus moved into main = true); at 375 px four pages have no horizontal scroll and the drawer opens from the keyboard. |
| Enter **hostile input** in every text field (very long text, `<script>`, quotes, emoji, negative numbers) | Tanmay T A | Seven hostile strings (script tags, an event-handler image, SQL, 5,000 characters, 60 emoji, a template expression, a negative number) were submitted through the account form, the user search and the course form: no JavaScript dialog, no uncaught page error, no HTTP 5xx. The stored name for the `<script>` payload is "alert(1)" (markup stripped). |
| Run **two sessions at once** (two browsers) and edit the same attendance sheet / grade sheet | Uttam B S | Two browser sessions saved the same roll-call within the same instant (conflicting values for one student): both saves succeeded, the roster has 50 unique rows, no HTTP 5xx; the last write wins (3 students absent in the final state). |

## Defect log

| Issue # | Criterion | Severity | Summary | Status |
| --- | --- | --- | --- | --- |
| DEF-1 (found by EX-3) | Exploratory | Low | "Skip to content" link scrolled to the page body but did not move keyboard focus into it, because `<main>` was not focusable (WCAG 2.4.1 usability). Fixed: `tabIndex={-1}` on `<main id="main">` in `AppShell.jsx`; EX-3 now asserts it. | Fixed, verified in the final run |

## Sign-off

The undersigned has witnessed the execution above and accepts the system as:

- [ ] **Accepted**
- [ ] **Accepted with conditions**
- [ ] **Rejected**

Conditions / remarks:

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Customer / Course Instructor | Dr. Adithya Balasubramanyam | | |
| QA Lead | Vibha Vasisht | Vibha Vasisht | 30-10-2026 |
| Test Engineer | Uttam B S | Uttam B S | 30-10-2026 |
| Developer | Tanmay T A | Tanmay T A | 30-10-2026 |
