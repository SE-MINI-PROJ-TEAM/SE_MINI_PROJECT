// System tests: authentication, role dashboards and UI-level RBAC (TC-ACC-02, TC-SEC-03/04, SYS-F-004)
import { test, expect } from '@playwright/test';
import { ACCOUNTS, signIn, signInAs, signOut } from '../helpers.js';

test('anonymous visitors are sent to the sign-in page and see no stale-session warning', async ({ page }) => {
  await page.goto('/catalog');
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await expect(page.getByText('Your session has ended')).toHaveCount(0); // regression: first visit must be clean
});

test('wrong credentials show an error and keep the user signed out', async ({ page }) => {
  await signIn(page, ACCOUNTS.student, 'not-the-password', { wait: false });
  await expect(page.getByRole('alert').filter({ hasText: 'Invalid credentials' })).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

for (const [role, widget] of [['admin', 'Institution metrics'], ['faculty', 'Roll-call needed'], ['student', 'Term GPA']]) {
  test(`${role} dashboard renders its widgets`, async ({ page }) => {
    await signInAs(page, role);
    await expect(page.getByText(widget).first()).toBeVisible();
    await signOut(page);
  });
}

test('a student cannot open admin screens through the URL', async ({ page }) => {
  await signInAs(page, 'student');
  await page.goto('/admin/users');
  await expect(page.getByText("You don't have access to this page")).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Manage users' })).toHaveCount(0);
});

test('navigation only offers what the role may use', async ({ page }) => {
  await signInAs(page, 'student');
  const nav = page.locator('.sidebar');
  await expect(nav.getByRole('link', { name: 'Course catalog' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Manage users' })).toHaveCount(0);
  await expect(nav.getByRole('link', { name: 'Take attendance' })).toHaveCount(0);
});

test('signing out ends the session for the protected API too', async ({ page }) => {
  await signInAs(page, 'admin');
  await signOut(page);
  const status = await page.evaluate(async () => (await fetch('/api/v1/users')).status);
  expect(status).toBe(401);
});
