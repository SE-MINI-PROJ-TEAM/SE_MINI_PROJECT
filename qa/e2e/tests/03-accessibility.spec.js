// Automated WCAG 2.1 AA checks with axe-core (SAD section 4.4 "UX Design": compliant with WCAG 2.1 AA).
// Automated rules catch roughly a third of accessibility problems; keyboard/screen-reader checks stay manual (see UAT).
import AxeBuilder from '@axe-core/playwright';
import { test, expect } from '@playwright/test';
import { signInAs } from '../helpers.js';

const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

async function scan(page, label) {
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const summary = violations.map((v) => `${v.id} [${v.impact}] x${v.nodes.length}: ${v.help}\n    e.g. ${v.nodes[0].target.join(' ')}`).join('\n');
  expect(violations, `${label} has accessibility violations:\n${summary}`).toEqual([]);
}

const PAGES = {
  student: ['/', '/catalog', '/my-attendance', '/my-grades', '/schedule', '/profile'],
  faculty: ['/', '/attendance', '/grading', '/analytics', '/disputes', '/faculty/sections'],
  admin: ['/', '/admin/users', '/admin/courses', '/admin/schedule', '/admin/publish', '/admin/attendance-override', '/admin/audit-log', '/admin/users/new'],
};

test('sign-in page', async ({ page }) => {
  await page.goto('/login');
  await page.getByRole('heading', { name: 'Welcome back' }).waitFor();
  await scan(page, '/login');
});

for (const [role, paths] of Object.entries(PAGES)) {
  test(`${role} screens`, async ({ page }) => {
    await signInAs(page, role);
    for (const path of paths) {
      await page.goto(path);
      await page.locator('main h1').first().waitFor();
      await page.waitForLoadState('networkidle');
      await scan(page, `${role} ${path}`);
    }
  });
}

test('dialogs are accessible and trap focus', async ({ page }) => {
  await signInAs(page, 'admin');
  await page.goto('/admin/courses');
  await page.getByRole('button', { name: 'New course' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await scan(page, 'course dialog');
  for (let i = 0; i < 40; i++) await page.keyboard.press('Tab');
  expect(await dialog.evaluate((el) => el.contains(document.activeElement))).toBe(true); // focus never leaves the modal
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
});
