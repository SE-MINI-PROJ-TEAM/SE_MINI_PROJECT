# Smoke test walkthrough

Prerequisites: the app is running (`docker compose up -d --build`, see the root README) and the demo data was seeded **today** with
`docker compose run --rm api python manage.py seed --reset` (session times are relative to the moment of seeding; "open" sessions stay
editable for 48 h). The application is at <http://localhost:8080>.

All seeded accounts use the password `Password@123`. Use a private window per role, or sign out between sections.
Type the email and password on the sign-in page (the one-click demo chips exist only in the Vite development server).

Legend: ✅ expected result.

---

## 0. Health
1. Open <http://localhost:8080/api/v1/health> → ✅ `{"status":"success","features":[…16 packages…]}`.
2. Open <http://localhost:8080> → ✅ the sign-in page, with no "session has ended" warning on a first visit.

## Sprint 1

### US-01 — Admin provisioning (TC-ACC-01)
Sign in as **admin001@srs.edu** → *Create user*.
1. Create: `Test Student`, `test.student@srs.edu`, ID `PES1UG26CS777`, role Student → ✅ a confirmation screen shows a one-time temporary password with a Copy button.
2. Create another user reusing the same **email** → ✅ error under the Email field (409). Reuse the same **ID** → ✅ error under the ID field (409).

### US-02 — Forced password reset (TC-ACC-02, TC-SEC-02)
1. Sign out; sign in as the user you just created with the temporary password (or `new.student@srs.edu` / `Temp@12345`) → ✅ you land on **Set a new password**, not the dashboard. Typing a URL such as `/catalog` bounces you back.
2. Enter a weak password (`abc`) → ✅ the checklist stays red and the button is disabled.
3. Enter a strong one (`Brand#New9pass`) → ✅ routed to the student dashboard; signing in again with the old password fails.

### US-03 — Profile (TC-ACC-03)
Sign in as **student001@srs.edu** → *My profile*.
1. ✅ Institutional ID, role, name and institutional email are shown read-only (lock icons).
2. Enter phone `abc` → ✅ validation error; enter `+91 98765 43210`, personal email `me@example.com`, address, emergency contact → **Save** → ✅ toast; reload the page and the values persist.
3. (API check, optional) `PUT /api/v1/profile` with `{"role":"Admin"}` → ✅ 403 `READ_ONLY_FIELD`.

### US-04 — Account management (TC-ACC-04)
Admin → *Manage users*.
1. Search `student003` → ✅ filtered table. Change a role via the dropdown → ✅ toast.
2. Toggle **Active** off for `student003@srs.edu` → confirm → ✅ badge turns Inactive.
   In a second browser/private window already signed in as student003 any next click/refresh → ✅ signed out with "account deactivated"; login is blocked.
3. Admin → *Audit log* → ✅ `USER_STATUS_CHANGED` row with actor and old/new values.

### US-05 — Course setup & rubric normalisation (TC-CRS-01)
Admin → *Course offerings* → **New course**.
1. Code `CS999`, title `Test Course`, capacity `3`, credits 3, faculty `FAC049`/`FAC050`. Rubric weights `1`, `1`, `1` (the preview badges show 33.34 / 33.33 / 33.33).
2. Create → ✅ the list shows the three components summing to 100 %. Duplicate the same code+section → ✅ conflict error.

### US-06 — Enrollment & 6-course cap (TC-CRS-02)
Sign in as **student001@srs.edu** → *Course catalog* (the counter shows 4 / 6).
1. Enroll in `CS999` → ✅ toast, seat count drops, badge "Enrolled", counter 5 / 6.
2. Enroll in one more section → counter 6 / 6, then try a **7th** → ✅ error toast "at most 6 courses per term".
3. Sign in as **student002@srs.edu** (already at the cap) → try Enroll → ✅ same error.
4. Find the full section (`AI201`, 30 / 30) → ✅ shows *Section full*.
5. Admin → catalog page → switch **Enrollment window** off → student attempts fail with "closed"; switch it back on.

### US-07 — Schedule & roster isolation (TC-CRS-03, TC-CRS-04)
1. Admin → *Manage schedule*: choose `CS999`, today's date, any room, Start/End, repeat 4 weeks → ✅ "4 session(s) scheduled"; they appear in the table. Booking the same room/time again → ✅ conflict.
2. Student (enrolled in CS999) → *Weekly schedule* and dashboard **This week** → ✅ sessions appear. Faculty owning the course sees them too.
3. Faculty **faculty001@srs.edu** → *My sections* → *View roster* → ✅ students of CS101/CS102/CS103 only.
   While still signed in as faculty001, open <http://localhost:8080/api/v1/schedule/roster/20> (a section taught by someone else) → ✅ a JSON 403 with code `NOT_ASSIGNED`, and no student names.

