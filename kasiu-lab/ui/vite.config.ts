import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@domain': path.resolve(__dirname, './src/domain'),
      '@adapters': path.resolve(__dirname, './src/adapters'),
      '@presentation': path.resolve(__dirname, './src/presentation'),
    },
  },
  server: {
    host: '127.0.0.1',
    strictPort: true,
    allowedHosts: ['localhost', '127.0.0.1'],
    cors: { origin: ['http://localhost:5173', 'http://127.0.0.1:5173'] },
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/storage': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: { host: '127.0.0.1', port: 5173, strictPort: true },
});
