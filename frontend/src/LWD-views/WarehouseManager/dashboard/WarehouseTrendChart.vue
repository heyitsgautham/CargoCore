<template>
    <!-- Charts Row -->
    <div class="glass-panel p-5 rounded-xl h-[300px] md:h-[400px] flex flex-col">
        <div class="flex justify-between items-center mb-2">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-teal-500">trending_up</span>
                Daily Throughput (Picks per Hour)
            </h3>
        </div>
        <div class="flex-1 relative w-full h-full">
            <Line v-if="throughputChartData" :key="throughputChartKey" :data="throughputChartData" :options="lineChartOptions" />
            <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Line } from 'vue-chartjs'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const { lineChartOptions, throughputChartData, throughputChartKey } = inject(wmDashboardPageKey)
</script>
