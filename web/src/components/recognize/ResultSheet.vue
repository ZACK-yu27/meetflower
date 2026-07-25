<template>
  <!-- P2 AI 科普页：上屏图片（约40%）+ 半屏卡片（4:6 ⇄ 2:8 双吸附档） -->
  <div ref="pageEl" class="p2-page">
    <!-- 上屏所拍花图（视频入口为静音循环预览） -->
    <div class="p2-img-wrap" :style="{ height: `calc(100% - ${cardH}%)` }">
      <video v-if="isVideo" class="p2-img" :src="previewUrl" muted autoplay loop playsinline></video>
      <img v-else class="p2-img" :src="previewUrl" alt="所拍花图" />
    </div>

    <!-- 下屏半屏卡片 -->
    <div class="p2-sheet" :class="{ dragging }" :style="{ height: cardH + '%' }">
      <!-- 拖拽把手（拖动切换吸附档） -->
      <div class="p2-grip" @pointerdown="onDragStart">
        <div class="sheet-handle-bar"></div>
      </div>

      <!-- 标题「识图结果」+ 右上 X（放弃本次识别、回 P0） -->
      <div class="p2-head" @pointerdown="onDragStart">
        <span class="p2-title text-tab">识图结果</span>
        <button class="p2-close" aria-label="关闭" @click.stop="$emit('close')">
          <ResIcon name="close" :size="18" />
        </button>
      </div>

      <!-- 内容区（纵向滚动） -->
      <div class="p2-content">
        <!-- 状态行：数据已就绪，展示「AI 生成回答」 -->
        <div class="ai-status"><b>AI</b> 生成回答</div>

        <div class="content-in">
          <!-- 品种名 + 主/辅色只读 chips + 置信度 Caption -->
          <h2 class="p2-species">{{ result.species }}</h2>
          <div class="p2-chips">
            <span class="chip">主色 · {{ result.main_color }}</span>
            <span class="chip">辅色 · {{ result.secondary_color }}</span>
          </div>
          <p class="p2-confidence text-caption ink-tertiary">
            识别置信度 {{ percentNumber(result.confidence) }}%
          </p>

          <!-- 广义的花：视频主体属性 + 相似理由（flower_resemble.md §3.3；拍照识别不渲染） -->
          <section v-if="result.resemble" class="p2-section p2-resemble">
            <h3 class="p2-section-title text-title">✨ 它为什么像 {{ result.species }}</h3>
            <p class="p2-resemble-subject text-body">
              视频里的「{{ result.resemble.subject }}」
            </p>
            <div class="p2-chips">
              <span class="chip">形态 · {{ result.resemble.shape }}</span>
              <span class="chip">颜色 · {{ result.resemble.color }}</span>
              <span class="chip">质感 · {{ result.resemble.texture }}</span>
            </div>
            <p v-if="result.resemble.reason" class="p2-resemble-reason text-body">
              {{ result.resemble.reason }}
            </p>
          </section>

          <!-- 科普正文（ark 模式异步补齐，空则显示生成中并轮询） -->
          <p class="p2-science text-body" :class="{ 'ink-tertiary': !scienceText }">
            {{ scienceText || 'AI 正在生成科普，请稍候…' }}
          </p>

          <!-- 「养护要点」编号小节（截断渐隐 + 展开更多） -->
          <section class="p2-section">
            <h3 class="p2-section-title text-title">🌿 养护要点</h3>
            <div class="tips-wrap" :class="{ collapsed: !tipsExpanded }">
              <ol class="p2-tips">
                <li v-for="(tip, i) in careTips" :key="i" class="text-body">
                  <span class="tip-num">{{ i + 1 }}.</span>{{ tip }}
                </li>
              </ol>
              <div v-if="!tipsExpanded" class="tips-fade"></div>
            </div>
            <div v-if="!tipsExpanded" class="tips-more">
              <button class="btn-ghost tips-more-btn" @click="tipsExpanded = true">
                展开更多
                <ResIcon name="chevron-down" :size="16" />
              </button>
            </div>
          </section>

          <!-- 「种入花园后的成长形态」横排 5 阶段图条 -->
          <section class="p2-section">
            <h3 class="p2-section-title text-title">🌱 种入花园后的成长形态</h3>
            <div class="p2-stages">
              <div v-for="stage in stageList" :key="stage.key" class="stage-item">
                <img :src="stage.img" :alt="stage.name" loading="lazy" />
                <span class="text-caption ink-secondary">{{ stage.name }}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      <!-- 底部固定主按钮「进入花园」 -->
      <div class="p2-footer">
        <button class="btn-cta" @click="pickerVisible = true">进入花园</button>
      </div>
    </div>

    <!-- 选择花园半屏卡（自底部上滑） -->
    <transition name="picker-fade">
      <div v-if="pickerVisible" class="picker-mask" @click.self="pickerVisible = false">
        <div class="picker-sheet">
          <div class="picker-head">
            <span class="text-tab">选择花园</span>
            <button class="picker-close" aria-label="关闭" @click="pickerVisible = false">
              <ResIcon name="close" :size="18" />
            </button>
          </div>
          <!-- 选项行：花园图标 + 名称 + 右侧选中圆点 -->
          <button class="picker-option" :disabled="planting" @click="doPlant">
            <ResIcon name="flower" variant="flat" :size="40" />
            <span class="picker-name text-body">我和小葵的花园</span>
            <span class="picker-dot"></span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ResIcon from '../ResIcon.vue'
