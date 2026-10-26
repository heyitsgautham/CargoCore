<template>
    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center border-2"
            :class="readyCount > 0 ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-transparent'">
            <div class="text-2xl font-bold text-emerald-400 flex items-center justify-center gap-1">
                {{ readyCount }}
                <span v-if="readyCount > 0" class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Ready</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-yellow-400">{{ pendingOrders.length }}</div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Pending</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-red-400">{{ urgentCount }}</div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Urgent</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-blue-400">{{ highCount }}</div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">High Priority</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ totalWeight.toLocaleString() }} kg</div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Total Weight</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-primary">{{ feasibleCount }}/{{ pendingOrders.length }}</div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Feasible</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const {
    feasibleCount,
    highCount,
    pendingOrders,
    readyCount,
    totalWeight,
    urgentCount,
} = inject(pendingQueuePageKey)
</script>