### US-08 — Roll-call & 48 h lock (TC-ATT-01, TC-ATT-02)
Sign in as **faculty001@srs.edu**.
1. Dashboard **Roll-call needed** lists open sessions → click *Take attendance* (2 clicks after login).
2. Toggle a few students to **Absent** → *Save attendance* → ✅ confirmation toast and "Saved".
3. *Take attendance* → **Frozen** tab → open one → ✅ read-only roster with a "frozen" banner. (Sessions older than 48 h cannot be edited — the backend also returns 403 `ATTENDANCE_FROZEN`.)
4. The CS102 / CS103 sessions show a "locks in …" countdown.

## Sprint 2

### US-09 — Admin override (TC-ATT-03)
Admin → *Attendance override* → course `CS101-A`, pick a **frozen** session.
1. Flip a student's value; try **Apply override** with no justification → ✅ blocked (reason required).
2. Enter a reason → Apply → ✅ toast. Admin → *Audit log* → filter `Attendance override` → ✅ entry with old value, new value, reason, admin and timestamp.

### US-10 — Student attendance dashboard (TC-ATT-04)
Student **student001@srs.edu** → dashboard **Attendance** card (or *My attendance*).
1. ✅ Per-course percentages; **CS102** is red with a "Below 75%" badge.
2. Click a course → ✅ total held / attended / missed plus a per-session table.
3. After faculty save roll-call (US-08), refresh → the numbers update.

### US-11 — Draft grade entry (TC-GRD-01)
Faculty **faculty001** → *Grade entry* → **CS103** (draft state).
1. ✅ One column per rubric component; enter/alter scores (0–100) → *Save drafts* → ✅ toast; rows stay `Draft`.
2. Student **student001** dashboard → CS103 shows **Pending** with no marks (hidden while Draft).

### US-12 — Submit & publish (TC-GRD-02, TC-GRD-03)
1. Faculty → open **CS103** → fill every component for a few students → *Submit grades* → ✅ those rows become `Submitted` with a weighted total; incomplete rows stay Draft and are reported.
2. Admin → dashboard **Awaiting publication** / *Publish grades* → select CS102 (47 grades, already submitted) → *Publish selected* → ✅ confirmation.
3. Student **student001** → dashboard **Course grades** → ✅ CS102 now shows total, letter and rubric breakdown immediately.

### US-13 — Regrade dispute (TC-GRD-04, TC-GRD-05)
1. Student **student001** → *My grades* → **CS101** (Published) → **Dispute** → submitting an empty/short reason is blocked → enter a reason → ✅ grade becomes **Under Review**.
2. Faculty **faculty001**: ✅ the *Regrade requests* sidebar item shows a red badge, and the dashboard card counts open requests. Open it, change a score, add a note → *Re-evaluate & re-publish*.
3. Student refreshes → ✅ grade is `Published` again with the new total and the faculty note.
4. ✅ The **Dispute** button is gone, replaced by a "Regrade used · final" badge: a grade can be disputed only **once**. (`student002` shows the same badge on CS101 straight after seeding.)

### US-14 — GPA & analytics (TC-REP-01, TC-REP-02)
1. Student dashboard **Term GPA** → ✅ credit-weighted GPA with letter chips and "Loaded in N ms" (< 800).
2. Faculty → *Class analytics* → ✅ A–F distribution bars, mean, median, graded count and attendance rate per section.

### US-15 — Metrics, CSV, security & performance (TC-REP-03, TC-PERF-*, TC-SEC-*)
1. Admin dashboard **Institution metrics** → ✅ totals; click **Export CSV** → ✅ a `system-metrics-….csv` downloads with one row per course plus a TOTAL row (open it in Excel to see attendance and grade-state columns).
2. Security & performance are verified by the automated suite:
   ```powershell
   cd backend
   ..\.venv\Scripts\python -m pytest tests\admin_metrics -s
   ```
   ✅ TLS/HSTS redirect, HTTP-only 48 h JWT, expired/tampered tokens, RBAC matrix, SQLi/XSS inertness, bcrypt cost 12,
   **200 simultaneous submissions with 0 failures** and **p95 < 800 ms** (the benchmark prints the measured value).
3. Optional manual TLS check: see "HTTPS / TLS 1.3" in the root README.

---

## Cross-cutting checks
* **Responsive**: resize to 375 px → the sidebar becomes a drawer, tables scroll horizontally, forms stack.
* **Theme**: sun/moon button in the top bar switches light/dark (remembered).
* **Keyboard**: Tab reaches every control with a visible focus ring; dialogs trap focus and close on Esc.
* **RBAC in the UI**: a student visiting `/admin/users` sees "You don't have access"; the API returns 403.
* **Session**: after sign-out the browser back button cannot show protected data (API returns 401).

## Full automated suite
```powershell
cd backend
..\.venv\Scripts\python -m pytest --cov --cov-report=term-missing   # ≥ 70 % coverage gate
cd ..\frontend; npm test
```
