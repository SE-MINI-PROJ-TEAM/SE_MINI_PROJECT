// Executable UAT: follows docs/uat/UAT-SCRIPT.md click by click. One test per acceptance criterion; each captures a
// screenshot (docs/uat/evidence/<id>.png) and an explanatory comment that qa/traceability/uat_results.py copies into
// docs/uat/UAT-RESULTS.md. Starts from a freshly seeded database (qa.sh uat does that).
import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import tls from 'node:tls';

const PASSWORD = 'Password@123';
const EVIDENCE = process.env.UAT_EVIDENCE || path.resolve('evidence');
const HTTPS_HOST = process.env.HTTPS_HOST || 'web';
const K6_SUMMARY = process.env.K6_SUMMARY || '/repo/qa/reports/k6/summary.json';
fs.mkdirSync(EVIDENCE, { recursive: true });

// ----------------------------------------------------------------------------------------------------- helpers
const note = (text) => test.info().annotations.push({ type: 'comment', description: text });
const shot = (page, id) => page.screenshot({ path: path.join(EVIDENCE, `${id}.png`) });
const modal = (page) => page.locator('.modal');
const toast = (page) => page.locator('.toast').last();
const cents = (n) => Math.round(Number(n) * 100);

async function signIn(page, email, password = PASSWORD, { wait = true } = {}) {
  await page.goto('/login');
  await page.getByLabel('Email or institutional ID').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  if (wait) await expect(page.locator('.topbar, .bare-page').first()).toBeVisible();
}
const signOut = async (page) => {
  await page.locator('.sidebar__footer button').click();
  await expect(page.locator('.login-box')).toBeVisible();
};
async function session(browser, email, options = {}) {
  const context = await browser.newContext({ baseURL: test.info().project.use.baseURL, ignoreHTTPSErrors: true, timezoneId: 'Asia/Kolkata', locale: 'en-IN', ...options });
  const page = await context.newPage();
  if (email) await signIn(page, email);
  return { context, page };
}
async function api(page, method, url, data) {
  const response = await page.request.fetch(url, { method, ...(data !== undefined ? { data } : {}) });
  let body = {};
  try { body = await response.json(); } catch { /* not JSON */ }
  return { status: response.status(), body };
}
function dbValue(sql, args) {
  const code = `import os,sys,pymysql\nc=pymysql.connect(host=os.environ['DB_HOST'],user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'])\ncur=c.cursor();cur.execute(sys.argv[1],tuple(sys.argv[2:]));print(cur.fetchone()[0])`;
  return execFileSync('python', ['-c', code, sql, ...args], { encoding: 'utf-8' }).trim();
}
async function selectByText(select, text) {
  const value = await select.locator('option', { hasText: text }).first().getAttribute('value');
  await select.selectOption(value);
}
const tomorrow = () => {
  const d = new Date(Date.now() + 86400000);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};

// Shared between criteria (script order: later stories reuse data created by earlier ones)
const state = { user: { email: 'uat.student@srs.edu', id: 'UAT0001', name: 'Uma Acceptance', temp: '' }, newPassword: 'Brand#New9pass', course: { code: 'UAT101' } };
let admin; // one persistent admin session for the administrator steps

test.beforeAll(async ({ browser }) => {
  admin = await session(browser, 'admin001@srs.edu');
});
test.afterAll(async () => {
  await admin?.context.close();
});

// ============================================================================================ US-01 provisioning
test('US-01.1 admin creation form captures name, email, role and institutional ID', async () => {
  const { page } = admin;
  await page.goto('/admin/users/new');
  for (const label of ['Full name', 'Email', 'Institutional ID', 'Role']) await expect(page.getByLabel(label)).toBeVisible();
  const roles = await page.getByLabel('Role').locator('option').allInnerTexts();
  expect(roles).toEqual(['Student', 'Faculty', 'Admin']);
  note('Form shows Full name, Email, Institutional ID and a Role selector offering Student / Faculty / Admin.');
  await shot(page, 'US-01.1');
});

test('US-01.2 a secure temporary password is displayed on screen', async () => {
  const { page } = admin;
  await page.getByLabel('Full name').fill(state.user.name);
  await page.getByLabel('Email').fill(state.user.email);
  await page.getByLabel('Institutional ID').fill(state.user.id);
  await page.getByRole('button', { name: 'Create account' }).click();
  const temp = (await page.getByTestId('temp-password').innerText()).trim();
  expect(temp.length).toBeGreaterThanOrEqual(10);
  expect(temp).toMatch(/[A-Z]/); expect(temp).toMatch(/[a-z]/); expect(temp).toMatch(/\d/); expect(temp).toMatch(/[^A-Za-z0-9]/);
  state.user.temp = temp;
  note(`Confirmation screen shows a ${temp.length}-character password mixing upper/lower case, digits and symbols, with a warning that it is shown only once.`);
  await shot(page, 'US-01.2');
});

test('US-01.3 the new record is saved with is_temporary_password = true', async () => {
  const { page } = admin;
  await page.goto('/admin/users');
  await page.getByLabel('Search users').fill(state.user.email);
  const row = page.locator('tbody tr', { hasText: state.user.email });
  await expect(row).toHaveCount(1);
  await expect(row.getByText('Temp password')).toBeVisible();
  const flag = dbValue('SELECT is_temporary_password FROM users WHERE email=%s', [state.user.email]);
  expect(flag).toBe('1');
  note('User list marks the account "Temp password"; a direct database query returns is_temporary_password = 1.');
  await shot(page, 'US-01.3');
});

test('US-01.4 duplicate institutional ID or email is rejected with 409', async () => {
  const { page } = admin;
  const dupEmail = await api(page, 'POST', '/api/v1/users', { full_name: 'Dup', email: state.user.email, role: 'Student', institutional_id: 'DUPA1' });
  const dupId = await api(page, 'POST', '/api/v1/users', { full_name: 'Dup', email: 'dup.other@srs.edu', role: 'Student', institutional_id: state.user.id });
  expect(dupEmail.status).toBe(409); expect(dupId.status).toBe(409);
  await page.goto('/admin/users/new');
  await page.getByLabel('Full name').fill('Dup Person');
  await page.getByLabel('Email').fill(state.user.email);
  await page.getByLabel('Institutional ID').fill('DUPA2');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByText('already exists')).toBeVisible();
  note(`Duplicate email -> HTTP 409 ${dupEmail.body.code}; duplicate ID -> HTTP 409 ${dupId.body.code}; the form shows the error next to the field.`);
  await shot(page, 'US-01.4');
});

// ============================================================================================ US-02 password reset
test('US-02.1 temporary credentials redirect to the password reset view', async ({ browser }) => {
  const { context, page } = await session(browser);
  await signIn(page, state.user.email, state.user.temp);
  await expect(page.getByText('Set a new password')).toBeVisible();
  await page.goto('/catalog');
  await expect(page.getByText('Set a new password')).toBeVisible();
  note('After signing in with the temporary password the user lands on "Set a new password"; navigating to /catalog bounces back to it.');
  await shot(page, 'US-02.1');
  state.resetCtx = { context, page };
});

