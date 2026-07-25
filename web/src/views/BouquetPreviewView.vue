<template>
  <!-- P5 花束预览页：上屏预览大图约 45% + 半屏卡片（§3-P5） -->
  <div class="p5-page">
    <!-- 上屏预览图（可点按放大查看；异步生成中显示占位） -->
    <div class="p5-img-wrap" @click="preview && preview.preview_url && (enlarged = true)">
      <img v-if="preview && preview.preview_url" class="p5-img" :src="preview.preview_url" alt="花束预览图" />
      <div v-else class="p5-img-loading">
        <SkeletonLines class="p5-img-skeleton" />
        <p v-if="preview" class="p5-img-pending text-caption">预览图生成中，请稍候…</p>
      </div>
    </div>

    <!-- 下屏半屏卡片 -->
    <div class="p5-sheet">
      <div class="sheet-handle-bar"></div>
      <div class="p5-head">
        <span class="text-tab">花束方案</span>
        <button class="p5-close" aria-label="关闭" @click="goBack">
          <ResIcon name="close" :size="18" />
        </button>
      </div>

      <div class="p5-content">
        <!-- 状态行：生成中 / 完成 -->
        <div class="ai-status">
          <template v-if="loading"><b>AI</b> 正在生成回答 <span class="ai-dots"><i>·</i><i>·</i><i>·</i></span></template>
          <template v-else><b>AI</b> 生成回答</template>
        </div>

        <SkeletonLines v-if="loading" />

        <template v-else-if="preview">
          <div class="content-in">
            <!-- 搭配说明（Body） -->
            <p v-if="preview.arrangement_note" class="p5-note text-body">{{ preview.arrangement_note }}</p>

            <!-- 轻量建议（如有：--accent-soft 底提示条，Caption） -->
            <p v-if="preview.suggestion" class="p5-suggestion text-caption">{{ preview.suggestion }}</p>

            <!-- 花材清单（赠送项带「赠送」chip；末尾合计 Caption） -->
            <div class="material-list">
              <div v-for="(m, i) in preview.material_list" :key="i" class="material-row">
                <span class="text-body">
                  {{ m.species }} · {{ m.color }}
                  <span v-if="m.gifted" class="gift-chip">赠送</span>
                </span>
                <span class="text-body">×{{ m.count }}</span>
              </div>
              <p class="text-caption ink-tertiary material-total">合计 {{ totalCount }} 朵</p>
            </div>

            <!-- 包装建议（Caption 行） -->
            <p v-if="preview.packaging" class="text-caption ink-secondary p5-packaging">
              包装建议：{{ preview.packaging }}
            </p>

            <p class="text-caption ink-tertiary p5-hint">预览不消耗花材，发送花店后才会扣除</p>

            <!-- 发送信息区：备注输入 + 接受相似花材替代（默认勾选） -->
            <div class="send-info">
              <input
                v-model="note"
                class="note-input text-caption"
                type="text"
                maxlength="50"
                placeholder="给花店捎句话（选填）"
              />
              <button class="substitute-row" role="checkbox" :aria-checked="acceptSubstitute" @click="acceptSubstitute = !acceptSubstitute">
                <span class="substitute-check" :class="{ on: acceptSubstitute }">
                  <ResIcon v-if="acceptSubstitute" name="check" :size="12" />
                </span>
                <span class="text-caption ink-secondary">接受相似花材替代</span>
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部固定区 -->
      <div class="p5-footer">
        <button class="btn-cta" :disabled="!preview || sending" @click="doSend">
          {{ sending ? '发送中…' : '发送花店' }}
        </button>
        <button class="btn-ghost p5-back" @click="goBack">返回调整</button>
      </div>
    </div>

    <!-- 点按放大查看 -->
    <div v-if="enlarged && preview && preview.preview_url" class="p5-enlarge" @click="enlarged = false">
      <img :src="preview.preview_url" alt="花束预览大图" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ResIcon from '../components/ResIcon.vue'
import SkeletonLines from '../components/SkeletonLines.vue'
import { sendBouquetOrder, errorMessage } from '../api/client'
import { useBouquetStore } from '../stores/bouquet'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const bouquet = useBouquetStore()
const toast = useToastStore()

