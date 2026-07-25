<template>
  <!-- P3 花园场景（中央主视觉）：等距 2.5D 土地块直接悬浮于渐变页底之上（无独立场景面板、无深色底） -->
  <div ref="sceneEl" class="scene">
    <!-- 土地块：草皮顶面（自然绿渐变+细草纹）+ 土层侧面（深棕渐变+颗粒纹理） -->
    <svg class="scene-svg" viewBox="0 0 400 460" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="grassGrad" x1="0" y1="0" x2="0.35" y2="1">
          <stop offset="0%" stop-color="#8FBE5D" />
          <stop offset="55%" stop-color="#6BA244" />
          <stop offset="100%" stop-color="#578A35" />
        </linearGradient>
        <radialGradient id="grassLight" cx="32%" cy="26%" r="65%">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.2" />
          <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
        </radialGradient>
        <linearGradient id="soilLeft" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#6E4B2F" />
          <stop offset="100%" stop-color="#4A2F1B" />
        </linearGradient>
        <linearGradient id="soilRight" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#59391F" />
          <stop offset="100%" stop-color="#38220F" />
        </linearGradient>
      </defs>

      <!-- 土层两侧面 + 土块颗粒 -->
      <polygon points="16,214 200,320 200,372 16,266" fill="url(#soilLeft)" />
      <polygon points="384,214 200,320 200,372 384,266" fill="url(#soilRight)" />
      <ellipse
        v-for="(g, i) in soilGrains"
        :key="'g' + i"
        :cx="g.x"
        :cy="g.y"
        :rx="g.rx"
        :ry="g.ry"
        :fill="g.color"
        :opacity="g.opacity"
      />
      <!-- 草皮顶面 + 下沿描边 + 细草纹 -->
      <polygon points="200,108 384,214 200,320 16,214" fill="url(#grassGrad)" />
      <polygon points="200,108 384,214 200,320 16,214" fill="url(#grassLight)" />
      <polyline points="16,214 200,320 384,214" fill="none" stroke="#4F7D31" stroke-width="2" opacity="0.5" />
      <line
        v-for="(t, i) in grassTicks"
        :key="'t' + i"
        :x1="t.x1"
        :y1="t.y1"
        :x2="t.x2"
        :y2="t.y2"
        :stroke="t.color"
        stroke-width="1.1"
        stroke-linecap="round"
        :opacity="t.opacity"
      />
    </svg>

    <!-- 植株层：地栽版透明底阶段图，按 index 排布菱形网格（已过滤 pressed） -->
    <div
      v-for="plant in laidOut"
      :key="plant.plant_id"
      class="plant"
      :class="{ selected: plant.plant_id === selectedId }"
      :style="{ left: plant.x + '%', top: plant.y + '%', zIndex: 10 + plant.z }"
      :ref="(el) => setPlantRef(plant.plant_id, el)"
      @click="$emit('select', plant)"
    >
      <span v-if="plant.plant_id === selectedId" class="halo"></span>
      <img
        :src="plant.stage_image"
        :alt="plant.stage_name"
        :style="{ width: sizeFor(plant) + 'px' }"
        :class="{ grow: growingIds.includes(plant.plant_id) }"
        draggable="false"
      />
    </div>

    <!-- 场景上沿资源条：三枚白色胶囊（扁平图标+数量），点击进 P3a -->
    <div class="res-bar">
      <button
        v-for="r in hudList"
        :key="r.key"
        class="res-pill"
        :ref="(el) => setHudRef(r.key, el)"
        :aria-label="r.name"
        @click="$emit('openResources')"
      >
        <ResIcon :name="r.icon" variant="flat" shape="none" :size="16" />
        <b>{{ r.count }}</b>
      </button>
    </div>

    <!-- 照料反馈：资源图标自资源条飞向植株（≤600ms） -->
    <span
      v-for="f in flying"
      :key="f.id"
      class="fly-icon"
      :style="{ left: f.x + 'px', top: f.y + 'px', '--dx': f.dx + 'px', '--dy': f.dy + 'px' }"
    >
      <ResIcon :name="f.icon" variant="flat" shape="none" :size="20" />
    </span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ResIcon from '../ResIcon.vue'

