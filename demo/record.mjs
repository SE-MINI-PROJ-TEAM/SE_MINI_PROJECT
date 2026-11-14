// Records the sprint demo videos by driving the real UI in a headless Chromium.
//   node record.mjs sprint1       -> videos/sprint1-raw.webm       (US-01 .. US-08, in order)
//   node record.mjs sprint2       -> videos/sprint2-raw.webm       (US-09 .. US-15, in order)
//   node record.mjs project-demo  -> videos/project-demo-raw.webm  (all 15 stories, in order)
// Prerequisites: API on :5000, UI on :5173, freshly seeded database (python manage.py seed --reset).
// make-videos.ps1 wraps all of this and trims the recordings to exactly 60 s and 120 s MP4s.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const BASE = process.env.BASE_URL || 'http://localhost:5173';
const which = process.argv[2];
const OUT = path.resolve('videos');
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: OUT, size: { width: 1280, height: 720 } },
  timezoneId: 'Asia/Kolkata',
  locale: 'en-IN',
  acceptDownloads: true,
});

// On-screen cursor + caption bar (screen recordings do not capture the OS cursor).
await context.addInitScript(() => {
  const mount = () => {
    if (document.getElementById('__cap')) return;
    const cursor = document.createElement('div');
    cursor.id = '__cur';
    cursor.style.cssText = 'position:fixed;z-index:2147483647;width:24px;height:24px;border-radius:50%;background:rgba(79,70,229,.30);border:2px solid #4f46e5;pointer-events:none;left:-60px;top:-60px;transform:translate(-50%,-50%);transition:transform .1s';
    const cap = document.createElement('div');
    cap.id = '__cap';
    cap.style.cssText = 'position:fixed;z-index:2147483647;left:50%;bottom:20px;transform:translateX(-50%);max-width:82%;padding:10px 22px;border-radius:12px;background:rgba(15,18,40,.93);color:#fff;font:600 18px Inter,system-ui,sans-serif;text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.4);display:none';
    document.documentElement.append(cursor, cap);
    try {
      const saved = sessionStorage.getItem('__cap');
      if (saved) { cap.textContent = saved; cap.style.display = 'block'; }
    } catch { /* ignore */ }
    addEventListener('mousemove', (e) => { cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { cursor.style.transform = 'translate(-50%,-50%) scale(.65)'; }, true);
    addEventListener('mouseup', () => { cursor.style.transform = 'translate(-50%,-50%)'; }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
});

const page = await context.newPage();
const created = Date.now();
page.setDefaultTimeout(15000);

const pause = (ms) => page.waitForTimeout(ms);
const DWELL = Number(process.env.CAPTION_DWELL ?? 1200); // reading time after each caption
const caption = async (text) => {
  await page.evaluate((t) => {
    try { sessionStorage.setItem('__cap', t); } catch { /* ignore */ }
    const el = document.getElementById('__cap');
    if (el) { el.textContent = t; el.style.display = t ? 'block' : 'none'; }
  }, text);
  if (text) await pause(DWELL);
};

async function glide(locator) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 14 });
}
async function click(locator) {
  await glide(locator);
  await pause(120);
  await locator.click();
}
async function typeInto(locator, text, delay = 28) {
  await click(locator);
  await locator.fill('');
  await locator.pressSequentially(text, { delay });
}
async function scroll(by) {
  for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, by / 6); await pause(60); }
}
const toast = async (ms = 1300) => { await page.locator('.toast').first().waitFor(); await pause(ms); };
const nav = (label) => click(page.locator('.sidebar').getByRole('link', { name: new RegExp(`^${label}`) })); // prefix match: badges add a count
const modal = () => page.locator('.modal');

const DEMO_ACCOUNTS = { Admin: 'admin001@srs.edu', Faculty: 'faculty001@srs.edu', Student: 'student001@srs.edu' };
async function signInAs(role) {
  await page.goto(`${BASE}/login`);
  await page.locator('.login-box').waitFor();
  await typeInto(page.getByLabel('Email or institutional ID'), DEMO_ACCOUNTS[role], 12); // the dev-only demo chips are not in production builds
  await typeInto(page.getByLabel('Password'), 'Password@123', 12);
  await click(page.getByRole('button', { name: 'Sign in' }));
  await page.locator('.topbar').waitFor();
}
async function signOut() {
  await click(page.locator('.sidebar__footer button'));
  await page.locator('.login-box').waitFor();
  await caption(''); // do not carry the previous caption onto the login screen
}

