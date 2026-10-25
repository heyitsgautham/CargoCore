<template>
  <div class="flex items-center gap-3 mb-2">
      <div class="relative">
          <img :src="driver.avatar" class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 object-cover">
          <span class="absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white dark:border-card-dark"
              :class="driver.statusColor"></span>
      </div>
      <div>
          <button @click.stop="$emit('view', driver)" class="text-sm font-semibold text-gray-900 dark:text-white hover:text-primary transition-colors text-left">{{ driver.name }}</button>
          <div class="text-[10px] text-gray-400">{{ driver.vehicle }} • {{ driver.id }}</div>
      </div>
      <span v-if="!driver.isAssignable" class="ml-auto rounded-full bg-yellow-500/15 px-2 py-0.5 text-[10px] font-semibold text-yellow-600 dark:text-yellow-400">
          {{ driver.busyReason || 'Busy' }}
      </span>
  </div>

  <div class="grid grid-cols-2 gap-2 text-[10px]">
      <div class="bg-gray-100 dark:bg-black/20 rounded px-2 py-1">
          <span class="text-gray-500 block">Load</span>
          <span class="text-gray-900 dark:text-white font-mono">{{ driver.load }}%</span>
      </div>
      <div class="bg-gray-100 dark:bg-black/20 rounded px-2 py-1">
          <span class="text-gray-500 block">Hours Left</span>
          <span class="text-gray-900 dark:text-white font-mono">{{ driver.hours }}h</span>
      </div>
  </div>

  <div
      class="mt-2 pt-2 border-t border-gray-200 dark:border-white/5 flex justify-between items-center opacity-70 group-hover:opacity-100 transition-opacity">
      <span class="text-[10px] text-gray-400 flex items-center gap-1">
          <span class="material-symbols-outlined text-[12px]">location_on</span> {{ driver.location }}
      </span>
      <button @click.stop="$emit('chat', driver)" class="text-primary hover:text-gray-900 dark:text-white transition-colors">
          <span class="material-symbols-outlined text-[16px]">chat</span>
      </button>
  </div>
</template>

<script setup>
defineProps({
    driver: { type: Object, required: true },
})
defineEmits(['chat', 'view'])
</script>
