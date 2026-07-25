import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发服务器代理 /api 与 /static 到 FastAPI 后端（见 docs/API.md §0）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000'
    }
  }
})
