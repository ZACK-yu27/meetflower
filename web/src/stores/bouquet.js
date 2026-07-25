import { defineStore } from 'pinia'
import { previewBouquet, getBouquet } from '../api/client'

// 花束预览会话：P4 发起 1.7 请求并跳转 P5，P5 读取本 store
// 刷新 /bouquet/preview 时数据丢失，页面负责重定向回 P4
export const useBouquetStore = defineStore('bouquet', {
  state: () => ({
    items: [], // 所选花材 [{ species, color, count }]
    bonus: null, // 推荐链路赠送花材 { species, color, count }（可空）
    occasion: null, // 送花意图（可空）
    loading: false, // 生成中
    preview: null, // 1.7 响应 { bouquet_id, preview_url, material_list, arrangement_note, packaging, suggestion, status }
    error: null // 失败原因（含 409）
  }),
  actions: {
    // P4 点击「生成花束预览」时调用（不 await，跳转后由 P5 观察状态）
    startPreview(items, { bonus = null, occasion = null } = {}) {
      this.items = items
      this.bonus = bonus
      this.occasion = occasion
      this.preview = null
      this.error = null
      this.loading = true
      previewBouquet(items, { bonus, occasion })
        .then((res) => {
          this.preview = res
          // ark 模式预览图异步生成：preview_url 为空则轮询补齐（每 3s，最长约 3 分钟）
          if (!res.preview_url) this._pollImage(res.bouquet_id, 0)
        })
        .catch((err) => {
          this.error = err
        })
        .finally(() => {
          this.loading = false
        })
    },
    _pollImage(bouquetId, count) {
      if (count >= 60) return
      setTimeout(async () => {
        // 会话已被清掉（返回调整 / 关闭）则停止轮询
        if (!this.preview || this.preview.bouquet_id !== bouquetId) return
        try {
          const b = await getBouquet(bouquetId)
          if (b.preview_url) {
            this.preview = { ...this.preview, preview_url: b.preview_url }
            return
          }
        } catch {
          /* 单次轮询失败静默，等待下一次 */
        }
        this._pollImage(bouquetId, count + 1)
      }, 3000)
    },
    clear() {
      this.items = []
      this.bonus = null
      this.occasion = null
      this.loading = false
      this.preview = null
      this.error = null
    }
  }
})