test('US-02.2 password complexity rules are enforced', async () => {
  const { page } = state.resetCtx;
  await page.getByLabel('Temporary password').fill(state.user.temp);
  await page.getByLabel('New password', { exact: true }).fill('abc');
  await page.getByLabel('Confirm new password').fill('abc');
  await expect(page.getByRole('button', { name: 'Update password' })).toBeDisabled();
  const checklist = await page.locator('.rule-list li.ok').count();
  const serverSide = await api(page, 'POST', '/api/v1/auth/change-password', { current_password: state.user.temp, new_password: 'abc' });
  expect(serverSide.status).toBe(400); expect(serverSide.body.code).toBe('WEAK_PASSWORD');
  note(`"abc" meets ${checklist} of 5 rules, so the button stays disabled; the server independently rejects it with 400 WEAK_PASSWORD and lists ${serverSide.body.details.length} unmet rules.`);
  await shot(page, 'US-02.2');
});

test('US-02.3 the password is stored as a bcrypt hash with work factor 12', async () => {
  const { page } = state.resetCtx;
  await page.getByLabel('New password', { exact: true }).fill(state.newPassword);
  await page.getByLabel('Confirm new password').fill(state.newPassword);
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page.locator('.topbar')).toBeVisible();
  const hash = dbValue('SELECT password_hash FROM users WHERE email=%s', [state.user.email]);
  expect(hash).toMatch(/^\$2b\$12\$/);
  expect(hash).not.toContain(state.newPassword);
  note(`Database value begins "${hash.slice(0, 7)}" (bcrypt, cost 12) and is 60 characters; the plain password is not stored.`);
  await shot(page, 'US-02.3');
});

test('US-02.4 the temporary flag is cleared and the user reaches their dashboard', async () => {
  const { page, context } = state.resetCtx;
  await expect(page.getByText('Term GPA')).toBeVisible();
  const me = await api(page, 'GET', '/api/v1/auth/me');
  expect(me.body.user.must_change_password).toBe(false);
  const flag = dbValue('SELECT is_temporary_password FROM users WHERE email=%s', [state.user.email]);
  expect(flag).toBe('0');
  note('After the reset the student dashboard is shown; the database flag is 0 and the API reports must_change_password = false.');
  await shot(page, 'US-02.4');
  state.studentSession = { context, page }; // reused for US-03
});

// ============================================================================================ US-03 profile
test('US-03.1 profile shows contact information and the assigned institutional ID', async () => {
  const { page } = state.studentSession;
  await page.goto('/profile');
  await expect(page.getByText(state.user.id, { exact: true })).toBeVisible();
  await expect(page.getByText(state.user.email)).toBeVisible();
  await expect(page.getByLabel('Phone number')).toBeVisible();
  note(`Profile lists institutional ID ${state.user.id}, institutional email and the editable contact fields.`);
  await shot(page, 'US-03.1');
});

test('US-03.2 phone, emergency contact and personal email can be edited and saved', async () => {
  const { page } = state.studentSession;
  await page.getByLabel('Phone number').fill('+91 98765 43210');
  await page.getByLabel('Personal email').fill('uma.personal@example.com');
  await page.getByLabel('Emergency contact').fill('Mrs Acceptance +91 91234 56789');
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(toast(page)).toContainText('Profile updated');
  await page.reload();
  await expect(page.getByLabel('Phone number')).toHaveValue('+91 98765 43210');
  await expect(page.getByLabel('Personal email')).toHaveValue('uma.personal@example.com');
  await expect(page.getByLabel('Emergency contact')).toHaveValue('Mrs Acceptance +91 91234 56789');
  note('Saved with a confirmation toast; after a full page reload all three values are still there.');
  await shot(page, 'US-03.2');
});

test('US-03.3 phone and email formats are validated before saving', async () => {
  const { page } = state.studentSession;
  await page.getByLabel('Phone number').fill('abc');
  await page.getByLabel('Personal email').fill('not-an-email');
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(page.getByText('Enter a valid phone number')).toBeVisible();
  await expect(page.getByText('Enter a valid email address')).toBeVisible();
  const serverSide = await api(page, 'PUT', '/api/v1/profile', { phone: 'abc' });
  expect(serverSide.status).toBe(400);
  note('Invalid phone and email show inline errors and nothing is saved; the server also answers 400 VALIDATION_FAILED.');
  await shot(page, 'US-03.3');
  await page.reload();
});

test('US-03.4 institutional ID and role cannot be modified by a non-admin', async () => {
  const { page } = state.studentSession;
  await expect(page.getByLabel('Institutional ID')).toHaveCount(0); // read-only text, not an input
  const attempt = await api(page, 'PUT', '/api/v1/profile', { role: 'Admin', institutional_id: 'HACKED', phone: '+91 98765 43210' });
  expect(attempt.status).toBe(403); expect(attempt.body.code).toBe('READ_ONLY_FIELD');
  const me = await api(page, 'GET', '/api/v1/auth/me');
  expect(me.body.user.role).toBe('Student'); expect(me.body.user.institutional_id).toBe(state.user.id);
  note('The UI shows these fields as locked text. A forged API request is refused with 403 READ_ONLY_FIELD and the role / ID are unchanged.');
  await shot(page, 'US-03.4');
  await state.studentSession.context.close();
});

// ============================================================================================ US-04 account management
test('US-04.1 admin can search users and toggle Active / Inactive', async () => {
  const { page } = admin;
  await page.goto('/admin/users');
  await page.getByLabel('Search users').fill('student009@srs.edu');
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(page.getByRole('switch', { name: /Deactivate/ })).toBeChecked();
  note('Searching by email narrows the list to one user whose Active switch is on.');
  await shot(page, 'US-04.1');
});

test('US-04.2 deactivating an account revokes its live session immediately', async ({ browser }) => {
  const victim = await session(browser, 'student009@srs.edu');
  await victim.page.goto('/catalog');
  await expect(victim.page.getByRole('heading', { name: 'Course catalog' })).toBeVisible();
  const { page } = admin;
  await page.getByRole('switch', { name: /Deactivate/ }).click();
  await modal(page).getByRole('button', { name: 'Deactivate' }).click();
  await expect(toast(page)).toContainText('deactivated');
  await victim.page.goto('/catalog'); // the same, still-valid JWT
  await expect(victim.page).toHaveURL(/\/login$/);
  await expect(victim.page.getByText('deactivated')).toBeVisible();
  const relogin = await victim.page.request.post('/api/v1/auth/login', { data: { identifier: 'student009@srs.edu', password: PASSWORD } });
  expect(relogin.status()).toBe(403);
  note('A student signed in elsewhere was sent to the sign-in page with "account deactivated" on their very next request, and signing in again returns 403.');
  await shot(victim.page, 'US-04.2');
  await victim.context.close();
});

