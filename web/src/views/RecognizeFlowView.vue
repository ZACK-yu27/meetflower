<template>
  <!-- 识图流程编排：P1 分析流程 → P2 AI 科普页（组件状态机驱动） -->
  <AnalyzeStage v-if="phase === 'analyze' && session.previewUrl" :preview-url="session.previewUrl" :is-video="isVideo" @cancel="onCancel" />
  <ResultSheet
    v-else-if="phase === 'result' && session.result"
    :preview-url="session.previewUrl"
    :is-video="isVideo"
    :result="session.result"
    @close="onClose"
    @planted="onPlanted"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AnalyzeStage from '../components/recognize/AnalyzeStage.vue'
import ResultSheet from '../components/recognize/ResultSheet.vue'
import { recognize, recognizeVideo, errorMessage } from '../api/client'
import { useRecognizeStore } from '../stores/recognize'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const session = useRecognizeStore()
const toast = useToastStore()

// P1 引导动画保底约 2s（§3-P1 节奏）
const MIN_ANIMATION_MS = 2000

const phase = ref('analyze')
let cancelled = false

// 广义的花：视频走 /recognitions/video（flower_resemble.md）
const isVideo = computed(() => Boolean(session.file?.type?.startsWith('video/')))

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

onMounted(async () => {
  // 刷新 / 直达 /recognize：无会话图片一律回 P0
  if (!session.file || !session.previewUrl) {
    router.replace('/')
    return
  }
  // 上传请求在动画开始时即发出；接口返回 + 动画保底后进入 P2
  try {
    const request = isVideo.value ? recognizeVideo(session.file) : recognize(session.file)
    const [result] = await Promise.all([request, delay(MIN_ANIMATION_MS)])
    if (cancelled) return
    session.setResult(result)
    phase.value = 'result'
  } catch (err) {
    if (cancelled) return
    toast.error(errorMessage(err, '识别失败，请重新拍摄'))
    onClose()
  }
})

// P1「取消」：中断并回 P0
function onCancel() {
  cancelled = true
  onClose()
}

// P2 右上 X / 失败：放弃本次识别、回 P0
function onClose() {
  session.clear()
  router.replace('/')
}

// 「进入花园」种植成功：进入 P-chat 仿抖音聊天页
function onPlanted() {
  session.clear()
  router.replace('/chat')
}
</script>
