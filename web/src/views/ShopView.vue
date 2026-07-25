<template>
  <!-- P6 抖音电商原型页（纯静态原型，不接后端；演示数据见 src/demo/shopDemo.js） -->
  <div class="p6-page">
    <PageHeader title="订单详情" />

    <div class="p6-body">
      <!-- 店铺条 -->
      <div class="shop-bar">
        <span class="shop-icon"><ResIcon name="shop" :size="20" /></span>
        <span class="text-body shop-name">{{ demo.shop.name }}</span>
        <span class="text-caption ink-tertiary">{{ demo.shop.tag }}</span>
      </div>

      <!-- 商品卡 -->
      <div class="product-card">
        <div class="product-img">💐</div>
        <div class="product-info">
          <p class="text-body product-title">{{ demo.product.title }}</p>
          <p class="text-caption ink-tertiary">
            <template v-for="(m, i) in demo.product.materials" :key="i">
              {{ m.species }}（{{ m.color }}）×{{ m.count }}<span v-if="m.gifted" class="gift-chip">赠送</span>{{ i < demo.product.materials.length - 1 ? ' · ' : '' }}
            </template>
          </p>
          <p class="product-price">
            <span class="price-symbol">¥</span>
            <span class="price-num">{{ demo.product.price.toFixed(2) }}</span>
          </p>
          <button class="btn-ghost btn-ghost-outline product-btn" @click="modalVisible = true">查看详情</button>
        </div>
      </div>

      <!-- 发送信息（包装建议 / 用户备注 / 替代选项态，Caption 行） -->
      <div class="delivery-card">
        <p class="text-caption ink-secondary delivery-row">包装建议：{{ demo.delivery.packaging }}</p>
        <p class="text-caption ink-secondary delivery-row">备注：{{ demo.delivery.note || '无' }}</p>
        <p class="text-caption ink-secondary delivery-row">
          接受相似花材替代：{{ demo.delivery.acceptSubstitute ? '已接受' : '不接受' }}
        </p>
      </div>

      <!-- 履约时间线（四节点竖向，当前及以前 --accent 高亮） -->
      <div class="timeline-card">
        <div
          v-for="(node, i) in demo.timeline.nodes"
          :key="node.name"
          class="tl-node"
          :class="{ reached: i <= demo.timeline.currentIndex }"
        >
          <span class="tl-dot"><ResIcon v-if="i <= demo.timeline.currentIndex" name="check" :size="10" /></span>
          <span v-if="i < demo.timeline.nodes.length - 1" class="tl-line"></span>
          <div class="tl-text">
            <p class="text-body tl-name">{{ node.name }}</p>
            <p class="text-mini ink-tertiary">{{ node.time }}</p>
          </div>
        </div>
      </div>

      <!-- 送达横幅（固定文案） -->
      <div class="done-banner">{{ demo.banner }}</div>

      <!-- 页脚（固定文案） -->
      <p class="p6-footer text-mini ink-tertiary">{{ demo.footer }}</p>
    </div>

    <!-- 静态原型的唯一「交互」：演示说明弹窗（按钮无跳转/无下单） -->
    <Modal
      v-model:visible="modalVisible"
      :title="demo.footer"
      body="本页为演示页面，所有内容均为演示数据"
      confirm-text="知道了"
      @confirm="modalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import ResIcon from '../components/ResIcon.vue'
import Modal from '../components/Modal.vue'
import { shopDemo } from '../demo/shopDemo'

const demo = shopDemo
const modalVisible = ref(false)
</script>

<style scoped>
.p6-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--close-bg);
}

.p6-body {
  padding: var(--space-page);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shop-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 14px var(--space-page);
}

.shop-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.shop-name {
  font-weight: 700;
}

.product-card {
  display: flex;
  gap: 12px;
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 14px var(--space-page);
}

.product-img {
  width: 96px;
  height: 96px;
  border-radius: var(--radius-inner);
  background: linear-gradient(135deg, #ffe9ef 0%, #fff6ec 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44px;
  flex-shrink: 0;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.product-title {
  font-weight: 700;
  line-height: 1.35;
}

.product-price {
  margin-top: auto;
  color: var(--accent-deep);
}

.price-symbol {
  font-size: 12px; /* ¥ 字号为数字的 60%（§2.2） */
  font-weight: 700;
  margin-right: 2px;
}

.price-num {
  font-size: 20px;
  font-weight: 700;
}

.product-btn {
  align-self: flex-start;
  margin-top: 6px;
  height: 32px;
  font-size: 13px;
}

/* 「赠送」chip（只读展示） */
.gift-chip {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 8px;
  margin: 0 4px;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  vertical-align: 1px;
}

/* 发送信息卡 */
.delivery-card {
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 12px var(--space-page);
}

.delivery-row {
  padding: 4px 0;
}

.timeline-card {
  background: var(--bg-page);
  border-radius: var(--radius-card);
  padding: 16px var(--space-page);
}

.tl-node {
  position: relative;
  display: flex;
  gap: 12px;
  padding-bottom: 22px;
}

.tl-node:last-child {
  padding-bottom: 0;
}

.tl-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--handle);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
  margin-top: 2px;
}

.tl-node.reached .tl-dot {
  background: var(--accent);
}

.tl-line {
  position: absolute;
  left: 8px;
  top: 22px;
  bottom: 0;
  width: 2px;
  background: var(--close-bg);
}

.tl-node.reached .tl-line {
  background: var(--accent);
  opacity: 0.4;
}

.tl-name {
  font-size: 15px;
  color: var(--ink-secondary);
}

.tl-node.reached .tl-name {
  color: var(--ink-primary);
  font-weight: 700;
}

.done-banner {
  background: var(--accent-soft);
  border-radius: var(--radius-card);
  color: var(--accent-deep);
  text-align: center;
  padding: 14px;
  font-size: 15px;
  font-weight: 700;
}

.p6-footer {
  text-align: center;
  padding: 8px 0 16px;
}
</style>
