import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// The dev server proxies /api so browser code never hard-codes a host or port.
// That keeps the app working behind the preview proxy and in production.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: { target: 'es2022', sourcemap: false },
})
