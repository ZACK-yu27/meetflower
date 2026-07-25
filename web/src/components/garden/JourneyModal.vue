<template>
  <!-- 「查看完整成长旅程」旅程弹窗：五阶段横排递进点亮（每档约 300ms）→「已盛放」 -->
  <transition name="journey-fade">
    <div v-if="visible" class="journey-mask">
      <div class="journey-card">
        <!-- 五阶段图横向递进 -->
        <div class="journey-stages">
          <div
            v-for="(s, i) in stages"
            :key="s.key"
            class="journey-stage"
            :class="{ lit: i < litCount }"
          >
            <img :src="s.img" :alt="s.name" />
            <span class="text-mini ink-tertiary">{{ s.name }}</span>
          </div>
        </div>

        <!-- 递进完成后展示 -->
        <template v-if="finished">
          <div class="journey-title text-title content-in">已盛放</div>
          <p class="journey-caption text-caption ink-tertiary content-in">这朵花经历了完整的成长旅程</p>
          <button class="btn-cta journey-cta content-in" @click="$emit('finish')">去压花收藏</button>
        </template>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { STAGE_ORDER, STAGE_NAMES } from '../../utils/format'

const props = defineProps({
  visible: { type: Boolean, default: false },
  plant: { type: Object, default: null } // 快进后的植株（stage_image 为盛放图）
})

defineEmits(['finish'])

const litCount = ref(0)
const finished = ref(false)
let timer = null

// 由当前阶段图 URL 推导五阶段图（同目录同命名规范，仅替换阶段后缀）
function stageUrl(stageKey) {
  const url = props.plant?.stage_image || ''
  if (/_stage_|_(seed|sprout|seedling|bud|bloom)\.png$/.test(url)) {
    return url.replace(/_(seed|sprout|seedling|bud|bloom)\.png$/, `_${stageKey}.png`)
  }
  return url
}

const stages = computed(() =>
  STAGE_ORDER.map((key) => ({ key, name: STAGE_NAMES[key], img: stageUrl(key) }))
)

watch(
  () => props.visible,
  (v) => {
    clearInterval(timer)
    litCount.value = 0
    finished.value = false
    if (!v) return
    // 每档约 300ms 逐一点亮
    timer = setInterval(() => {
      litCount.value += 1
      if (litCount.value >= stages.value.length) {
        clearInterval(timer)
        finished.value = true
      }
    }, 300)
  }
)

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.journey-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 150;
}

.journey-card {
  width: 86%;
  max-width: 400px;
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 24px 18px 20px;
  text-align: center;
}

.journey-stages {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 18px;
}

.journey-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  opacity: 0.3;
  filter: grayscale(1);
  transform: scale(0.92);
  transition: opacity 300ms, filter 300ms, transform 300ms;
}

.journey-stage.lit {
  opacity: 1;
  filter: none;
  transform: scale(1);
}

.journey-stage img {
  width: 52px;
  height: 52px;
  object-fit: contain;
  border-radius: var(--radius-inner);
  background: var(--close-bg);
}

.journey-title {
  font-size: 20px;
  margin-bottom: 4px;
}

.journey-caption {
  margin-bottom: 16px;
}

.journey-cta {
  height: 44px;
}

/* 弹窗：遮罩淡入 + 卡片 0.95→1.0 缩放，200ms */
.journey-fade-enter-active,
.journey-fade-leave-active {
  transition: opacity 200ms;
}

.journey-fade-enter-active .journey-card,
.journey-fade-leave-active .journey-card {
  transition: transform 200ms;
}

.journey-fade-enter-from,
.journey-fade-leave-to {
  opacity: 0;
}

.journey-fade-enter-from .journey-card,
.journey-fade-leave-to .journey-card {
  transform: scale(0.95);
}

/* §8 减弱动态效果：递进动画简化为淡入 */
@media (prefers-reduced-motion: reduce) {
  .journey-stage,
  .journey-stage.lit {
    transition: opacity 200ms;
    transform: none;
    filter: none;
  }
}
</style>
