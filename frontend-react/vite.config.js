import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_BASE is set by the GitHub Pages build (served from /<repo>/).
// The dev server forwards /api to the backend, so the dashboard and the API
// share one origin: it then works through `tailscale serve` from your phone
// while the backend itself stays bound to 127.0.0.1.
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [react()],
  server: {
    allowedHosts: ['.ts.net'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
