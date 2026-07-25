<template>
  <!-- P-chat 仿抖音聊天页（互动模拟器 · 聊天入口叙事） -->
  <div class="chat-page">
    <!-- 标题栏：左返回 + 居中「小葵」+ Mini 灰字 -->
    <header class="chat-head">
      <button class="head-back" aria-label="返回" @click="goBack">
        <ResIcon name="back" :size="24" />
      </button>
      <div class="chat-title">
        <span class="text-tab">小葵</span>
        <span class="chat-sub text-mini ink-tertiary">伴侣火花 · 关系花园</span>
      </div>
      <span class="head-spacer"></span>
    </header>

    <!-- 消息流（纵向滚动） -->
    <div ref="listEl" class="chat-scroll">
      <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="[`from-${m.from}`, { system: m.type === 'system' }]">
        <!-- 系统灰条（延续互动） -->
        <span v-if="m.type === 'system'" class="sys-bar text-mini">{{ m.text }}</span>
        <!-- 视频卡泡（分享视频） -->
        <div v-else-if="m.type === 'video'" class="video-card">
          <span class="video-play"></span>
          <span class="video-caption text-caption">分享视频</span>
        </div>
        <!-- 文本泡 -->
        <div v-else class="bubble">{{ m.text }}</div>
      </div>
    </div>

    <!-- 底部固定区 -->
    <div class="chat-bottom">
      <!-- 模拟输入条（占位不可输入） -->
      <div class="fake-input text-body">发消息…</div>

      <!-- 「花园」入口条 -->
      <button class="garden-entry" @click="router.push('/garden')">
        <ResIcon name="flower" variant="flat" shape="none" :size="22" />
        <span class="entry-label text-body">花园</span>
        <ResIcon name="chevron-right" :size="18" class="entry-arrow" />
      </button>

      <!-- Demo 互动模拟器 -->
      <div class="sim-box">
        <p class="sim-caption text-caption ink-tertiary">Demo 互动模拟器 · 点击模拟聊天互动</p>
        <div class="sim-row">
          <button v-for="d in demos" :key="d.kind" class="sim-btn" :disabled="simBusy" @click="doInteract(d.kind)">
            {{ d.label }}
          </button>
        </div>
        <button class="btn-ghost sim-reset" @click="resetVisible = true">重新体验</button>
      </div>
    </div>

    <!-- 「重新体验」确认弹窗（§P7） -->
    <Modal
      v-model:visible="resetVisible"
      title="重新体验"
      body="将清空当前演示数据并恢复初始状态"
      confirm-text="重新体验"
      :busy="resetting"
      @confirm="doReset"
    />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import ResIcon from '../components/ResIcon.vue'
import Modal from '../components/Modal.vue'
import { simulateInteraction, resetDemo, errorMessage } from '../api/client'
import { useToastStore } from '../stores/toast'
import { chatDemo } from '../demo/chatDemo'

const router = useRouter()
const toast = useToastStore()

const messages = ref([...chatDemo.preset])
const listEl = ref(null)
const simBusy = ref(false)
const resetVisible = ref(false)
const resetting = ref(false)

const demos = [
  { kind: 'mutual_message', label: '互发消息' },
  { kind: 'share_video', label: '分享视频' },
  { kind: 'streak', label: '延续互动' }
]

async function scrollToBottom() {
  await nextTick()
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
}

async function doInteract(kind) {
  if (simBusy.value) return
  simBusy.value = true
  try {
    const res = await simulateInteraction(kind)
    // 消息流追加对应模拟消息
    if (kind === 'mutual_message') {
      messages.value.push(...chatDemo.simulated.mutual_message.map((m) => ({ ...m })))
    } else if (kind === 'share_video') {
      // 归属按接口文案区分：「TA 分享…」= 左泡（ta），否则右泡（我）
      const from = res.event?.description?.startsWith('TA') ? 'ta' : 'me'
      messages.value.push({ from, ...chatDemo.simulated.share_video })
    } else if (kind === 'streak') {
      messages.value.push({ from: 'system', ...chatDemo.simulated.streak })
    }
    await scrollToBottom()
    // toast 展示资源来源文案（接口 event.description 原文）
    if (res.event?.description) toast.success(res.event.description)
  } catch (err) {
    toast.error(errorMessage(err))
  } finally {
    simBusy.value = false
  }
}

