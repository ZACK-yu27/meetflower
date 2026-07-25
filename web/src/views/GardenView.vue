<template>
  <!-- P3 花园页（续火花主页面形态，§3-P3）：柔粉渐变整页纵向滚动 -->
  <div class="p3-page">
    <!-- 顶部栏：双人叠放头像 + 右上「···」白底圆钮 -->
    <header class="p3-topbar">
      <div class="avatars" aria-label="我和小葵">
        <span class="avatar avatar-a">我</span>
        <span class="avatar avatar-b">葵</span>
      </div>
      <button class="more-btn" aria-label="更多" @click="toast.show('更多玩法敬请期待')">
        <ResIcon name="more" :size="20" />
      </button>
    </header>

    <!-- 中央主视觉：花园场景 + 右侧工具列 -->
    <div class="p3-visual">
      <GardenScene
        ref="sceneRef"
        :plants="scenePlants"
        :resources="myResources"
        :selected-id="selectedId"
        :growing-ids="growingIds"
        @select="onSelect"
        @open-resources="router.push('/garden/resources')"
      />
      <!-- 右侧工具列：白底图标卡（56px）+ 独立白色胶囊标签，间距 20px -->
      <div class="p3-tools">
        <button v-for="t in tools" :key="t.label" class="tool-btn" @click="router.push(t.to)">
          <span class="tool-icon"><ResIcon :name="t.icon" variant="flat" shape="none" :size="42" /></span>
          <span class="tool-label">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- 花园题注（n = 未收藏植株数） -->
    <p class="p3-caption text-caption">我和小葵的花园 · 共种下 {{ scenePlants.length }} 朵花</p>

    <!-- 提示条（badge）：浅黄底 + 灯泡图标 + 右侧 X 可关，点击正文刷新并消失 -->
    <div v-if="bannerVisible" class="p3-banner">
      <ResIcon name="bulb" variant="flat" shape="none" :size="18" class="banner-bulb" />
      <span class="banner-text text-caption" @click="refreshAll">花园有新的变化，去看看吧</span>
      <button class="banner-x" aria-label="关闭提示" @click="dismissBanner">
        <ResIcon name="close" :size="14" />
      </button>
    </div>

    <!-- 白色卡片区 -->
    <div class="p3-cards">
      <!-- 植株卡 -->
      <div class="white-card plant-card" :class="{ highlight: cardHighlight }">
        <div v-if="loading" class="card-loading"><SkeletonLines /></div>

        <p v-else-if="!selectedPlant" class="card-empty text-caption">
          点击花园里的一朵花，开始照料它
        </p>

        <div v-else class="card-detail content-in" :key="selectedPlant.plant_id">
          <div class="detail-head">
            <img class="detail-img" :src="selectedPlant.stage_image" :alt="selectedPlant.stage_name" />
            <div class="detail-title">
              <span class="text-title detail-stage">{{ selectedPlant.stage_name }}</span>
              <span class="text-caption ink-tertiary">
                {{ selectedPlant.species }}（{{ selectedPlant.main_color }}）
              </span>
            </div>
            <span class="text-caption ink-tertiary detail-next">
              {{ selectedPlant.is_bloom ? '已盛放' : `下一阶段：${selectedPlant.next_stage_name || '—'}` }}
            </span>
          </div>

          <!-- 「我 / TA」并列进度块 -->
          <div v-if="!selectedPlant.is_bloom" class="care-rows">
            <div v-for="side in careRows" :key="side.key" class="care-row">
              <span class="care-who text-caption">{{ side.label }}</span>
              <span v-for="r in side.marks" :key="r.key" class="care-mark text-caption">
                {{ r.name }}
                <ResIcon v-if="r.ok" name="check" :size="14" class="mark-ok" />
                <ResIcon v-else name="close" :size="13" class="mark-no" />
              </span>
              <span class="care-state text-caption" :class="side.done ? 'state-done' : 'state-wait'">
                {{ side.done ? '已完成' : '等待中' }}
              </span>
            </div>
          </div>

          <!-- 状态提示语 -->
          <p class="text-caption ink-secondary status-hint">{{ statusHint }}</p>

          <!-- 主按钮：点亮条件 = me.can_care；bloom 时替换为「压花收藏」 -->
          <button v-if="!selectedPlant.is_bloom" class="btn-cta" :disabled="!canCare || caring" @click="doCare">
            {{ caring ? '照料中…' : '照料这朵花' }}
          </button>
          <button v-else class="btn-cta" :disabled="pressing" @click="doPress">
            {{ pressing ? '收藏中…' : '压花收藏' }}
          </button>
          <!-- 灰置原因 Caption -->
          <p v-if="!selectedPlant.is_bloom && !canCare && careBlockReason" class="text-caption ink-tertiary block-reason">
            {{ careBlockReason }}
          </p>

          <!-- 查看完整成长旅程（Demo 专用，非 bloom 可见） -->
          <button
            v-if="!selectedPlant.is_bloom"
            class="btn-ghost journey-btn"
            :disabled="journeyBusy"
            @click="doJourney"
          >
            {{ journeyBusy ? '快进中…' : '查看完整成长旅程' }}
          </button>
        </div>
      </div>

      <!-- 入口卡：再识一朵花 -->
      <div class="white-card entry-card">
        <span class="entry-icon"><ResIcon name="camera" variant="flat" :size="44" /></span>
        <div class="entry-texts">
          <p class="entry-title">再识一朵花</p>
          <p class="text-caption ink-tertiary">看到喜欢的花，拍下来种进花园</p>
        </div>
        <button class="entry-cta" @click="router.push('/')">去识花</button>
      </div>
    </div>

    <!-- 提醒 TA 弹窗（§P7） -->
    <Modal
      v-model:visible="remindVisible"
      title="提醒TA照料鲜花"
      body="你已经完成这一阶段的照料，提醒 TA 也来照料这朵花吧"
      confirm-text="提醒 TA"
      secondary-text="知道了"
      @confirm="onRemind"
      @secondary="remindVisible = false"
    />

    <!-- 旅程弹窗（五阶段递进点亮 →「已盛放」） -->
    <JourneyModal :visible="journeyVisible" :plant="selectedPlant" @finish="journeyVisible = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import GardenScene from '../components/garden/GardenScene.vue'
