import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // server: {
  //   host: true, // Needed for Docker - listen on all addresses
  //   port: 5173,
  //   strictPort: true, // Force the port to be used
  //   watch: {
  //     usePolling: true // Better performance for Docker volumes
  //   },
  //   hmr: {
  //     host: 'localhost',
  //     protocol: 'ws'
  //   },
  //   proxy: {
  //     '/api': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //       rewrite: (path) => path.replace(/^\/api/, ''),
  //     },
  //   },
  // },
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