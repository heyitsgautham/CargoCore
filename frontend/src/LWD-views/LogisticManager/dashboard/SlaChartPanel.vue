<template>
    <div class="glass-panel p-5 rounded-2xl w-full mt-6 flex flex-col">
        <!-- Tabs Header -->
        <div
            class="flex items-center gap-4 mb-6 border-b border-gray-200 dark:border-white/10 pb-2 overflow-x-auto hide-scrollbar">
            <button @click="activeTab = 'sla'"
                class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                :class="activeTab === 'sla' ? 'text-primary border-b-2 border-primary -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                SLA Compliance Trend
            </button>
            <button @click="activeTab = 'revenue'"
                class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                :class="activeTab === 'revenue' ? 'text-emerald-500 border-b-2 border-emerald-500 -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                Revenue Analysis
            </button>
            <button @click="activeTab = 'orders'"
                class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                :class="activeTab === 'orders' ? 'text-purple-500 border-b-2 border-purple-500 -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                Order Volume
            </button>
            <div class="ml-auto flex-shrink-0 pl-4">
                <!-- Time Period Selection -->
                <select v-model="selectedTimePeriod"
                    class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg text-xs text-gray-700 dark:text-gray-300 px-3 py-1.5 outline-none transition-colors cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">
                    <option value="week" class="bg-white dark:bg-gray-800">Last 7 Days</option>
                    <option value="month" class="bg-white dark:bg-gray-800">This Month</option>
                </select>
            </div>
        </div>

        <!-- Chart Container -->
        <div class="h-64 lg:h-80 w-full relative">
            <Line :key="activeTab + '-' + selectedTimePeriod" :data="chartData" :options="chartOptions" />
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Line } from 'vue-chartjs'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const { activeTab, chartData, chartOptions, selectedTimePeriod } = inject(lmDashboardPageKey)
</script>
