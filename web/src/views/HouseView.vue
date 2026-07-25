<template>
  <!-- P4 花房：45% 黑遮罩 + 底部上滑半屏卡（形态同 P3a，§3-P4） -->
  <div class="p4-page">
    <!-- 遮罩：压暗背景，点击返回花园页 -->
    <div class="p4-mask" :class="{ in: entered }" @click="goGarden"></div>

    <div class="p4-sheet" :class="{ in: entered }">
      <!-- 头部：左「AI插花」（多选态变「取消」）+ 居中标题 + 右上 X -->
      <div class="p4-head">
        <button class="ai-arrange text-body" @click="onHeadLeft">
          {{ picking ? '取消' : 'AI插花' }}
        </button>
        <span class="text-tab">花房</span>
        <button class="sheet-x" aria-label="关闭" @click="goGarden">
          <ResIcon name="close" :size="18" />
        </button>
      </div>

      <div class="p4-scroll">
        <SkeletonLines v-if="loading" />

        <!-- 空态（固定文案） -->
        <div v-else-if="!items.length" class="empty-state">还没有收藏的花朵，先去花园种一朵吧</div>

        <!-- 库存双列网格 -->
        <div v-else class="p4-grid">
          <div v-for="item in items" :key="item.item_id" class="grid-cell" :class="{ 'is-zero': item.quantity === 0 }">
            <div class="cell-img-wrap">
              <img class="cell-img" :src="item.flower_image" :alt="item.species" loading="lazy" />
              <!-- 数量角标：badge-pink 粉底白字胶囊（×0 灰卡角标「x0」） -->
              <span class="cell-badge">x{{ item.quantity }}</span>
            </div>
            <p class="text-caption ink-secondary cell-name">{{ item.species }} · {{ item.color }}</p>

            <!-- ×0 灰态卡：次按钮「重新种植」（§4.3） -->
            <button
              v-if="item.quantity === 0"
              class="btn-ghost replant-btn"
              :disabled="replantingId === item.item_id"
              @click="doReplant(item)"
            >
              {{ replantingId === item.item_id ? '种下中…' : '重新种植' }}
            </button>

            <!-- 自由搭配多选态：步进器（0–库存上限） -->
            <div v-else-if="picking" class="stepper">
              <button class="stepper-btn" :disabled="countOf(item) <= 0" aria-label="减少" @click="change(item, -1)">
                <ResIcon name="minus" :size="16" />
              </button>
              <span class="stepper-num text-body">{{ countOf(item) }}</span>
              <button
                class="stepper-btn"
                :disabled="countOf(item) >= item.quantity"
                aria-label="增加"
                @click="change(item, 1)"
              >
                <ResIcon name="plus" :size="16" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 自由搭配底部操作栏（卡片内 footer） -->
      <div v-if="picking" class="pick-bar">
        <span class="text-caption ink-secondary">已选 {{ totalSelected }} 朵</span>
        <button class="btn-cta pick-cta" :disabled="totalSelected === 0" @click="doPreviewFree">生成花束预览</button>
      </div>
    </div>

    <!-- 「AI插花」动作面板：自底部上滑小弹层（面板外点击 / X 关闭） -->
    <transition name="panel-fade">
      <div v-if="panel" class="panel-mask" @click.self="closePanel">
        <div class="panel-sheet">
          <!-- 面板菜单：双入口 -->
          <template v-if="panel === 'menu'">
            <div class="panel-head">
              <span class="text-tab">AI插花</span>
              <button class="panel-x" aria-label="关闭" @click="closePanel">
                <ResIcon name="close" :size="18" />
              </button>
            </div>
            <button class="panel-option" @click="panel = 'intent'">
              <ResIcon name="spark" variant="flat" shape="none" :size="40" />
              <span class="option-texts">
                <span class="option-title">AI 推荐搭配</span>
                <span class="text-caption ink-tertiary">告诉我送花意图，AI 帮你配</span>
              </span>
            </button>
            <button class="panel-option" @click="enterFreePick">
              <ResIcon name="warehouse" variant="flat" shape="none" :size="40" />
              <span class="option-texts">
                <span class="option-title">自由搭配</span>
                <span class="text-caption ink-tertiary">自己挑选花材</span>
              </span>
            </button>
          </template>

          <!-- 意图选择卡：标题 + 5 个胶囊 chips（可换行） -->
          <template v-else-if="panel === 'intent'">
            <div class="panel-head">
              <span class="text-tab">送花意图</span>
              <button class="panel-x" aria-label="关闭" @click="closePanel">
                <ResIcon name="close" :size="18" />
              </button>
            </div>
            <template v-if="recommending">
              <div class="ai-status">
                <b>AI</b> 正在生成回答 <span class="ai-dots"><i>·</i><i>·</i><i>·</i></span>
              </div>
              <SkeletonLines class="intent-loading" />
            </template>
            <div v-else class="intent-chips">
              <button v-for="o in OCCASIONS" :key="o" class="intent-chip" @click="doRecommend(o)">{{ o }}</button>
            </div>
          </template>

          <!-- 推荐结果卡 -->
          <template v-else-if="panel === 'result' && recommend">
            <div class="panel-head">
              <span class="text-tab">AI 推荐搭配</span>
              <button class="panel-x" aria-label="关闭" @click="closePanel">
                <ResIcon name="close" :size="18" />
              </button>
            </div>
            <div class="ai-status"><b>AI</b> 生成回答</div>
            <p class="recommend-reason text-body content-in">{{ recommend.reason }}</p>
            <div class="recommend-list content-in">
              <div v-for="(m, i) in recommendMaterials" :key="i" class="material-row">
                <span class="text-body">
                  {{ m.species }} · {{ m.color }}
                  <span v-if="m.gifted" class="gift-chip">赠送</span>
                </span>
                <span class="text-body">×{{ m.count }}</span>
              </div>
            </div>
            <button class="btn-cta recommend-cta" @click="doPreviewRecommend">生成花束预览</button>
          </template>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ResIcon from '../components/ResIcon.vue'
