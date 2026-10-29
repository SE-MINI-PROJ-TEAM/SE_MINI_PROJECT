// @ts-check
import { defineConfig } from '@playwright/test';
import path from 'node:path';

const out = process.env.E2E_OUT || path.resolve('reports/e2e');

export default defineConfig({
  testDir: './tests',
  // Tests share one seeded database and run in file order: later files build on earlier ones.
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [
    ['list'],
    ['junit', { outputFile: path.join(out, 'junit.xml') }],
    ['html', { outputFolder: path.join(out, 'html'), open: 'never' }],
  ],
  outputDir: path.join(out, 'artifacts'),
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:4173',
    timezoneId: 'Asia/Kolkata',
    locale: 'en-IN',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1280, height: 720 },
  },
});
