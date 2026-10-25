<template>
    <!-- 6. RETURNS & REVERSE LOGISTICS -->
    <div v-if="activeTab === 'returns'" class="space-y-6 animate-fade-in">
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
            <div
                class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5 flex gap-4 items-center">
                <h3 class="font-bold text-gray-900 dark:text-white">RMA Returns Processing</h3>
                <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-bold">{{
                    store.filteredReturns.length }} Active</span>
            </div>
            <table class="w-full text-left text-xs">
                <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-4">RMA ID</th>
                        <th class="p-4">Customer</th>
                        <th class="p-4">Order Ref</th>
                        <th class="p-4">Reason</th>
                        <th class="p-4">Condition</th>
                        <th class="p-4 text-center">Images</th>
                        <th class="p-4">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="rma in store.filteredReturns" :key="rma.id"
                        class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-4 font-mono font-bold">{{ rma.id }}</td>
                        <td class="p-4">{{ rma.customer }}</td>
                        <td class="p-4 font-mono text-blue-600 font-bold cursor-pointer hover:underline">
                            {{ rma.orderId ? `#ORD-${rma.orderId.slice(-4).toUpperCase()}` : 'N/A' }}</td>
                        <td class="p-4">{{ rma.reason }}</td>
                        <td class="p-4 whitespace-nowrap">
                            <span class="px-2 py-1 rounded border"
                                :class="rma.condition === 'Damaged' ? 'bg-red-50 border-red-200 text-red-600' : 'bg-green-50 border-green-200 text-green-600'">{{
                                rma.condition }}</span>
                        </td>
                        <td class="p-4 text-center">
                            <button v-if="rma.images.length"
                                class="text-blue-500 hover:underline hover:text-blue-600">View {{
                                rma.images.length }}</button>
                            <span v-else class="text-gray-400">-</span>
                        </td>
                        <td class="p-4">
                            <span class="font-bold"
                                :class="{ 'Pending': 'text-yellow-500', 'Approved': 'text-green-500' }[rma.status]">{{
                                rma.status }}</span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- RMA vs Order Analytics -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">RMA Rate vs Total Orders</h3>
                <div class="h-74 relative">
                    <Line :data="rmaVsOrdersData" :options="chartOptions" />
                </div>
            </div>
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Reason for Return (Pareto)</h3>
                <div class="h-74 relative">
                    <Bar :data="rmaReasonsData" :options="chartOptions" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    chartOptions,
    rmaReasonsData,
    rmaVsOrdersData,
    store,
} = inject(reportsPageKey)
</script>
