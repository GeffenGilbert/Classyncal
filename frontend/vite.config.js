import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/upload-syllabus": "http://localhost:8000",
      "/add-events": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
    },
  },
})
