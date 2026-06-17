<template>
  <button
    class="w-9 h-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
    @click="toggleTheme"
  >
    <span class="material-symbols-outlined text-[18px] text-gray-600 dark:text-gray-200">
      {{ isDark ? 'light_mode' : 'dark_mode' }}
    </span>
  </button>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { applyThemePreference, initializeTheme } from '@/utils/theme'

const isDark = ref(false)
let themeObserver = null

function toggleTheme() {
  isDark.value = applyThemePreference(isDark.value ? 'light' : 'dark') === 'dark'
}

onMounted(() => {
  initializeTheme()
  isDark.value = document.documentElement.classList.contains('dark')

  themeObserver = new MutationObserver(() => {
    isDark.value = document.documentElement.classList.contains('dark')
  })

  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

onUnmounted(() => {
  themeObserver?.disconnect()
})
</script>