import { plantRecognition, getRecognition, errorMessage } from '../../api/client'
import { useToastStore } from '../../stores/toast'
import { percentNumber, STAGE_ORDER, STAGE_NAMES } from '../../utils/format'
import { buildCareTips } from '../../utils/careTips'

const props = defineProps({
  previewUrl: { type: String, required: true },
  isVideo: { type: Boolean, default: false },
  result: { type: Object, required: true }
})

const emit = defineEmits(['close', 'planted'])

const toast = useToastStore()
const planting = ref(false)
const tipsExpanded = ref(false)
const pickerVisible = ref(false) // 选择花园半屏卡

const careTips = computed(() => buildCareTips(props.result.species))

// 科普文案：ark 模式接口先返回、科普异步补齐；空则每 2s 轮询（最长约 40s）
const scienceText = ref(props.result.science_text || '')
let pollTimer = null
let pollCount = 0

onMounted(() => {
  if (scienceText.value) return
  pollTimer = setInterval(async () => {
    pollCount += 1
    try {
      const r = await getRecognition(props.result.recognition_id)
      if (r.science_text) {
        scienceText.value = r.science_text
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch {
      /* 单次轮询失败静默，等待下一次 */
    }
    if (pollCount >= 20 && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// 5 阶段图条（地栽版，种子→萌芽→幼苗→花苞→盛放）
const stageList = computed(() =>
  STAGE_ORDER.map((key) => ({
    key,
    name: STAGE_NAMES[key],
    img: props.result.stage_images?.[key]
  })).filter((s) => s.img)
)

// ---- 卡片双吸附档拖拽（4:6 初始 ⇄ 2:8 展开，≤300ms） ----
const COLLAPSED = 60 // 卡片高 60%（图 4 : 卡 6）
const EXPANDED = 80 // 卡片高 80%（图 2 : 卡 8）
const cardH = ref(COLLAPSED)
const dragging = ref(false)
const pageEl = ref(null)
let dragStartY = 0
let dragStartH = COLLAPSED

function onDragStart(e) {
  if (e.button !== undefined && e.button !== 0) return
  dragging.value = true
  dragStartY = e.clientY
  dragStartH = cardH.value
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', onDragEnd, { once: true })
}

function onDragMove(e) {
  const pageH = pageEl.value?.clientHeight || window.innerHeight
  const delta = ((dragStartY - e.clientY) / pageH) * 100
  cardH.value = Math.min(85, Math.max(45, dragStartH + delta))
}

function onDragEnd() {
  window.removeEventListener('pointermove', onDragMove)
  dragging.value = false
  // 松手吸附到最近档位
  cardH.value = cardH.value >= (COLLAPSED + EXPANDED) / 2 ? EXPANDED : COLLAPSED
}

async function doPlant() {
  if (planting.value) return
  planting.value = true
  try {
    await plantRecognition(props.result.recognition_id)
    toast.success('已种到我的花园')
    pickerVisible.value = false
    emit('planted')
  } catch (err) {
    toast.error(errorMessage(err, '种下失败，请重试'))
  } finally {
    planting.value = false
  }
}
</script>

<style scoped>
.p2-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-dark);
}

.p2-img-wrap {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  overflow: hidden;
  transition: height 300ms ease;
}

.p2-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.p2-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  display: flex;
  flex-direction: column;
  transition: height 300ms ease;
}

.p2-sheet.dragging,
.p2-sheet.dragging + * {
  transition: none;
}

.p2-grip {
  padding: 10px 0 6px;
  touch-action: none;
  cursor: grab;
}

.sheet-handle-bar {
  width: 36px;
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--handle);
  margin: 0 auto;
}

.p2-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px var(--space-page) 10px;
  touch-action: none;
}

.p2-title {
  font-size: 17px;
}

.p2-close {
  width: 44px;
  height: 44px;
  margin: -6px -10px -6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.p2-close::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--close-bg);
}

.p2-close svg {
  position: relative;
  color: var(--ink-primary);
}

.p2-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-page) var(--space-block);
}

