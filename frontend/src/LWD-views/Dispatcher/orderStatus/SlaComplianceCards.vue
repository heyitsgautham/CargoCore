<template>
    <!-- SLA Compliance Tracking -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">Ready → Assigned Time</span>
                <span class="material-symbols-outlined text-[16px] text-yellow-400">timer</span>
            </div>
            <div class="text-xl font-bold text-gray-900 dark:text-white">—</div>
            <div class="text-[10px] text-gray-500">Target: &lt;10 min</div>
        </div>
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">On-Time Pickup %</span>
                <span class="material-symbols-outlined text-[16px] text-blue-400">local_shipping</span>
            </div>
            <div class="text-xl font-bold text-gray-900 dark:text-white">{{ dispatchedCount + inTransitCount + deliveredCount > 0 ? Math.round(((dispatchedCount + deliveredCount) / (orders.length || 1)) * 100) + '%' : '—' }}</div>
            <div class="text-[10px] text-gray-500">SLA target: 95%</div>
        </div>
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">On-Time Dispatch %</span>
                <span class="material-symbols-outlined text-[16px] text-purple-400">send</span>
            </div>
            <div class="text-xl font-bold text-gray-900 dark:text-white">{{ orders.length > 0 ? Math.round(((orders.length - readyCount) / orders.length) * 100) + '%' : '—' }}</div>
            <div class="text-[10px] text-gray-500">SLA target: 95%</div>
        </div>
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">Missed Window</span>
                <span class="material-symbols-outlined text-[16px] text-red-400">report</span>
            </div>
            <div class="text-xl font-bold" :class="overdueCount > 0 ? 'text-red-400' : 'text-gray-900 dark:text-white'">{{ overdueCount }}</div>
            <div class="text-[10px] text-gray-500">Orders delayed today</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const {
    deliveredCount,
    dispatchedCount,
    inTransitCount,
    orders,
    overdueCount,
    readyCount,
} = inject(orderStatusPageKey)
</script>
