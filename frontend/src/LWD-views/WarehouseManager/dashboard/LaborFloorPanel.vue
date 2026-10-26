<template>
    <!-- Right: Labor Status & Floor Map -->
    <div class="flex flex-col gap-6">
        <!-- Labor Distribution Chart -->
        <div class="glass-panel p-5 rounded-xl flex-1 flex flex-col">
            <h3 class="font-bold text-gray-900 dark:text-white mb-2">Real-time Labor Status</h3>

            <div class="flex-1 relative w-full flex justify-center items-center min-h-[160px]">
                <Doughnut v-if="laborChartData" :data="laborChartData" :options="doughnutOptions" />
                <div v-else class="flex items-center justify-center text-gray-500">No data available</div>
            </div>

            <div
                class="mt-4 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">Efficiency Insight</div>
                <div class="text-sm text-gray-900 dark:text-white">{{ efficiencyInsight }}</div>
            </div>
        </div>

        <!-- Return Processing Queue (Small) -->
        <div class="glass-panel p-4 rounded-xl space-y-2 bg-gray-100 dark:bg-gray-800/20">
            <div class="flex justify-between items-center mb-1">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Recent Returns</h3>
                <span class="text-xs text-gray-500">Today</span>
            </div>
            <div v-if="recentReturns.length === 0" class="text-xs text-gray-500 text-center py-4">
                No recent returns
            </div>
            <div v-for="returnItem in recentReturns.slice(0, 3)" :key="returnItem.id"
                class="flex items-center justify-between p-2 rounded bg-gray-100 dark:bg-black/20 text-xs text-gray-600 dark:text-gray-300">
                <span>{{ returnItem.description }}</span>
                <span class="font-medium" :class="returnItem.action === 'Scrap' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                    {{ returnItem.action }}
                </span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const { doughnutOptions, efficiencyInsight, laborChartData, recentReturns } = inject(wmDashboardPageKey)
</script>