const t0 = Date.now();
await page.goto(`${BASE}/login`);
await page.locator('.login-box').waitFor();
const contentStart = (Date.now() - created) / 1000; // seconds of blank video before the first paint

// ───────────────────────────────────────────────────────────────── The stories, in order
// Every story is one step. `as(role)` signs out and in only when the role changes, so the recordings follow US-01 → US-15
// exactly and a story is never shown before the data it needs exists.
const T = Number(process.env.TYPE_DELAY ?? 12); // typing speed (ms per character)
const demo = { role: null, email: 'meera.kapoor@srs.edu', temp: '', password: 'Welcome#2026x' };

async function signInWith(email, password) {
  if (!(await page.locator('.login-box').isVisible())) await page.goto(`${BASE}/login`); // signing out already lands here
  await page.locator('.login-box').waitFor();
  await typeInto(page.getByLabel('Email or institutional ID'), email, T);
  await typeInto(page.getByLabel('Password'), password, T);
  await click(page.getByRole('button', { name: 'Sign in' }));
  await page.locator('.topbar').waitFor();
}
async function as(role) {
  if (demo.role === role) return;
  if (demo.role) await signOut();
  demo.role = role;
  if (role === 'NewUser') await signInWith(demo.email, demo.password);
  else await signInWith(DEMO_ACCOUNTS[role], 'Password@123');
}

async function us01() {
  await as('Admin');
  await caption('US-01 · Admin provisions an account — temporary password shown once');
  await nav('Create user');
  await typeInto(page.getByLabel('Full name'), 'Meera Kapoor', T);
  await typeInto(page.getByLabel('Email'), demo.email, T);
  await typeInto(page.getByLabel('Institutional ID'), 'PES1UG26CS201', T);
  await click(page.getByRole('button', { name: 'Create account' }));
  demo.temp = (await page.getByTestId('temp-password').innerText()).trim();
  await pause(1500);
}

async function us02() {
  if (demo.role) await signOut();
  demo.role = 'NewUser';
  await caption('US-02 · First login with the temporary password forces a reset');
  await typeInto(page.getByLabel('Email or institutional ID'), demo.email, T);
  await typeInto(page.getByLabel('Password'), demo.temp, T);
  await click(page.getByRole('button', { name: 'Sign in' }));
  await page.getByText('Set a new password').waitFor();
  await typeInto(page.getByLabel('Temporary password'), demo.temp, 6);
  await typeInto(page.getByLabel('New password', { exact: true }), demo.password, T);
  await typeInto(page.getByLabel('Confirm new password'), demo.password, 8);
  await pause(700);
  await click(page.getByRole('button', { name: 'Update password' }));
  await page.locator('.topbar').waitFor();
}

async function us03() {
  await as('NewUser');
  await caption('US-03 · Self-service contact details (admin fields are read-only)');
  await nav('My profile');
  await typeInto(page.getByLabel('Phone number'), '+91 98765 43210', T);
  await click(page.getByRole('button', { name: 'Save changes' }));
  await toast(700);
}

async function us04() {
  await as('Admin');
  await caption('US-04 · Admin deactivates an account — audited, sessions revoked');
  await nav('Manage users');
  await typeInto(page.getByLabel('Search users'), 'student003', T);
  await pause(800);
  await click(page.getByRole('switch', { name: /Deactivate/ }));
  await click(modal().getByRole('button', { name: 'Deactivate' }));
  await toast(800);
}

async function us05() {
  await as('Admin');
  await caption('US-05 · New course — rubric weights auto-normalise to 100%');
  await nav('Course offerings');
  await click(page.getByRole('button', { name: 'New course' }));
  await typeInto(modal().getByLabel('Course code'), 'CS901', T);
  await typeInto(modal().getByLabel('Title'), 'Cloud Native Systems', T);
  await modal().getByLabel('Primary faculty').selectOption({ index: 49 });
  for (const n of [1, 2, 3]) await typeInto(modal().getByLabel(`Component ${n} raw weight`), '1', T);
  await pause(1200);
  await click(modal().getByRole('button', { name: 'Create course' }));
  await toast(700);
}

