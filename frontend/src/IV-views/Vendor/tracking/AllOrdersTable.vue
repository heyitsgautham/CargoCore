<template>
    <!-- All Orders Table -->
    <div v-if="globalTab === 'table'" class="flex-1 glass-panel rounded-2xl overflow-hidden flex flex-col">
        <!-- Mini stats -->
        <div class="grid grid-cols-4 divide-x divide-gray-100 dark:divide-white/5 border-b border-gray-100 dark:border-white/5">
            <div class="p-4">
                <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Total Valuation</div>
                <div class="text-sm font-bold text-gray-900 dark:text-white">₹{{ (store.shipments.reduce((a, s) => a + s.amount, 0)).toLocaleString() }}</div>
            </div>
            <div class="p-4">
                <div class="text-[9px] text-blue-500 uppercase font-bold mb-1">Active</div>
                <div class="text-sm font-bold text-blue-600 dark:text-blue-400">{{ store.activeShipments.length }} shipments</div>
            </div>
            <div class="p-4">
                <div class="text-[9px] text-green-500 uppercase font-bold mb-1">On-Time Rate</div>
                <div class="text-sm font-bold text-green-600 dark:text-green-400">{{ store.analyticsData.onTime }}%</div>
            </div>
            <div class="p-4">
                <div class="text-[9px] text-purple-500 uppercase font-bold mb-1">Avg Transit</div>
                <div class="text-sm font-bold text-purple-600 dark:text-purple-400">{{ store.analyticsData.avgTransit }} days</div>
            </div>
        </div>
        <div class="flex-1 overflow-auto">
            <table class="w-full text-left text-sm min-w-[640px]">
                <thead class="text-gray-500 dark:text-gray-400 uppercase text-[10px] border-b border-gray-100 dark:border-white/5 sticky top-0 bg-white dark:bg-card-dark z-10">
                    <tr>
                        <th class="px-5 py-3 font-semibold">Order ID</th>
                        <th class="px-5 py-3 font-semibold">Route</th>
                        <th class="px-5 py-3 font-semibold">Amount</th>
                        <th class="px-5 py-3 font-semibold">ETA</th>
                        <th class="px-5 py-3 font-semibold">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-white/5">
                    <tr v-for="s in filteredShipments" :key="'tbl-'+s.id"
                        @click="selected = s; detailTab = 'overview'"
                        class="hover:bg-blue-50/50 dark:hover:bg-white/5 cursor-pointer transition-colors group">
                        <td class="px-5 py-3 font-mono text-blue-500 text-xs font-bold group-hover:text-blue-600">{{ s.id }}</td>
                        <td class="px-5 py-3">
                            <div class="text-xs font-semibold text-gray-900 dark:text-white">{{ s.origin }}</div>
                            <div class="text-[10px] text-gray-400 flex items-center gap-0.5 mt-0.5">
                                <span class="material-symbols-outlined text-[10px]">arrow_forward</span> {{ s.destination }}
                            </div>
                        </td>
                        <td class="px-5 py-3 font-bold text-green-600 dark:text-green-400 text-xs">₹{{ s.amount.toLocaleString() }}</td>
                        <td class="px-5 py-3 text-gray-600 dark:text-gray-300 text-xs">{{ s.eta }}</td>
                        <td class="px-5 py-3">
                            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold" :class="statusClass(s.statusKey)">{{ s.status }}</span>
                        </td>
                    </tr>
                    <tr v-if="filteredShipments.length === 0">
                        <td colspan="5" class="px-5 py-12 text-center text-gray-400 text-sm">No shipments match</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    detailTab,
    filteredShipments,
    globalTab,
    selected,
    statusClass,
    store,
} = inject(vendorTrackingPageKey)
</script>
