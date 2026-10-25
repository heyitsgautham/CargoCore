<template>
  <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col">
      <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Top Leaderboard</h3>
      <div class="space-y-4 overflow-y-auto pr-2 flex-grow custom-scrollbar">
          <div v-for="driver in searchedTopDrivers" :key="driver.id"
              class="flex items-center gap-4 p-3 rounded-lg border transition-colors shadow-sm"
              :class="driver.dispatcherSuspended
                  ? 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/20'
                  : 'bg-gray-50 dark:bg-white/5 border-transparent'">
              <!-- Avatar -->
              <div class="relative shrink-0">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm"
                      :class="driver.dispatcherSuspended ? 'bg-red-700 opacity-60' : (driver.avatarColor || 'bg-gray-600')">
                      {{ (driver.name || '?').charAt(0) }}
                  </div>
                  <span v-if="driver.dispatcherSuspended"
                      class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-red-500 border-2 border-white dark:border-gray-900 flex items-center justify-center">
                      <span class="material-symbols-outlined text-white" style="font-size:8px">block</span>
                  </span>
              </div>
              <div class="flex-1 min-w-0">
                  <div class="flex justify-between items-center gap-2">
                      <span class="font-bold text-sm truncate"
                          :class="driver.dispatcherSuspended ? 'text-red-700 dark:text-red-400' : 'text-gray-900 dark:text-white'">
                          {{ driver.name }}
                      </span>
                      <!-- Suspended overrides rating badge -->
                      <span v-if="driver.dispatcherSuspended"
                          class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400 border border-red-300 dark:border-red-500/30 shrink-0 flex items-center gap-1">
                          <span class="material-symbols-outlined" style="font-size:10px">block</span>
                          Suspended
                      </span>
                      <span v-else
                          class="text-yellow-500 dark:text-yellow-400 font-bold text-sm bg-yellow-50 dark:bg-yellow-500/10 px-2 py-0.5 rounded-full border border-yellow-200 dark:border-yellow-500/20 shrink-0">
                          ★ {{ driver.rating }}
                      </span>
                  </div>
                  <div class="text-xs mt-1"
                      :class="driver.dispatcherSuspended ? 'text-red-400/70 dark:text-red-400/50' : 'text-gray-500 dark:text-gray-400'">
                      <span v-if="driver.dispatcherSuspended" class="font-semibold text-red-500 dark:text-red-400/80">Blocked from dispatch</span>
                      <template v-else>
                          {{ driver.trips }} trips •
                          <span class="font-medium"
                              :class="driver.ontime > 95 ? 'text-green-500 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                              {{ driver.ontime }}% On-time
                          </span>
                      </template>
                  </div>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
defineProps({
    searchedTopDrivers: { type: Array, required: true },
})

</script>
