/**
 * Vite configuration — MiroFish Frontend
 *
 * - Vue 3 SFC support via @vitejs/plugin-vue
 * - Dev server on port 3000 with auto-open
 * - API proxy: forwards /api/* requests to the Flask backend at localhost:5001
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    open: true,
    // Proxy API requests to the Python backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