import JourneyModal from '../components/garden/JourneyModal.vue'
import ResIcon from '../components/ResIcon.vue'
import SkeletonLines from '../components/SkeletonLines.vue'
import Modal from '../components/Modal.vue'
import { getGarden, carePlant, pressPlant, getBadge, fastForward, errorMessage } from '../api/client'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const toast = useToastStore()

const loading = ref(true)
const garden = ref(null)
const selectedId = ref(null)
const caring = ref(false)
const pressing = ref(false)
const sceneRef = ref(null)

// 成长动画：stage_advanced_at 晚于上次访问的植株
const growingIds = ref([])
const cardHighlight = ref(false)
const LAST_VISIT_KEY = 'garden_last_visit'

// 提醒 TA / 旅程弹窗
const remindVisible = ref(false)
const journeyVisible = ref(false)
const journeyBusy = ref(false)

// 提示条
const badgeMessage = ref('')
const bannerDismissed = ref(false)
const bannerVisible = computed(() => !!badgeMessage.value && !bannerDismissed.value)

let badgeTimer = null
let growClearTimer = null

const tools = [
  { label: '花房', icon: 'warehouse', to: '/house' },
  { label: '资源', icon: 'ledger', to: '/garden/resources' },
  { label: '聊天', icon: 'message', to: '/chat' }
]

// 我的储备（资源条展示 me）
const myResources = computed(() => garden.value?.resources?.me || {})

// 已压花收藏的植株不再出现在场景中
const scenePlants = computed(() => (garden.value?.plants || []).filter((p) => !p.pressed))

const selectedPlant = computed(
  () => scenePlants.value.find((p) => p.plant_id === selectedId.value) || null
)

const NEED_META = [
  { key: 'water', name: '水滴', gapLabel: '滴水' },
  { key: 'sunlight', name: '阳光', gapLabel: '缕阳光' },
  { key: 'nutrient', name: '养料', gapLabel: '份养料' }
]

// 「我 / TA」并列进度块：逐资源 ✓/✕ + 已完成/等待中（已完成后该侧逐项视为已满足）
const careRows = computed(() => {
  const p = selectedPlant.value
  if (!p) return []
  return [
    { key: 'me', label: '我的照料：', done: !!p.me?.done, marks: marksFor(p.me) },
    { key: 'ta', label: 'TA 的照料：', done: !!p.ta?.done, marks: marksFor(p.ta) }
  ]
})

function marksFor(side) {
  return NEED_META.map((m) => ({
    ...m,
    ok: side?.done ? true : !!side?.sufficient?.[m.key]
  }))
}

const canCare = computed(() => !!selectedPlant.value?.me?.can_care)

