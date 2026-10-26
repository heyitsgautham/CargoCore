<template>
    <!-- 5. Seasonal / Dynamic -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-black/20">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-500">trending_up</span> Dynamic Pricing
            </h3>
        </div>
        <div class="p-5 space-y-4">
            <div
                class="flex items-center justify-between border-b border-gray-100 dark:border-white/10 pb-3">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Harvest/Peak Surge</span>
                <div class="flex items-center gap-2">
                    <span class="text-xs text-gray-500">x</span>
                    <input type="number" :disabled="!isEditMode" step="0.1"
                        v-model.number="rates.dynamic.peak"
                        class="w-16 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1 text-sm font-mono text-center outline-none">
                </div>
            </div>
            <div class="flex items-center justify-between">
                <span
                    class="text-sm font-medium text-red-600 dark:text-red-400 flex items-center gap-1"><span
                        class="material-symbols-outlined text-[16px]">warning</span> Emergency
                    Priority</span>
                <div class="flex items-center gap-2">
                    <span class="text-xs text-gray-500">x</span>
                    <input type="number" :disabled="!isEditMode" step="0.1"
                        v-model.number="rates.dynamic.emergency"
                        class="w-16 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-300 rounded px-2 py-1 text-sm font-mono text-center outline-none">
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { isEditMode, rates } = inject(rateGovernancePageKey)
</script>