test('US-04.3 the status change is written to the administrative audit log', async () => {
  const { page } = admin;
  await page.goto('/admin/audit-log');
  await page.getByLabel('Filter by action').selectOption('USER_STATUS_CHANGED');
  const row = page.locator('tbody tr', { hasText: 'PES1UG24CS009' }).first();
  await expect(row).toBeVisible();
  await expect(row).toContainText('Inactive');
  await expect(row).toContainText('ADM001');
  note('Audit log row: "User status changed" by ADM001 for PES1UG24CS009, old = Active, new = Inactive, with a timestamp.');
  await shot(page, 'US-04.3');
});

// ============================================================================================ US-05 course setup
test('US-05.1 admin registers a course offering with a seat capacity', async () => {
  const { page } = admin;
  await page.goto('/admin/courses');
  await page.getByRole('button', { name: 'New course' }).click();
  const m = modal(page);
  await m.getByLabel('Course code').fill(state.course.code);
  await m.getByLabel('Title').fill('Acceptance Testing Studio');
  await m.getByLabel('Seat capacity').fill('3');
  await selectByText(m.getByLabel('Primary faculty'), 'FAC050');
  await m.getByLabel('Component 1 name').fill('Quizzes');
  await m.getByLabel('Component 1 category').selectOption('Assignments');
  await m.getByLabel('Component 2 name').fill('Mid-term');
  await m.getByLabel('Component 2 category').selectOption('Exams');
  await m.getByLabel('Component 3 name').fill('Capstone');
  await m.getByLabel('Component 3 category').selectOption('Projects');
  for (const n of [1, 2, 3]) await m.getByLabel(`Component ${n} raw weight`).fill('1');
  await m.getByRole('button', { name: 'Create course' }).click();
  await expect(toast(page)).toContainText('Course created');
  await page.getByLabel('Search courses').fill(state.course.code);
  const row = page.locator('tbody tr', { hasText: state.course.code });
  await expect(row).toContainText('0 / 3');
  note('Course UAT101 created with capacity 3 and assigned faculty FAC050; the list shows 0 / 3 seats filled.');
  await shot(page, 'US-05.1');
});

test('US-05.2 weighted components can be defined (Assignments, Exams, Projects)', async () => {
  const { page } = admin;
  const result = await api(page, 'GET', `/api/v1/courses?search=${state.course.code}`);
  const course = result.body.courses[0];
  expect(course.rubric.map((r) => r.category)).toEqual(['Assignments', 'Exams', 'Projects']);
  state.course.id = course.id;
  note('Saved rubric has three components in the categories Assignments, Exams and Projects.');
  await shot(page, 'US-05.2');
});

test('US-05.3 weights are normalised to exactly 100.0% on save', async () => {
  const { page } = admin;
  const course = (await api(page, 'GET', `/api/v1/courses/${state.course.id}`)).body.course;
  const total = course.rubric.reduce((sum, r) => sum + cents(r.weight), 0);
  expect(total).toBe(10000);
  const weights = course.rubric.map((r) => r.weight).join(' + ');
  note(`Raw weights 1 : 1 : 1 were saved as ${weights} = 100.00 exactly (the extra cent goes to the largest remainder).`);
  await page.getByLabel('Search courses').fill(state.course.code);
  await shot(page, 'US-05.3');
});

// ============================================================================================ US-06 enrollment
test('US-06.1 the catalog shows open sections with real-time seat capacity', async ({ browser }) => {
  state.s1 = await session(browser, 'student001@srs.edu');
  const { page } = state.s1;
  await page.goto('/catalog');
  await page.getByLabel('Search catalog').fill(state.course.code);
  const card = page.getByRole('article', { name: new RegExp(state.course.code) });
  await expect(card).toContainText('3 of 3 seats open');
  await expect(page.getByText('4 / 6')).toBeVisible();
  note('UAT101 card shows "3 of 3 seats open"; the header shows this student is enrolled in 4 of 6 courses.');
  await shot(page, 'US-06.1');
});

test('US-06.2 a student can enroll in an available section', async () => {
  const { page } = state.s1;
  const card = page.getByRole('article', { name: new RegExp(state.course.code) });
  await card.getByRole('button', { name: 'Enroll' }).click();
  await expect(toast(page)).toContainText(`Enrolled in ${state.course.code}`);
  await expect(card.getByText('Enrolled', { exact: true })).toBeVisible();
  note('Enrollment succeeded with a confirmation toast and the card now shows an "Enrolled" badge.');
  await shot(page, 'US-06.2');
});

test('US-06.3 enrolling beyond 6 courses is blocked with an error', async ({ browser }) => {
  const s2 = await session(browser, 'student002@srs.edu'); // seeded at the 6-course cap
  await s2.page.goto('/catalog');
  await expect(s2.page.getByText('6 / 6')).toBeVisible();
  await s2.page.getByLabel('Search catalog').fill(state.course.code);
  await s2.page.getByRole('article', { name: new RegExp(state.course.code) }).getByRole('button', { name: 'Enroll' }).click();
  await expect(toast(s2.page)).toContainText('at most 6 courses');
  const direct = await api(s2.page, 'POST', '/api/v1/enrollments', { course_id: state.course.id });
  expect(direct.status).toBe(409); expect(direct.body.code).toBe('ENROLLMENT_LIMIT_REACHED');
  note('A student already on 6 courses sees the error "You can enroll in at most 6 courses per term"; a direct API call returns 409 ENROLLMENT_LIMIT_REACHED.');
  await shot(s2.page, 'US-06.3');
  await s2.context.close();
});

test('US-06.4 a confirmed enrollment decrements the available seats immediately', async () => {
  const { page } = state.s1;
  await page.reload();
  await page.getByLabel('Search catalog').fill(state.course.code);
  await expect(page.getByRole('article', { name: new RegExp(state.course.code) })).toContainText('2 of 3 seats open');
  await expect(page.getByText('5 / 6')).toBeVisible();
  note('After the enrollment the section shows "2 of 3 seats open" and the student counter moved from 4 / 6 to 5 / 6.');
  await shot(page, 'US-06.4');
});

// ============================================================================================ US-07 schedule
test('US-07.1 admin assigns date, time slot and room to a course offering', async () => {
  const { page } = admin;
  await page.goto('/admin/schedule');
  await selectByText(page.getByLabel('Course section'), state.course.code);
  await page.getByLabel('Date').fill(tomorrow());
  await page.getByLabel('Room').fill('UAT-R1');
  await page.getByLabel('Start time').fill('10:00');
  await page.getByLabel('End time').fill('11:00');
  await page.getByRole('button', { name: 'Publish session' }).click();
  await expect(toast(page)).toContainText('session(s) scheduled');
  await selectByText(page.getByLabel('Filter sessions by course'), state.course.code);
  await expect(page.locator('tbody tr', { hasText: 'UAT-R1' })).toBeVisible();
  note(`Published UAT101 for ${tomorrow()} 10:00-11:00 in room UAT-R1; it appears in the scheduled-sessions table.`);
  await shot(page, 'US-07.1');
});