import SkeletonLines from '../components/SkeletonLines.vue'
import { getFlowerHouse, replantFlower, recommendBouquet, errorMessage } from '../api/client'
import { useBouquetStore } from '../stores/bouquet'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const bouquet = useBouquetStore()
const toast = useToastStore()

const entered = ref(false) // 上滑进入动画（300ms）
const loading = ref(true)
const items = ref([])

// ---- 自由搭配多选态 ----
const picking = ref(false)
const selections = ref({}) // { [item_id]: count }

const totalSelected = computed(() => Object.values(selections.value).reduce((s, n) => s + n, 0))

function countOf(item) {
  return selections.value[item.item_id] || 0
}

function change(item, delta) {
  // 夹取在 0–库存 之间
  selections.value[item.item_id] = Math.max(0, Math.min(item.quantity, countOf(item) + delta))
}

function enterFreePick() {
  panel.value = null
  picking.value = true
}

// ---- AI插花动作面板（menu / intent / result） ----
const panel = ref(null)
const OCCASIONS = ['情侣约会', '毕业季', '生日祝福', '探望问候', '日常惊喜']
const recommending = ref(false)
const recommend = ref(null) // 1.13 响应 { occasion, items, bonus_flower, reason }

// 推荐结果花材列表：库存花材 + 赠送花材（带 gifted 标记）
const recommendMaterials = computed(() => {
  if (!recommend.value) return []
  const list = [...(recommend.value.items || [])]
  if (recommend.value.bonus_flower) list.push({ ...recommend.value.bonus_flower, gifted: true })
  return list
})

function onHeadLeft() {
  if (picking.value) {
    // 「取消」：退出多选态并清空选择
    picking.value = false
    selections.value = {}
  } else {
    panel.value = 'menu'
  }
}

function closePanel() {
  panel.value = null
  recommend.value = null
}

// 点选意图 → 调 1.13 推荐接口 → 推荐结果卡
async function doRecommend(occasion) {
  if (recommending.value) return
  recommending.value = true
  recommend.value = null
  try {
    recommend.value = await recommendBouquet(occasion)
    panel.value = 'result'
  } catch (err) {
    toast.error(errorMessage(err, '推荐失败，请重试'))
  } finally {
    recommending.value = false
  }
}

// 推荐链路「生成花束预览」：携带赠送花材与意图（items 可为空 = 纯赠送组合）
function doPreviewRecommend() {
  if (!recommend.value) return
  bouquet.startPreview(recommend.value.items || [], {
    bonus: recommend.value.bonus_flower || null,
    occasion: recommend.value.occasion || null
  })
  closePanel()
  router.push('/bouquet/preview')
}

// 自由搭配「生成花束预览」：发起 1.7 并跳转 P5（生成中状态由 P5 展示；409 在 P5 toast 展示 detail）
function doPreviewFree() {
  const selected = items.value
    .filter((item) => countOf(item) > 0)
    .map((item) => ({ species: item.species, color: item.color, count: countOf(item) }))
  if (!selected.length) return
  bouquet.startPreview(selected)
  router.push('/bouquet/preview')
}

// ---- ×0 灰卡「重新种植」（1.2 复种：品种 + 颜色入参） ----
const replantingId = ref(null)

