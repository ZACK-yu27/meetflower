<template>
  <!-- 图标组件（§2.3 双档）：
       variant="line" = chrome 图标：圆角线性（≈2px 描边、端点圆润），stroke=currentColor；
       variant="flat" = 内容图标：续火花扁平风（圆润饱满、暖色、浅色衬底 + 饱和图形），
                        shape 控制衬底（square 圆角块 / circle 圆形 / none 无衬底） -->
  <svg
    v-if="variant === 'line'"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="linePaths"
  ></svg>

  <svg v-else :width="size" :height="size" viewBox="0 0 48 48" aria-hidden="true">
    <!-- 浅色衬底（square / circle / none） -->
    <rect v-if="shape === 'square'" x="2" y="2" width="44" height="44" rx="12" :fill="flatDef.bg" />
    <circle v-else-if="shape === 'circle'" cx="24" cy="24" r="22" :fill="flatDef.bg" />
    <g v-html="flatDef.glyph"></g>
    <!-- 奖励/任务类：黄星 + 红色 +N 角标 -->
    <template v-if="name === 'star' && badge > 0">
      <rect x="27" y="30" width="19" height="13" rx="6.5" fill="#FF5A45" />
      <text x="36.5" y="40.5" text-anchor="middle" font-size="11" font-weight="700" fill="#fff">
        +{{ badge }}
      </text>
    </template>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 24 },
  variant: { type: String, default: 'line' }, // line = chrome 线性 / flat = 续火花扁平
  shape: { type: String, default: 'square' }, // 仅 flat：square / circle / none
  badge: { type: Number, default: 0 } // 仅 flat star：红色 +N 角标
})

/* ---- chrome 线性图标库（feather 风格，24 viewBox） ---- */
const LINE_ICONS = {
  water: '<path d="M12 2.7C12 2.7 5.9 9.6 5.9 14a6.1 6.1 0 0 0 12.2 0C18.1 9.6 12 2.7 12 2.7z"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 1.8v2.4M12 19.8v2.4M4.2 4.2l1.7 1.7M18.1 18.1l1.7 1.7M1.8 12h2.4M19.8 12h2.4M4.2 19.8l1.7-1.7M18.1 5.9l1.7-1.7"/>',
  nutrient: '<path d="M12 21.5v-8.5"/><path d="M12 13C12 9.7 9.3 7 5.5 7H4v1.5C4 12.3 7 15 12 15z"/><path d="M12 11c0-3.3 2.7-6 6.5-6H20v1.5c0 3.8-3 6.5-8 6.5z"/>',
  warehouse: '<path d="M21 8.5v7a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 15.5v-7a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8.5z"/><path d="M3.3 7.3 12 12l8.7-4.7"/><path d="M12 22V12"/>',
  layers: '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
  back: '<path d="M15 18l-6-6 6-6"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  camera: '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
  shop: '<path d="M4 7h16l-1.2-4H5.2L4 7z"/><path d="M4 7v13a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V7"/><path d="M9 21v-6h6v6"/>',
  'chevron-down': '<path d="M6 9l6 6 6-6"/>',
  'chevron-right': '<path d="M9 18l6-6-6-6"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  // 更多（···）
  more: '<circle cx="5" cy="12" r="1.7" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.7" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.7" fill="currentColor" stroke="none"/>'
}

