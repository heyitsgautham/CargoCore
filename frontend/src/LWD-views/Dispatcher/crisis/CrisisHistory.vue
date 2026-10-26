<template>
    <div class="glass-panel rounded-xl p-6">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-green-600 dark:text-green-500">task_alt</span>
            Resolved Incidents (Today)
        </h3>
        <div class="space-y-3">
            <div v-for="resolved in resolvedIncidents" :key="resolved.id"
                class="flex items-start gap-3 p-3 rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-all">
                <span class="material-symbols-outlined text-green-600 dark:text-green-500 text-[20px]">check_circle</span>
                <div class="flex-1">
                    <div class="text-gray-800 dark:text-gray-200 text-sm font-semibold mb-1">{{ resolved.title }}</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400">{{ resolved.detail }}</div>
                </div>
                <span class="text-xs text-gray-700 dark:text-gray-300 font-mono font-semibold bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">{{ resolved.time }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { crisisPageKey } from './crisisPageContext'

const { resolvedIncidents } = inject(crisisPageKey)
</script>
