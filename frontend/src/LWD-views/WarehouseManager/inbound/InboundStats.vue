<template>
    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-green-600 dark:text-green-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ arrivedCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Arrived Today</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-blue-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-blue-400">{{ inTransitCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">In Transit</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-red-600 dark:text-red-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-red-600 dark:text-red-400">{{ mismatchCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Mismatches Found</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div v-if="loading" class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 animate-pulse">--</div>
            <div v-else class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ damageCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Damage Reports</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const {
    arrivedCount,
    damageCount,
    inTransitCount,
    loading,
    mismatchCount,
} = inject(inboundPageKey)
</script>