/* ---- 续火花扁平风内容图标库（48 viewBox，圆润饱满、暖色） ---- */
const FLAT_ICONS = {
  // 水滴：淡蓝衬底 + 蓝色水滴
  water: {
    bg: '#E3F1FD',
    glyph: '<path d="M24 11C24 11 14.8 21.4 14.8 28.2a9.2 9.2 0 0 0 18.4 0C33.2 21.4 24 11 24 11z" fill="#45A9F5"/><ellipse cx="20.4" cy="27" rx="2.4" ry="3.2" fill="#9CD2FA" transform="rotate(-18 20.4 27)"/>'
  },
  // 阳光：淡黄衬底 + 橙黄太阳
  sun: {
    bg: '#FDF3D7',
    glyph: '<circle cx="24" cy="25" r="8.4" fill="#FFB531"/><circle cx="21" cy="22" r="3" fill="#FFD37A"/><g stroke="#FFB531" stroke-width="3" stroke-linecap="round"><path d="M24 10.5v3"/><path d="M24 36.5v-3"/><path d="M10.5 25h3"/><path d="M34.5 25h3"/><path d="M14.3 15.3l2.1 2.1"/><path d="M31.6 32.6l2.1 2.1"/><path d="M33.7 15.3l-2.1 2.1"/><path d="M16.4 32.6l-2.1 2.1"/></g>'
  },
  // 养料：淡绿衬底 + 绿色嫩芽
  nutrient: {
    bg: '#E6F6E8',
    glyph: '<path d="M24 37V25" stroke="#3E9146" stroke-width="3" stroke-linecap="round"/><path d="M24 26.5C24 19.8 18.6 15.5 11 15.5 11 23.4 16.8 27.5 24 26.5z" fill="#57B25E"/><path d="M24 22.5C24 16.4 29 12.5 35.5 12.5 35.5 19.4 30.4 23.5 24 22.5z" fill="#6EC770"/>'
  },
  // 花房：木箱
  warehouse: {
    bg: '#F3E7D8',
    glyph: '<rect x="13" y="18.5" width="22" height="16.5" rx="3" fill="#D9A066"/><rect x="11" y="12.5" width="26" height="7.5" rx="3" fill="#C08A52"/><path d="M24 21v11.5" stroke="#B87F45" stroke-width="3"/><path d="M13 26.8h22" stroke="#B87F45" stroke-width="2"/>'
  },
  // 资源：明细账本
  ledger: {
    bg: '#FDEBD3',
    glyph: '<rect x="13" y="11" width="22" height="26" rx="4" fill="#F2994A"/><rect x="17" y="15" width="14" height="17" rx="2" fill="#FFF3E4"/><g stroke="#F2C288" stroke-width="2" stroke-linecap="round"><path d="M20 20h8"/><path d="M20 24h8"/><path d="M20 28h5"/></g><path d="M28 11h5v8.5l-2.5-2-2.5 2z" fill="#E2564B"/>'
  },
  // 互发消息：对话气泡
  message: {
    bg: '#E3F0FF',
    glyph: '<rect x="19" y="10" width="18" height="12" rx="6" fill="#9CD2FA"/><path d="M33 22l3 4-6-1.5z" fill="#9CD2FA"/><rect x="10" y="16" width="20" height="13" rx="6.5" fill="#45A9F5"/><path d="M15 29l-2.5 4.5L18 30z" fill="#45A9F5"/><g fill="#fff"><circle cx="16.5" cy="22.5" r="1.5"/><circle cx="21" cy="22.5" r="1.5"/><circle cx="25.5" cy="22.5" r="1.5"/></g>'
  },
  // 分享视频：播放按钮
  video: {
    bg: '#FDE8EF',
    glyph: '<rect x="11" y="13" width="26" height="21" rx="7" fill="#F2567C"/><path d="M21.5 18.8v9.4c0 .9 1 1.5 1.8 1l7.4-4.7c.8-.5.8-1.6 0-2.1l-7.4-4.6c-.8-.5-1.8.1-1.8 1z" fill="#fff"/>'
  },
  // 连续互动：火花
  spark: {
    bg: '#FDEBD3',
    glyph: '<path d="M24 9.5c3 5.4 8 8.4 8 15a8 8 0 0 1-16 0c0-5.2 5-8.6 8-15z" fill="#FF7A45"/><path d="M24 20c1.9 3 4.3 4.4 4.3 7.6a4.3 4.3 0 0 1-8.6 0c0-3.2 2.4-4.6 4.3-7.6z" fill="#FFC531"/><path d="M36 8l1.1 2.6 2.6 1.1-2.6 1.1L36 15.4l-1.1-2.6-2.6-1.1 2.6-1.1z" fill="#FFC531"/>'
  },
  // 相机
  camera: {
    bg: '#E7F0F9',
    glyph: '<path d="M18 16.5l2-4h8l2 4z" fill="#4577CE"/><rect x="10" y="16" width="28" height="19" rx="6" fill="#5B8DEF"/><circle cx="24" cy="25.5" r="6" fill="#fff"/><circle cx="24" cy="25.5" r="3.6" fill="#4577CE"/><circle cx="31.5" cy="20.5" r="1.6" fill="#FFE28A"/>'
  },
  // 灯泡
  bulb: {
    bg: '#FDF3D7',
    glyph: '<path d="M24 11a8.5 8.5 0 0 1 4.6 15.6c-.9.6-1.6 1.5-1.6 2.4v1h-6v-1c0-.9-.7-1.8-1.6-2.4A8.5 8.5 0 0 1 24 11z" fill="#FFC531"/><rect x="21" y="30.5" width="6" height="4" rx="1.6" fill="#E89B0C"/><g stroke="#F2C94C" stroke-width="2" stroke-linecap="round"><path d="M24 4.5v2.5"/><path d="M12.5 9l1.8 1.8"/><path d="M35.5 9l-1.8 1.8"/></g>'
  },
  // 黄星（奖励/任务，可带红色 +N 角标）
  star: {
    bg: '#FDF3D7',
    glyph: '<path d="M24 8.5l3.7 9.3 10 1-7.5 6.5 2.3 9.7-8.5-5.2-8.5 5.2 2.3-9.7-7.5-6.5 10-1z" fill="#FFC531"/><circle cx="19.5" cy="17" r="2.2" fill="#FFDF8E"/>'
  },
  // 花朵（花园入口）
  flower: {
    bg: '#FDE8EF',
    glyph: '<g fill="#FF8FA8"><circle cx="24" cy="14.5" r="5.2"/><circle cx="15.5" cy="21" r="5.2"/><circle cx="32.5" cy="21" r="5.2"/><circle cx="18.5" cy="31" r="5.2"/><circle cx="29.5" cy="31" r="5.2"/></g><circle cx="24" cy="23" r="5.6" fill="#FFC531"/><path d="M24 34v7" stroke="#57B25E" stroke-width="3" stroke-linecap="round"/><path d="M24 38.5c-3 0-5-1.8-5.5-4 3 0 5 1.3 5.5 4z" fill="#6EC770"/>'
  }
}

const linePaths = computed(() => LINE_ICONS[props.name] || '')
const flatDef = computed(() => FLAT_ICONS[props.name] || { bg: '#F4F3F4', glyph: '' })
</script>
