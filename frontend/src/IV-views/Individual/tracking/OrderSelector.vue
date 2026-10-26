<template>
    <!-- Active Orders Selector -->
    <div v-if="displayOrders.length > 1" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-4">
        <button v-for="order in displayOrders" :key="order.id" @click="selectOrder(order.id)"
            class="px-4 py-3 rounded-xl border transition-all text-left w-full shadow-sm"
            :class="selectedOrderId === order.id ? 'bg-green-50 dark:bg-green-900/20 border-green-500' : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-green-500/50'">
            <div class="flex justify-between items-center mb-1.5">
                <span class="font-bold text-sm font-mono"
                    :class="selectedOrderId === order.id ? 'text-green-700 dark:text-green-400' : 'text-gray-900 dark:text-white'">{{
                        order.id }}</span>
                <span
                    class="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase"
                    :class="order.status === 'in-transit' ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400'
                        : order.status === 'dispatched' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
                        : order.status === 'delivered' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400'
                        : order.status === 'cancelled' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
                        : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400'">{{ 
                        order.status === 'dispatched' ? 'ASSIGNED' : order.status.replace('-', ' ') }}</span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]"><span
                    class="font-medium">{{ order.cargoType }}</span></div>
            <div class="text-xs text-gray-400 dark:text-gray-500 truncate max-w-[200px] mt-0.5">{{
                order.pickup.split(',')[0] }} → {{ order.destination.split(',')[0] }}</div>
        </button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { displayOrders, selectOrder, selectedOrderId } = inject(customerTrackingPageKey)
</script>
