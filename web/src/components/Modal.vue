<template>
  <!-- §3-P7 模态弹窗：遮罩黑 45% + 居中白卡（宽 76%），主按钮胶囊 + 可选次按钮 -->
  <transition name="modal-fade">
    <div v-if="visible" class="modal-mask" @click.self="onMask">
      <div class="modal-card">
        <div class="modal-title text-body">{{ title }}</div>
        <div class="modal-body text-body">{{ body }}</div>
        <button class="btn-cta modal-btn" :disabled="busy" @click="$emit('confirm')">{{ confirmText }}</button>
        <button v-if="secondaryText" class="btn-ghost modal-btn-sub" :disabled="busy" @click="$emit('secondary')">
          {{ secondaryText }}
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  confirmText: { type: String, default: '知道了' },
  secondaryText: { type: String, default: '' }, // 次按钮文案（如「知道了」），空则不展示
  busy: { type: Boolean, default: false },
  closeOnMask: { type: Boolean, default: true }
})

const emit = defineEmits(['confirm', 'secondary', 'update:visible'])

function onMask() {
  emit('update:visible', false)
}
</script>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 150;
}

.modal-card {
  width: 76%;
  max-width: 360px;
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 22px 20px 20px;
  text-align: center;
}

.modal-title {
  font-weight: 700;
  margin-bottom: 8px;
}

.modal-body {
  color: var(--ink-secondary);
  font-size: 15px;
  margin-bottom: 18px;
}

.modal-btn {
  height: 42px;
  font-size: 15px;
}

.modal-btn-sub {
  width: 100%;
  margin-top: 8px;
}

/* §6 弹窗：遮罩淡入 + 卡片 0.95→1.0 缩放，200ms */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 200ms;
}

.modal-fade-enter-active .modal-card,
.modal-fade-leave-active .modal-card {
  transition: transform 200ms;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal-card,
.modal-fade-leave-to .modal-card {
  transform: scale(0.95);
}
</style>
