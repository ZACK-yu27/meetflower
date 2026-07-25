// P6 抖音电商原型页演示数据（纯静态，不接后端；集中管理便于演示前巡检，§10）
export const shopDemo = {
  // 店铺条
  shop: {
    name: '春风花店',
    tag: '抖音本地生活 · 演示'
  },
  // 商品卡：花材摘要含「赠送」标记（gifted: true）
  product: {
    title: 'AI 定制花束 · 同款鲜花',
    materials: [
      { species: '玫瑰', color: '红', count: 3 },
      { species: '洋甘菊', color: '白', count: 5 },
      { species: '满天星', color: '紫', count: 2, gifted: true }
    ],
    price: 66.0 // 演示金额
  },
  // 发送信息（包装建议 / 用户备注 / 接受相似花材替代 选项态，Caption 行）
  delivery: {
    packaging: '奶白色雾面纸包裹，配浅粉丝带',
    note: '请下午 5 点后送达，谢谢',
    acceptSubstitute: true
  },
  // 履约时间线（四节点，currentIndex 及以前高亮；演示为已送达态）
  timeline: {
    currentIndex: 3,
    nodes: [
      { name: '花店已接单', time: '14:02' },
      { name: '花束制作中', time: '14:10' },
      { name: '骑手配送中', time: '14:28' },
      { name: '已送达', time: '14:56' }
    ]
  },
  // 送达横幅（固定文案）
  banner: '收到同款鲜花花束，旅程闭环 🎉',
  // 页脚（固定文案）
  footer: '演示原型，不构成真实交易'
}
