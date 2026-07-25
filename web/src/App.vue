<template>
  <!-- 抖音内程序形态：页面栈导航，无全局 TabBar（§1） -->
  <div class="app-frame">
    <router-view />
    <Toast />
  </div>
</template>

<script setup>
import Toast from './components/Toast.vue'
</script>
