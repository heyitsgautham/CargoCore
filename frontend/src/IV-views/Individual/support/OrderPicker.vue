<template>
    <div class="flex flex-col items-center text-center gap-3 mb-6">
        <div class="w-14 h-14 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center">
            <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
        </div>
        <div>
            <p class="font-bold text-gray-900 dark:text-white">Start Support Chat</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Select an active order for context, or start a general chat without one.
            </p>
        </div>
    </div>

    <div v-if="loadingOrders" class="flex justify-center py-6 text-sm text-gray-400">
        Loading your orders…
    </div>

    <template v-else>
        <div v-if="selectableOrders.length > 0" class="space-y-2 mb-4">
            <p class="text-xs font-bold uppercase tracking-wide text-gray-400 mb-3">Your Active Orders</p>
            <button
                v-for="order in selectableOrders"
                :key="order.backendId"
                @click="selectOrder(order)"
                class="w-full flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/60 hover:bg-green-50/50 dark:hover:bg-white/8 transition-all group"
            >
                <div class="text-left">
                    <div class="font-bold text-sm text-gray-900 dark:text-white font-mono">{{ order.trackingCode || order.id }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ order.id !== order.trackingCode ? order.id : '' }}</div>
                </div>
                <div class="flex items-center gap-3">
                    <span
                        class="text-[11px] font-bold uppercase px-2 py-0.5 rounded-full"
                        :class="statusBadgeClass(order.status)"
                    >{{ order.status }}</span>
                    <span class="material-symbols-outlined text-gray-400 group-hover:text-green-500 transition-colors text-[18px]">arrow_forward</span>
                </div>
            </button>
        </div>
        <div v-else class="text-center py-4 mb-4">
            <span class="material-symbols-outlined text-4xl text-gray-300 dark:text-white/20 mb-2 block">inbox</span>
            <p class="text-sm text-gray-500 dark:text-gray-400">No active orders found.</p>
        </div>

        <!-- Chat without order -->
        <div class="pt-3 border-t border-gray-200 dark:border-white/10">
            <button
                @click="startWithoutOrder"
                class="w-full flex items-center justify-center gap-2 p-3 rounded-xl border border-dashed border-gray-300 dark:border-white/15 bg-gray-50 dark:bg-white/5 hover:border-green-500/60 hover:bg-green-50/30 dark:hover:bg-white/8 transition-all text-sm text-gray-600 dark:text-gray-400 hover:text-green-700 dark:hover:text-green-400"
            >
                <span class="material-symbols-outlined text-[18px]">chat</span>
                Chat without selecting an order
            </button>
        </div>
    </template>
</template>

<script setup>
import { inject } from 'vue'
import { individualSupportPageKey } from './individualSupportPageContext'

const {
    loadingOrders,
    selectOrder,
    selectableOrders,
    startWithoutOrder,
    statusBadgeClass,
} = inject(individualSupportPageKey)
</script>
