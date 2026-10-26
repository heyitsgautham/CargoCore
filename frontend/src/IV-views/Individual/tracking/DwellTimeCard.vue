<template>
    <!-- Dwell Time Card -->
    <div v-if="activeMove.dwellTime && activeMove.dwellTime.total > 0"
        class="glass-panel p-4 sm:p-5 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
            <span class="material-symbols-outlined text-purple-500 text-lg">timer</span> Dwell Time Log
        </h3>
        <div class="grid grid-cols-3 gap-3">
            <div
                class="p-3 bg-blue-50 dark:bg-blue-500/5 rounded-lg text-center border border-blue-200 dark:border-blue-500/20">
                <div class="text-xs text-gray-500 dark:text-gray-400">Loading</div>
                <div class="text-xl font-bold text-blue-600 dark:text-blue-400">{{
                    activeMove.dwellTime.loading }}<span class="text-xs font-normal"> min</span></div>
            </div>
            <div
                class="p-3 bg-amber-50 dark:bg-amber-500/5 rounded-lg text-center border border-amber-200 dark:border-amber-500/20">
                <div class="text-xs text-gray-500 dark:text-gray-400">Unloading</div>
                <div class="text-xl font-bold text-amber-600 dark:text-amber-400">{{
                    activeMove.dwellTime.unloading }}<span class="text-xs font-normal"> min</span></div>
            </div>
            <div
                class="p-3 bg-purple-50 dark:bg-purple-500/5 rounded-lg text-center border border-purple-200 dark:border-purple-500/20">
                <div class="text-xs text-gray-500 dark:text-gray-400">Total Dwell</div>
                <div class="text-xl font-bold text-purple-600 dark:text-purple-400">{{
                    activeMove.dwellTime.total }}<span class="text-xs font-normal"> min</span></div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove } = inject(customerTrackingPageKey)
</script>
