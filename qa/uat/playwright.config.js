// @ts-check
// Executes docs/uat/UAT-SCRIPT.md against the running system. One test per acceptance criterion (title starts with the
// criterion id, e.g. "US-08.4"), run in script order because later stories reuse data created by earlier ones.
import { defineConfig } from '@playwright/test';
import path from 'node:path';

const reports = process.env.UAT_REPORTS || path.resolve('reports/uat');

export default defineConfig({
  testDir: '.',
  testMatch: 'uat.spec.js',
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['json', { outputFile: path.join(reports, 'results.json') }]],
  outputDir: path.join(reports, 'artifacts'),
  use: {
    baseURL: process.env.BASE_URL || 'http://web',
    ignoreHTTPSErrors: true, // the Docker stack uses a self-signed certificate
    timezoneId: 'Asia/Kolkata',
    locale: 'en-IN',
    viewport: { width: 1280, height: 720 },
    trace: 'off',
    screenshot: 'only-on-failure',
  },
});
