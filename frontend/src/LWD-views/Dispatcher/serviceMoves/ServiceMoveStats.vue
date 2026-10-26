<template>
    <!-- Summary Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ serviceMoves.length }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Active Moves</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-blue-400">{{ totalCrewCount }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Crew Deployed</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-purple-400">{{ blockedHours }}h</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Time Blocked</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-yellow-400">{{ vehiclesReserved }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Vehicles Reserved</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-primary">{{ completedToday }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Completed Today</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const {
    blockedHours,
    completedToday,
    serviceMoves,
    totalCrewCount,
    vehiclesReserved,
} = inject(serviceMovesPageKey)
</script>
