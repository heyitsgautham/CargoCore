<template>
    <!-- Secondary Charts Row -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">

        <!-- 1. Orders VS Returns (Bar) -->
        <div class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                <span class="material-symbols-outlined text-blue-400">compare_arrows</span>
                Orders vs Returns
            </h3>
            <div class="relative flex-1 w-full min-h-0">
                <Bar v-if="ordersReturnsData" :data="ordersReturnsData" :options="barOptions" class="absolute inset-0 pb-2" />
                <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
            </div>
        </div>

        <!-- 2. Stock vs Packaging (Pie) -->
        <div class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                <span class="material-symbols-outlined text-purple-400">inventory</span>
                Inventory Composition
            </h3>
            <div class="relative flex-1 w-full min-h-0">
                <Pie v-if="stockPackagingData" :data="stockPackagingData" :options="pieOptions" class="absolute inset-0 pb-2" />
                <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
            </div>
        </div>

        <!-- 3. Active Workers vs Drivers (Doughnut) -->
        <div
            class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80 sm:col-span-2 md:col-span-1">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                <span class="material-symbols-outlined text-yellow-400">group</span>
                On-Site Labor
            </h3>
            <div class="relative flex-1 w-full min-h-0">
                <Doughnut v-if="activeStaffData" :data="activeStaffData" :options="doughnutOptions" class="absolute inset-0 pb-2" />
                <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Doughnut, Pie } from 'vue-chartjs'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const {
    activeStaffData,
    barOptions,
    doughnutOptions,
    ordersReturnsData,
    pieOptions,
    stockPackagingData,
} = inject(wmDashboardPageKey)
</script>
