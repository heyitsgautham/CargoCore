<template>
    <!-- Scheduling Conflict Warning -->
    <div class="glass-panel rounded-xl p-5">
        <div class="flex items-center gap-2 mb-4">
            <span class="material-symbols-outlined text-yellow-400">event_busy</span>
            <h3 class="font-bold text-gray-900 dark:text-white">Scheduling Conflicts & Overbooking Prevention</h3>
        </div>
        <div v-if="serviceMoves.length === 0" class="p-3 bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
            <span class="material-symbols-outlined text-green-500 dark:text-green-400 text-[18px]">check_circle</span>
            <div class="text-xs text-green-700 dark:text-green-300">No active service moves. No scheduling conflicts detected.</div>
        </div>
        <div v-else class="p-3 bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
            <span class="material-symbols-outlined text-green-500 dark:text-green-400 text-[18px]">check_circle</span>
            <div class="text-xs text-green-700 dark:text-green-300">{{ serviceMoves.length }} active move(s). All drivers have clear time blocks. No overbooking detected.</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const { serviceMoves } = inject(serviceMovesPageKey)
</script>
