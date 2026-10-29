import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The dev server proxies /api to Flask so the HTTP-only JWT cookie is same-origin (no CORS, SameSite=Lax works).
const target = process.env.VITE_API_TARGET || 'http://localhost:5000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target, changeOrigin: false, secure: false } },
  },
  // `vite preview` serves the production build (used by the QA E2E stage) with the same API proxy.
  preview: {
    proxy: { '/api': { target, changeOrigin: false, secure: false } },
  },
  test: { environment: 'node' },
});
