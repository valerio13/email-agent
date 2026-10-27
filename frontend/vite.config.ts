import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // In development the API runs on its own port. The proxy keeps every request same-origin,
    // as it is in production, where the API serves the built frontend.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
