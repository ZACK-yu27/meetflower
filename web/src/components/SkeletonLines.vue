<template>
  <!-- §4.4 骨架屏：3 根横条（100% / 85% / 70% 宽），呼吸动画 -->
  <div class="skeleton-group" aria-hidden="true">
    <div class="skeleton-line" style="width: 100%"></div>
    <div class="skeleton-line" style="width: 85%"></div>
    <div class="skeleton-line" style="width: 70%"></div>
  </div>
</template>

<style scoped>
.skeleton-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}
</style>