// 状态提示语（按 me.done / ta.done / can_care 派生）
const statusHint = computed(() => {
  const p = selectedPlant.value
  if (!p || p.is_bloom) return ''
  if (p.me?.done && p.ta?.done) return '花朵正在成长，去看看吧'
  if (p.me?.done && !p.ta?.done) return '你已完成今天的照料，等 TA 的资源到位，这朵花就会长大'
  if (!p.me?.can_care) return '资源不足时，去聊天页互动获取吧'
  return '资源已就绪，去照料这朵花吧'
})

// 主按钮灰置原因：已完成等待 TA / 资源缺口
const careBlockReason = computed(() => {
  const p = selectedPlant.value
  if (!p || p.is_bloom || canCare.value) return ''
  if (p.me?.done) return '你已完成，等待 TA 照料'
  const me = myResources.value
  // 与后端 409 文案同口径：「还差 2 滴水、1 缕阳光，去聊天获取吧」
  const gaps = NEED_META.filter((m) => (p.needs?.[m.key] ?? 0) > (me[m.key] ?? 0)).map(
    (m) => `${p.needs[m.key] - (me[m.key] ?? 0)} ${m.gapLabel}`
  )
  return gaps.length ? `还差 ${gaps.join('、')}，去聊天获取吧` : ''
})

function onSelect(plant) {
  selectedId.value = selectedId.value === plant.plant_id ? null : plant.plant_id
}

async function loadGarden() {
  garden.value = await getGarden()
  checkGrowth()
}

// 成长动画：stage_advanced_at 晚于上次访问（localStorage）的植株 → 场景缩放 + 卡高亮
function checkGrowth() {
  const plants = garden.value?.plants || []
  const last = localStorage.getItem(LAST_VISIT_KEY)
  const nowTs = Date.now()
  if (last !== null) {
    const lastTs = Number(last)
    const ids = plants
      .filter((p) => p.stage_advanced_at && new Date(p.stage_advanced_at).getTime() > lastTs)
      .map((p) => p.plant_id)
    if (ids.length) {
      growingIds.value = ids
      cardHighlight.value = selectedId.value != null && ids.includes(selectedId.value)
      clearTimeout(growClearTimer)
      growClearTimer = setTimeout(() => {
        growingIds.value = []
        cardHighlight.value = false
      }, 650)
    }
  }
  localStorage.setItem(LAST_VISIT_KEY, String(nowTs))
}

// 点击提示条正文：刷新聚合视图并消失（查看花园后后端清除 badge）
async function refreshAll() {
  try {
    await loadGarden()
    badgeMessage.value = ''
    bannerDismissed.value = false
  } catch (err) {
    toast.error(errorMessage(err))
  }
}

function dismissBanner() {
  bannerDismissed.value = true
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function doCare() {
  const plant = selectedPlant.value
  if (!plant || caring.value || !canCare.value) return
  caring.value = true
  try {
    const res = await carePlant(plant.plant_id)
    // 资源图标自资源条飞向植株（≤600ms）
    sceneRef.value?.flyToPlant(res.applied, plant.plant_id)
    // 我完成照料且 TA 未完成 → 提醒 TA 弹窗
    if (res.me_done && !res.ta_done) remindVisible.value = true
    await sleep(620)
    await loadGarden()
  } catch (err) {
    // 已完成 / 资源缺口 409：toast 展示接口 detail 原文
    toast.error(errorMessage(err))
  } finally {
    caring.value = false
  }
}

function onRemind() {
  remindVisible.value = false
  toast.success('已提醒 TA，等 TA 来照料')
}

async function doPress() {
  const plant = selectedPlant.value
  if (!plant || pressing.value) return
  pressing.value = true
  try {
    await pressPlant(plant.plant_id)
    toast.success('已压花收藏，去花房看看吧')
    selectedId.value = null
    await loadGarden()
  } catch (err) {
    toast.error(errorMessage(err))
  } finally {
    pressing.value = false
  }
}

// 「查看完整成长旅程」：调快进接口 → 旅程弹窗
async function doJourney() {
  const plant = selectedPlant.value
  if (!plant || journeyBusy.value) return
  journeyBusy.value = true
  try {
    await fastForward(plant.plant_id)
    await loadGarden()
    selectedId.value = plant.plant_id
    journeyVisible.value = true
  } catch (err) {
    toast.error(errorMessage(err))
  } finally {
    journeyBusy.value = false
  }
}

async function pollBadge() {
  try {
    const res = await getBadge()
    if (res.has_update) badgeMessage.value = res.message || '花园有新的变化，去看看吧'
  } catch {
    // badge 轮询失败静默，不打断演示
  }
}

onMounted(async () => {
  try {
    await loadGarden()
  } catch (err) {
    toast.error(errorMessage(err, '花园加载失败，请重试'))
  } finally {
    loading.value = false
  }
  badgeTimer = setInterval(pollBadge, 5000)
})

onUnmounted(() => {
  clearInterval(badgeTimer)
  clearTimeout(growClearTimer)
})
</script>

<style scoped>
.p3-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg-garden);
  padding-bottom: calc(24px + env(safe-area-inset-bottom));
}