async function us06() {
  await as('NewUser');
  await caption('US-06 · Self-enrol in a section — seats update immediately');
  await nav('Course catalog');
  await typeInto(page.getByLabel('Search catalog'), 'CS901', T);
  const card = page.getByRole('article', { name: /CS901/ });
  await card.waitFor();
  await click(card.getByRole('button', { name: 'Enroll' }));
  await toast(900);
}

async function us07() {
  await as('Admin');
  await caption('US-07 · Admin publishes a class session to the timetable');
  await nav('Manage schedule');
  const option = await page.locator('select option', { hasText: 'CS901' }).first().getAttribute('value');
  await page.getByLabel('Course section').selectOption(option);
  await typeInto(page.getByLabel('Room'), 'LH-901', T);
  await click(page.getByRole('button', { name: 'Publish session' }));
  await toast(800);
}

async function us08() {
  await as('Faculty');
  await caption('US-08 · Roll-call in three clicks — locks automatically after 48 hours');
  await click(page.locator('.dash-grid').getByRole('link', { name: 'Take attendance' }).first());
  await page.locator('tbody tr').first().waitFor();
  for (const i of [1, 4]) await click(page.locator('tbody tr').nth(i).getByRole('button', { name: 'Absent' }));
  await click(page.getByRole('button', { name: 'Save attendance' }));
  await toast(1200);
}

async function us09() {
  await as('Admin');
  await caption('US-09 · Override a frozen attendance record — justification is mandatory');
  await nav('Attendance override');
  const course = await page.locator('select[aria-label="Course"] option', { hasText: 'CS101-A' }).first().getAttribute('value');
  await page.getByLabel('Course', { exact: true }).selectOption(course);
  await pause(500);
  const frozen = await page.locator('select[aria-label="Session"] option', { hasText: 'frozen' }).first().getAttribute('value');
  await page.getByLabel('Session', { exact: true }).selectOption(frozen);
  await page.locator('tbody tr').first().waitFor();
  const row = page.locator('tbody tr').first();
  const current = (await row.locator('.badge').innerText()).trim();
  await click(row.getByRole('button', { name: current === 'Present' ? 'Absent' : 'Present' }));
  await typeInto(page.getByLabel(/Justification/), 'Medical certificate verified by department', 16);
  await click(page.getByRole('button', { name: 'Apply override' }));
  await toast(600);
  await caption('Every override lands in the immutable audit log');
  await nav('Audit log');
  await page.getByLabel('Filter by action').selectOption('ATTENDANCE_OVERRIDE');
  await pause(2200);
}

async function us10() {
  await as('Student');
  await caption('US-10 · Attendance per course — alert below 75%');
  await nav('My attendance');
  await page.locator('li.list__item').first().waitFor();
  await pause(2400);
}

async function us11() {
  await as('Faculty');
  await caption('US-11 · Faculty enters rubric marks in Draft — hidden from students');
  await nav('Grade entry');
  await click(page.locator('article', { hasText: 'CS103' }).getByRole('link', { name: 'Open grade sheet' }));
  await page.locator('tbody tr').first().waitFor();
  const marks = [['78', '85.5', '91'], ['64.5', '70', '58'], ['88', '92.5', '95']];
  for (let r = 0; r < marks.length; r++) {
    const inputs = page.locator('tbody tr').nth(r).locator('input[type=number]');
    for (let c = 0; c < marks[r].length; c++) await typeInto(inputs.nth(c), marks[r][c], 22);
  }
  await pause(900);
  await click(page.getByRole('button', { name: 'Save drafts' }));
  await toast(700);
}

async function us12() {
  await caption('US-12 · Submit — weighted totals are calculated server-side');
  await click(page.getByRole('button', { name: /Submit grades/ }));
  await click(modal().getByRole('button', { name: 'Submit', exact: true }));
  await toast(900);
  await as('Admin');
  await caption('US-12 · Admin batch-publishes submitted grades');
  await nav('Publish grades');
  await click(page.getByLabel('Select CS102'));
  await click(page.getByRole('button', { name: /Publish selected/ }));
  await click(modal().getByRole('button', { name: 'Publish', exact: true }));
  await toast(900);
  await as('Student');
  await caption('US-12 · Published grades are visible to the student immediately');
  await nav('My grades');
  await page.locator('li.list__item').first().waitFor();
  await pause(2400);
}

