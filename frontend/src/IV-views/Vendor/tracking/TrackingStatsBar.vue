<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <div class="glass-panel p-4 rounded-xl flex items-center gap-3 border border-blue-500/10">
          <div class="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-blue-500 text-[20px]">local_shipping</span>
          </div>
          <div class="min-w-0">
              <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide truncate">Active</div>
              <div class="text-2xl font-black text-gray-900 dark:text-white leading-none mt-0.5">{{ store.activeShipments.length }}</div>
          </div>
      </div>
      <div class="glass-panel p-4 rounded-xl flex items-center gap-3 border border-yellow-500/10">
          <div class="w-10 h-10 rounded-xl bg-yellow-500/10 flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-yellow-500 text-[20px]">pending</span>
          </div>
          <div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Pending</div>
              <div class="text-2xl font-black text-gray-900 dark:text-white leading-none mt-0.5">{{ store.pendingShipments.length }}</div>
          </div>
      </div>
      <div class="glass-panel p-4 rounded-xl flex items-center gap-3 border border-green-500/10">
          <div class="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-green-500 text-[20px]">check_circle</span>
          </div>
          <div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Delivered</div>
              <div class="text-2xl font-black text-gray-900 dark:text-white leading-none mt-0.5">{{ store.deliveredShipments.length }}</div>
          </div>
      </div>
      <div class="glass-panel p-4 rounded-xl flex items-center gap-3 border border-emerald-500/10">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-emerald-500 text-[20px]">schedule</span>
          </div>
          <div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">On-Time</div>
              <div class="text-2xl font-black text-emerald-500 leading-none mt-0.5">{{ store.analyticsData.onTime }}%</div>
          </div>
      </div>
      <div class="glass-panel p-4 rounded-xl flex items-center gap-3 border border-orange-500/10">
          <div class="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-orange-500 text-[20px]">route</span>
          </div>
          <div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Avg Transit</div>
              <div class="text-2xl font-black text-gray-900 dark:text-white leading-none mt-0.5">{{ store.analyticsData.avgTransit }}<span class="text-sm font-bold text-gray-400">d</span></div>
          </div>
      </div>
  </div>
</template>

<script setup>
defineProps({
    store: { type: Object, required: true },
})

</script>
