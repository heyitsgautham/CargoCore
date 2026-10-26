<template>
    <div v-if="stats.total_orders > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-panel p-5 md:p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Monthly Spending</h3>
            <div class="h-56">
                <Bar :data="barChartData" :options="chartOptions" />
            </div>
        </div>
        <div class="glass-panel p-5 md:p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Move Status Distribution</h3>
            <div class="h-56 flex items-center justify-center">
                <Doughnut :data="doughnutData" :options="doughnutOptions" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { individualDashboardPageKey } from './individualDashboardPageContext'

const {
    barChartData,
    chartOptions,
    doughnutData,
    doughnutOptions,
    stats,
} = inject(individualDashboardPageKey)
</script>
