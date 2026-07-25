<template>
  <!-- P3a 资源明细卡：45% 黑遮罩 + 底部上滑半屏卡（§3-P3a；v2.2 起不再设演示工具区） -->
  <div class="p3a-page">
    <!-- 遮罩：压暗背景，点击返回花园页 -->
    <div class="p3a-mask" :class="{ in: entered }" @click="goGarden"></div>

    <div class="p3a-sheet" :class="{ in: entered }">
      <!-- 居中标题 + 右上 X -->
      <div class="p3a-head">
        <span class="text-tab">资源明细</span>
        <button class="sheet-x" aria-label="关闭" @click="goGarden">
          <ResIcon name="close" :size="18" />
        </button>
      </div>

      <div class="p3a-scroll">
        <SkeletonLines v-if="loading" />

        <template v-else-if="garden">
          <!-- 余额条：三枚资源余额横排（我的储备 = resources.me） -->
          <div class="balance-row">
            <div v-for="r in resourceList" :key="r.key" class="balance-item">
              <ResIcon :name="r.icon" variant="flat" :size="44" />
              <span class="balance-count">{{ r.count }}</span>
              <span class="text-caption ink-tertiary">{{ r.name }}</span>
            </div>
          </div>

          <!-- 明细列表：圆形扁平类型图标 + 文案/时间 + 资源 +n（倒序 ≤20 条，只展示事件） -->
          <div class="detail-list">
            <p v-if="!events.length" class="text-caption ink-tertiary list-empty">
              还没有资源收入，去聊天页互动获取吧
            </p>
            <div v-for="ev in events" :key="ev.id" class="detail-row">
              <span class="row-icon">
                <ResIcon :name="typeIcon(ev.type)" variant="flat" shape="circle" :size="40" />
              </span>
              <div class="row-mid">
                <p class="row-desc">{{ ev.description }}</p>
                <p class="text-caption ink-tertiary">{{ formatMinute(ev.occurred_at) }}</p>
              </div>
              <span class="row-delta">
                <ResIcon :name="deltaIcon(ev)" variant="flat" shape="none" :size="16" />
                <b>+{{ deltaValue(ev) }}</b>
              </span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ResIcon from '../components/ResIcon.vue'
import SkeletonLines from '../components/SkeletonLines.vue'
import { getGarden, errorMessage } from '../api/client'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const toast = useToastStore()

const entered = ref(false) // 上滑进入动画（300ms）
const loading = ref(true)
const garden = ref(null)

// 余额条（名称口径：水滴/阳光/养料；API v0.2 起 resources 分 me/ta，此处展示我的储备）
const resourceList = computed(() => {
  const r = garden.value?.resources?.me || {}
  return [
    { key: 'water', icon: 'water', name: '水滴', count: r.water ?? 0 },
    { key: 'sunlight', icon: 'sun', name: '阳光', count: r.sunlight ?? 0 },
    { key: 'nutrient', icon: 'nutrient', name: '养料', count: r.nutrient ?? 0 }
  ]
})

// 明细列表：接口已按时间倒序、最多 20 条
const events = computed(() => garden.value?.events || [])

// 互动类型 → 圆形扁平图标（互发消息 / 分享视频 / 连续互动火花）
const TYPE_ICONS = { mutual_message: 'message', share_video: 'video', streak: 'spark' }
function typeIcon(type) {
  return TYPE_ICONS[type] || 'message'
}

// 事件 delta → 对应资源小图标与 +n
function deltaKey(ev) {
  return Object.keys(ev.delta || {})[0] || 'water'
}
function deltaIcon(ev) {
  return { water: 'water', sunlight: 'sun', nutrient: 'nutrient' }[deltaKey(ev)] || 'water'
}
function deltaValue(ev) {
  return ev.delta?.[deltaKey(ev)] ?? 0
}

// 时间精确到分（参照火星明细行格式）
function formatMinute(iso) {
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}年${p(d.getMonth() + 1)}月${p(d.getDate())}日 ${p(d.getHours())}:${p(d.getMinutes())}`
}

async function load() {
  garden.value = await getGarden()
}

// 遮罩点击 / 右上 X：返回花园页
function goGarden() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/garden')
  }
}

onMounted(async () => {
  // 卡片自底部上滑进入（300ms）
  requestAnimationFrame(() => requestAnimationFrame(() => (entered.value = true)))
  try {
    await load()
  } catch (err) {
    toast.error(errorMessage(err, '加载失败，请重试'))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.p3a-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-garden);
}

.p3a-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  opacity: 0;
  transition: opacity 300ms;
}

.p3a-mask.in {
  opacity: 1;
}

.p3a-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 76%; /* §7：约占屏 70–80% */
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  transform: translateY(100%);
  transition: transform 300ms ease-out;
  display: flex;
  flex-direction: column;
}

.p3a-sheet.in {
  transform: translateY(0);
}

.p3a-head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px var(--space-page) 10px;
  flex-shrink: 0;
}

.sheet-x {
  position: absolute;
  right: var(--space-page);
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  margin: -6px -10px -6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sheet-x::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--close-bg);
}

.sheet-x svg {
  position: relative;
  color: var(--ink-primary);
}

.p3a-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-page) calc(16px + env(safe-area-inset-bottom));
}

/* ---- 余额条 ---- */
.balance-row {
  display: flex;
  padding: 6px 0 14px;
}

.balance-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.balance-count {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.3;
}

/* ---- 明细列表 ---- */
.list-empty {
  text-align: center;
  padding: 24px 0;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.row-icon {
  flex-shrink: 0;
  display: flex;
}

.row-mid {
  flex: 1;
  min-width: 0;
}

.row-desc {
  font-size: 15px;
  line-height: 1.45;
}

.row-delta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.row-delta b {
  font-size: 16px;
  font-weight: 700;
}

/* §8 减弱动态效果 */
@media (prefers-reduced-motion: reduce) {
  .p3a-mask,
  .p3a-sheet {
    transition: opacity 200ms;
  }

  .p3a-sheet {
    transform: none;
    opacity: 0;
  }

  .p3a-sheet.in {
    opacity: 1;
  }
}
</style>
