<template>
    <div class="space-y-4">
        <!-- Selected order info -->
        <div v-if="selectedOrder" class="glass-panel p-4 sm:p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Active Order</h3>
            <div class="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                <div class="flex justify-between">
                    <span>Order ID</span>
                    <span class="font-mono font-bold text-gray-900 dark:text-white">{{ selectedOrder.trackingCode || selectedOrder.id }}</span>
                </div>
                <div class="flex justify-between">
                    <span>Status</span>
                    <span class="font-bold" :class="statusTextClass(selectedOrder.status)">{{ selectedOrder.status }}</span>
                </div>
                <div v-if="selectedOrder.pickupLocation || selectedOrder.from" class="flex justify-between">
                    <span>From</span>
                    <span class="text-right max-w-[140px] truncate">{{ selectedOrder.pickupLocation || selectedOrder.from }}</span>
                </div>
                <div v-if="selectedOrder.deliveryLocation || selectedOrder.to" class="flex justify-between">
                    <span>To</span>
                    <span class="text-right max-w-[140px] truncate">{{ selectedOrder.deliveryLocation || selectedOrder.to }}</span>
                </div>
            </div>
            <button @click="resetSession"
                class="mt-4 w-full text-xs text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors py-1.5 border border-gray-200 dark:border-white/10 rounded-lg hover:border-red-300 dark:hover:border-red-500/30">
                Change Order
            </button>
        </div>
        <!-- General chat (no order selected) -->
        <div v-else class="glass-panel p-4 sm:p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-2 text-sm">General Support</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">Chatting without a linked order. You can ask general questions or request human support.</p>
            <button @click="resetSession"
                class="mt-4 w-full text-xs text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors py-1.5 border border-gray-200 dark:border-white/10 rounded-lg hover:border-red-300 dark:hover:border-red-500/30">
                New Chat
            </button>
        </div>

        <!-- Quick actions -->
        <div class="glass-panel p-4 sm:p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Quick Actions</h3>
            <div class="space-y-2">
                <button
                    v-for="action in quickActions"
                    :key="action.label"
                    @click="sendQuickAction(action.message)"
                    class="w-full text-left p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/5 hover:border-green-500/50 hover:bg-gray-100 dark:hover:bg-white/10 transition-all flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300"
                >
                    <span class="material-symbols-outlined text-lg" :class="action.color">{{ action.icon }}</span>
                    {{ action.label }}
                </button>
            </div>
        </div>

        <!-- Service mods -->
        <div class="glass-panel p-4 sm:p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Service Modifications</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">Modify your selected order:</p>
            <div class="space-y-2">
                <button
                    v-for="mod in serviceMods"
                    :key="mod.label"
                    @click="sendQuickAction(mod.message)"
                    class="w-full text-left p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/5 hover:border-blue-500/50 hover:bg-gray-100 dark:hover:bg-white/10 transition-all flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300"
                >
                    <span class="material-symbols-outlined text-lg" :class="mod.color">{{ mod.icon }}</span>
                    {{ mod.label }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { individualSupportPageKey } from './individualSupportPageContext'

const {
    quickActions,
    resetSession,
    selectedOrder,
    sendQuickAction,
    serviceMods,
    statusTextClass,
} = inject(individualSupportPageKey)
</script>
