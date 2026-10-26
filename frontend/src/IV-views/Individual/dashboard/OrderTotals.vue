<template>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ stats.total_orders || 0 }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Moves</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ stats.active_orders || 0 }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Active</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ stats.pending_orders || 0 }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Pending</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">₹{{
                Number(stats.total_spent || 0).toLocaleString() }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Spent</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { individualDashboardPageKey } from './individualDashboardPageContext'

const { stats } = inject(individualDashboardPageKey)
</script>
