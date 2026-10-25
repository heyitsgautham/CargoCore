<template>
  <div class="glass-panel p-6 rounded-xl">
      <h3 class="font-bold text-gray-900 dark:text-white mb-4">Packing Stations</h3>
      <div v-if="stations.length === 0"
          class="rounded-lg border border-dashed border-gray-200 dark:border-white/10 p-4 text-center text-sm text-gray-500">
          No packing stations configured yet. A station will appear here once the warehouse starts packing orders.
      </div>
      <div v-else class="space-y-4">
          <div v-for="station in stations" :key="station.id"
              class="p-4 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-lg">
              <div class="flex justify-between items-center mb-2">
                  <span class="font-bold text-gray-900 dark:text-white">{{ station.name }}</span>
                  <span class="w-2 h-2 rounded-full"
                      :class="station.active ? 'bg-green-500 animate-pulse' : 'bg-gray-500'"></span>
              </div>
              <div class="text-xs text-gray-600 dark:text-gray-400 mb-2">{{ station.packer }}</div>
              <div class="flex justify-between items-end text-sm">
                  <div>
                      <div class="text-gray-500 text-[10px] uppercase">Throughput</div>
                      <div class="text-gray-900 dark:text-white font-bold">{{ station.rate }} / hr</div>
                  </div>
                  <button @click="$emit('monitor', station)"
                      class="bg-gray-100 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white px-2 py-1 rounded text-xs transition-colors"
                      :class="showStationMonitor && monitoredStation?.id === station.id ? 'ring-1 ring-primary bg-primary/20 text-primary' : ''">
                      {{ showStationMonitor && monitoredStation?.id === station.id ? '● Live' : 'Monitor' }}
                  </button>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
defineProps({
    stations: { type: Array, required: true },
    showStationMonitor: { type: Boolean, required: true },
    monitoredStation: { type: Object, default: null },
})
defineEmits(['monitor'])
</script>