// 「重新体验」：确认后调 1.15 → toast → 回 P0
async function doReset() {
  if (resetting.value) return
  resetting.value = true
  try {
    await resetDemo()
    resetVisible.value = false
    toast.success('已重置，欢迎体验')
    router.replace('/')
  } catch (err) {
    toast.error(errorMessage(err, '重置失败，请重试'))
  } finally {
    resetting.value = false
  }
}

function goBack() {
  // → P3 或页面栈上一页
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/garden')
  }
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
}

/* ---- 标题栏 ---- */
.chat-head {
  display: flex;
  align-items: center;
  padding: calc(6px + env(safe-area-inset-top)) var(--space-page) 8px;
  flex-shrink: 0;
}

.head-back {
  width: 44px;
  height: 44px;
  margin-left: -10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-primary);
}

.chat-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.3;
}

.chat-sub {
  margin-top: 1px;
}

.head-spacer {
  margin-left: auto;
  width: 44px;
}

/* ---- 消息流 ---- */
.chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px var(--space-page);
}

.msg-row {
  display: flex;
  margin-bottom: 12px;
}

.msg-row.from-ta {
  justify-content: flex-start;
}

.msg-row.from-me {
  justify-content: flex-end;
}

.msg-row.system {
  justify-content: center;
}

.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
}

.from-ta .bubble {
  background: var(--close-bg);
  color: var(--ink-primary);
  border-top-left-radius: 6px;
}

.from-me .bubble {
  background: var(--accent-soft);
  color: var(--ink-primary);
  border-top-right-radius: 6px;
}

.sys-bar {
  background: var(--close-bg);
  color: var(--ink-tertiary);
  padding: 4px 14px;
  border-radius: var(--radius-pill);
}

.video-card {
  width: 148px;
  height: 96px;
  border-radius: var(--radius-inner);
  background: linear-gradient(135deg, #3a4a5c 0%, #232c38 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.video-play {
  width: 0;
  height: 0;
  border-left: 14px solid #fff;
  border-top: 9px solid transparent;
  border-bottom: 9px solid transparent;
  margin-left: 4px;
}

.video-caption {
  color: rgba(255, 255, 255, 0.85);
}

/* ---- 底部固定区 ---- */
.chat-bottom {
  flex-shrink: 0;
  border-top: 1px solid var(--close-bg);
  padding: 10px var(--space-page) calc(10px + env(safe-area-inset-bottom));
}

.fake-input {
  height: 40px;
  border-radius: var(--radius-pill);
  background: var(--close-bg);
  color: var(--ink-tertiary);
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-size: 15px;
}

.garden-entry {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 6px;
}

.entry-label {
  flex: 1;
  text-align: left;
  font-weight: 700;
}

.entry-arrow {
  color: var(--ink-tertiary);
}

.sim-box {
  background: var(--close-bg);
  border-radius: var(--radius-card);
  padding: 10px 12px 12px;
}

.sim-caption {
  margin-bottom: 8px;
}

.sim-row {
  display: flex;
  gap: 8px;
}

.sim-btn {
  flex: 1;
  min-height: 44px; /* §8 模拟器按钮扩展热区 */
  border-radius: var(--radius-pill);
  background: #ffebd2;
  color: #f2994a;
  font-size: 14px;
  font-weight: 700;
}

.sim-btn:active {
  opacity: 0.8;
}

.sim-btn:disabled {
  opacity: 0.5;
}

.sim-reset {
  width: 100%;
  margin-top: 10px;
  background: #fff;
}
</style>
