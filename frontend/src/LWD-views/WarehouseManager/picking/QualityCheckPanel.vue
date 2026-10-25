<template>
  <div class="glass-panel p-6 rounded-xl">
      <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <span class="material-symbols-outlined text-green-600 dark:text-green-400">verified</span>
          Quality Verification
      </h3>
      <div class="space-y-3">
          <div v-for="check in qualityChecks" :key="check.orderId"
              class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
              <div class="flex justify-between items-center mb-2">
                  <span class="font-mono text-primary text-xs font-bold">{{ check.orderId }}</span>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                      :class="check.isPassed ? 'bg-green-500/20 text-green-600 dark:text-green-400' : check.verified ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                      {{ check.isPassed ? 'Passed' : check.verified ? 'Ready' : 'Pending' }}
                  </span>
              </div>
              <div class="space-y-1 text-xs">
                  <div v-for="(field, fIdx) in checkFields" :key="fIdx"
                      @click="$emit('toggle-check', check, field.key)"
                      class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:bg-white/5 rounded p-0.5 transition-colors">
                      <span class="material-symbols-outlined text-[14px]"
                          :class="check[field.key] ? 'text-green-600 dark:text-green-400' : 'text-gray-600'">{{
                              check[field.key] ? 'check_circle' : 'radio_button_unchecked' }}</span>
                      <span class="text-gray-600 dark:text-gray-300">{{ field.label }}</span>
                  </div>
              </div>
              <button v-if="check.isPassed"
                  class="mt-3 w-full py-2 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-xs font-bold cursor-default opacity-70">
                  Dispatch Queue Updated
              </button>
              <button v-else-if="check.verified" @click="$emit('dispatch', check)"
                  class="mt-3 w-full py-2 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 rounded text-xs font-bold transition-colors flex items-center justify-center gap-1">
                  <span class="material-symbols-outlined text-[14px]">send</span> Ready for Dispatch
              </button>
              <button v-else
                  class="mt-3 w-full py-2 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded text-xs font-bold cursor-not-allowed opacity-50">
                  Complete all checks first
              </button>
          </div>
          <div v-if="qualityChecks.length === 0" class="text-center text-xs text-gray-500 py-4">
              No orders pending quality check
          </div>
      </div>
  </div>
</template>

<script setup>
defineProps({
    qualityChecks: { type: Array, required: true },
    checkFields: { type: Array, required: true },
})
defineEmits(['dispatch', 'toggle-check'])
</script>