const props = defineProps({
  plants: { type: Array, default: () => [] }, // 已过滤 pressed
  resources: { type: Object, default: () => ({}) }, // 我的储备（resources.me）
  selectedId: { type: Number, default: null },
  growingIds: { type: Array, default: () => [] } // 正在播放成长动画的植株
})

defineEmits(['select', 'openResources'])

/* ---- 场景装饰纹理：种子随机，保证渲染稳定 ---- */
function mulberry32(seed) {
  return function () {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rand = mulberry32(20260725)

// 草皮菱形：中心 (200,214)，rx=184，ry=106
const grassTicks = []
for (let i = 0; i < 54; i++) {
  const u = rand() * 2 - 1
  const v = rand() * 2 - 1
  if (Math.abs(u) + Math.abs(v) > 1) continue
  const x = 200 + u * 184
  const y = 214 + v * 106
  const len = 3 + rand() * 3.5
  const tilt = (rand() - 0.5) * 1.1
  grassTicks.push({
    x1: x.toFixed(1),
    y1: y.toFixed(1),
    x2: (x + Math.sin(tilt) * len).toFixed(1),
    y2: (y - Math.cos(tilt) * len * 0.55).toFixed(1),
    color: rand() > 0.5 ? '#4F7D31' : '#A4CB72',
    opacity: (0.3 + rand() * 0.3).toFixed(2)
  })
}

// 土层颗粒：t 沿斜边、s 沿厚度方向
const soilGrains = []
for (let i = 0; i < 48; i++) {
  const t = rand()
  const s = rand()
  const right = rand() > 0.5
  const x = right ? 384 - t * 184 : 16 + t * 184
  const y = 214 + t * 106 + s * 50
  soilGrains.push({
    x: (x + (rand() - 0.5) * 4).toFixed(1),
    y: y.toFixed(1),
    rx: (1.5 + rand() * 2).toFixed(1),
    ry: (1 + rand() * 1.4).toFixed(1),
    color: rand() > 0.45 ? '#8A6540' : '#2E1C0C',
    opacity: (0.25 + rand() * 0.3).toFixed(2)
  })
}

/* ---- 植株菱形网格排布（4×4 槽位，中心优先） ---- */
const SLOTS = [
  [1, 1], [2, 1], [1, 2], [2, 2],
  [1, 0], [0, 1], [2, 3], [3, 2],
  [0, 2], [2, 0], [3, 1], [1, 3],
  [0, 0], [3, 3], [0, 3], [3, 0]
]

const laidOut = computed(() =>
  props.plants.slice(0, SLOTS.length).map((p, i) => {
    const [c, r] = SLOTS[i]
    return {
      ...p,
      z: c + r,
      x: ((200 + (c - r) * 34) / 400) * 100,
      y: ((128 + ((c + r) / 6) * 172) / 460) * 100
    }
  })
)

// 阶段越高，植株图越大
const STAGE_SIZES = [34, 44, 56, 66, 78]
function sizeFor(plant) {
  return STAGE_SIZES[Math.min(plant.stage_order ?? 0, 4)]
}

/* ---- 资源条 ---- */
const hudList = computed(() => [
  { key: 'water', icon: 'water', name: '水滴', count: props.resources.water ?? 0 },
  { key: 'sunlight', icon: 'sun', name: '阳光', count: props.resources.sunlight ?? 0 },
  { key: 'nutrient', icon: 'nutrient', name: '养料', count: props.resources.nutrient ?? 0 }
])

/* ---- 生长反馈 ---- */

/* ---- 照料飞行动画：资源图标自资源条飞向植株 ---- */
const sceneEl = ref(null)
const hudRefs = {}
const plantRefs = {}
const flying = ref([])
let flySeq = 0

function setHudRef(key, el) {
  if (el) hudRefs[key] = el
}

function setPlantRef(id, el) {
  if (el) plantRefs[id] = el
}

const FLY_ICONS = { water: 'water', sunlight: 'sun', nutrient: 'nutrient' }

function flyToPlant(applied, plantId) {
  const sceneRect = sceneEl.value?.getBoundingClientRect()
  const plantRect = plantRefs[plantId]?.getBoundingClientRect()
  if (!sceneRect || !plantRect) return
  const endX = plantRect.left - sceneRect.left + plantRect.width / 2
  const endY = plantRect.top - sceneRect.top + plantRect.height / 3
  const kinds = ['water', 'sunlight', 'nutrient'].filter((k) => applied?.[k] > 0)
  kinds.forEach((kind, i) => {
    const pillRect = hudRefs[kind]?.getBoundingClientRect()
    const startX = pillRect ? pillRect.left - sceneRect.left + pillRect.width / 2 : 30 + i * 30
    const startY = pillRect ? pillRect.top - sceneRect.top + pillRect.height / 2 : 30
    flying.value.push({
      id: ++flySeq,
      icon: FLY_ICONS[kind],
      x: startX - 10,
      y: startY - 10,
      dx: endX - startX,
      dy: endY - startY
    })
  })
  if (kinds.length) setTimeout(() => (flying.value = []), 600)
}

defineExpose({ flyToPlant })
</script>

<style scoped>
.scene {
  position: relative;
  height: 100%;
}

.scene-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.plant {
  position: absolute;
  transform: translate(-50%, -88%);
  cursor: pointer;
  padding: 6px; /* 扩大点选热区 */
}

.plant img {
  transition: transform 200ms ease;
  filter: drop-shadow(0 3px 3px rgba(0, 0, 0, 0.25));
}

.plant.selected img {
  transform: translateY(-4px); /* 选中轻微上浮 */
}

/* 选中地面光圈高亮 */
.halo {
  position: absolute;
  left: 50%;
  bottom: 2px;
  width: 54px;
  height: 18px;
  transform: translateX(-50%);
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(255, 255, 255, 0.55) 0%, rgba(255, 255, 255, 0) 70%);
  border: 1.5px solid rgba(255, 255, 255, 0.75);
  animation: halo-pulse 1.6s ease-in-out infinite;
}

@keyframes halo-pulse {
  0%,
  100% {
    opacity: 0.85;
  }
  50% {
    opacity: 0.45;
  }
}

/* 成长动画（§6：0.9→1.05→1.0，≤600ms） */
.plant img.grow {
  animation: plant-grow 600ms ease;
}

@keyframes plant-grow {
  0% {
    transform: translateY(-4px) scale(0.9);
  }
  50% {
    transform: translateY(-4px) scale(1.05);
  }
  100% {
    transform: translateY(-4px) scale(1);
  }
}

/* 资源条：三枚白色胶囊 */
.res-bar {
  position: absolute;
  top: calc(10px + env(safe-area-inset-top));
  left: var(--space-page);
  display: flex;
  gap: 8px;
  z-index: 30;
}

.res-pill {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 44px;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-pill);
  background: #fff;
  box-shadow: var(--shadow-float);
  color: var(--ink-primary);
  font-size: 14px;
}

/* §8：热区扩展至 ≥44px（视觉尺寸不变） */
.res-pill::after {
  content: '';
  position: absolute;
  inset: -6px -4px;
}

.res-pill b {
  font-weight: 700;
}

.res-pill:active {
  opacity: 0.8;
}

/* 飞行资源图标 */
.fly-icon {
  position: absolute;
  z-index: 40;
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.7));
  animation: fly-to-plant 550ms ease-in forwards;
  pointer-events: none;
}

@keyframes fly-to-plant {
  to {
    transform: translate(var(--dx), var(--dy)) scale(0.6);
    opacity: 0.2;
  }
}

/* §8 减弱动态效果 */
@media (prefers-reduced-motion: reduce) {
  .halo,
  .plant img.grow {
    animation: none;
  }

  .fly-icon {
    animation: fly-fade-only 400ms ease forwards;
  }
}

@keyframes fly-fade-only {
  to {
    opacity: 0;
  }
}
</style>
