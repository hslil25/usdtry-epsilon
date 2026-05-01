import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // VITE_BASE_PATH is injected by GitHub Actions as /<repo-name>/
  // Falls back to '/' for local dev.
  base: (process.env.VITE_BASE_PATH as string | undefined) ?? '/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/snapshot': 'http://localhost:8000',
      '/health':   'http://localhost:8000',
    },
  },
})
