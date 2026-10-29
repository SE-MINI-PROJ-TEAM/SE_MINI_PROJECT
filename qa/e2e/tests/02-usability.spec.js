// TC-UX-01 / SYS-NF-004: key workflows are reachable in <= 3 clicks from login; layout works from 375 px to 1920 px.
import { test, expect } from '@playwright/test';
import { signInAs } from '../helpers.js';

/** Counts real user clicks from now on. */
async function startClickCounter(page) {
  await page.evaluate(() => {
    window.__clicks = 0;
    document.addEventListener('click', (e) => { if (e.isTrusted) window.__clicks++; }, true);
  });
}
const clicks = (page) => page.evaluate(() => window.__clicks);

test('roll-call is completed within 3 clicks of signing in (TC-UX-01)', async ({ page }) => {
  await signInAs(page, 'faculty'); // authentication itself is not counted
  await startClickCounter(page);

  await page.locator('.dash-grid').getByRole('link', { name: 'Take attendance' }).first().click(); // 1
  await page.locator('tbody tr').first().waitFor();
  await page.getByRole('button', { name: 'Save attendance' }).click(); // 2 (default is everyone Present; toggling absentees would add clicks)
  await expect(page.locator('.toast').first()).toContainText('Attendance recorded');

  expect(await clicks(page)).toBeLessThanOrEqual(3);
});

test('the GPA is visible on the student dashboard with zero clicks', async ({ page }) => {
  await signInAs(page, 'student');
  await expect(page.getByTestId('term-gpa')).toBeVisible();
  const gpa = Number(await page.getByTestId('term-gpa').innerText());
  expect(gpa).toBeGreaterThan(0);
  expect(gpa).toBeLessThanOrEqual(10);
});

const VIEWPORTS = [
  { name: 'phone 375 px', width: 375, height: 667 },
  { name: 'tablet 768 px', width: 768, height: 1024 },
  { name: 'desktop 1920 px', width: 1920, height: 1080 },
];
const STUDENT_PAGES = ['/', '/catalog', '/my-attendance', '/my-grades', '/schedule', '/profile'];

for (const vp of VIEWPORTS) {
  test(`student pages fit the screen without horizontal page scroll at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await signInAs(page, 'student');
    for (const path of STUDENT_PAGES) {
      await page.goto(path);
      await page.locator('main h1').first().waitFor();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow, `${path} overflows by ${overflow}px`).toBeLessThanOrEqual(1);
    }
  });
}

test('on a phone the navigation collapses into a drawer', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await signInAs(page, 'student');
  const sidebar = page.locator('.sidebar');
  await expect(sidebar).not.toBeInViewport();
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await expect(sidebar).toBeInViewport();
  await sidebar.getByRole('link', { name: 'Course catalog' }).click();
  await expect(page.getByRole('heading', { name: 'Course catalog' })).toBeVisible();
  await expect(sidebar).not.toBeInViewport(); // closes after navigating
});

test('the theme toggle persists across reloads', async ({ page }) => {
  await signInAs(page, 'student');
  const before = await page.evaluate(() => document.documentElement.dataset.theme);
  await page.getByRole('button', { name: /Switch to (dark|light) theme/ }).click();
  await page.reload();
  const after = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(after).not.toBe(before);
});
