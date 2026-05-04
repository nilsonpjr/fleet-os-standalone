import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  base: '/fleet_os/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@core': path.resolve(__dirname, './src/core'),
      '@portals': path.resolve(__dirname, './src/portals'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
  server: {
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/react') || id.includes('react-router-dom')) return 'vendor-react'
          if (id.includes('recharts')) return 'vendor-charts'
          if (id.includes('jspdf')) return 'vendor-pdf'
          if (id.includes('react-hook-form') || id.includes('zod')) return 'vendor-forms'
        },
      },
    },
  },
})
