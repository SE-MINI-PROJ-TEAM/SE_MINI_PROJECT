// System tests: complete multi-role workflows through the real UI (TC-ACC-01/02, TC-CRS-02, TC-GRD-01..05).
import { test, expect } from '@playwright/test';
import { ACCOUNTS, newSession, signIn, signInAs } from '../helpers.js';

const uniq = Date.now();

test('admin provisions a user; the user must reset the temporary password, then can enrol', async ({ page }) => {
  await signInAs(page, 'admin');
  await page.getByRole('link', { name: 'Create user', exact: true }).first().click();
  await page.getByLabel('Full name').fill('E2E Student');
  await page.getByLabel('Email').fill(`e2e.${uniq}@srs.edu`);
  await page.getByLabel('Institutional ID').fill(`E2E${uniq}`);
  await page.getByRole('button', { name: 'Create account' }).click();
  const temp = (await page.getByTestId('temp-password').innerText()).trim();
  expect(temp.length).toBeGreaterThanOrEqual(10);

  // Duplicate email is rejected inline (409 surfaced next to the field)
  await page.getByRole('button', { name: 'Create another account' }).click();
  await page.getByLabel('Full name').fill('Dup');
  await page.getByLabel('Email').fill(`e2e.${uniq}@srs.edu`);
  await page.getByLabel('Institutional ID').fill(`DUP${uniq}`);
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByText('already exists')).toBeVisible();

  await page.locator('.sidebar__footer button').click();
  await signIn(page, `e2e.${uniq}@srs.edu`, temp);
  await expect(page.getByText('Set a new password')).toBeVisible(); // forced reset (SYS-F-002)
  await page.goto('/catalog'); // cannot skip it
  await expect(page.getByText('Set a new password')).toBeVisible();

  await page.getByLabel('Temporary password').fill(temp);
  await page.getByLabel('New password', { exact: true }).fill('Brand#New9pass');
  await page.getByLabel('Confirm new password').fill('Brand#New9pass');
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page.locator('.topbar')).toBeVisible();

  await page.getByRole('link', { name: 'Course catalog', exact: true }).first().click();
  await page.getByRole('button', { name: 'Enroll', exact: true }).first().click(); // the first cards are full sections
  await expect(page.locator('.toast').first()).toContainText('Enrolled in');
});

test('the 6-course cap is enforced in the UI', async ({ page }) => {
  await signIn(page, 'student002@srs.edu'); // seeded with 6 courses
  await page.getByRole('link', { name: 'Course catalog', exact: true }).first().click();
  await expect(page.getByText('6 / 6')).toBeVisible();
  await page.getByRole('button', { name: 'Enroll', exact: true }).first().click();
  await expect(page.locator('.toast').first()).toContainText('at most 6 courses');
});

test('grade lifecycle: Draft -> Submitted -> Published -> dispute -> resolved -> final', async ({ browser, baseURL }) => {
  const faculty = await newSession(browser, baseURL);
  const admin = await newSession(browser, baseURL);
  const student = await newSession(browser, baseURL);
  {
    // faculty completes student001's CS103 marks and submits
    await signIn(faculty.page, ACCOUNTS.faculty);
    await faculty.page.goto('/grading');
    await faculty.page.locator('article', { hasText: 'CS103' }).getByRole('link', { name: 'Open grade sheet' }).click();
    const row = faculty.page.locator('tbody tr').first();
    const inputs = row.locator('input[type=number]');
    await expect(inputs).toHaveCount(3); // the grid renders asynchronously
    for (let i = 0; i < 3; i++) await inputs.nth(i).fill(String(70 + i * 5));
    await faculty.page.getByRole('button', { name: 'Save drafts' }).click();
    await expect(faculty.page.locator('.toast').first()).toContainText('Draft marks saved');

    // the student cannot see marks while Draft
    await signIn(student.page, ACCOUNTS.student);
    await student.page.goto('/my-grades');
    const cs103 = student.page.locator('li.list__item', { hasText: 'CS103' });
    await expect(cs103).toContainText('Pending');
    await expect(cs103).toContainText('Marks will appear here once published');

    await faculty.page.getByRole('button', { name: /Submit grades/ }).click();
    await faculty.page.locator('.modal').getByRole('button', { name: 'Submit', exact: true }).click();
    await expect(faculty.page.locator('.toast').first()).toContainText('submitted for publication');

    // admin publishes
    await signIn(admin.page, ACCOUNTS.admin);
    await admin.page.goto('/admin/publish');
    await admin.page.getByLabel('Select CS103').check();
    await admin.page.getByRole('button', { name: /Publish selected/ }).click();
    await admin.page.locator('.modal').getByRole('button', { name: 'Publish', exact: true }).click();
    await expect(admin.page.locator('.toast').first()).toContainText('Published');

    // student sees the grade, disputes it
    await student.page.reload();
    await expect(cs103).toContainText('Published');
    await student.page.getByRole('button', { name: 'Dispute grade for CS103' }).click();
    await student.page.getByRole('dialog').getByRole('button', { name: 'Submit request' }).click();
    await expect(student.page.getByRole('dialog').getByRole('alert')).toBeVisible(); // empty explanation refused
    await student.page.getByRole('dialog').getByLabel(/Why should/).fill('The end-term answer to question 3 deserves partial credit.');
    await student.page.getByRole('dialog').getByRole('button', { name: 'Submit request' }).click();
    await expect(cs103).toContainText('Under Review');

    // faculty resolves
    await faculty.page.goto('/disputes');
    const card = faculty.page.locator('.card').filter({ hasText: 'Re-evaluate' }).first();
    await card.getByLabel('Resolution note').fill('Re-marked, partial credit given.');
    await card.getByRole('button', { name: /Re-evaluate/ }).click();
    await expect(faculty.page.locator('.toast').first()).toContainText('re-published');

    // the grade is final: no second dispute possible
    await student.page.reload();
    await expect(cs103).toContainText('Published');
    await expect(cs103).toContainText('Regrade used');
    await expect(student.page.getByRole('button', { name: 'Dispute grade for CS103' })).toHaveCount(0);
  }
});

test('deactivating a user signs them out of a live session', async ({ browser, baseURL }) => {
  const admin = await newSession(browser, baseURL);
  const victim = await newSession(browser, baseURL);
  {
    await signIn(victim.page, 'student009@srs.edu');
    await expect(victim.page.locator('.topbar')).toBeVisible();
    await signIn(admin.page, ACCOUNTS.admin);
    await admin.page.goto('/admin/users');
    await admin.page.getByLabel('Search users').fill('student009@srs.edu');
    const toggle = admin.page.getByRole('switch', { name: /Deactivate/ });
    await expect(toggle).toHaveCount(1); // wait for the debounced search to narrow the table to one user
    await toggle.click();
    await admin.page.locator('.modal').getByRole('button', { name: 'Deactivate' }).click();
    await expect(admin.page.locator('.toast').first()).toContainText('deactivated');

    await victim.page.goto('/catalog'); // fresh API call with the still-unexpired JWT
    await expect(victim.page).toHaveURL(/\/login$/);
    await expect(victim.page.getByText('deactivated')).toBeVisible();
  }
});
