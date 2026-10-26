<template>
    <!-- Stat Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500">
            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Total Trips</div>
            <div class="text-3xl font-bold text-blue-400 mt-1">{{ todayTrips.length }}</div>
            <div class="text-xs text-gray-500 mt-1">Today</div>
        </div>
        <div class="glass-panel p-4 rounded-xl border-l-4 border-yellow-500">
            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Active</div>
            <div class="text-3xl font-bold text-yellow-400 mt-1">{{ activeCount }}</div>
            <div class="text-xs text-gray-500 mt-1">In transit</div>
        </div>
        <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500">
            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Completed</div>
            <div class="text-3xl font-bold text-green-400 mt-1">{{ completedCount }}</div>
            <div class="text-xs text-gray-500 mt-1">Delivered</div>
        </div>
        <div class="glass-panel p-4 rounded-xl" :class="assetAlertCount > 0 ? 'border-l-4 border-red-500' : 'border-l-4 border-gray-400 dark:border-gray-600'">
            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Asset Alerts</div>
            <div class="text-3xl font-bold mt-1" :class="assetAlertCount > 0 ? 'text-red-400' : 'text-gray-400'">{{ assetAlertCount }}</div>
            <div class="text-xs text-gray-500 mt-1">Missing items</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { manifestPageKey } from './manifestPageContext'

const { activeCount, assetAlertCount, completedCount, todayTrips } = inject(manifestPageKey)
</script>
