<template>
    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="glass-panel p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm">Category Comparison (Bar)</h3>
            <div class="h-64 w-full relative">
                <BarChart :data="barChartData" :options="barChartOptions" />
            </div>
        </div>
        <div class="glass-panel p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm">Category Distribution (Doughnut)
            </h3>
            <div class="h-64 w-full relative">
                <DoughnutChart :data="doughnutChartData" :options="doughnutChartOptions" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { defineAsyncComponent, inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

// Chart.js loads on first use, so the booking form does not pay for it.
let chartLibraryPromise = null
let chartsRegistered = false

function loadChartComponent(componentName) {
    if (!chartLibraryPromise) {
        chartLibraryPromise = Promise.all([
            import('chart.js'),
            import('vue-chartjs'),
        ]).then(([chartJs, vueChartJs]) => {
            if (!chartsRegistered) {
                chartJs.Chart.register(
                    chartJs.CategoryScale,
                    chartJs.LinearScale,
                    chartJs.BarElement,
                    chartJs.Title,
                    chartJs.Tooltip,
                    chartJs.Legend,
                    chartJs.ArcElement,
                )
                chartsRegistered = true
            }
            return vueChartJs
        })
    }

    return chartLibraryPromise.then((vueChartJs) => vueChartJs[componentName])
}

const BarChart = defineAsyncComponent(() => loadChartComponent('Bar'))
const DoughnutChart = defineAsyncComponent(() => loadChartComponent('Doughnut'))

const { barChartData, barChartOptions, doughnutChartData, doughnutChartOptions } = inject(createShipmentPageKey)
</script>
