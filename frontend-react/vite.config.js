import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_BASE is set by the GitHub Pages build (served from /<repo>/).
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [react()],
})