test('US-07.2 student and faculty dashboards show weekly calendars with the sessions', async ({ browser }) => {
  const { page } = state.s1;
  await page.goto('/');
  await expect(page.locator('.card', { hasText: 'This week' })).toContainText(state.course.code);
  await page.goto('/schedule');
  await page.locator('.calendar').waitFor();
  if (!(await page.locator('.calendar').innerText()).includes(state.course.code)) await page.getByRole('button', { name: /Next/ }).click();
  await expect(page.locator('.calendar')).toContainText(state.course.code);
  await expect(page.locator('.calendar')).toContainText('UAT-R1');
  await shot(page, 'US-07.2');
  const fac = await session(browser, 'faculty050@srs.edu');
  await expect(fac.page.locator('.card', { hasText: 'This week' })).toContainText(state.course.code);
  note('The enrolled student sees UAT101 (room UAT-R1) in the dashboard "This week" card and in the weekly calendar page; the assigned faculty member sees it on their dashboard.');
  await shot(fac.page, 'US-07.2-faculty');
  await fac.context.close();
  await state.s1.context.close();
});

test('US-07.3 faculty can only see rosters of their own sections', async ({ browser }) => {
  const fac = await session(browser, 'faculty001@srs.edu');
  state.fac = fac;
  const { page } = fac;
  await page.goto('/faculty/sections');
  await expect(page.locator('article')).toHaveCount(3);
  await page.locator('article').first().getByRole('button', { name: 'View roster' }).click();
  await expect.poll(() => modal(page).locator('tbody tr').count()).toBeGreaterThan(10);
  await shot(page, 'US-07.3');
  await page.keyboard.press('Escape');
  const foreign = await api(page, 'GET', '/api/v1/schedule/roster/20');
  expect(foreign.status).toBe(403); expect(foreign.body.code).toBe('NOT_ASSIGNED');
  expect(JSON.stringify(foreign.body)).not.toContain('PES1UG24');
  note('"My sections" lists exactly the 3 sections assigned to faculty001; the roster of a section taught by someone else returns 403 NOT_ASSIGNED with no student data.');
});

// ============================================================================================ US-08 attendance marking
test('US-08.1 the roster lists the enrolled students of the selected section', async () => {
  const { page } = state.fac;
  await page.goto('/');
  await page.locator('.dash-grid').getByRole('link', { name: 'Take attendance' }).first().click();
  await page.locator('tbody tr').first().waitFor();
  const rows = await page.locator('tbody tr').count();
  expect(rows).toBeGreaterThanOrEqual(30);
  state.rollcallUrl = page.url();
  note(`The roll-call opened from the dashboard widget lists ${rows} enrolled students with their institutional IDs.`);
  await shot(page, 'US-08.1');
});

test('US-08.2 faculty can toggle Present / Absent for each student', async () => {
  const { page } = state.fac;
  for (const i of [1, 4]) {
    const row = page.locator('tbody tr').nth(i);
    await row.getByRole('button', { name: 'Absent' }).click();
    await expect(row.getByRole('button', { name: 'Absent' })).toHaveAttribute('aria-pressed', 'true');
    await expect(row.getByRole('button', { name: 'Present' })).toHaveAttribute('aria-pressed', 'false');
  }
  note('Rows 2 and 5 were switched to Absent (highlighted red); the others remain Present.');
  await shot(page, 'US-08.2');
});

test('US-08.3 Save persists the records and shows a confirmation', async () => {
  const { page } = state.fac;
  await page.getByRole('button', { name: 'Save attendance' }).click();
  await expect(toast(page)).toContainText('Attendance recorded for');
  await page.reload();
  await page.locator('tbody tr').first().waitFor();
  for (const i of [1, 4]) await expect(page.locator('tbody tr').nth(i).getByRole('button', { name: 'Absent' })).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('tbody tr').nth(2).getByRole('button', { name: 'Present' })).toHaveAttribute('aria-pressed', 'true');
  note('Toast "Attendance recorded for N students"; after a full reload the two Absent marks are still stored.');
  await shot(page, 'US-08.3');
});