.p2-species {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
  margin-top: 14px;
}

.p2-chips {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.p2-confidence {
  margin-top: 8px;
}

.p2-science {
  margin-top: 12px;
  color: var(--ink-primary);
}

/* 广义的花：相似理由区 */
.p2-resemble .p2-chips {
  flex-wrap: wrap;
  margin-top: 10px;
}

.p2-resemble-subject {
  font-weight: 700;
  color: var(--ink-primary);
}

.p2-resemble-reason {
  margin-top: 10px;
  color: var(--ink-secondary);
}

.p2-section {
  margin-top: var(--space-block);
}

.p2-section-title {
  font-size: 18px;
  margin-bottom: 10px;
}

/* 养护要点：截断渐隐（底部 24px 渐变遮罩） */
.tips-wrap {
  position: relative;
  overflow: hidden;
  transition: max-height 300ms ease;
  max-height: 1000px;
}

.tips-wrap.collapsed {
  max-height: 96px;
}

.p2-tips {
  list-style: none;
}

.p2-tips li {
  padding: 5px 0;
  color: var(--ink-primary);
}

.tip-num {
  font-weight: 700;
  margin-right: 8px;
}

.tips-fade {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, #fff 100%);
}

.tips-more {
  display: flex;
  justify-content: center;
  margin-top: 10px;
}

.tips-more-btn {
  box-shadow: var(--shadow-float); /* §2.3 唯一允许的浮层阴影之一 */
  gap: 4px;
}

/* 成长形态横排图条 */
.p2-stages {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.stage-item {
  flex-shrink: 0;
  width: 76px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stage-item img {
  width: 76px;
  height: 76px;
  object-fit: contain;
  border-radius: var(--radius-inner);
  background: var(--close-bg);
}

.p2-footer {
  padding: 10px var(--space-page) calc(12px + env(safe-area-inset-bottom));
  background: var(--bg-page);
}

/* ---- 选择花园半屏卡 ---- */
.picker-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 60;
  display: flex;
  align-items: flex-end;
}

.picker-sheet {
  width: 100%;
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  padding: 14px var(--space-page) calc(18px + env(safe-area-inset-bottom));
}

.picker-head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 12px;
}

.picker-close {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  margin: -8px -10px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-close::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--close-bg);
}

.picker-close svg {
  position: relative;
}

.picker-option {
  width: 100%;
  min-height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 4px;
  text-align: left;
}

.picker-name {
  flex: 1;
  font-weight: 700;
}

.picker-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 5px solid var(--accent);
  flex-shrink: 0;
}

/* 遮罩淡入 + 卡片上滑（300ms） */
.picker-fade-enter-active,
.picker-fade-leave-active {
  transition: opacity 300ms;
}

.picker-fade-enter-active .picker-sheet,
.picker-fade-leave-active .picker-sheet {
  transition: transform 300ms ease-out;
}

.picker-fade-enter-from,
.picker-fade-leave-to {
  opacity: 0;
}

.picker-fade-enter-from .picker-sheet,
.picker-fade-leave-to .picker-sheet {
  transform: translateY(100%);
}
</style>
