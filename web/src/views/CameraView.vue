<template>
  <!-- P0 相机入口页：深底 --bg-dark 整页 -->
  <div class="p0-page">
    <!-- 左上 X（演示环境：回到页面栈上一页或停留在本页） -->
    <button class="p0-close" aria-label="关闭" @click="onClose">
      <ResIcon name="close" :size="22" />
    </button>

    <!-- 中央下方大号虚线胶囊大卡（拍照/相册） -->
    <div class="p0-upload-card" role="button" tabindex="0" @click="pickImage" @keydown.enter="pickImage">
      <span class="p0-plus">
        <ResIcon name="plus" :size="30" />
      </span>
      <span class="p0-upload-title">拍照识花</span>
      <span class="p0-upload-sub">或从相册上传</span>
    </div>

    <!-- 约束 Caption -->
    <p class="p0-caption text-caption">JPEG/PNG，≤10MB</p>

    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png"
      hidden
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ResIcon from '../components/ResIcon.vue'
import { useRecognizeStore } from '../stores/recognize'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const recognize = useRecognizeStore()
const toast = useToastStore()

const fileInput = ref(null)

function pickImage() {
  fileInput.value.click()
}

function onFileChange(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  // 上传非法以 toast 提示（§3-P7）
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    toast.error('只支持 JPEG/PNG 图片，换一张试试')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    toast.error('图片不能超过 10MB，换一张试试')
    return
  }
  // 选定图片后立即进入 P1
  recognize.startSession(file)
  router.push('/recognize')
}

function onClose() {
  // 演示环境：有历史则返回上一页，否则停留本页
  if (window.history.length > 1) router.back()
}
</script>

<style scoped>
.p0-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg-dark);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding-bottom: calc(120px + env(safe-area-inset-bottom));
  position: relative;
}

.p0-close {
  position: absolute;
  top: calc(10px + env(safe-area-inset-top));
  left: 6px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.85);
}

.p0-upload-card {
  width: calc(100% - 2 * var(--space-page));
  border: 2px dashed rgba(255, 255, 255, 0.45);
  border-radius: var(--radius-card);
  padding: 44px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #fff;
}

.p0-upload-card:active {
  background: rgba(255, 255, 255, 0.06);
}

.p0-plus {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.p0-upload-title {
  font-size: 18px;
  font-weight: 700;
}

.p0-upload-sub {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.p0-caption {
  margin-top: 14px;
  color: rgba(255, 255, 255, 0.45);
}
</style>
