<template>
    <!-- SLA Alerts -->
    <div class="glass-panel rounded-xl p-5">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-red-400">notification_important</span>
            SLA Violation Alerts
        </h3>
        <div v-if="overdueOrders.length" class="space-y-3">
            <div v-for="order in overdueOrders" :key="order.id" class="p-3 bg-red-100 dark:bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-red-500 dark:text-red-400">error</span>
                    <div>
                        <div class="text-sm text-red-700 dark:text-red-300 font-bold">{{ order.id }} — ETA Overdue</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">Driver: {{ order.driver || 'Unassigned' }} • Status: {{ order.statusLabel }}</div>
                    </div>
                </div>
                <button @click="resolveAlert(order.id)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-colors border"
                    :class="alertResolved[order.id] ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 text-red-700 dark:text-red-400 border-red-300 dark:border-red-500/30'">
                    {{ alertResolved[order.id] ? '✓ Resolved' : 'Resolve Now' }}
                </button>
            </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500 text-sm">
            <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
            No active SLA violations
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const { alertResolved, overdueOrders, resolveAlert } = inject(orderStatusPageKey)
</script>
