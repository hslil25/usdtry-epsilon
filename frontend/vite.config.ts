import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // VITE_BASE_PATH must match your GitHub repo name, e.g. /usdtry-epsilon/
  // Leave empty (or unset) for local dev — the proxy handles it.
  const base = env.VITE_BASE_PATH ?? '/'

  return {
    base,
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/snapshot': 'http://localhost:8000',
        '/health':   'http://localhost:8000',
      },
    },
  }
})
