import { defineStore } from 'pinia'

// 全局 toast（§3-P7：顶部下浮黑底白字胶囊，2s 自消）
export const useToastStore = defineStore('toast', {
  state: () => ({ message: '', timer: null }),
  actions: {
    show(message) {
      this.message = message
      if (this.timer) clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        this.message = ''
      }, 2000)
    },
    error(message) {
      this.show(message)
    },
    success(message) {
      this.show(message)
    }
  }
})
