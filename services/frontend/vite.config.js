import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/scheduler': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace('/api/scheduler', ''),
      },
      '/api/youtube': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace('/api/youtube', ''),
      },
      '/api/instagram': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace('/api/instagram', ''),
      },
      '/api/monitoring': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace('/api/monitoring', ''),
      },
    },
  },
})
