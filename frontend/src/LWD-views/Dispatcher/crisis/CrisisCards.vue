<template>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div v-for="crisis in activeCrises" :key="crisis.id"
            class="border rounded-xl p-6 relative overflow-hidden"
            :class="crisis.level === 'CRITICAL' ? 'bg-red-500/10 border-red-500/30' : 'bg-yellow-500/10 border-yellow-500/30'">
            <div class="flex justify-between items-start mb-4">
                <div class="flex items-center gap-2">
                    <span class="px-2 py-1 text-xs font-bold rounded"
                        :class="crisis.level === 'CRITICAL' ? 'bg-red-500 text-white animate-pulse' : 'bg-yellow-500 text-black'">
                        {{ crisis.level }}
                    </span>
                    <span class="text-gray-900 dark:text-white font-bold">{{ crisis.title }}</span>
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ crisis.timeAgo }}</div>
            </div>
            <div class="text-gray-600 dark:text-gray-200 text-sm mb-3">{{ crisis.description }}</div>

            <!-- Affected Orders / Reassignment -->
            <div v-if="crisis.affectedOrders?.length" class="mb-3 p-3 bg-gray-100 dark:bg-black/30 rounded-lg">
                <div class="text-[10px] text-gray-500 dark:text-gray-500 uppercase font-bold mb-2">Affected Orders – Backup Driver Planning</div>
                <div class="space-y-1">
                    <div v-for="order in crisis.affectedOrders" :key="order.id"
                        class="flex items-center justify-between text-xs">
                        <span class="text-gray-600 dark:text-gray-300">{{ order.id }} – {{ order.dest }}</span>
                        <div class="flex items-center gap-2">
                            <span v-if="order.reassigned" class="text-green-400 font-bold">→ {{ order.newDriver }}</span>
                            <button v-else @click="reassignOrder(crisis.id, order.id)"
                                class="bg-emerald-600 hover:bg-emerald-700 dark:bg-primary/20 dark:hover:bg-primary/30 text-white dark:text-primary px-2.5 py-1 rounded-lg font-bold transition-colors text-xs shadow-sm">
                                Suggest Backup
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ETA Update + AI Bot Notification -->
            <div class="mb-3 flex items-center gap-2 text-[10px]">
                <span class="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded font-bold">ETA Updated</span>
                <span class="text-gray-500">
                    {{ crisis.type === 'broadcast' ? 'Drivers notified via AI Bot' : (crisis.driverId || crisis.driver_id) ? 'Driver + Customers notified via AI Bot' : 'Customers notified via AI Bot' }}
                </span>
            </div>

            <div class="flex gap-3">
                <button v-for="action in crisis.actions" :key="action.label"
                    @click="handleCrisisAction(crisis, action)"
                    :class="[action.baseClass, action.done ? 'opacity-60 cursor-default' : '']" 
                    class="flex-1 font-bold py-2.5 rounded-lg transition-all text-sm border shadow-md">{{ action.done ? '✓ ' + action.label : action.label }}</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { crisisPageKey } from './crisisPageContext'

const { activeCrises, handleCrisisAction, reassignOrder } = inject(crisisPageKey)
</script>
