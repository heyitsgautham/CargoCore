<template>
    <div v-if="disruptions.length" class="space-y-2">
        <div v-for="d in disruptions" :key="d.id"
            class="flex items-center justify-between p-3 rounded-lg border"
            :class="d.severity === 'critical' ? 'bg-red-500/10 border-red-500/20' : 'bg-yellow-500/10 border-yellow-500/20'">
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined"
                    :class="d.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'">{{ d.icon }}</span>
                <div>
                    <div class="text-sm text-gray-900 dark:text-white font-medium">{{ d.title }}</div>
                    <div class="text-[10px] text-gray-500 dark:text-gray-400">{{ d.detail }} • Affects {{ d.affected }} drivers</div>
                </div>
            </div>
            <div class="flex gap-2">
                <button @click="autoReroute(d)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-all border shadow-sm"
                    :class="d.rerouted ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white border-gray-300 dark:border-white/20'">
                    {{ d.rerouted ? '✓ Plan Built' : 'Build Recovery Plan' }}
                </button>
                <button @click="updateETAs(d)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-all border shadow-sm"
                    :class="d.etaUpdated ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-blue-600 dark:bg-blue-500/20 hover:bg-blue-700 dark:hover:bg-blue-500/30 text-white dark:text-blue-400 border-blue-700 dark:border-blue-500/30'">
                    {{ d.etaUpdated ? '✓ ETAs Refreshed' : 'Refresh ETAs' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { crisisPageKey } from './crisisPageContext'

const { autoReroute, disruptions, updateETAs } = inject(crisisPageKey)
</script>
