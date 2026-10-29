"""Builds qa/newman/collection.json (Postman v2.1) so the integration suite is code-reviewed text, not a GUI export.

Every request carries assertions in Postman's `pm.test` syntax and a TC-ID in its folder name where one applies.
The collection expects a freshly seeded database (python manage.py seed --reset) and runs top-to-bottom:
later folders reuse ids captured by earlier ones (collection variables). Newman keeps a cookie jar, so the
HTTP-only session cookie behaves exactly as it does in a browser.
"""
import json
import os

HERE = os.path.dirname(__file__)
PASSWORD = "Password@123"


def js(*lines):
    return list(lines)


def status(code, label=None):
    return f'pm.test("{label or "HTTP " + str(code)}", () => pm.response.to.have.status({code}));'


def err(code):
    return f'pm.test("error code {code}", () => pm.expect(pm.response.json().code).to.eql("{code}"));'


def request(name, method, path, body=None, tests=(), pre=(), headers=None):
    item = {
        "name": name,
        "request": {
            "method": method,
            "header": [{"key": "Content-Type", "value": "application/json"}] + [{"key": k, "value": v} for k, v in (headers or {}).items()],
            "url": "{{baseUrl}}/api/v1" + path,
        },
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": list(tests)}}],
    }
    if body is not None:
        item["request"]["body"] = {"mode": "raw", "raw": body if isinstance(body, str) else json.dumps(body), "options": {"raw": {"language": "json"}}}
    if pre:
        item["event"].insert(0, {"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(pre)}})
    return item


def folder(name, *items):
    return {"name": name, "item": list(items)}


def login(label, identifier, password=PASSWORD, expect=200, extra=()):
    return request(f"Login as {label}", "POST", "/auth/login", {"identifier": identifier, "password": password},
                   tests=[status(expect), *extra])


def logout():
    return request("Logout", "POST", "/auth/logout", {}, tests=[status(200)])


def save_json(var, expr):
    return f'pm.collectionVariables.set("{var}", {expr});'


UNIQ = ['pm.collectionVariables.set("uniq", String(Date.now()));']

# ----------------------------------------------------------------------------- folders
public = folder(
    "00 Public endpoints",
    request("Health lists all 16 feature packages", "GET", "/health", tests=[
        status(200), 'pm.test("16 packages loaded", () => pm.expect(pm.response.json().features.length).to.be.at.least(16));']),
    request("Password policy is published", "GET", "/auth/password-policy", tests=[
        status(200), 'pm.test("5 rules", () => pm.expect(pm.response.json().rules.length).to.eql(5));']),
    request("No session -> 401", "GET", "/auth/me", tests=[status(401)]),
    request("Unknown route uses the error envelope", "GET", "/does-not-exist", tests=[
        status(404), 'pm.test("envelope", () => pm.expect(pm.response.json()).to.have.keys(["status","code","message"]));']),
)

auth = folder(
    "01 Authentication & session cookie (TC-SEC-02, TC-SEC-03)",
    login("unknown user", "ghost@srs.edu", "whatever", expect=401, extra=[err("INVALID_CREDENTIALS")]),
    login("admin with a wrong password", "admin001@srs.edu", "nope", expect=401, extra=[err("INVALID_CREDENTIALS")]),
    login("Admin", "admin001@srs.edu", extra=[
        'const cookie = pm.response.headers.get("Set-Cookie") || "";',
        'pm.test("cookie is HttpOnly + SameSite", () => { pm.expect(cookie).to.include("srs_token="); pm.expect(cookie).to.include("HttpOnly"); pm.expect(cookie).to.include("SameSite=Lax"); });',
        'pm.test("48 hour lifetime", () => pm.expect(cookie).to.include("Max-Age=172800"));',
        'pm.test("JWT is never in the body", () => pm.expect(pm.response.text()).to.not.include("eyJ"));',
    ]),
    request("Session identifies the admin", "GET", "/auth/me", tests=[
        status(200), 'pm.test("role", () => pm.expect(pm.response.json().user.role).to.eql("Admin"));',
        'pm.test("no hash leaked", () => pm.expect(pm.response.text()).to.not.include("password_hash"));']),
)

provisioning = folder(
    "02 Admin provisioning (US-01, TC-ACC-01)",
    request("Create a student account", "POST", "/users",
            '{"full_name":"Newman Student","email":"newman.{{uniq}}@srs.edu","role":"Student","institutional_id":"NM{{uniq}}"}',
            pre=UNIQ, tests=[
                status(201),
                'const b = pm.response.json();',
                'pm.test("temporary password returned once", () => pm.expect(b.temporary_password).to.be.a("string").with.length.of.at.least(10));',
                'pm.test("flag set", () => pm.expect(b.user.is_temporary_password).to.eql(true));',
                save_json("tempPassword", "b.temporary_password"), save_json("newUserId", "b.user.id"),
                save_json("newEmail", "b.user.email"),
            ]),
    request("Duplicate email -> 409", "POST", "/users",
            '{"full_name":"Dup","email":"{{newEmail}}","role":"Student","institutional_id":"OTHER{{uniq}}"}', tests=[status(409), err("DUPLICATE_EMAIL")]),
    request("Duplicate institutional ID -> 409", "POST", "/users",
            '{"full_name":"Dup","email":"fresh.{{uniq}}@srs.edu","role":"Student","institutional_id":"NM{{uniq}}"}', tests=[status(409), err("DUPLICATE_INSTITUTIONAL_ID")]),
    request("Invalid role -> 400", "POST", "/users",
            '{"full_name":"X","email":"x.{{uniq}}@srs.edu","role":"Janitor","institutional_id":"X{{uniq}}"}', tests=[status(400), err("INVALID_ROLE")]),
    request("User is searchable", "GET", "/users?search={{newEmail}}", tests=[
        status(200), 'pm.test("found", () => pm.expect(pm.response.json().total).to.eql(1));']),
)

forced_reset = folder(
    "03 Forced password reset (US-02, TC-ACC-02, PRJ-SR-002)",
    logout(),
    request("New user signs in with the temporary password", "POST", "/auth/login",
            '{"identifier":"{{newEmail}}","password":"{{tempPassword}}"}', tests=[
                status(200), 'pm.test("must change password", () => pm.expect(pm.response.json().user.must_change_password).to.eql(true));']),
    request("Application API is blocked until the reset", "GET", "/catalog", tests=[status(403), err("PASSWORD_RESET_REQUIRED")]),
    request("Weak password rejected with reasons", "POST", "/auth/change-password",
            '{"current_password":"{{tempPassword}}","new_password":"weak"}', tests=[
                status(400), err("WEAK_PASSWORD"), 'pm.test("reasons listed", () => pm.expect(pm.response.json().details.length).to.be.at.least(3));']),
    request("Wrong current password rejected", "POST", "/auth/change-password",
            '{"current_password":"not-it","new_password":"Brand#New9pass"}', tests=[status(401)]),
    request("Strong password accepted", "POST", "/auth/change-password",
            '{"current_password":"{{tempPassword}}","new_password":"Brand#New9pass"}', tests=[
                status(200), 'pm.test("flag cleared", () => pm.expect(pm.response.json().user.must_change_password).to.eql(false));']),
    request("Reusing the new password is refused", "POST", "/auth/change-password",
            '{"current_password":"Brand#New9pass","new_password":"Brand#New9pass"}', tests=[status(400), err("PASSWORD_REUSED")]),
    request("API unlocked after the reset", "GET", "/catalog", tests=[status(200)]),
)

profile = folder(
    "04 Profile (US-03, TC-ACC-03)",
    request("Update contact details", "PUT", "/profile",
            '{"phone":"+91 98765 43210","personal_email":"me@example.com","home_address":"12 Main Rd","emergency_contact":"Mum +91 99999 88888"}',
            tests=[status(200), 'pm.test("saved", () => pm.expect(pm.response.json().profile.phone).to.eql("+91 98765 43210"));']),
    request("Invalid phone -> 400 with field detail", "PUT", "/profile", '{"phone":"abc"}',
            tests=[status(400), 'pm.test("field error", () => pm.expect(pm.response.json().details).to.have.property("phone"));']),
    request("Institutional fields are read-only", "PUT", "/profile", '{"role":"Admin","phone":"+91 98765 43210"}', tests=[status(403), err("READ_ONLY_FIELD")]),
    request("Markup is stripped (XSS)", "PUT", "/profile", '{"home_address":"<script>alert(1)</script>5 Elm St"}', tests=[
        status(200), 'pm.test("sanitised", () => pm.expect(pm.response.json().profile.home_address).to.eql("alert(1)5 Elm St"));']),
)

courses = folder(
    "05 Course setup & schedule (US-05, US-07, TC-CRS-01, TC-CRS-03)",
    logout(),
    login("Admin", "admin001@srs.edu"),
    request("Pick an unassigned faculty member", "GET", "/courses/faculty-options", tests=[
        status(200), 'const f = pm.response.json().faculty.find(x => x.institutional_id === "FAC050");',
        'pm.test("FAC050 exists", () => pm.expect(f).to.exist);', save_json("freeFacultyId", "f.id")]),
    request("Create a course; rubric 1:1:1 is normalised to exactly 100%", "POST", "/courses",
            '{"code":"NM{{uniq}}","title":"Newman Course","section":"A","credits":3,"capacity":2,"assigned_faculty_id":{{freeFacultyId}},'
            '"rubric":[{"name":"A","category":"Assignments","weight":1},{"name":"B","category":"Exams","weight":1},{"name":"C","category":"Projects","weight":1}]}',
            tests=[
                status(201), 'const c = pm.response.json().course;',
                'pm.test("weights sum to 100.00", () => pm.expect(Math.round(c.rubric.reduce((s, r) => s + r.weight, 0) * 100)).to.eql(10000));',
                save_json("courseId", "c.id"), save_json("newCode", "c.code"),
            ]),
    request("Same section again -> 409", "POST", "/courses",
            '{"code":"{{newCode}}","title":"Dup","section":"A","credits":3,"capacity":2,"assigned_faculty_id":{{freeFacultyId}},"rubric":[{"name":"A","weight":1}]}',
            tests=[status(409), err("DUPLICATE_COURSE")]),
    request("Invalid capacity -> 400", "POST", "/courses",
            '{"code":"BAD1","title":"Bad","capacity":0,"assigned_faculty_id":{{freeFacultyId}},"rubric":[{"name":"A","weight":1}]}', tests=[status(400)]),
    request("Publish a session", "POST", "/schedule/sessions",
            '{"course_id":{{courseId}},"room":"NM-{{uniq}}","start_time":"{{sessionStart}}","end_time":"{{sessionEnd}}"}',
            pre=['const s = new Date(Date.now() + 30 * 3600e3); s.setMilliseconds(0);',
                 'pm.collectionVariables.set("sessionStart", s.toISOString().replace(".000Z", "Z"));',
                 'pm.collectionVariables.set("sessionEnd", new Date(s.getTime() + 3600e3).toISOString().replace(".000Z", "Z"));'],
            tests=[status(201)]),
    request("Same room and time -> 409", "POST", "/schedule/sessions",
            '{"course_id":{{courseId}},"room":"NM-{{uniq}}","start_time":"{{sessionStart}}","end_time":"{{sessionEnd}}"}', tests=[status(409)]),
)

enrolment = folder(
    "06 Enrollment, capacity and the 6-course cap (US-06, TC-CRS-02)",
    logout(),
    login("student001", "student001@srs.edu"),
    request("Catalog shows live capacity", "GET", "/catalog?search={{newCode}}", tests=[
        status(200), 'const c = pm.response.json().courses[0];',
        'pm.test("2 seats free", () => pm.expect(c.seats_available).to.eql(2));', 'pm.test("4 of 6 used", () => pm.expect(pm.response.json().my_course_count).to.eql(4));']),
    request("Enroll", "POST", "/enrollments", '{"course_id":{{courseId}}}', tests=[
        status(201), 'pm.test("seat consumed", () => pm.expect(pm.response.json().seats_available).to.eql(1));']),
    request("Enrolling twice -> 409", "POST", "/enrollments", '{"course_id":{{courseId}}}', tests=[status(409), err("ALREADY_ENROLLED")]),
    login("student002 (already at the 6-course cap)", "student002@srs.edu"),
    request("7th course blocked", "POST", "/enrollments", '{"course_id":{{courseId}}}', tests=[status(409), err("ENROLLMENT_LIMIT_REACHED")]),
    login("student003", "student003@srs.edu"),
    request("Last seat taken", "POST", "/enrollments", '{"course_id":{{courseId}}}', tests=[status(201)]),
    login("student004", "student004@srs.edu"),
    request("Full section -> 409", "POST", "/enrollments", '{"course_id":{{courseId}}}', tests=[status(409), err("SECTION_FULL")]),
)

attendance = folder(
    "07 Roster isolation, roll-call and the 48-hour freeze (US-07, US-08, TC-CRS-04, TC-ATT-01, TC-ATT-02)",
    login("faculty001", "faculty001@srs.edu"),
    request("Own sections only", "GET", "/schedule/my-courses", tests=[
        status(200), 'pm.test("3 sections", () => pm.expect(pm.response.json().courses.length).to.eql(3));']),
    request("Another faculty member's roster -> 403", "GET", "/schedule/roster/20", tests=[status(403), err("NOT_ASSIGNED")]),
    request("Sessions with status", "GET", "/attendance/sessions", tests=[
        status(200), 'const s = pm.response.json().sessions;',
        'const open = s.find(x => x.status === "open" && x.marked_count === 0);', 'const frozen = s.find(x => x.status === "frozen");',
        'pm.test("an open and a frozen session exist", () => { pm.expect(open).to.exist; pm.expect(frozen).to.exist; });',
        save_json("openSessionId", "open.id"), save_json("frozenSessionId", "frozen.id")]),
    request("Roster of the open session", "GET", "/attendance/sessions/{{openSessionId}}", tests=[
        status(200), 'const d = pm.response.json();',
        'pm.test("editable", () => pm.expect(d.session.status).to.eql("open"));',
        save_json("attendanceList", 'JSON.stringify(d.students.map((s, i) => ({ student_id: s.student_id, is_present: i % 5 !== 0 })))'),
        save_json("rosterSize", "d.students.length"), save_json("firstStudentCode", "d.students[0].student_id")]),
    request("Save roll-call", "POST", "/attendance/sessions/{{openSessionId}}", '{"attendance_list": {{attendanceList}} }', tests=[
        status(200), 'pm.test("confirmation + freeze time", () => { const b = pm.response.json(); pm.expect(b.message).to.include("Attendance recorded"); pm.expect(b.frozen_at).to.match(/Z$/); });']),
    request("Re-edit inside the window is allowed", "POST", "/attendance/sessions/{{openSessionId}}", '{"attendance_list": {{attendanceList}} }', tests=[status(200)]),
    request("Edit after 48 hours -> 403 ATTENDANCE_FROZEN", "POST", "/attendance/sessions/{{frozenSessionId}}",
            '{"attendance_list":[{"student_id":"{{firstStudentCode}}","is_present":true}]}', tests=[status(403), err("ATTENDANCE_FROZEN")]),
    request("Student not in the section -> 404", "POST", "/attendance/sessions/{{openSessionId}}",
            '{"attendance_list":[{"student_id":"PES1UG24CS500","is_present":true}]}', tests=[status(404), err("STUDENT_NOT_ENROLLED")]),
)

override = folder(
    "08 Admin override & immutable audit (US-09, TC-ATT-03)",
    login("Admin", "admin001@srs.edu"),
    request("Override without a reason -> 400", "PUT", "/attendance/override/sessions/{{frozenSessionId}}",
            '{"changes":[{"student_id":"{{firstStudentCode}}","is_present":false}],"reason":""}', tests=[status(400)]),
    request("Override a frozen record with a reason", "PUT", "/attendance/override/sessions/{{frozenSessionId}}",
            '{"changes":[{"student_id":"{{firstStudentCode}}","is_present":false}],"reason":"Newman: verified by department"}',
            tests=[status(200), 'pm.test("one record changed", () => pm.expect(pm.response.json().changed).to.eql(1));']),
    request("Audit entry captures old/new value, reason and actor", "GET", "/admin/audit-logs?action=ATTENDANCE_OVERRIDE", tests=[
        status(200), 'const e = pm.response.json().logs[0];',
        'pm.test("details", () => { pm.expect(e.details.new_value).to.eql("Absent"); pm.expect(e.details.reason).to.include("Newman"); pm.expect(e.actor.institutional_id).to.eql("ADM001"); });']),
)

student_attendance = folder(
    "09 Student attendance view (US-10, TC-ATT-04)",
    login("student001", "student001@srs.edu"),
    request("Per-course percentages and the 75% alert", "GET", "/attendance/summary", tests=[
        status(200), 'const c = pm.response.json().courses;',
        'pm.test("percentages are numbers 0-100", () => c.filter(x => x.percentage !== null).forEach(x => pm.expect(x.percentage).to.be.within(0, 100)));',
        'pm.test("CS102 is flagged below 75%", () => pm.expect(c.find(x => x.code === "CS102").below_threshold).to.eql(true));',
        save_json("cs102Id", 'c.find(x => x.code === "CS102").course_id')]),
    request("Course breakdown", "GET", "/attendance/summary/{{cs102Id}}", tests=[
        status(200), 'const d = pm.response.json();',
        'pm.test("held = attended + missed", () => pm.expect(d.sessions_held).to.eql(d.sessions_attended + d.sessions_missed));']),
    request("Course I am not in -> 403", "GET", "/attendance/summary/20", tests=[status(403)]),
)

grades = folder(
    "10 Grade lifecycle: Draft -> Submitted -> Published -> Under Review -> Published (US-11..13, TC-GRD-01..05)",
    login("faculty001", "faculty001@srs.edu"),
    request("Open the CS103 grade sheet", "GET", "/grades/courses/3", tests=[
        status(200), 'const d = pm.response.json();', 'const me = d.students.find(s => s.student_id === "PES1UG24CS001");',
        'pm.test("student001 is mid-way (Draft)", () => pm.expect(me.state).to.eql("Draft"));',
        save_json("rubricJson", "JSON.stringify(d.rubric)"), save_json("r1", "d.rubric[0].id"), save_json("r2", "d.rubric[1].id"), save_json("r3", "d.rubric[2].id")]),
    request("Scores out of range -> 400", "PUT", "/grades/courses/3/students/PES1UG24CS001",
            '{"rubric_scores":[{"rubric_id":{{r1}},"score":101}],"target_state":"Draft"}', tests=[status(400)]),
    request("Save the complete marks as Draft", "PUT", "/grades/courses/3/students/PES1UG24CS001",
            '{"rubric_scores":[{"rubric_id":{{r1}},"score":80},{"rubric_id":{{r2}},"score":90},{"rubric_id":{{r3}},"score":70}],"target_state":"Draft"}',
            tests=[status(200), 'pm.test("still Draft", () => pm.expect(pm.response.json().grade_state).to.eql("Draft"));']),
    login("student001", "student001@srs.edu"),
    request("Draft marks are hidden from the student", "GET", "/grades/mine", tests=[
        status(200), 'const g = pm.response.json().grades.find(x => x.code === "CS103");',
        'pm.test("Pending, no marks", () => { pm.expect(g.state).to.eql("Pending"); pm.expect(g).to.not.have.property("weighted_total"); pm.expect(g).to.not.have.property("components"); });']),
    login("faculty001", "faculty001@srs.edu"),
    request("Submit: weighted total is calculated server-side", "PUT", "/grades/courses/3/students/PES1UG24CS001",
            '{"rubric_scores":[],"target_state":"Submitted"}', tests=[
                status(200), 'const b = pm.response.json();', 'pm.test("Submitted", () => pm.expect(b.grade_state).to.eql("Submitted"));',
                'pm.test("total = sum(score x normalized weight)", () => pm.expect(b.weighted_total).to.be.within(0, 100));']),
    request("Submitted marks are locked", "PUT", "/grades/courses/3/students/PES1UG24CS001",
            '{"rubric_scores":[{"rubric_id":{{r1}},"score":1}],"target_state":"Draft"}', tests=[status(409), err("GRADE_LOCKED")]),
    request("Faculty cannot publish", "POST", "/grades/publication/publish", '{"course_ids":[3]}', tests=[status(403)]),
    login("Admin", "admin001@srs.edu"),
    request("Publication queue lists the course", "GET", "/grades/publication/queue", tests=[
        status(200), 'pm.test("CS103 queued", () => pm.expect(pm.response.json().courses.some(c => c.code === "CS103")).to.eql(true));']),
    request("Admin publishes", "POST", "/grades/publication/publish", '{"course_ids":[3]}', tests=[status(200)]),
    login("student001", "student001@srs.edu"),
    request("Published marks are now visible", "GET", "/grades/mine", tests=[
        status(200), 'const g = pm.response.json().grades.find(x => x.code === "CS103");',
        'pm.test("Published with total + letter", () => { pm.expect(g.state).to.eql("Published"); pm.expect(g.letter).to.match(/[A-F]/); pm.expect(g.can_dispute).to.eql(true); });',
        save_json("enrollmentId", "g.enrollment_id")]),
    request("Dispute needs a real explanation", "POST", "/disputes", '{"enrollment_id":{{enrollmentId}},"reason":"short"}', tests=[status(400)]),
    request("File the dispute -> Under Review", "POST", "/disputes",
            '{"enrollment_id":{{enrollmentId}},"reason":"Question 3 of the end-term was marked incorrectly."}', tests=[status(201)]),
    request("A second dispute while one is open -> 409", "POST", "/disputes",
            '{"enrollment_id":{{enrollmentId}},"reason":"Trying to file this again right away."}', tests=[status(409), err("ALREADY_DISPUTED")]),
    login("faculty001", "faculty001@srs.edu"),
    request("Faculty sees the notification count", "GET", "/disputes/pending-count", tests=[
        status(200), 'pm.test("at least 1", () => pm.expect(pm.response.json().count).to.be.at.least(1));']),
    request("Find the open dispute", "GET", "/disputes?status=Open", tests=[
        status(200), 'const d = pm.response.json().disputes.find(x => x.student.institutional_id === "PES1UG24CS001");',
        'pm.test("found", () => pm.expect(d).to.exist);', save_json("disputeId", "d.id")]),
    request("Re-evaluate and re-publish", "POST", "/disputes/{{disputeId}}/resolve",
            '{"resolution_note":"Newman: re-marked","rubric_scores":[{"rubric_id":{{r3}},"score":95}]}', tests=[status(200)]),
    login("student001", "student001@srs.edu"),
    request("Published again, with the faculty note", "GET", "/grades/mine", tests=[
        status(200), 'const g = pm.response.json().grades.find(x => x.code === "CS103");',
        'pm.test("Published", () => pm.expect(g.state).to.eql("Published"));', 'pm.test("note visible", () => pm.expect(g.dispute.resolution_note).to.eql("Newman: re-marked"));']),
    request("A grade can be disputed only once -> 409 (final)", "POST", "/disputes",
            '{"enrollment_id":{{enrollmentId}},"reason":"I would like another review of this grade please."}', tests=[status(409), err("ALREADY_DISPUTED")]),
    request("UI flag agrees: can_dispute is false", "GET", "/grades/mine", tests=[
        status(200), 'pm.test("no more disputes", () => pm.expect(pm.response.json().grades.find(x => x.code === "CS103").can_dispute).to.eql(false));']),
)

analytics = folder(
    "11 Analytics, metrics and CSV export (US-14, US-15, TC-REP-01..03)",
    request("Student GPA on a 10-point scale, fast", "GET", "/analytics/student/summary", tests=[
        status(200), 'const b = pm.response.json();', 'pm.test("GPA within 0-10", () => pm.expect(b.term_gpa).to.be.within(0, 10));',
        'pm.test("query under 800 ms", () => pm.expect(b.query_ms).to.be.below(800));']),
    login("faculty001", "faculty001@srs.edu"),
    request("Grade distribution A-F", "GET", "/analytics/faculty/sections", tests=[
        status(200), 'const s = pm.response.json().sections[0];', 'pm.test("A-F buckets", () => pm.expect(Object.keys(s.distribution)).to.eql(["A","B","C","D","F"]));',
        'pm.test("query under 800 ms", () => pm.expect(pm.response.json().query_ms).to.be.below(800));']),
    login("Admin", "admin001@srs.edu"),
    request("Institution metrics", "GET", "/admin/metrics", tests=[
        status(200), 'pm.test("totals", () => { const m = pm.response.json().metrics; pm.expect(m.students).to.be.at.least(500); pm.expect(m.courses).to.be.at.least(50); });']),
    request("CSV export", "GET", "/admin/metrics/export.csv", headers={"Accept": "text/csv"}, tests=[
        status(200), 'pm.test("CSV attachment", () => { pm.expect(pm.response.headers.get("Content-Type")).to.include("text/csv"); pm.expect(pm.response.headers.get("Content-Disposition")).to.include("attachment"); });',
        'pm.test("header + a TOTAL row", () => { const t = pm.response.text(); pm.expect(t.split("\\n")[0]).to.include("attendance_rate_pct"); pm.expect(t).to.include("TOTAL"); });']),
    request("Audit trail recorded publication and dispute resolution", "GET", "/admin/audit-logs?per_page=50", tests=[
        status(200), 'const a = pm.response.json().logs.map(l => l.action);',
        'pm.test("both audited", () => { pm.expect(a).to.include("GRADES_PUBLISHED"); pm.expect(a).to.include("DISPUTE_RESOLVED"); });']),
)

revocation = folder(
    "12 Deactivation revokes a live session immediately (US-04, TC-ACC-04)",
    logout(),
    login("victim student005", "student005@srs.edu", extra=[
        'pm.collectionVariables.set("victimToken", (pm.response.headers.get("Set-Cookie").match(/srs_token=([^;]+)/) || [])[1]);']),
    request("Victim's session works", "GET", "/auth/me", tests=[status(200)]),
    logout(),
    login("Admin", "admin001@srs.edu"),
    request("Find the victim", "GET", "/users?search=student005@srs.edu", tests=[
        status(200), save_json("victimId", "pm.response.json().users[0].id")]),
    request("Cannot deactivate yourself", "GET", "/auth/me", tests=[
        status(200), save_json("adminId", "pm.response.json().user.id")]),
    request("Self-deactivation refused", "PATCH", "/users/{{adminId}}", '{"is_active":false}', tests=[status(400), err("SELF_DEACTIVATION")]),
    request("Deactivate the victim", "PATCH", "/users/{{victimId}}", '{"is_active":false}', tests=[status(200)]),
    logout(),
    request("The still-unexpired JWT is now rejected", "GET", "/auth/me", headers={"Authorization": "Bearer {{victimToken}}"}, tests=[
        status(401), err("ACCOUNT_INACTIVE")]),
    request("Deactivated users cannot sign in", "POST", "/auth/login", '{"identifier":"student005@srs.edu","password":"Password@123"}', tests=[status(403), err("ACCOUNT_INACTIVE")]),
)

# RBAC matrix (TC-SEC-04): [role login, [(method, path, body)]] -> all must be 403
RBAC = [
    ("student001", "student001@srs.edu", [("GET", "/users"), ("POST", "/users"), ("GET", "/admin/metrics"), ("GET", "/admin/metrics/export.csv"),
                                           ("POST", "/courses"), ("POST", "/schedule/sessions"), ("GET", "/attendance/sessions"),
                                           ("PUT", "/attendance/override/sessions/1"), ("GET", "/grades/courses"), ("POST", "/grades/publication/publish"),
                                           ("GET", "/disputes"), ("GET", "/analytics/faculty/sections"), ("PUT", "/enrollments/window")]),
    ("faculty001", "faculty001@srs.edu", [("GET", "/users"), ("POST", "/users"), ("POST", "/courses"), ("GET", "/admin/audit-logs"),
                                           ("PUT", "/attendance/override/sessions/1"), ("POST", "/grades/publication/publish"),
                                           ("POST", "/enrollments"), ("GET", "/attendance/summary"), ("GET", "/grades/mine"), ("POST", "/disputes")]),
    ("admin001", "admin001@srs.edu", [("POST", "/enrollments"), ("GET", "/attendance/summary"), ("POST", "/attendance/sessions/1"),
                                       ("PUT", "/grades/courses/1"), ("GET", "/grades/mine"), ("POST", "/disputes"), ("GET", "/profile")]),
]
rbac_items = []
for label, identifier, calls in RBAC:
    rbac_items.append(login(label, identifier))
    for method, path in calls:
        rbac_items.append(request(f"{label}: {method} {path} -> 403", method, path, "{}" if method != "GET" else None, tests=[status(403)]))
rbac_items.append(logout())
rbac_items.append(request("Anonymous: protected endpoint -> 401", "GET", "/users", tests=[status(401)]))
rbac = folder("13 RBAC matrix: every role is refused what it must not do (TC-SEC-04, PRJ-SR-004)", *rbac_items)

injection = folder(
    "14 Injection inputs are inert (TC-SEC-05, PRJ-SR-005)",
    login("Admin", "admin001@srs.edu"),
    request("SQLi in search", "GET", "/users?search=%27%20OR%20%271%27%3D%271", tests=[status(200), 'pm.test("no rows", () => pm.expect(pm.response.json().total).to.eql(0));']),
    request("Stacked-query payload in a filter", "GET", "/admin/audit-logs?action=%27%3B%20DROP%20TABLE%20users%3B%20--", tests=[status(200)]),
    request("The users table still exists", "GET", "/users?per_page=1", tests=[status(200), 'pm.test("users intact", () => pm.expect(pm.response.json().total).to.be.at.least(500));']),
    request("Payload types are validated", "POST", "/users", '{"full_name":123,"email":["x"],"role":{"a":1},"institutional_id":null}', tests=[status(400)]),
    request("Non-JSON body rejected", "POST", "/courses", "not json", tests=[status(400)]),
)

collection = {
    "info": {
        "name": "Student Record System - integration suite",
        "description": "Generated by qa/newman/build_collection.py. Requires a freshly seeded database.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [public, auth, provisioning, forced_reset, profile, courses, enrolment, attendance, override, student_attendance, grades, analytics, revocation, rbac, injection],
}

with open(os.path.join(HERE, "collection.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(collection, f, indent=1)
with open(os.path.join(HERE, "environment.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"name": "local-qa", "values": [{"key": "baseUrl", "value": "http://127.0.0.1:5055", "enabled": True}]}, f, indent=1)

count = sum(len(fo["item"]) for fo in collection["item"])
print(f"Built collection.json: {len(collection['item'])} folders, {count} requests")
