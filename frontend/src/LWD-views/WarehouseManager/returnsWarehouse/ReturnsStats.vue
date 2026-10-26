<template>
    <!-- Stats Row -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-blue-600 dark:text-blue-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ damageReviewQueue.length }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Damage Reviews Pending</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ processingItems.length }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Awaiting Physical Inspection</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-green-600 dark:text-green-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ completedItems.filter(i => i.disposition === 'restock').length }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Restocked Today</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-red-600 dark:text-red-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-red-600 dark:text-red-400">{{ completedItems.filter(i => i.disposition === 'claims').length }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Sent to Claims</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-gray-600 dark:text-gray-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-gray-600 dark:text-gray-400">{{ completedItems.filter(i => i.disposition === 'discard' || i.disposition === 'recycle').length }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Discarded / Recycled</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { returnsWarehousePageKey } from './returnsWarehousePageContext'

const { completedItems, damageReviewQueue, loading, processingItems } = inject(returnsWarehousePageKey)
</script>
