<template>
    <!-- 1. CONTROL TOWER (Executive Summary) -->
    <div v-if="activeTab === 'control_tower'" class="space-y-6 animate-fade-in">

        <!-- ⚠ CRITICAL FINANCIAL ALERT: Both Revenue and Capital Flow Empty -->
        <!-- Guard on store.initialized so this never flashes during loading -->
        <div v-if="store.initialized && financeSummary.capital_flow_empty"
            class="relative overflow-hidden rounded-2xl border-2 border-red-500 shadow-2xl animate-pulse-border">
            <!-- Animated background -->
            <div class="absolute inset-0 bg-gradient-to-r from-red-900/90 via-orange-900/90 to-red-900/90 animate-gradient-x"></div>
            <div class="absolute inset-0 bg-red-500/10 backdrop-blur-sm"></div>

            <div class="relative z-10 p-6 flex flex-col md:flex-row items-start md:items-center gap-6">
                <!-- Icon + Pulsing Ring -->
                <div class="relative shrink-0">
                    <div class="absolute inset-0 rounded-full bg-red-500/30 animate-ping"></div>
                    <div class="w-20 h-20 rounded-full bg-red-500/20 border-2 border-red-400 flex items-center justify-center relative z-10">
                        <span class="material-symbols-outlined text-5xl text-red-300 animate-bounce">emergency</span>
                    </div>
                </div>

                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <span class="px-3 py-1 rounded-full bg-red-500 text-white text-xs font-black uppercase tracking-widest animate-pulse">🚨 CRITICAL ALERT</span>
                        <span class="text-red-300 text-xs font-mono">System Level Alert • Finance & Payroll</span>
                    </div>
                    <h2 class="text-2xl md:text-3xl font-black text-white mb-2">
                        ⚠ Revenue Flow is at Zero!
                    </h2>
                    <p class="text-red-200 text-sm leading-relaxed mb-4">
                        <strong>Revenue (MTD) has been fully consumed by expenses and payouts.</strong>
                        Further payments — staff bonuses, payroll, or procurement — will draw from Capital Inflow.
                        If capital is also exhausted, all payments will fail. <strong>Add a capital investment now</strong>
                        via <strong>Reports → Finances → Capital Investment Log</strong> to restore funding.
                    </p>
                    <div class="flex flex-wrap gap-3">
                        <button @click="activeTab = 'financials'"
                            class="px-5 py-2 bg-orange-500 hover:bg-orange-400 text-white font-bold rounded-xl text-sm flex items-center gap-2 transition-all shadow-lg shadow-orange-500/30 border border-orange-400">
                            <span class="material-symbols-outlined text-[18px]">add_card</span>
                            Fund Now — Log Capital Investment
                        </button>
                        <div class="flex items-center gap-3 text-xs text-red-300 font-mono">
                            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">payments</span> Revenue: ₹{{ (financeSummary.total_revenue || 0).toLocaleString() }}</span>
                            <span>•</span>
                            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">add_card</span> Capital: ₹{{ (financeSummary.capital_invested || 0).toLocaleString() }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Top Row Alerts -->
        <div v-if="crisisAlerts.length > 0" class="flex gap-4 overflow-x-auto pb-2">
            <div v-for="alert in crisisAlerts" :key="alert.id"
                class="flex-shrink-0 w-80 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 p-4 rounded-xl flex items-start gap-3 shadow-sm">
                <span class="material-symbols-outlined text-red-600 animate-bounce">warning</span>
                <div class="flex-1 min-w-0">
                    <h4 class="font-bold text-red-700 dark:text-red-400 text-sm">{{ alert.title }}</h4>
                    <p class="text-xs text-red-600/80 dark:text-red-400/80 mt-1">{{ alert.desc }}</p>
                    <div class="flex items-center gap-2 mt-2">
                        <p class="text-[10px] text-red-500 font-mono">Active Alert</p>
                        <button @click="store.resolveAlert(alert.id)"
                            class="text-[10px] px-2 py-0.5 rounded bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-500/30 font-bold transition-colors">
                            Dismiss
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Daily Orders Gauge -->
            <div
                class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center relative overflow-hidden group hover:scale-[1.02] transition-transform">
                <h3 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-4">
                    Daily Completion</h3>
                <div class="relative h-74 w-40 mx-auto">
                    <svg class="h-full w-full -rotate-90" viewBox="0 0 36 36">
                        <path class="text-gray-200 dark:text-gray-700"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none" stroke="currentColor" stroke-width="3" />
                        <path class="text-primary transition-all duration-1000 ease-out"
                            :stroke-dasharray="`${completionRate}, 100`"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none" stroke="currentColor" stroke-width="3" />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <span class="text-xl font-black text-gray-900 dark:text-white">{{ completedOrders }}/{{
                            totalOrders }}</span>
                        <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Orders</span>
                    </div>
                </div>
            </div>

            <!-- System Health + Dues -->
            <div class="lg:col-span-1 space-y-4">
                <div
                    class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                    <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">System Health</h3>
                    <div class="flex items-end gap-2">
                        <span class="text-4xl font-black text-green-500">{{ store.dashboardStats.deliverySuccess
                            }}%</span>
                        <span
                            class="text-xs font-bold mb-1 px-2 py-0.5 rounded-full"
                            :class="store.dashboardStats.deliverySuccess >= 80 ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100'"
                        >
                            {{ store.dashboardStats.deliverySuccess >= 80 ? '▲ On Track' : '▼ Below Target' }}
                        </span>
                    </div>
                    <p class="text-xs text-gray-400 mt-2">Delivery Success Rate</p>
                </div>
                <div
                    class="p-5 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-500/20 rounded-2xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform">
                    <div
                        class="absolute -right-4 -top-4 bg-red-500 w-16 h-16 rounded-full opacity-20 blur-xl group-hover:opacity-30 transition-opacity">
                    </div>
                    <h3
                        class="text-xs font-bold text-red-600 dark:text-red-400 uppercase mb-2 flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">payments</span> Pending Dues
                    </h3>
                    <span class="text-3xl font-black text-gray-900 dark:text-white">₹{{ (store.reportMetrics.pending_dues || 0).toLocaleString() }}</span>
                    <p class="text-xs text-red-500 mt-1 font-medium">Critical Collection Required</p>
                </div>
            </div>

            <!-- AI Daily Summary -->
            <div
                class="lg:col-span-2 p-6 bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/10 dark:to-white/5 border border-purple-100 dark:border-purple-500/20 rounded-2xl shadow-sm relative">
                <span
                    class="material-symbols-outlined absolute top-4 right-4 text-purple-300 text-6xl opacity-20 animate-pulse">auto_awesome</span>
                <h3 class="font-bold text-purple-900 dark:text-purple-300 flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined">smart_toy</span> Daily AI Briefing
                </h3>
                <div v-if="aiThinking" class="flex items-center gap-2 text-sm text-purple-500 animate-pulse mb-2">
                    <span class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                    Analysing...
                </div>
                <ul v-if="aiInsights.length" class="space-y-2">
                    <li v-for="(insight, i) in aiInsights" :key="i"
                        class="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <span class="mt-1 h-1.5 w-1.5 rounded-full bg-purple-500 shrink-0"></span>
                        <span v-html="insight"></span>
                    </li>
                </ul>
                <div v-else-if="!aiThinking" class="flex flex-col items-center justify-center py-4 text-center">
                    <span class="material-symbols-outlined text-3xl text-purple-300 mb-2">auto_awesome</span>
                    <p class="text-sm text-gray-400 dark:text-gray-500">Ask the AI above to generate insights.<br>
                        <span class="text-xs text-purple-400">e.g. "Show me top spending vendors"</span>
                    </p>
                </div>
            </div>
        </div>

        <!-- Entity Stats Overview Table -->
        <EntityOverviewTable :store="store" :avg-driver-efficiency="avgDriverEfficiency" :vehicles-in-maintenance="vehiclesInMaintenance" />
    </div>
</template>

<script setup>
import { inject } from 'vue'
import EntityOverviewTable from './EntityOverviewTable.vue'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    aiInsights,
    aiThinking,
    avgDriverEfficiency,
    completedOrders,
    completionRate,
    crisisAlerts,
    financeSummary,
    store,
    totalOrders,
    vehiclesInMaintenance,
} = inject(reportsPageKey)
</script>

<style scoped src="./Reports.css"></style>
