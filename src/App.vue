<template>
  <AppLoading :visible="isLoading" />
  <router-view v-slot="{ Component, route: currentRoute }">
    <transition :name="currentRoute.name === 'NoInternet' ? '' : 'fade'" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
  <ToastNotification />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLoading from './components/AppLoading.vue'
import ToastNotification from './components/ToastNotification.vue'

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)

router.beforeEach((to) => {
  if (to.name !== 'NoInternet') isLoading.value = true
})
router.afterEach(() => {
  isLoading.value = false
})

const handleOffline = () => {
  if (route.name !== 'NoInternet') router.replace('/offline')
}

onMounted(() => {
  window.addEventListener('offline', handleOffline)
  if (!navigator.onLine && route.name !== 'NoInternet') router.push('/offline')
})
onUnmounted(() => {
  window.removeEventListener('offline', handleOffline)
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
