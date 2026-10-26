<template>
    <div v-if="showThresholdModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showThresholdModal = false">
        <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg">Configure Safety Thresholds</h3>
                <button @click="showThresholdModal = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                <div v-for="item in stockItems" :key="item.sku"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                    <div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                        <div class="text-xs text-gray-500 font-mono">{{ item.sku }} • Current: {{ item.current }}</div>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-xs text-gray-600 dark:text-gray-400">Threshold:</label>
                        <input type="number" v-model.number="thresholdEdits[item.sku]"
                            class="w-20 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center focus:outline-none focus:border-primary/50" />
                    </div>
                </div>
            </div>
            <div class="p-6 border-t border-gray-100 dark:border-white/5">
                <button @click="saveThresholds"
                    class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Save
                    Thresholds</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { safetyStockPageKey } from './safetyStockPageContext'

const { saveThresholds, showThresholdModal, stockItems, thresholdEdits } = inject(safetyStockPageKey)
</script>
