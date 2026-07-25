import axios from 'axios'

// axios 实例：baseURL 由环境变量控制
// 开发: '/'（vite devServer proxy）
// 生产: 'https://<render-app>.onrender.com'（构建时注入）
const baseURL = import.meta.env.VITE_API_BASE_URL || '/'
const client = axios.create({ baseURL, timeout: 30000 })

// 1.1 识花（multipart 上传图片；真实 VLM 首响约 10–30s，单独放宽超时）
export function recognize(imageFile) {
  const form = new FormData()
  form.append('image', imageFile)
  return client.post('/api/v1/recognitions', form, { timeout: 60000 }).then((r) => r.data)
}

// 1.1b 识花结果轮询（ark 模式科普文案异步补齐，science_text 非空即就绪）
export function getRecognition(recognitionId) {
  return client.get(`/api/v1/recognitions/${recognitionId}`).then((r) => r.data)
}

// 1.2 种植（识花结果种入）
export function plantRecognition(recognitionId) {
  return client.post('/api/v1/gardens/1/plants', { recognition_id: recognitionId }).then((r) => r.data)
}

// 1.2 复种（×0 灰卡「重新种植」：品种+颜色入参）
export function replantFlower(species, mainColor) {
  return client
    .post('/api/v1/gardens/1/plants', { species, main_color: mainColor })
    .then((r) => r.data)
}

// 1.3 花园聚合视图（resources 为 { me, ta } 双人账户；plants 含 me/ta 照料态）
export function getGarden() {
  return client.get('/api/v1/gardens/1').then((r) => r.data)
}

// 1.4 照料（空体即可；整组扣除 + 双人各完成一次）
export function carePlant(plantId) {
  return client.post(`/api/v1/gardens/1/plants/${plantId}/care`, {}).then((r) => r.data)
}

// 1.5 压花收藏
export function pressPlant(plantId) {
  return client.post(`/api/v1/gardens/1/plants/${plantId}/press`, {}).then((r) => r.data)
}

// 1.6 花房库存（含 quantity=0 灰态项）
export function getFlowerHouse() {
  return client.get('/api/v1/flower-house').then((r) => r.data)
}

// 1.7 花束预览（不扣库存；bonus = 推荐链路赠送花材，occasion = 送花意图，均可空）
// ark 模式首响为文案（并行 LLM 约 10–30s），单独放宽超时；预览图异步补齐经 getBouquet 轮询
export function previewBouquet(items, { bonus = null, occasion = null } = {}) {
  const body = { items }
  if (bonus) body.bonus = bonus
  if (occasion) body.occasion = occasion
  return client.post('/api/v1/bouquets/preview', body, { timeout: 90000 }).then((r) => r.data)
}

// 1.7b 花束方案轮询（预览图异步生成，preview_url 非空即就绪）
export function getBouquet(bouquetId) {
  return client.get(`/api/v1/bouquets/${bouquetId}`).then((r) => r.data)
}

// 1.8 发送花店（携带备注与替代选项；note 可空，accept_substitute 默认 true）
export function sendBouquetOrder(bouquetId, { note = '', acceptSubstitute = true } = {}) {
  return client
    .post(`/api/v1/bouquets/${bouquetId}/orders`, { note, accept_substitute: acceptSubstitute })
    .then((r) => r.data)
}

// 1.9 订单详情（含时间线）
export function getOrder(orderId) {
  return client.get(`/api/v1/orders/${orderId}`).then((r) => r.data)
}

// 1.10 订单列表
export function getOrders() {
  return client.get('/api/v1/orders').then((r) => r.data)
}

// 1.11 模拟互动（kind: mutual_message | share_video | streak；双人账户入账）
export function simulateInteraction(kind) {
  return client.post('/api/v1/demo/interactions', { kind }).then((r) => r.data)
}

// 1.12 花园新变化提示
export function getBadge() {
  return client.get('/api/v1/badge').then((r) => r.data)
}

// 1.13 AI 推荐搭配（occasion 枚举：情侣约会 / 毕业季 / 生日祝福 / 探望问候 / 日常惊喜）
export function recommendBouquet(occasion) {
  return client.post('/api/v1/bouquets/recommend', { occasion }).then((r) => r.data)
}

// 1.14 演示快进（「查看完整成长旅程」：直升 bloom）
export function fastForward(plantId) {
  return client.post('/api/v1/demo/fast-forward', { plant_id: plantId }).then((r) => r.data)
}

// 1.15 演示重置（「重新体验」：清空演示数据并重新播种）
export function resetDemo() {
  return client.post('/api/v1/demo/reset', {}).then((r) => r.data)
}

// 统一提取后端错误文案：{ detail: "人类可读的中文错误信息" }
export function errorMessage(err, fallback = '请求失败，请稍后再试') {
  return err?.response?.data?.detail || fallback
}

export default client
