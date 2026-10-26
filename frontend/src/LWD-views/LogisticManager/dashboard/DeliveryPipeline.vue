<template>
    <!-- Active Delivery Pipeline -->
    <div class="glass-panel p-5 rounded-2xl flex flex-col justify-between">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Active Delivery Pipeline</h3>
            <div
                class="px-2 py-1 bg-primary/10 text-primary rounded text-xs font-bold uppercase tracking-wider">
                Live Pulse
            </div>
        </div>

        <div class="space-y-6 my-auto">
            <!-- Stage: Processing -->
            <div>
                <div class="flex justify-between text-sm mb-2">
                    <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                        Processing at Hubs
                    </span>
                    <span class="text-gray-900 dark:text-white font-bold">{{
                        store.dashboardStats.processing.toLocaleString() }}</span>
                </div>
                <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full transition-all duration-1000"
                        :style="{ width: pipelinePercentages.processing + '%' }"></div>
                </div>
            </div>

            <!-- Stage: In Transit -->
            <div>
                <div class="flex justify-between text-sm mb-2">
                    <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
                        In Transit
                    </span>
                    <span class="text-gray-900 dark:text-white font-bold">{{
                        store.dashboardStats.activeDeliveries.toLocaleString() }}</span>
                </div>
                <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                    <div class="h-full bg-yellow-500 rounded-full transition-all duration-1000"
                        :style="{ width: pipelinePercentages.inTransit + '%' }"></div>
                </div>
            </div>

            <!-- Stage: Delivered -->
            <div>
                <div class="flex justify-between text-sm mb-2">
                    <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-green-500"></span>
                        Delivered Today
                    </span>
                    <span class="text-gray-900 dark:text-white font-bold">{{
                        store.dashboardStats.ordersToday.toLocaleString() }}</span>
                </div>
                <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                    <div class="h-full bg-green-500 rounded-full transition-all duration-1000"
                        :style="{ width: pipelinePercentages.delivered + '%' }"></div>
                </div>
            </div>
        </div>

        <div
            class="mt-6 pt-4 border-t border-gray-100 dark:border-white/5 flex gap-4 text-xs font-medium text-gray-500 dark:text-gray-400">
            <div>
                <span class="text-gray-900 dark:text-white font-bold">{{
                    store.dashboardStats.deliverySuccess
                }}%</span> Success Rate
            </div>
            <div>
                <span class="text-gray-900 dark:text-white font-bold">{{ store.dashboardStats.activeDrivers ?? '—' }}</span> Active Drivers
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const { pipelinePercentages, store } = inject(lmDashboardPageKey)
</script>
