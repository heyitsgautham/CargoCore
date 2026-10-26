<template>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="glass-panel p-5 rounded-xl">
            <div class="flex items-center justify-between mb-3">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Active Orders</div>
                <span class="material-symbols-outlined text-blue-400 text-[20px]">local_shipping</span>
            </div>
            <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ stats.active_orders || 0 }}</div>
            <div class="text-amber-500 text-xs mt-1">{{ stats.pending_orders || 0 }} pending</div>
        </div>
        <div class="glass-panel p-5 rounded-xl">
            <div class="flex items-center justify-between mb-3">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Total Spent</div>
                <span class="material-symbols-outlined text-purple-400 text-[20px]">payments</span>
            </div>
            <div class="text-3xl font-bold text-gray-900 dark:text-white">₹{{ (stats.total_spent || 0).toLocaleString() }}</div>
            <div class="text-gray-500 text-xs mt-1">All-time</div>
        </div>
        <router-link to="/individual/wallet" class="glass-panel p-5 rounded-xl hover:border-green-500/30 transition-all cursor-pointer">
            <div class="flex items-center justify-between mb-3">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Wallet Balance</div>
                <span class="material-symbols-outlined text-green-400 text-[20px]">account_balance_wallet</span>
            </div>
            <div class="text-3xl font-bold text-green-500">₹{{ walletBalance.toLocaleString() }}</div>
            <div class="text-gray-500 text-xs mt-1">Available credit</div>
        </router-link>
        <div class="glass-panel p-5 rounded-xl">
            <div class="flex items-center justify-between mb-3">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Completed</div>
                <span class="material-symbols-outlined text-green-400 text-[20px]">verified</span>
            </div>
            <div class="text-3xl font-bold text-green-500">{{ stats.delivered_orders || 0 }}</div>
            <div class="text-green-500 text-xs mt-1">Successful moves</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { individualDashboardPageKey } from './individualDashboardPageContext'

const { stats, walletBalance } = inject(individualDashboardPageKey)
</script>
