<template>
    <div class="glass-panel rounded-xl overflow-hidden p-6">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Ready for Dispatch — Outbound Queue</h3>
        <div v-if="outboundOrders.length === 0" class="text-center text-gray-500 py-6">
            <span class="material-symbols-outlined text-4xl mb-2 opacity-50">local_shipping</span>
            <p class="text-sm">No orders ready for dispatch yet</p>
        </div>
        <div v-else class="space-y-3">
            <div v-for="order in outboundOrders" :key="order.id"
                class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                <div class="flex items-center gap-4">
                    <div
                        class="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-gray-900 dark:text-white font-bold text-xs flex-col">
                        <span>{{ order.eta }}</span>
                        <span class="text-[8px] text-gray-600 dark:text-gray-400">DUE</span>
                    </div>
                    <div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ order.tracking }}</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">{{ order.type }} • {{ order.items
                            }} items</div>
                        <div class="text-[10px] mt-0.5">
                            <span class="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-600 dark:text-blue-400">{{
                                order.status }}</span>
                        </div>
                    </div>
                </div>
                <button @click="selectedOutbound = order; showTruckDetail = true"
                    class="text-primary hover:underline text-xs">Details</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const { outboundOrders, selectedOutbound, showTruckDetail } = inject(loadingDockPageKey)
</script>
