<template>
  <!-- §3-P7 toast：顶部下浮黑底白字胶囊，2s 自消（样式在 main.css .toast） -->
  <transition name="toast-fade">
    <div v-if="toast.message" class="toast">{{ toast.message }}</div>
  </transition>
</template>

<script setup>
import { useToastStore } from '../stores/toast'

const toast = useToastStore()
</script>
