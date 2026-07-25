<template>
  <!-- 白底整页标题栏：左返回 + 居中标题 + 右侧插槽（抖音小程序式 chrome） -->
  <header class="page-header">
    <button class="header-back" aria-label="返回" @click="goBack">
      <ResIcon name="back" :size="24" />
    </button>
    <h1 class="header-title text-tab">{{ title }}</h1>
    <div class="header-right">
      <slot name="right" />
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import ResIcon from './ResIcon.vue'

defineProps({
  title: { type: String, required: true }
})

const router = useRouter()

function goBack() {
  // 页面栈返回；无历史时回花园（演示直达场景）
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/garden')
  }
}
</script>

<style scoped>
.page-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  height: calc(52px + env(safe-area-inset-top));
  padding: env(safe-area-inset-top) var(--space-page) 0;
  background: var(--bg-page);
}

.header-back {
  width: 44px; /* §8 可点区域 ≥44×44 */
  height: 44px;
  margin-left: -10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-primary);
}

.header-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  min-height: 44px;
}
</style>
