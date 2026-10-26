<template>
    <!-- Status Pipeline -->
    <div class="glass-panel rounded-xl p-6">
        <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Dispatch Pipeline Overview</h3>
            <span class="text-xs text-gray-400">Today: {{ new Date().toLocaleDateString() }}</span>
        </div>

        <div class="flex items-center gap-0">
            <!-- Ready -->
            <div class="flex-1 relative">
                <div class="bg-yellow-100 dark:bg-yellow-500/10 border border-yellow-500/20 rounded-l-xl p-4 text-center">
                    <div class="text-3xl font-bold text-yellow-500 dark:text-yellow-400 mb-1">{{ readyCount }}</div>
                    <div class="text-xs text-yellow-600 dark:text-yellow-300 font-bold">READY</div>
                    <div class="text-[10px] text-gray-500 mt-1">Awaiting dispatch</div>
                </div>
            </div>
            <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

            <!-- Dispatched -->
            <div class="flex-1 relative">
                <div class="bg-blue-100 dark:bg-blue-500/10 border border-blue-500/20 p-4 text-center">
                    <div class="text-3xl font-bold text-blue-500 dark:text-blue-400 mb-1">{{ dispatchedCount }}</div>
                    <div class="text-xs text-blue-600 dark:text-blue-300 font-bold">DISPATCHED</div>
                    <div class="text-[10px] text-gray-500 mt-1">Assigned to driver</div>
                </div>
            </div>
            <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

            <!-- In Transit -->
            <div class="flex-1 relative">
                <div class="bg-purple-100 dark:bg-purple-500/10 border border-purple-500/20 p-4 text-center">
                    <div class="text-3xl font-bold text-purple-500 dark:text-purple-400 mb-1">{{ inTransitCount }}</div>
                    <div class="text-xs text-purple-600 dark:text-purple-300 font-bold">IN TRANSIT</div>
                    <div class="text-[10px] text-gray-500 mt-1">On the road</div>
                </div>
            </div>
            <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

            <!-- Delivered -->
            <div class="flex-1 relative">
                <div class="bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-r-xl p-4 text-center">
                    <div class="text-3xl font-bold text-green-500 dark:text-green-400 mb-1">{{ deliveredCount }}</div>
                    <div class="text-xs text-green-600 dark:text-green-300 font-bold">DELIVERED</div>
                    <div class="text-[10px] text-gray-500 mt-1">PoD confirmed</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const { deliveredCount, dispatchedCount, inTransitCount, readyCount } = inject(orderStatusPageKey)
</script>
