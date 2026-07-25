import { defineStore } from 'pinia'

// 识图会话：在 P0 → P1 → P2 之间传递图片与识别结果
// 刷新 /recognize 时 session 丢失，页面负责重定向回 P0
export const useRecognizeStore = defineStore('recognize', {
  state: () => ({
    file: null, // 原始 File（用于上传）
    previewUrl: '', // 本地预览 objectURL
    result: null // 1.1 识花接口响应
  }),
  actions: {
    // P0 选定图片后开启会话
    startSession(file) {
      this.clear()
      this.file = file
      this.previewUrl = URL.createObjectURL(file)
    },
    setResult(result) {
      this.result = result
    },
    clear() {
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl)
      this.file = null
      this.previewUrl = ''
      this.result = null
    }
  }
})
