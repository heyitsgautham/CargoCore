<template>
    <!-- Top KPI Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div class="glass-panel p-4 rounded-xl flex flex-col justify-between h-32 relative overflow-hidden group">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-4xl text-teal-500">inventory_2</span>
            </div>
            <div class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Total
                Inventory Value</div>
            <div class="flex items-baseline gap-1">
                <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatLargeNumber(totalInventoryValue) }}</span>
                <span v-if="inventoryValueChangePercent !== 0" class="text-xs" :class="inventoryValueChangePercent > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                    {{ inventoryValueChangePercent > 0 ? '+' : '' }}{{ inventoryValueChangePercent }}%
                </span>
            </div>
            <div class="w-full bg-gray-100 dark:bg-gray-800 h-1 mt-2 rounded-full overflow-hidden">
                <div class="bg-teal-500 h-full transition-all" :style="`width: ${Math.min(100, (totalInventoryValue / 5000000) * 100)}%`"></div>
            </div>
        </div>

        <div
            class="glass-panel p-4 rounded-xl flex flex-col justify-between h-32 group border-l-4 border-yellow-500">
            <div class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Orders
                Pending Pick</div>
            <div class="flex items-baseline gap-1">
                <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ pendingOrdersCount }}</span>
                <span v-if="pendingOrdersCount > 10" class="text-xs text-yellow-500">Critical</span>
            </div>
            <div class="text-xs text-gray-500">Avg Pick Time: {{ avgPickTime }}m</div>
        </div>

        <div class="glass-panel p-4 rounded-xl flex flex-col justify-between h-32 group">
            <div class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Ready for
                Dispatch</div>
            <div class="flex items-baseline gap-1">
                <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ readyForDispatch }}</span>
            </div>
            <div class="text-xs text-blue-400 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">local_shipping</span> Next Truck: {{ nextTruckMinutes }}m
            </div>
        </div>

        <div class="glass-panel p-4 rounded-xl flex flex-col justify-between h-32 group">
            <div class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Labor Active
            </div>
            <div class="flex items-baseline gap-1">
                <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ activeLabor }}</span>
                <span class="text-xs text-gray-500">/ {{ totalLabor }}</span>
            </div>
            <div class="flex -space-x-2 mt-2" v-if="activeLabor > 0">
                <div class="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 border border-black"></div>
                <div class="w-6 h-6 rounded-full bg-gray-600 border border-black"></div>
                <div v-if="activeLabor > 2"
                    class="w-6 h-6 rounded-full bg-gray-500 border border-black flex items-center justify-center text-[8px] text-gray-900 dark:text-white">
                    +{{ activeLabor - 2 }}</div>
            </div>
        </div>

        <!-- Dynamic Restock KPI Card -->
        <div class="glass-panel p-4 rounded-xl flex flex-col justify-between h-32 group transition-colors"
            :class="criticalSkus.length > 0 ? 'bg-red-50 dark:bg-red-900/10 border-red-500/20' : 'bg-green-50 dark:bg-green-900/10 border-green-500/20'">
            <div class="text-xs font-semibold uppercase tracking-wide"
                :class="criticalSkus.length > 0 ? 'text-red-600 dark:text-red-300' : 'text-green-600 dark:text-green-300'">
                Safety Stock Alerts
            </div>
            <div class="flex items-baseline gap-1">
                <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ criticalSkus.length }}</span>
                <span v-if="criticalSkus.length > 0" class="text-xs text-red-600 dark:text-red-400">SKUs Warning</span>
                <span v-else class="text-xs text-green-600 dark:text-green-400">All Good</span>
            </div>
            <button v-if="criticalSkus.length > 0" @click="showRestockModal = true"
                class="text-xs bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-300 py-1 px-2 rounded transition-colors w-fit shadow-sm">
                Restock Now
            </button>
            <div v-else class="text-xs text-green-600 dark:text-green-500/70 py-1 font-medium">Fully Stocked</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const {
    activeLabor,
    avgPickTime,
    criticalSkus,
    formatLargeNumber,
    inventoryValueChangePercent,
    nextTruckMinutes,
    pendingOrdersCount,
    readyForDispatch,
    showRestockModal,
    totalInventoryValue,
    totalLabor,
} = inject(wmDashboardPageKey)
</script>
