<template>
    <!-- 7. REPORT HISTORY & ANALYTICS -->
    <div v-if="activeTab === 'reports_history'" class="space-y-6 animate-fade-in">
        <!-- Analytics Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-xl p-6 shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">SLA Compliance Trends</h3>
                <div class="h-74 relative w-full">
                    <Line :data="analyticsSLAData" :options="chartOptions" />
                </div>
            </div>
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-xl p-6 shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Hub Efficiency Leaderboard</h3>
                <div class="h-74 relative">
                    <Bar :data="analyticsHubData" :options="chartOptions" />
                </div>
            </div>
        </div>

        <!-- Reports List -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="report in store.filteredReports" :key="report.id"
                class="p-4 bg-white hover:bg-gray-50 dark:bg-white/5 dark:hover:bg-white/10 rounded-xl border border-gray-200 dark:border-white/5 hover:border-primary/50 dark:hover:border-primary/30 cursor-pointer transition-all group flex items-start gap-4 shadow-sm">
                <div class="p-2.5 rounded-lg shadow-sm"
                    :class="`bg-${report.color}-50 text-${report.color}-600 dark:bg-${report.color}-500/10 dark:text-${report.color}-400`">
                    <span class="material-symbols-outlined">{{ report.icon }}</span>
                </div>
                <div>
                    <div
                        class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-primary transition-colors leading-tight mb-1">
                        {{ report.title }}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">Date: {{ report.date }} • {{
                        activeWarehouseName }}</div>
                    <button @click.stop="downloadReport(report.id)"
                        class="mt-2 text-[10px] font-bold text-primary flex items-center gap-1 hover:underline">
                        <span class="material-symbols-outlined text-[12px]">download</span> Download PDF
                    </button>
                </div>
            </div>
            <!-- Previous Report Placeholder -->
            <button
                class="p-4 border-2 border-dashed border-gray-200 dark:border-white/10 rounded-xl flex items-center justify-center text-gray-400 hover:text-primary hover:border-primary/50 transition-colors gap-2">
                <span class="material-symbols-outlined">history</span> Load Archived Reports
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    analyticsHubData,
    analyticsSLAData,
    chartOptions,
    downloadReport,
    store,
} = inject(reportsPageKey)
</script>