async function us13() {
  await as('Student');
  await caption('US-13 · Dispute a published grade — an explanation is required, once per grade');
  await click(page.getByRole('button', { name: 'Dispute grade for CS101' }));
  await typeInto(modal().getByLabel(/Why should/), 'My end-term answer to question 3 deserves partial credit.', 18);
  await click(modal().getByRole('button', { name: 'Submit request' }));
  await toast(800);
  await as('Faculty');
  await caption('US-13 · Faculty is notified, re-evaluates and re-publishes');
  await nav('Regrade requests');
  const first = page.locator('.card').filter({ hasText: 'Re-evaluate' }).first();
  await first.waitFor();
  await typeInto(first.locator('input[type=number]').first(), '92', 22);
  await typeInto(first.getByLabel('Resolution note'), 'Question 3 re-marked; partial credit awarded.', 16);
  await click(first.getByRole('button', { name: /Re-evaluate/ }));
  await toast(800);
  await as('Student');
  await caption('The re-published grade is final — a grade can be disputed only once');
  await nav('My grades');
  await page.getByText('Regrade used').first().waitFor();
  await pause(2400);
}

async function us14() {
  await as('Student');
  await caption('US-14 · Credit-weighted GPA on a 10-point scale, loaded in milliseconds');
  await click(page.locator('.sidebar').getByRole('link', { name: 'Dashboard', exact: true }));
  await page.getByText('Term GPA').waitFor();
  await pause(2400);
  await as('Faculty');
  await caption('US-14 · Grade distribution (A–F), mean, median and attendance per section');
  await nav('Class analytics');
  await page.locator('.bars').first().waitFor();
  await pause(2800);
}

async function us15() {
  await as('Admin');
  await caption('US-15 · Institution metrics with one-click CSV export');
  await click(page.locator('.sidebar').getByRole('link', { name: 'Dashboard', exact: true }));
  await page.getByRole('button', { name: 'Export CSV' }).waitFor();
  await pause(1500);
  await click(page.getByRole('button', { name: 'Export CSV' }));
  await toast(1200);
}

const RECORDINGS = {
  sprint1: { title: 'Sprint 1 — Accounts, courses, enrolment & attendance', steps: [us01, us02, us03, us04, us05, us06, us07, us08], outro: 'Sprint 1 delivered — US-01 to US-08' },
  sprint2: { title: 'Sprint 2 — Attendance admin, grading, disputes, analytics & metrics', steps: [us09, us10, us11, us12, us13, us14, us15], outro: 'Sprint 2 delivered — US-09 to US-15' },
  'project-demo': {
    title: 'Student Record System — all 15 user stories, in order',
    steps: [us01, us02, us03, us04, us05, us06, us07, us08, us09, us10, us11, us12, us13, us14, us15],
    outro: 'All 15 user stories delivered',
  },
};

async function record(name) {
  const { title, steps, outro } = RECORDINGS[name];
  await caption(title);
  await pause(2000);
  for (const step of steps) await step();
  await caption(outro);
  await pause(2200);
  // Hold the last frame until the requested length so the trimmed video never cuts a story short.
  const target = Number(process.env.TARGET_SECONDS ?? 0);
  const elapsed = (Date.now() - t0) / 1000;
  if (target && elapsed < target) await pause((target - elapsed) * 1000);
}

try {
  if (!RECORDINGS[which]) throw new Error('usage: node record.mjs sprint1|sprint2|project-demo');
  await record(which);
} catch (error) {
  await page.screenshot({ path: path.join(OUT, `${which}-failure.png`) });
  console.error('Recording failed:', error.message);
  await context.close();
  await browser.close();
  process.exit(1);
}

const video = page.video();
await context.close();
fs.renameSync(await video.path(), path.join(OUT, `${which}-raw.webm`));
await browser.close();
fs.writeFileSync(path.join(OUT, `${which}.json`), JSON.stringify({ contentStart, scriptSeconds: (Date.now() - t0) / 1000 }));
console.log(`${which}: raw video saved (${((Date.now() - t0) / 1000).toFixed(1)} s of scripted activity)`);
