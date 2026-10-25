<template>
  <Teleport to="body">
      <div v-if="showStationMonitor"
          class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          @click.self="$emit('close')">
          <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
              <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                  <div>
                      <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                          <span class="material-symbols-outlined text-green-500 animate-pulse">radio_button_checked</span>
                          Live Monitor — {{ monitoredStation?.name }}
                      </h3>
                      <p class="text-xs text-gray-500 mt-1">Real-time packing station activity</p>
                  </div>
                  <button @click="$emit('close')" class="text-gray-500 hover:text-gray-900 dark:text-white">
                      <span class="material-symbols-outlined">close</span>
                  </button>
              </div>
              <div class="p-6 space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                      <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                          <div class="text-3xl font-bold text-primary">{{ monitoredStation?.rate || 0 }}</div>
                          <div class="text-xs text-gray-500 mt-1">Items Packed Today</div>
                      </div>
                      <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                          <div class="text-3xl font-bold" :class="monitoredStation?.active ? 'text-green-500' : 'text-gray-500'">
                              {{ monitoredStation?.active ? 'Active' : 'Idle' }}
                          </div>
                          <div class="text-xs text-gray-500 mt-1">Station Status</div>
                      </div>
                  </div>
                  <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl">
                      <div class="text-xs text-gray-500 mb-2">Current Order</div>
                      <div v-if="monitoredStation?.currentOrderTracking" class="font-mono text-primary font-bold">
                          {{ monitoredStation.currentOrderTracking }}
                      </div>
                      <div v-else class="text-gray-500 text-sm">No order in progress</div>
                  </div>
                  <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl">
                      <div class="text-xs text-gray-500 mb-2">Assigned Packer</div>
                      <div class="font-bold text-gray-900 dark:text-white">{{ monitoredStation?.packer || 'Unassigned' }}</div>
                  </div>
                  <div class="flex gap-2">
                      <button @click="$emit('refresh')" class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">
                          Refresh Data
                      </button>
                      <button @click="$emit('close')" class="flex-1 py-2 bg-primary text-background-dark rounded-lg text-sm font-bold">
                          Close
                      </button>
                  </div>
              </div>
          </div>
      </div>
  </Teleport>
</template>

<script setup>
defineProps({
    showStationMonitor: { type: Boolean, required: true },
    monitoredStation: { type: Object, default: null },
})
defineEmits(['close', 'refresh'])
</script>
