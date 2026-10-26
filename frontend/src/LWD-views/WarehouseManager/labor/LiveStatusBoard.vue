<template>
    <!-- Live Status Board -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500 cursor-pointer hover:bg-gray-50 dark:bg-white/5 transition-colors"
            @click="statusFilter = statusFilter === 'In Warehouse' ? '' : 'In Warehouse'">
            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">In Warehouse
            </div>
            <div class="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">{{ statusCounts.inWarehouse }}</div>
            <div class="flex items-center gap-1 mt-1">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span class="text-xs text-green-600/70 dark:text-green-400/70">Active on floor</span>
            </div>
        </div>
        <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500 cursor-pointer hover:bg-gray-50 dark:bg-white/5 transition-colors"
            @click="statusFilter = statusFilter === 'Warehouse Order' ? '' : 'Warehouse Order'">
            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Warehouse
                Order</div>
            <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ statusCounts.warehouseOrder }}</div>
            <div class="text-xs text-blue-600/70 dark:text-blue-400/70 mt-1">Pick, pack, loading tasks</div>
        </div>
        <div class="glass-panel p-4 rounded-xl border-l-4 border-purple-500 cursor-pointer hover:bg-gray-50 dark:bg-white/5 transition-colors"
            @click="statusFilter = statusFilter === 'Customer Move' ? '' : 'Customer Move'">
            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Customer
                Move</div>
            <div class="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ statusCounts.customerMove }}</div>
            <div class="text-xs text-purple-600/70 dark:text-purple-400/70 mt-1">Service move / with driver</div>
        </div>
        <div class="glass-panel p-4 rounded-xl border-l-4 border-gray-500 cursor-pointer hover:bg-gray-50 dark:bg-white/5 transition-colors"
            @click="statusFilter = statusFilter === 'Off Duty' ? '' : 'Off Duty'">
            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Off Duty
            </div>
            <div class="text-3xl font-bold text-gray-600 dark:text-gray-400 mt-1">{{ statusCounts.offDuty }}</div>
            <div class="text-xs text-gray-500 mt-1">Shift ended / Break</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const { statusCounts, statusFilter } = inject(laborPageKey)
</script>
