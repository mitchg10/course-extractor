import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/', // Use relative paths
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: process.env.PORT || 5173,
    strictPort: true,
    watch: {
      usePolling: true
    }
  },
  define: {
    'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000')
  }
})