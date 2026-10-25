<template>
  <div class="glass-panel p-4 rounded-xl">
      <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold mb-3">Order Fulfillment
          Pipeline</div>
      <div v-if="pipelineLoading" class="flex items-center justify-center py-4">
          <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
      </div>
      <div v-else class="flex items-center justify-between gap-2">
          <div v-for="(step, idx) in pipelineSteps" :key="step.label"
              class="flex-1 flex flex-col items-center relative group">
              <div class="w-full flex items-center">
                  <div class="flex-1 h-1 rounded-full"
                      :class="idx === 0 ? 'bg-transparent' : step.active ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'">
                  </div>
                  <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all"
                      :class="step.active ? 'bg-primary text-background-dark shadow-lg shadow-primary/30' : 'bg-gray-50 dark:bg-white/5 text-gray-500 border border-gray-200 dark:border-white/10'">
                      <span class="material-symbols-outlined text-[18px]">{{ step.icon }}</span>
                  </div>
                  <div class="flex-1 h-1 rounded-full"
                      :class="idx === pipelineSteps.length - 1 ? 'bg-transparent' : pipelineSteps[idx + 1]?.active ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'">
                  </div>
              </div>
              <div class="text-[10px] mt-2 font-bold text-center"
                  :class="step.active ? 'text-primary' : 'text-gray-500'">{{ step.label }}</div>
              <div class="text-[10px] text-gray-600 text-center">{{ step.count }} orders</div>
          </div>
      </div>
  </div>
</template>

<script setup>
defineProps({
    pipelineSteps: { type: Array, required: true },
    pipelineLoading: { type: Boolean, required: true },
})

</script>
