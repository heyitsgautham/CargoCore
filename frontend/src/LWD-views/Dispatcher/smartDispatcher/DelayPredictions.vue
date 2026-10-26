<template>
    <div class="glass-panel p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-yellow-400">schedule</span>
            AI Dispatch Risk Engine
        </h3>
        <div v-if="delayPredictions.length === 0" class="text-center py-8 text-gray-500 text-sm">
            <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
            No delay risks detected. Routes are running smoothly.
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div v-for="pred in delayPredictions" :key="pred.key" class="p-4 rounded-xl border"
                :class="pred.risk === 'High' ? 'bg-red-500/5 border-red-500/20' : pred.risk === 'Medium' ? 'bg-yellow-500/5 border-yellow-500/20' : 'bg-green-500/5 border-green-500/20'">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-gray-900 dark:text-white font-bold text-sm">{{ pred.route }}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full font-bold"
                        :class="pred.risk === 'High' ? 'bg-red-500/20 text-red-400' : pred.risk === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'">
                        {{ pred.risk }} Risk
                    </span>
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ pred.reason }}</div>
                <div class="flex items-center gap-2 mt-2">
                    <div class="flex-1 h-2 bg-gray-100 dark:bg-black/30 rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all"
                            :class="pred.risk === 'High' ? 'bg-red-500' : pred.risk === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'"
                            :style="{ width: pred.probability + '%' }"></div>
                    </div>
                    <span class="text-xs font-bold"
                        :class="pred.risk === 'High' ? 'text-red-400' : pred.risk === 'Medium' ? 'text-yellow-400' : 'text-green-400'">
                        {{ pred.probability }}%
                    </span>
                </div>
                <div class="flex items-center justify-between mt-2">
                    <div class="text-[10px] text-gray-500">Est. delay: {{ pred.delay }}</div>
                    <button @click="mitigateDelay(pred)" class="text-[10px] font-bold transition-colors"
                        :class="pred.mitigated ? 'text-green-400' : 'text-blue-400 hover:text-gray-900 dark:text-white'">
                        {{ pred.mitigated ? '✓ Mitigated' : 'Mitigate' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { smartDispatcherPageKey } from './smartDispatcherPageContext'

const { delayPredictions, mitigateDelay } = inject(smartDispatcherPageKey)
</script>
