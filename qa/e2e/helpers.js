import { expect } from '@playwright/test';

export const PASSWORD = 'Password@123';
export const ACCOUNTS = {
  admin: 'admin001@srs.edu',
  faculty: 'faculty001@srs.edu',
  student: 'student001@srs.edu',
};

/** Signs in and (by default) waits until the app has left the login form - navigating away earlier would abort the request. */
export async function signIn(page, email, password = PASSWORD, { wait = true } = {}) {
  await page.goto('/login');
  await page.getByLabel('Email or institutional ID').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  if (wait) await expect(page.locator('.topbar, .bare-page').first()).toBeVisible(); // dashboard, or the forced-reset screen
}

export async function signInAs(page, role) {
  await signIn(page, ACCOUNTS[role]);
  await expect(page.locator('.topbar')).toBeVisible();
}

export async function signOut(page) {
  await page.locator('.sidebar__footer button').click();
  await expect(page.locator('.login-box')).toBeVisible();
}

/** Opens a fresh, isolated browser context (own cookies) so several roles can be signed in at once. */
export async function newSession(browser, baseURL) {
  const context = await browser.newContext({ baseURL, timezoneId: 'Asia/Kolkata', locale: 'en-IN' });
  return { context, page: await context.newPage() };
}
