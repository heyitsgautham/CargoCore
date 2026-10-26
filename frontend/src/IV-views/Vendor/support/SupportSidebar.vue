<template>
    <!-- LEFT SIDEBAR -->
    <div class="w-full md:w-72 flex flex-col gap-6 shrink-0">
        <!-- Priority Support -->
        <div class="glass-panel p-5 rounded-xl flex flex-col items-center text-center justify-center">
            <div class="w-14 h-14 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 mb-3">
                <span class="material-symbols-outlined text-2xl">phone_in_talk</span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Priority Support</h3>
            <p class="text-[10px] text-gray-400 mb-3">Dedicated line for enterprise partners.</p>
            <div class="text-base font-bold text-gray-900 dark:text-white">+91 1800 999 0000</div>
        </div>

        <!-- Status Breakdown Chart -->
        <div class="glass-panel p-5 rounded-xl flex flex-col items-center justify-center relative min-h-[220px]">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 absolute top-5 left-5">Status Breakdown</h3>
            <div class="w-full h-36 flex justify-center items-center mt-6">
                <Doughnut :data="chartData" :options="chartOptions" />
            </div>
        </div>

        <!-- Ticket Summary Stats -->
        <div class="glass-panel p-5 rounded-xl flex flex-col justify-center">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Ticket Summary</h3>
            <div class="space-y-4 text-sm mt-2">
                <div class="flex flex-col gap-1">
                    <div class="flex justify-between items-end">
                        <span class="text-gray-500 font-medium">Open</span>
                        <span class="font-bold text-yellow-500 text-lg">{{ openCount }}</span>
                    </div>
                    <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-yellow-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (openCount / store.tickets.length) * 100 : 0}%`"></div>
                    </div>
                </div>
                <div class="flex flex-col gap-1">
                    <div class="flex justify-between items-end">
                        <span class="text-gray-500 font-medium">In Progress</span>
                        <span class="font-bold text-blue-500 text-lg">{{ inProgressCount }}</span>
                    </div>
                    <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-blue-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (inProgressCount / store.tickets.length) * 100 : 0}%`"></div>
                    </div>
                </div>
                <div class="flex flex-col gap-1">
                    <div class="flex justify-between items-end">
                        <span class="text-gray-500 font-medium">Resolved</span>
                        <span class="font-bold text-green-500 text-lg">{{ resolvedCount }}</span>
                    </div>
                    <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-green-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (resolvedCount / store.tickets.length) * 100 : 0}%`"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    chartData,
    chartOptions,
    inProgressCount,
    openCount,
    resolvedCount,
    store,
} = inject(vendorSupportPageKey)
</script>