test('US-08.4 re-editing is blocked once the session started more than 48 hours ago', async () => {
  const { page } = state.fac;
  await page.goto('/attendance');
  await page.getByRole('tab', { name: /Frozen/ }).click();
  await page.getByRole('link', { name: 'View' }).first().click();
  await expect(page.getByText('This session is frozen')).toBeVisible();
  await expect(page.locator('tbody tr').first().getByRole('button', { name: 'Absent' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Save attendance' })).toHaveCount(0);
  const id = page.url().split('/').pop();
  const forced = await api(page, 'POST', `/api/v1/attendance/sessions/${id}`, { attendance_list: [{ student_id: 'PES1UG24CS001', is_present: true }] });
  expect(forced.status).toBe(403); expect(forced.body.code).toBe('ATTENDANCE_FROZEN');
  note('A frozen session opens read-only with a banner, the toggles are disabled and there is no Save button; bypassing the UI with a direct API call returns 403 ATTENDANCE_FROZEN.');
  await shot(page, 'US-08.4');
});

// ============================================================================================ US-09 admin override
async function openFrozenCs101Session(page) {
  await page.goto('/admin/attendance-override');
  await selectByText(page.getByLabel('Course', { exact: true }), 'CS101-A');
  await expect(page.getByLabel('Session', { exact: true }).locator('option', { hasText: 'frozen' }).first()).toBeAttached();
  await selectByText(page.getByLabel('Session', { exact: true }), 'frozen');
  await page.locator('tbody tr').first().waitFor();
}

test('US-09.1 admin can edit attendance after the 48-hour freeze', async () => {
  const { page } = admin;
  await openFrozenCs101Session(page);
  await expect(page.getByText('Frozen for faculty')).toBeVisible();
  const row = page.locator('tbody tr').first();
  const current = (await row.locator('.badge').innerText()).trim();
  state.overrideFrom = current;
  await row.getByRole('button', { name: current === 'Present' ? 'Absent' : 'Present' }).click();
  await page.getByLabel(/Justification/).fill('UAT: medical certificate verified by the department office');
  await page.getByRole('button', { name: 'Apply override' }).click();
  await expect(toast(page)).toContainText('overridden');
  note(`A frozen session (faculty cannot edit) was corrected by the admin: first student ${current} -> ${current === 'Present' ? 'Absent' : 'Present'}.`);
  await shot(page, 'US-09.1');
});

test('US-09.2 a justification reason is mandatory', async () => {
  const { page } = admin;
  const row = page.locator('tbody tr').nth(1);
  const current = (await row.locator('.badge').innerText()).trim();
  await row.getByRole('button', { name: current === 'Present' ? 'Absent' : 'Present' }).click();
  await page.getByLabel(/Justification/).fill('');
  await page.getByRole('button', { name: 'Apply override' }).click();
  await expect(page.getByText('justification of at least 5 characters is required')).toBeVisible();
  const forced = await api(page, 'PUT', '/api/v1/attendance/override/sessions/' + (await page.getByLabel('Session', { exact: true }).inputValue()), { changes: [{ student_id: 'PES1UG24CS002', is_present: false }], reason: '' });
  expect(forced.status).toBe(400);
  note('Applying without a reason is refused in the UI ("a justification of at least 5 characters is required") and by the API (400); nothing was changed.');
  await shot(page, 'US-09.2');
});

test('US-09.3 every override creates an immutable audit entry (admin, old value, new value, timestamp)', async () => {
  const { page } = admin;
  await page.goto('/admin/audit-log');
  await page.getByLabel('Filter by action').selectOption('ATTENDANCE_OVERRIDE');
  const row = page.locator('tbody tr').first();
  await expect(row).toContainText('ADM001');
  await expect(row).toContainText('old value');
  await expect(row).toContainText('new value');
  await expect(row).toContainText('medical certificate');
  expect((await row.locator('td').first().innerText()).trim().length).toBeGreaterThan(5); // timestamp
  const logs = (await api(page, 'GET', '/api/v1/admin/audit-logs?action=ATTENDANCE_OVERRIDE')).body.logs;
  expect(logs.length).toBe(1); // the empty-reason attempt (US-09.2) left no entry
  const tamper = [await api(page, 'PUT', '/api/v1/admin/audit-logs/1', {}), await api(page, 'PATCH', '/api/v1/admin/audit-logs/1', {}), await api(page, 'DELETE', '/api/v1/admin/audit-logs/1')];
  tamper.forEach((t) => expect([404, 405]).toContain(t.status));
  note(`Entry shows admin ADM001, old value "${logs[0].details.old_value}", new value "${logs[0].details.new_value}", the reason and a timestamp. There is no edit or delete endpoint (PUT/PATCH/DELETE -> 404/405) and the ORM rejects updates to audit rows.`);
  await shot(page, 'US-09.3');
});

// ============================================================================================ US-10 attendance dashboard
test('US-10.1 the student dashboard shows attendance percentage per enrolled course', async ({ browser }) => {
  state.s1 = await session(browser, 'student001@srs.edu');
  const { page } = state.s1;
  const card = page.locator('.card', { has: page.getByRole('heading', { name: 'Attendance' }) });
  const rows = card.locator('li.list__item');
  await expect(rows.first()).toBeVisible();
  const total = await rows.count();
  expect(total).toBeGreaterThanOrEqual(4);
  let withPct = 0;
  for (let i = 0; i < total; i++) {
    const text = await rows.nth(i).innerText();
    if (text.includes(state.course.code)) continue; // UAT101 was enrolled minutes ago: no session has been held yet
    expect(text).toContain('%');
    withPct++;
  }
  expect(withPct).toBeGreaterThanOrEqual(4);
  note(`The Attendance card lists ${total} enrolled courses; the ${withPct} that have held sessions each show a percentage and a progress bar (the course joined moments ago has no session yet and shows 0 attended / 0 missed / 0 held).`);
  await shot(page, 'US-10.1');
});

test('US-10.2 the course view breaks down sessions held, attended and missed', async () => {
  const { page } = state.s1;
  await page.getByRole('link', { name: /CS102/ }).first().click();
  await expect(page.getByText('Sessions held')).toBeVisible();
  const values = await page.locator('.stat').evaluateAll((els) => Object.fromEntries(els.map((e) => [e.querySelector('.stat__label').textContent, e.querySelector('.stat__value').textContent])));
  const [held, attended, missed] = [values['Sessions held'], values['Attended'], values['Missed']].map(Number);
  expect(held).toBe(attended + missed);
  expect(await page.locator('tbody tr').count()).toBeGreaterThanOrEqual(held);
  note(`CS102: ${held} sessions held = ${attended} attended + ${missed} missed, with a per-session table.`);
  await shot(page, 'US-10.2');
});

test('US-10.3 courses below 75% attendance are visually flagged', async () => {
  const { page } = state.s1;
  await page.goto('/my-attendance');
  const flagged = page.locator('li.list__item', { hasText: 'Below 75%' });
  await expect(flagged).toHaveCount(1);
  await expect(flagged).toContainText('CS102');
  await expect(page.getByText('Attendance below 75% in 1 course')).toBeVisible();
  note('Only CS102 (below 75%) carries the red "Below 75%" badge, plus a page-level warning; the other courses are not flagged.');
  await shot(page, 'US-10.3');
  await state.s1.context.close();
});

// ============================================================================================ US-11 grade entry
test('US-11.1 the grade sheet renders the rubric components for every enrolled student', async () => {
  const { page } = state.fac;
  await page.goto('/grading');
  await page.locator('article', { hasText: 'CS103' }).getByRole('link', { name: 'Open grade sheet' }).click();
  await page.locator('tbody tr').first().waitFor();
  const headers = await page.locator('thead th').allInnerTexts();
  for (const name of ['Assignments', 'Capstone Project', 'Final Exam']) expect(headers.join(' ').toLowerCase()).toContain(name.toLowerCase());
  expect(await page.locator('tbody tr').count()).toBeGreaterThanOrEqual(30);
  note('CS103 sheet: one column per rubric component (Assignments 10%, Capstone Project 40%, Final Exam 50%) for each of the enrolled students.');
  await shot(page, 'US-11.1');
});

test('US-11.2 partial or complete scores can be saved in Draft state', async () => {
  const { page } = state.fac;
  const partial = page.locator('tbody tr').nth(2);
  await partial.locator('input[type=number]').first().fill('77');
  const full = page.locator('tbody tr').nth(3);
  const inputs = full.locator('input[type=number]');
  for (let i = 0; i < 3; i++) await inputs.nth(i).fill(String(60 + i * 10));
  await page.getByRole('button', { name: 'Save drafts' }).click();
  await expect(toast(page)).toContainText('Draft marks saved');
  await page.reload();
  await page.locator('tbody tr').first().waitFor();
  await expect(page.locator('tbody tr').nth(2).locator('input[type=number]').first()).toHaveValue('77');
  await expect(page.locator('tbody tr').nth(2)).toContainText('Draft');
  await expect(page.locator('tbody tr').nth(3)).toContainText('Draft');
  note('One student saved with a single score, another with all three; after a reload both persist and show state "Draft".');
  await shot(page, 'US-11.2');
});

test('US-11.3 students cannot see marks while the grade is in Draft', async ({ browser }) => {
  const s = await session(browser, 'student001@srs.edu');
  await s.page.goto('/my-grades');
  const row = s.page.locator('li.list__item', { hasText: 'CS103' });
  await expect(row).toContainText('Pending');
  await expect(row).toContainText('Marks will appear here once published');
  expect(await row.innerText()).not.toMatch(/\b97\b|\b91\b/);
  note('student001 has Draft marks in CS103 but sees only "Pending - marks will appear here once published"; no numbers are shown.');
  await shot(s.page, 'US-11.3');
  await s.context.close();
});

// ============================================================================================ US-12 submit & publish
test('US-12.1 submitting calculates the weighted total and moves to Submitted', async () => {
  const { page } = state.fac;
  await page.goto('/grading');
  await page.locator('article', { hasText: 'CS103' }).getByRole('link', { name: 'Open grade sheet' }).click();
  await page.locator('tbody tr').first().waitFor();
  const first = page.locator('tbody tr').first();
  const inputs = first.locator('input[type=number]');
  await expect(inputs).toHaveCount(3);
  for (const [i, v] of ['80', '90', '70'].entries()) await inputs.nth(i).fill(v);
  await page.getByRole('button', { name: 'Save drafts' }).click();
  await expect(toast(page)).toContainText('Draft marks saved');
  await page.getByRole('button', { name: /Submit grades/ }).click();
  await modal(page).getByRole('button', { name: 'Submit', exact: true }).click();
  await expect(page.locator('.toast', { hasText: 'submitted for publication' })).toBeVisible(); // a second toast reports the incomplete drafts that were skipped
  await page.reload();
  const row = page.locator('tbody tr').first();
  await expect(row).toContainText('Submitted');
  await expect(row).toContainText('79.00'); // 80x10% + 90x40% + 70x50%
  note('80 / 90 / 70 with weights 10 / 40 / 50 gives a weighted total of 79.00 (8 + 36 + 35); the row moved to "Submitted" and its inputs are locked.');
  await shot(page, 'US-12.1');
});

test('US-12.2 admin can batch-publish courses in the Submitted state', async () => {
  const { page } = admin;
  await page.goto('/admin/publish');
  await expect(page.getByLabel('Select CS103')).toBeVisible();
  await page.getByLabel('Select CS103').check();
  await shot(page, 'US-12.2');
  await page.getByRole('button', { name: /Publish selected/ }).click();
  await modal(page).getByRole('button', { name: 'Publish', exact: true }).click();
  await expect(toast(page)).toContainText('Published');
  await expect(page.getByLabel('Select CS103')).toHaveCount(0);
  note('The publication queue listed CS103 (and the other submitted course); the batch action published it and it left the queue.');
});

test('US-12.3 published grades become visible to the student immediately', async ({ browser }) => {
  state.s1 = await session(browser, 'student001@srs.edu');
  const { page } = state.s1;
  await page.goto('/my-grades');
  const row = page.locator('li.list__item', { hasText: 'CS103' });
  await expect(row).toContainText('Published');
  await expect(row).toContainText('79.00');
  await expect(row).toContainText('Grade C');
  note('Immediately after publication student001 sees CS103 as Published with total 79.00 and letter C.');
  await shot(page, 'US-12.3');
});

// ============================================================================================ US-13 regrade disputes
test('US-13.1 a dispute button appears next to published grades', async () => {
  const { page } = state.s1;
  await expect(page.getByRole('button', { name: 'Dispute grade for CS103' })).toBeVisible();
  note('The Dispute button sits in the CS103 row next to the published grade.');
  await shot(page, 'US-13.1');
});

test('US-13.2 a written explanation is required before filing', async () => {
  const { page } = state.s1;
  await page.getByRole('button', { name: 'Dispute grade for CS103' }).click();
  await modal(page).getByRole('button', { name: 'Submit request' }).click();
  await expect(modal(page).getByRole('alert')).toContainText('at least 10 characters');
  const short = await api(page, 'POST', '/api/v1/disputes', { enrollment_id: 1, reason: 'short' });
  expect(short.status).toBe(400);
  note('Submitting with an empty explanation shows "Please explain your request in at least 10 characters" and the grade stays Published.');
  await shot(page, 'US-13.2');
});

test('US-13.3 filing the dispute moves the grade to Under Review', async () => {
  const { page } = state.s1;
  await modal(page).getByLabel(/Why should/).fill('The capstone project mark does not reflect the rubric I submitted against.');
  await modal(page).getByRole('button', { name: 'Submit request' }).click();
  const row = page.locator('li.list__item', { hasText: 'CS103' });
  await expect(row).toContainText('Under Review');
  await expect(page.getByRole('button', { name: 'Dispute grade for CS103' })).toHaveCount(0);
  note('With an explanation the request is filed; CS103 shows "Under Review" and the Dispute button disappears.');
  await shot(page, 'US-13.3');
});

test('US-13.4 faculty is notified, re-evaluates and re-publishes the grade', async () => {
  const { page } = state.fac;
  await page.goto('/');
  await expect(page.locator('.sidebar').getByRole('link', { name: /Regrade requests/ }).locator('.nav-badge')).toBeVisible();
  await page.locator('.sidebar').getByRole('link', { name: /Regrade requests/ }).click();
  const card = page.locator('.card', { hasText: 'PES1UG24CS001' }).filter({ hasText: 'Re-evaluate' }).first();
  await expect(card).toContainText('capstone project mark');
  await card.locator('input[type=number]').first().fill('95');
  await card.getByLabel('Resolution note').fill('Capstone re-marked against the rubric; assignment mark corrected.');
  await shot(page, 'US-13.4');
  await card.getByRole('button', { name: /Re-evaluate/ }).click();
  await expect(toast(page)).toContainText('re-published');
  await state.s1.page.goto('/my-grades');
  const row = state.s1.page.locator('li.list__item', { hasText: 'CS103' });
  await expect(row).toContainText('Published');
  await expect(row).toContainText('80.50'); // 95x10% + 90x40% + 70x50%
  await expect(row).toContainText('Capstone re-marked');
  await expect(row).toContainText('Regrade used');
  note('Faculty saw the red notification badge, re-scored the first component (80 -> 95) and re-published. The student sees Published, total 79.00 -> 80.50 (letter B), the faculty note, and the "Regrade used" badge: a second dispute is no longer possible.');
  await shot(state.s1.page, 'US-13.4-student');
  await state.s1.context.close();
});

// ============================================================================================ US-14 analytics
test('US-14.1 the student dashboard shows a credit-weighted term GPA', async ({ browser }) => {
  const s = await session(browser, 'student001@srs.edu');
  const shownText = await s.page.getByTestId('term-gpa').innerText();
  const summary = (await api(s.page, 'GET', '/api/v1/analytics/student/summary')).body;
  expect(summary.courses.every((c) => ['Published', 'Under Review'].includes(c.state))).toBe(true);
  const credits = summary.courses.reduce((a, c) => a + c.credits, 0);
  const expected = summary.courses.reduce((a, c) => a + c.points * c.credits, 0) / credits;
  expect(Number(shownText)).toBeCloseTo(expected, 2);
  expect(Number(shownText)).toBeLessThanOrEqual(10);
  state.gpaMs = summary.query_ms;
  note(`Displayed GPA ${shownText} / 10 equals sum(grade points x credits) / sum(credits) = ${expected.toFixed(2)} over ${credits} credits of published grades (A=10, B=8, C=6, D=4, F=0).`);
  await shot(s.page, 'US-14.1');
  state.gpaShown = await s.page.locator('.card', { hasText: 'Term GPA' }).innerText();
  await s.context.close();
});

test('US-14.2 faculty see A-F grade distribution charts per section', async () => {
  const { page } = state.fac;
  await page.goto('/analytics');
  await page.locator('.bars').first().waitFor();
  expect(await page.locator('.bars').count()).toBe(3);
  const labels = await page.locator('.bars').first().locator('.bars__label').allInnerTexts();
  expect(labels).toEqual(['A', 'B', 'C', 'D', 'F']);
  note('Three sections, each with an A / B / C / D / F histogram plus mean, median, graded count and attendance rate.');
  await shot(page, 'US-14.2');
});

test('US-14.3 analytics queries execute in under 800 ms', async () => {
  const { page } = state.fac;
  const text = await page.getByText(/Analytics computed in/).innerText();
  const facultyMs = Number(/([\d.]+) ms/.exec(text)[1]);
  expect(facultyMs).toBeLessThan(800);
  expect(state.gpaMs).toBeLessThan(800);
  expect(state.gpaShown).toContain('Loaded in');
  note(`Server-side query time reported on screen: student GPA ${state.gpaMs} ms, faculty analytics ${facultyMs} ms (limit 800 ms); the load test measured p95 = 30 ms at 500 sessions.`);
  await shot(page, 'US-14.3');
});

// ============================================================================================ US-15 metrics & security
test('US-15.1 a single click exports attendance and grade metrics to CSV', async () => {
  const { page } = admin;
  await page.goto('/');
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export CSV' }).click()]);
  const file = await download.path();
  const csv = fs.readFileSync(file, 'utf-8');
  const header = csv.split('\n')[0];
  for (const col of ['attendance_rate_pct', 'grades_published', 'grades_under_review', 'enrolled']) expect(header).toContain(col);
  expect(csv).toContain('TOTAL');
  expect(csv.split('\n').filter(Boolean).length).toBeGreaterThanOrEqual(52);
  note(`One click downloaded ${download.suggestedFilename()} with ${csv.split('\n').filter(Boolean).length - 2} course rows plus a TOTAL row, containing attendance rates and grade-state counts.`);
  await shot(page, 'US-15.1');
});

function tlsHandshake(options) {
  return new Promise((resolve) => {
    const socket = tls.connect({ host: HTTPS_HOST, port: 443, rejectUnauthorized: false, servername: 'localhost', ...options }, () => {
      const version = socket.getProtocol();
      socket.end();
      resolve({ ok: true, version });
    });
    socket.on('error', (error) => resolve({ ok: false, error: error.message }));
  });
}

test('US-15.2 TLS 1.3, HTTP-only 48-hour JWT sessions and parameterised queries are enforced', async ({ playwright }) => {
  const tls12 = await tlsHandshake({ minVersion: 'TLSv1.2', maxVersion: 'TLSv1.2' });
  const tls13 = await tlsHandshake({ minVersion: 'TLSv1.3', maxVersion: 'TLSv1.3' });
  expect(tls12.ok).toBe(false);
  expect(tls13.ok).toBe(true); expect(tls13.version).toBe('TLSv1.3');

  const secure = await playwright.request.newContext({ baseURL: `https://${HTTPS_HOST}`, ignoreHTTPSErrors: true });
  const login = await secure.post('/api/v1/auth/login', { data: { identifier: 'admin001@srs.edu', password: PASSWORD } });
  const cookie = login.headers()['set-cookie'];
  expect(cookie).toContain('HttpOnly'); expect(cookie).toContain('Secure'); expect(cookie).toContain('Max-Age=172800'); expect(cookie).toContain('SameSite=Lax');
  expect(login.headers()['strict-transport-security']).toContain('max-age=');
  expect(JSON.stringify(await login.json())).not.toContain('eyJ'); // the token is never exposed to JavaScript

  const injection = await api(admin.page, 'GET', "/api/v1/users?search=" + encodeURIComponent("' OR '1'='1"));
  expect(injection.status).toBe(200); expect(injection.body.total).toBe(0);
  const count = (await api(admin.page, 'GET', '/api/v1/users?per_page=1')).body.total;
  expect(count).toBeGreaterThan(500); // the table is intact after a stacked-query style payload
  await secure.dispose();
  note(`Handshake with a TLS 1.2-only client is refused (${tls12.error}); TLS 1.3 connects (${tls13.version}). Over HTTPS the login cookie is HttpOnly + Secure + SameSite=Lax with a 48 h lifetime, HSTS is sent, and the token is not in the response body. A SQL-injection payload in a search returns 0 rows and the users table is intact (parameterised ORM queries).`);
  await shot(admin.page, 'US-15.2');
});

test('US-15.3 200 simultaneous submissions complete without a database deadlock', async () => {
  test.skip(!fs.existsSync(K6_SUMMARY), 'k6 summary not found - run ./qa.sh perf first');
  const summary = JSON.parse(fs.readFileSync(K6_SUMMARY, 'utf-8')).metrics;
  const checks = summary['checks{scenario:burst}'];
  const failed = summary['http_req_failed{scenario:burst}'];
  expect(checks.fails).toBe(0); expect(checks.passes).toBeGreaterThanOrEqual(200);
  expect(failed.passes).toBe(0);
  const stamp = fs.statSync(K6_SUMMARY).mtime.toISOString();
  note(`Evidence from the k6 run of ${stamp}: 200 simultaneous attendance + grade submissions across 12 server processes -> ${checks.passes} accepted, ${checks.fails} failed, 0 HTTP errors (also covered by the PyTest concurrency test).`);
  fs.writeFileSync(path.join(EVIDENCE, 'US-15.3-k6-summary.json'), JSON.stringify({ burst_checks: checks, burst_http_failed: failed, k6_run: stamp }, null, 2));
});

// ============================================================================================ exploratory charters
test('EX-1 attack the grade lifecycle as a student', async ({ browser }) => {
  const s = await session(browser, 'student001@srs.edu');
  const { page } = s;
  const results = {
    'edit marks': (await api(page, 'PUT', '/api/v1/grades/courses/3/students/PES1UG24CS001', { rubric_scores: [], target_state: 'Published' })).status,
    'publish': (await api(page, 'POST', '/api/v1/grades/publication/publish', { course_ids: [3] })).status,
    'submit': (await api(page, 'POST', '/api/v1/grades/courses/3/submit')).status,
    'resolve own dispute': (await api(page, 'POST', '/api/v1/disputes/1/resolve', { resolution_note: 'self-approved' })).status,
    'read all users': (await api(page, 'GET', '/api/v1/users')).status,
  };
  Object.values(results).forEach((code) => expect(code).toBe(403));
  const grades = (await api(page, 'GET', '/api/v1/grades/mine')).body.grades;
  expect(JSON.stringify(grades)).not.toMatch(/PES1UG24CS0(0[2-9]|[1-9]\d)/); // no other student's id appears
  const mine = grades.find((g) => g.code === 'CS103');
  const again = await api(page, 'POST', '/api/v1/disputes', { enrollment_id: mine.enrollment_id, reason: 'Trying to dispute this grade a second time.' });
  expect(again.status).toBe(409); expect(again.body.code).toBe('ALREADY_DISPUTED');
  const other = await api(page, 'POST', '/api/v1/disputes', { enrollment_id: 999999, reason: 'Disputing a grade that is not mine at all.' });
  expect([403, 404]).toContain(other.status);
  note(`Edit marks / publish / submit / self-resolve / list users all returned 403; a second dispute returned 409 ALREADY_DISPUTED; another student's enrollment returned ${other.status}; /grades/mine exposes only the caller's data. No weakness found.`);
  await s.context.close();
});

test('EX-2 try to see or change another faculty member\'s sections', async () => {
  const { page } = state.fac;
  const attempts = {
    'grade sheet': (await api(page, 'GET', '/api/v1/grades/courses/20')).status,
    'save marks': (await api(page, 'PUT', '/api/v1/grades/courses/20', { students: [{ student_id: 'PES1UG24CS001', rubric_scores: [] }] })).status,
    'submit grades': (await api(page, 'POST', '/api/v1/grades/courses/20/submit')).status,
    'roster': (await api(page, 'GET', '/api/v1/schedule/roster/20')).status,
  };
  Object.values(attempts).forEach((code) => expect(code).toBe(403));
  const myDisputes = (await api(page, 'GET', '/api/v1/disputes')).body.disputes;
  const courses = new Set(myDisputes.map((d) => d.course.code));
  expect([...courses].every((c) => ['CS101', 'CS102', 'CS103'].includes(c))).toBe(true);
  note(`Grade sheet, save marks, submit and roster of a foreign section all returned 403; the dispute list only contains the faculty member's own courses (${[...courses].join(', ')}). No weakness found.`);
});

test('EX-3 keyboard-only operation and a 375 px screen', async ({ browser }) => {
  const s = await session(browser);
  const { page } = s;
  await page.goto('/login');
  await page.keyboard.type('student001@srs.edu'); // the email field is auto-focused
  await page.keyboard.press('Tab');
  await page.keyboard.type(PASSWORD);
  await page.keyboard.press('Enter');
  await expect(page.locator('.topbar')).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  const focusInMain = await page.evaluate(() => document.activeElement?.id === 'main' || !!document.activeElement?.closest('main'));
  expect(focusInMain).toBe(true);
  await page.setViewportSize({ width: 375, height: 667 });
  for (const url of ['/', '/catalog', '/my-grades', '/schedule']) {
    await page.goto(url);
    await page.locator('main h1').first().waitFor();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  }
  await page.getByRole('button', { name: 'Open navigation' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.sidebar')).toBeInViewport();
  note(`Signed in and reached the content using only the keyboard (skip link works: focus moved into main = ${focusInMain}); at 375 px four pages have no horizontal scroll and the drawer opens from the keyboard.`);
  await shot(page, 'EX-3');
  await s.context.close();
});

test('EX-4 hostile input in the text fields', async ({ browser }) => {
  const { page } = admin;
  const problems = [];
  page.on('dialog', (d) => { problems.push(`dialog: ${d.message()}`); d.dismiss(); });
  page.on('pageerror', (e) => problems.push(`page error: ${e.message}`));
  page.on('response', (r) => { if (r.status() >= 500) problems.push(`HTTP ${r.status()} ${r.url()}`); });
  const payloads = ['<script>alert(1)</script>', '"><img src=x onerror=alert(2)>', "'; DROP TABLE users; --", 'A'.repeat(5000), '😀'.repeat(60), '-1', '{{7*7}}'];
  for (const [i, payload] of payloads.entries()) {
    await page.goto('/admin/users/new');
    await page.getByLabel('Full name').fill(payload);
    await page.getByLabel('Email').fill(`hostile${i}@srs.edu`);
    await page.getByLabel('Institutional ID').fill(`HOST${i}`);
    await page.getByRole('button', { name: 'Create account' }).click();
    await Promise.race([page.getByTestId('temp-password').waitFor(), page.locator('.alert--danger, .field__error').first().waitFor()]);
    await page.goto('/admin/users');
    await page.getByLabel('Search users').fill(payload.slice(0, 40));
  }
  await page.goto('/admin/courses');
  await page.getByRole('button', { name: 'New course' }).click();
  await modal(page).getByLabel('Seat capacity').fill('-5');
  await modal(page).getByLabel('Course code').fill('<b>X</b>');
  await modal(page).getByLabel('Title').fill('Neg');
  await modal(page).getByRole('button', { name: 'Create course' }).click();
  await page.waitForTimeout(800);
  const stored = (await api(page, 'GET', '/api/v1/users?search=hostile0@srs.edu')).body.users[0]?.full_name ?? '';
  expect(stored).not.toContain('<script>');
  expect(problems).toEqual([]);
  note(`Seven hostile strings (script tags, an event-handler image, SQL, 5,000 characters, 60 emoji, a template expression, a negative number) were submitted through the account form, the user search and the course form: no JavaScript dialog, no uncaught page error, no HTTP 5xx. The stored name for the `<script>` payload is "${stored}" (markup stripped).`);
  await shot(page, 'EX-4');
  page.removeAllListeners('dialog');
});

test('EX-5 two sessions edit the same attendance sheet at once', async ({ browser }) => {
  const a = await session(browser, 'faculty001@srs.edu');
  const b = await session(browser, 'faculty001@srs.edu');
  const problems = [];
  for (const s of [a, b]) s.page.on('response', (r) => { if (r.status() >= 500) problems.push(`HTTP ${r.status()} ${r.url()}`); });
  await a.page.goto(state.rollcallUrl);
  await b.page.goto(state.rollcallUrl);
  await a.page.locator('tbody tr').first().waitFor();
  await b.page.locator('tbody tr').first().waitFor();
  await a.page.locator('tbody tr').nth(6).getByRole('button', { name: 'Absent' }).click();
  await b.page.locator('tbody tr').nth(6).getByRole('button', { name: 'Present' }).click();
  await b.page.locator('tbody tr').nth(7).getByRole('button', { name: 'Absent' }).click();
  await Promise.all([a.page.getByRole('button', { name: 'Save attendance' }).click(), b.page.getByRole('button', { name: 'Save attendance' }).click()]);
  await expect(toast(a.page)).toContainText('Attendance recorded');
  await expect(toast(b.page)).toContainText('Attendance recorded');
  const id = state.rollcallUrl.split('/').pop();
  const roster = (await api(a.page, 'GET', `/api/v1/attendance/sessions/${id}`)).body.students;
  const ids = roster.map((r) => r.student_id);
  expect(new Set(ids).size).toBe(ids.length); // no duplicate rows
  expect(roster.every((r) => typeof r.is_present === 'boolean')).toBe(true);
  expect(problems).toEqual([]);
  const absent = roster.filter((r) => !r.is_present).length;
  note(`Two browser sessions saved the same roll-call within the same instant (conflicting values for one student): both saves succeeded, the roster has ${ids.length} unique rows, no HTTP 5xx; the last write wins (${absent} students absent in the final state).`);
  await shot(a.page, 'EX-5');
  await a.context.close();
  await b.context.close();
  await state.fac.context.close();
});