const sending = ref(false)
const enlarged = ref(false)

// 发送信息区（§3-P5）：备注（可空）+ 接受相似花材替代（默认勾选）
const note = ref('')
const acceptSubstitute = ref(true)

const loading = computed(() => bouquet.loading)
const preview = computed(() => bouquet.preview)
const totalCount = computed(
  () => preview.value?.material_list?.reduce((s, m) => s + m.count, 0) ?? 0
)

// 生成失败（含库存不足 409）：toast 展示 detail 并回 P4
watch(
  () => bouquet.error,
  (err) => {
    if (!err) return
    toast.error(errorMessage(err, '生成失败，请重试'))
    bouquet.clear()
    router.replace('/house')
  }
)

onMounted(() => {
  // 刷新 / 直达：无预览会话一律回 P4（推荐链路允许空 items + 仅赠送花材）
  if (!bouquet.loading && !bouquet.preview && !bouquet.error && !bouquet.items.length && !bouquet.bonus) {
    router.replace('/house')
  }
})

// X / 返回调整：回 P4 重选（不消耗）
function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/house')
  }
}

async function doSend() {
  if (!preview.value || sending.value) return
  sending.value = true
  try {
    // 1.8：携带备注与替代选项调下单接口
    await sendBouquetOrder(preview.value.bouquet_id, {
      note: note.value.trim(),
      acceptSubstitute: acceptSubstitute.value
    })
    router.push('/shop')
  } catch (err) {
    // 库存不足 / 重复提交 409：toast 展示 detail 并回 P4
    toast.error(errorMessage(err, '发送失败，请重试'))
    router.replace('/house')
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.p5-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-dark);
}

.p5-img-wrap {
  height: 45%;
  overflow: hidden;
}

.p5-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
}

.p5-img-loading {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 48px;
}

.p5-img-pending {
  color: var(--ink-tertiary);
}

.p5-img-skeleton {
  width: 100%;
}

.p5-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 55%;
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  display: flex;
  flex-direction: column;
  padding-top: 10px;
}

.sheet-handle-bar {
  width: 36px;
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--handle);
  margin: 0 auto 8px;
  flex-shrink: 0;
}

.p5-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px var(--space-page) 10px;
}

.p5-close {
  width: 44px;
  height: 44px;
  margin: -6px -10px -6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.p5-close::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--close-bg);
}

.p5-close svg {
  position: relative;
}

.p5-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-page);
}

/* 搭配说明 */
.p5-note {
  margin-top: 12px;
  color: var(--ink-primary);
}

/* 轻量建议：--accent-soft 底提示条 */
.p5-suggestion {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-inner);
  background: var(--accent-soft);
  color: var(--ink-secondary);
}

.material-list {
  margin-top: 12px;
}

.material-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--close-bg);
}

.material-row:last-of-type {
  border-bottom: none;
}

/* 「赠送」chip（只读展示） */
.gift-chip {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 10px;
  margin-left: 6px;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
}

.material-total {
  text-align: right;
  padding-top: 6px;
}

.p5-packaging {
  margin-top: 10px;
}

.p5-hint {
  margin-top: 6px;
}

/* ---- 发送信息区 ---- */
.send-info {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.note-input {
  width: 100%;
  height: 40px;
  border: none;
  outline: none;
  border-radius: var(--radius-pill);
  background: var(--close-bg);
  padding: 0 18px;
  font-family: inherit;
  color: var(--ink-primary);
}

.note-input::placeholder {
  color: var(--ink-tertiary);
}

.substitute-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px; /* §8 可点区域 ≥44 */
}

.substitute-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1.5px solid var(--handle);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.substitute-check.on {
  background: var(--accent);
  border-color: var(--accent);
}

.p5-footer {
  padding: 10px var(--space-page) calc(12px + env(safe-area-inset-bottom));
}

.p5-back {
  width: 100%;
  margin-top: 8px;
  height: 40px;
}

.p5-enlarge {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.p5-enlarge img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
</style>