async function doReplant(item) {
  if (replantingId.value != null) return
  replantingId.value = item.item_id
  try {
    await replantFlower(item.species, item.color)
    toast.success('已重新种下，去花园看看吧')
  } catch (err) {
    toast.error(errorMessage(err, '种下失败，请重试'))
  } finally {
    replantingId.value = null
  }
}

// 遮罩点击 / 右上 X：返回花园页
function goGarden() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/garden')
  }
}

async function load() {
  const res = await getFlowerHouse()
  items.value = res.items || []
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
.p4-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-garden);
}

.p4-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  opacity: 0;
  transition: opacity 300ms;
}

.p4-mask.in {
  opacity: 1;
}

.p4-sheet {
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

.p4-sheet.in {
  transform: translateY(0);
}

.p4-head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px var(--space-page) 10px;
  flex-shrink: 0;
}

.ai-arrange {
  position: absolute;
  left: var(--space-page);
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent);
  font-weight: 700;
  min-height: 44px;
  padding: 0 4px;
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

.p4-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-page) calc(16px + env(safe-area-inset-bottom));
}

/* ---- 库存双列网格 ---- */
.p4-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding-top: 6px;
}

.grid-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ×0 灰态卡：整卡灰化（灰滤镜 + 60% 透明度），操作按钮保持可读 */
.grid-cell.is-zero .cell-img-wrap,
.grid-cell.is-zero .cell-name {
  filter: grayscale(1);
  opacity: 0.6;
}

.cell-img-wrap {
  position: relative;
}

.cell-img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: var(--radius-inner);
  background: var(--close-bg);
}

.cell-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: var(--badge-pink);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.cell-name {
  text-align: center;
}

.replant-btn {
  width: 100%;
}

.stepper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.stepper-btn {
  width: 44px; /* §8 热区 ≥44 */
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-primary);
}

.stepper-btn:disabled {
  color: var(--handle);
}

.stepper-num {
  min-width: 24px;
  text-align: center;
  font-weight: 700;
}

/* ---- 自由搭配底部操作栏（卡片内 footer） ---- */
.pick-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px var(--space-page) calc(10px + env(safe-area-inset-bottom));
  background: var(--bg-page);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.05);
}

.pick-cta {
  width: auto;
  padding: 0 24px;
  height: 44px;
}

/* ---- 「AI插花」动作面板 ---- */
.panel-mask {
  position: absolute;
  inset: 0;
  z-index: 60;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
}

.panel-sheet {
  width: 100%;
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  padding: 14px var(--space-page) calc(18px + env(safe-area-inset-bottom));
}

.panel-head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 12px;
}

.panel-x {
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

.panel-x::before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--close-bg);
}

.panel-x svg {
  position: relative;
  color: var(--ink-primary);
}

.panel-option {
  width: 100%;
  min-height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 4px;
  text-align: left;
}

.panel-option:active {
  opacity: 0.7;
}

.option-texts {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-title {
  font-size: 16px;
  font-weight: 700;
}

/* 意图 chips（§4.3 chips 组间距 8px，可换行） */
.intent-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0 6px;
}

.intent-chip {
  min-height: 34px;
  padding: 0 16px;
  border-radius: var(--radius-pill);
  background: var(--close-bg);
  color: var(--ink-secondary);
  font-size: 13px;
}

.intent-chip:active {
  border: 1px solid var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

.intent-loading {
  padding: 10px 0 6px;
}

.panel-sheet .ai-status {
  padding-bottom: 8px;
}

.recommend-reason {
  margin-bottom: 12px;
  color: var(--ink-primary);
}

.recommend-list {
  margin-bottom: 16px;
}

.material-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--close-bg);
}

.material-row:last-child {
  border-bottom: none;
}

/* 「赠送」chip（§4.3：--accent-soft 底，只读展示） */
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

.recommend-cta {
  height: 44px;
}

/* 面板：遮罩淡入 + 卡片上滑（300ms） */
.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 300ms;
}

.panel-fade-enter-active .panel-sheet,
.panel-fade-leave-active .panel-sheet {
  transition: transform 300ms ease-out;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
}

.panel-fade-enter-from .panel-sheet,
.panel-fade-leave-to .panel-sheet {
  transform: translateY(100%);
}

/* §8 减弱动态效果 */
@media (prefers-reduced-motion: reduce) {
  .p4-mask,
  .p4-sheet {
    transition: opacity 200ms;
  }

  .p4-sheet {
    transform: none;
    opacity: 0;
  }

  .p4-sheet.in {
    opacity: 1;
  }

  .panel-fade-enter-active .panel-sheet,
  .panel-fade-leave-active .panel-sheet {
    transition: none;
    transform: none;
  }
}
</style>