/* ---- 顶部栏 ---- */
.p3-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(10px + env(safe-area-inset-top)) var(--space-page) 0;
}

.avatars {
  display: flex;
  align-items: center;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}

.avatar-a {
  background: linear-gradient(135deg, #8fc7f9 0%, #5b9def 100%);
  z-index: 1;
}

.avatar-b {
  background: linear-gradient(135deg, #ffc7d6 0%, #ff9ebb 100%);
  margin-left: -12px;
}

.more-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-float);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-primary);
}

.more-btn:active {
  opacity: 0.8;
}

/* ---- 中央主视觉 ---- */
.p3-visual {
  position: relative;
  height: 46vh;
  min-height: 340px;
}

.p3-tools {
  position: absolute;
  top: calc(50px + env(safe-area-inset-top));
  right: var(--space-page);
  z-index: 32;
  display: flex;
  flex-direction: column;
  gap: 20px; /* §3-P3：工具按钮间距 20px */
}

.tool-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  min-width: 44px;
}

.tool-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-inner);
  background: #fff;
  box-shadow: var(--shadow-float);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-btn:active .tool-icon {
  opacity: 0.8;
}

/* 独立白色胶囊标签 */
.tool-label {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: #fff;
  box-shadow: var(--shadow-float);
  font-size: 12px;
  color: var(--ink-primary);
}

/* ---- 花园题注 ---- */
.p3-caption {
  text-align: center;
  color: var(--ink-secondary);
  margin: 6px 0 12px;
}

/* ---- 提示条（badge） ---- */
.p3-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 var(--space-page) 12px;
  padding: 8px 12px;
  border-radius: var(--radius-card);
  background: var(--banner-tip);
}

.banner-bulb {
  flex-shrink: 0;
}

.banner-text {
  flex: 1;
  color: var(--ink-primary);
  min-height: 32px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.banner-x {
  width: 44px;
  height: 44px;
  margin: -6px -10px -6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-tertiary);
  flex-shrink: 0;
}

/* ---- 白色卡片区 ---- */
.p3-cards {
  padding: 0 var(--space-page);
  display: flex;
  flex-direction: column;
  gap: var(--space-block);
}

.white-card {
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 16px;
}

/* 植株卡高亮（成长动画配套，600ms） */
.plant-card.highlight {
  animation: card-glow 600ms ease;
}

@keyframes card-glow {
  0%,
  100% {
    background: var(--bg-page);
  }
  50% {
    background: var(--accent-soft);
  }
}

.card-empty {
  text-align: center;
  color: var(--ink-tertiary);
  padding: 20px 0;
}

/* 植株卡 */
.detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.detail-img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  border-radius: var(--radius-inner);
  background: var(--close-bg);
  flex-shrink: 0;
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-stage {
  font-size: 18px;
}

.detail-next {
  margin-left: auto;
  flex-shrink: 0;
}

/* 「我 / TA」并列进度块 */
.care-rows {
  margin-bottom: 10px;
}

.care-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 10px;
  padding: 4px 0;
}

.care-who {
  color: var(--ink-primary);
  font-weight: 700;
}

.care-mark {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--ink-secondary);
}

.mark-ok {
  color: var(--success);
}

.mark-no {
  color: var(--handle);
}

.care-state {
  margin-left: auto;
}

.state-done {
  color: var(--success);
  font-weight: 700;
}

.state-wait {
  color: var(--ink-tertiary);
}

.status-hint {
  margin-bottom: 12px;
}

.block-reason {
  text-align: center;
  margin-top: 8px;
}

.journey-btn {
  width: 100%;
  margin-top: 10px;
}

/* 入口卡 */
.entry-card {
  display: flex;
  align-items: center;
  gap: 12px;
}

.entry-icon {
  flex-shrink: 0;
  display: flex;
}

.entry-texts {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.entry-title {
  font-size: 16px;
  font-weight: 700;
}

.entry-cta {
  flex-shrink: 0;
  height: 36px;
  padding: 0 18px;
  border-radius: var(--radius-pill);
  background: var(--accent-cta);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.entry-cta:active {
  opacity: 0.85;
}

/* §8 减弱动态效果 */
@media (prefers-reduced-motion: reduce) {
  .plant-card.highlight {
    animation: none;
  }
}
</style>
