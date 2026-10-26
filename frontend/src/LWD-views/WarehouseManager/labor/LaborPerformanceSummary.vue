<template>
    <!-- Performance Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="glass-panel p-6 rounded-xl">
            <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Active Staff</div>
            <div class="text-4xl font-bold text-gray-900 dark:text-white mt-2">{{ staffList.length }}</div>
            <div class="text-green-600 dark:text-green-400 text-xs mt-1">Full Roster</div>
        </div>
        <div class="glass-panel p-6 rounded-xl">
            <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Avg. Productivity</div>
            <div class="text-4xl font-bold text-primary mt-2">{{ avgProductivity }}%</div>
            <div class="text-gray-500 text-xs mt-1">{{ avgProductivity >= 100 ? 'Above target' : 'Below target' }}</div>
        </div>
        <div class="glass-panel p-6 rounded-xl">
            <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Total Hours Logged</div>
            <div class="text-4xl font-bold text-yellow-600 dark:text-yellow-400 mt-2">{{ totalHours }}h</div>
            <div class="text-gray-500 text-xs mt-1">Today</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const { avgProductivity, staffList, totalHours } = inject(laborPageKey)
</script>
