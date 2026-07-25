import { createRouter, createWebHistory } from 'vue-router'

// 页面栈路由（§3，无 TabBar）：
// / = P0 相机入口；/recognize = P1/P2 识图流程（组件状态机驱动）
// /garden = P3；/garden/resources = P3a；/house = P4；/bouquet/preview = P5；/shop = P6
const routes = [
  { path: '/', name: 'camera', component: () => import('./views/CameraView.vue'), meta: { title: '拍照识花' } },
  { path: '/recognize', name: 'recognize', component: () => import('./views/RecognizeFlowView.vue'), meta: { title: '识图' } },
  { path: '/garden', name: 'garden', component: () => import('./views/GardenView.vue'), meta: { title: '花园' } },
  { path: '/chat', name: 'chat', component: () => import('./views/ChatView.vue'), meta: { title: '小葵' } },
  { path: '/garden/resources', name: 'resources', component: () => import('./views/ResourcesView.vue'), meta: { title: '资源明细' } },
  { path: '/house', name: 'house', component: () => import('./views/HouseView.vue'), meta: { title: '花房' } },
  { path: '/bouquet/preview', name: 'bouquet-preview', component: () => import('./views/BouquetPreviewView.vue'), meta: { title: '花束方案' } },
  { path: '/shop', name: 'shop', component: () => import('./views/ShopView.vue'), meta: { title: '订单详情' } },
  // 兜底：未知路径回 P0
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
