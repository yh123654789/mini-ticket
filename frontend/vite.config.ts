import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// 开发时把 /api 代理到本地后端，生产由 nginx 代理，前端代码里只写相对路径
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
