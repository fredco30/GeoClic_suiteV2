import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/fleet/',
  server: {
    proxy: {
      '/api/fleet': 'http://localhost:5555',
      '/api/auth': 'http://localhost:8000',
    },
  },
})
