<template>
    <!-- Top KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
            class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
            <div
                class="absolute -right-6 -top-6 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors">
            </div>
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Total Orders Today</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                        store.dashboardStats.ordersToday.toLocaleString()
                    }}
                    </div>
                </div>
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    <span class="material-symbols-outlined">shopping_cart</span>
                </div>
            </div>
            <div class="flex items-center text-sm">
                <span class="font-medium flex items-center" :class="ordersTrend >= 0 ? 'text-primary' : 'text-red-400'">
                    <span class="material-symbols-outlined text-[16px] mr-1">{{ ordersTrend >= 0 ? 'trending_up' : 'trending_down' }}</span>
                    {{ ordersTrend >= 0 ? '+' : '' }}{{ ordersTrend }}%
                </span>
                <span class="text-gray-500 dark:text-gray-400 ml-2">vs yesterday</span>
            </div>
        </div>

        <div
            class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
            <div
                class="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-colors">
            </div>
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Active Deliveries</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                        store.dashboardStats.activeDeliveries }}
                    </div>
                </div>
                <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500">
                    <span class="material-symbols-outlined">local_shipping</span>
                </div>
            </div>
            <div class="flex items-center text-sm">
                <span class="text-gray-500 dark:text-gray-400 font-medium">
                    {{ store.dashboardStats.deliverySuccess }}% On-Time
                </span>
                <div class="ml-auto w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 transition-all duration-500"
                        :style="{ width: `${Math.min(store.dashboardStats.deliverySuccess, 100)}%` }"></div>
                </div>
            </div>
        </div>

        <div
            class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
            <div
                class="absolute -right-6 -top-6 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-colors">
            </div>
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Delivery Success Rate</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                        store.dashboardStats.deliverySuccess }}%
                    </div>
                </div>
                <div class="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500">
                    <span class="material-symbols-outlined">verified</span>
                </div>
            </div>
            <div class="flex items-center text-sm">
                <span class="font-medium flex items-center" :class="successRateColor">
                    {{ successRateLabel }}
                </span>
                <span class="text-gray-500 dark:text-gray-400 ml-2">{{ successRateStatus }}</span>
            </div>
        </div>

        <div
            class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
            <div
                class="absolute -right-6 -top-6 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors">
            </div>
            <div class="flex justify-between items-start mb-4">
                <div>
                    <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Revenue Today</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">₹{{
                        (store.dashboardStats.revenueToday /
                            1000).toFixed(1) }}k</div>
                </div>
                <div
                    class="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                    <span class="material-symbols-outlined">payments</span>
                </div>
            </div>
            <div class="flex items-center text-sm">
                <span class="font-medium flex items-center" :class="revenueTrend >= 0 ? 'text-emerald-400' : 'text-red-400'">
                    <span class="material-symbols-outlined text-[16px] mr-1">{{ revenueTrend >= 0 ? 'trending_up' : 'trending_down' }}</span>
                    {{ revenueTrend >= 0 ? '+' : '' }}{{ revenueTrend }}%
                </span>
                <span class="text-gray-500 dark:text-gray-400 ml-2">vs yesterday</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const {
    ordersTrend,
    revenueTrend,
    store,
    successRateColor,
    successRateLabel,
    successRateStatus,
} = inject(lmDashboardPageKey)
</script>
