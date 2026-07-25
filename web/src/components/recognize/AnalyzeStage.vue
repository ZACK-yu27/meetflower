<template>
  <!-- P1 识图分析流程（全屏，按参考图复刻：扫描 → 框选 → 卡片上滑） -->
  <div class="p1-page">
    <!-- 所拍图片全屏铺满 + 压暗（黑 40%）；视频入口为静音循环预览 -->
    <video v-if="isVideo" class="p1-img" :src="previewUrl" muted autoplay loop playsinline></video>
    <img v-else class="p1-img" :src="previewUrl" alt="识别中的图片" />
    <div class="p1-dim"></div>

    <!-- 白色扫描光点：随机位置浮动闪烁，持续循环 -->
    <span
      v-for="dot in dots"
      :key="dot.id"
      class="p1-dot"
      :style="{
        left: dot.x + '%',
        top: dot.y + '%',
        width: dot.size + 'px',
        height: dot.size + 'px',
        opacity: dot.opacity,
        animationDelay: dot.delay + 's',
        animationDuration: dot.duration + 's'
      }"
    ></span>

    <!-- 状态二：白色括弧框自画面边缘收缩至中央主体区（约 600ms） -->
    <div v-if="stage !== 'scan'" class="p1-frame" :class="{ shrink: stage !== 'scan', fade: stage === 'card' }">
      <span class="corner tl"></span>
      <span class="corner tr"></span>
      <span class="corner bl"></span>
      <span class="corner br"></span>
    </div>

    <!-- 状态二：左上识别帧缩略图淡入（56px） -->
    <video v-if="isVideo && stage !== 'scan'" class="p1-thumb" :src="previewUrl" muted autoplay loop playsinline></video>
    <img v-else-if="stage !== 'scan'" class="p1-thumb" :src="previewUrl" alt="识别帧" />

    <!-- 状态三：底部半屏卡片上滑（300ms），「AI 正在生成回答 …」+ 骨架条 -->
    <div class="p1-sheet" :class="{ up: stage === 'card' }">
      <div class="sheet-handle"></div>
      <div class="ai-status p1-status">
        <b>AI</b> 正在生成回答
        <span class="ai-dots"><i>·</i><i>·</i><i>·</i></span>
      </div>
      <div class="p1-hint">{{ hint }}</div>
      <SkeletonLines />
    </div>

    <!-- 底部居中深色胶囊「取消」（卡片上滑后隐藏） -->
    <button v-if="stage !== 'card'" class="p1-cancel" @click="$emit('cancel')">取消</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import SkeletonLines from '../SkeletonLines.vue'

defineEmits(['cancel'])

// 流程状态：scan（扫描）→ frame（框选）→ card（卡片上滑）
const stage = ref('scan')
// 分阶段进度文案：真实模型识别约 10–30s（视频链路含抽帧+两段式，可能更久），随等待时长轮换提示
const props = defineProps({
  previewUrl: { type: String, required: true },
  isVideo: { type: Boolean, default: false }
})
const hint = ref(props.isVideo ? '正在逐帧分析视频主体…' : '正在识别花朵品种…')
let timers = []

// 随机扫描光点（直径 6–10px、白色 60–80% 不透明）
const dots = Array.from({ length: 14 }, (_, i) => ({
  id: i,
  x: Math.round(Math.random() * 92 + 2),
  y: Math.round(Math.random() * 88 + 2),
  size: Math.round(Math.random() * 4 + 6),
  opacity: (Math.random() * 0.2 + 0.6).toFixed(2),
  delay: (Math.random() * 1.6).toFixed(2),
  duration: (Math.random() * 1.2 + 1).toFixed(2)
}))

onMounted(() => {
  // 约 0.8s 后进入框选；框选约 600ms 后卡片上滑
  timers.push(setTimeout(() => (stage.value = 'frame'), 800))
  timers.push(setTimeout(() => (stage.value = 'card'), 1400))
  timers.push(setTimeout(() => (hint.value = props.isVideo ? '正在匹配最相似的花卉…' : '正在撰写专属科普…'), 8000))
  timers.push(setTimeout(() => (hint.value = props.isVideo ? '视频分析较耗时，请耐心等待…' : '模型有点忙，马上就好…'), 20000))
  timers.push(setTimeout(() => (hint.value = '首次使用可能较慢，马上就好…'), 45000))
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
})
</script>

<style scoped>
.p1-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-dark);
}

.p1-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.p1-dim {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
}

.p1-dot {
  position: absolute;
  border-radius: 50%;
  background: #fff;
  animation: dot-float 1.6s ease-in-out infinite alternate;
}

@keyframes dot-float {
  from {
    transform: translate(0, 0);
  }
  to {
    transform: translate(6px, -10px);
    opacity: 0.35;
  }
}

/* 括弧框：初始铺满画面边缘，shrink 后收缩至中央主体区 */
.p1-frame {
  position: absolute;
  left: 4%;
  top: calc(4% + env(safe-area-inset-top));
  right: 4%;
  bottom: 14%;
  transition: left 600ms ease, right 600ms ease, top 600ms ease, bottom 600ms ease, opacity 300ms;
}

.p1-frame.shrink {
  left: 12%;
  right: 12%;
  top: 22%;
  bottom: 38%;
}

.p1-frame.fade {
  opacity: 0;
}

.corner {
  position: absolute;
  width: 28px;
  height: 28px;
  border: 2px solid #fff;
}

.corner.tl {
  left: 0;
  top: 0;
  border-right: none;
  border-bottom: none;
  border-top-left-radius: 10px;
}

.corner.tr {
  right: 0;
  top: 0;
  border-left: none;
  border-bottom: none;
  border-top-right-radius: 10px;
}

.corner.bl {
  left: 0;
  bottom: 0;
  border-right: none;
  border-top: none;
  border-bottom-left-radius: 10px;
}

.corner.br {
  right: 0;
  bottom: 0;
  border-left: none;
  border-top: none;
  border-bottom-right-radius: 10px;
}

.p1-thumb {
  position: absolute;
  top: calc(14px + env(safe-area-inset-top));
  left: var(--space-page);
  width: 56px;
  height: 56px;
  border-radius: var(--radius-inner);
  object-fit: cover;
  border: 1.5px solid rgba(255, 255, 255, 0.9);
  animation: thumb-in 300ms ease-out;
}

@keyframes thumb-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.p1-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-page);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  padding: 10px var(--space-page) calc(20px + env(safe-area-inset-bottom));
  transform: translateY(100%);
  transition: transform 300ms ease-out;
}

.p1-sheet.up {
  transform: translateY(0);
}

.sheet-handle {
  width: 36px;
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--handle);
  margin: 0 auto 12px;
}

.p1-status {
  margin-bottom: 10px;
}

.p1-hint {
  font-size: 12px;
  color: var(--ink-tertiary);
  margin: -4px 0 10px;
}

.p1-cancel {
  position: absolute;
  bottom: calc(28px + env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  min-width: 120px;
  height: 44px;
  padding: 0 28px;
  border-radius: var(--radius-pill);
  background: var(--float-pill);
  color: #fff;
  font-size: 15px;
}

/* §8 减弱动态效果：扫描/框选简化为淡入淡出 */
@media (prefers-reduced-motion: reduce) {
  .p1-dot {
    animation: none;
  }

  .p1-frame {
    transition: opacity 300ms;
  }
}
</style>
