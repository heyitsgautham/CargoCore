<template>
    <div class="glass-panel p-5 md:p-6 rounded-xl">
        <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900 dark:text-white text-lg">Recent Orders</h3>
            <router-link to="/individual/orders"
                class="text-sm text-green-600 dark:text-green-400 font-bold hover:underline">View All
                →</router-link>
        </div>

        <!-- Empty State for Recent Orders -->
        <div v-if="recentOrders.length === 0" class="text-center py-8">
            <span class="material-symbols-outlined text-4xl text-gray-400 dark:text-gray-600 mb-2">inbox</span>
            <p class="text-gray-500 dark:text-gray-400 text-sm">No orders yet. Book your first move to get started!</p>
        </div>

        <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr
                        class="text-xs text-gray-500 dark:text-gray-400 uppercase border-b border-gray-200 dark:border-white/5">
                        <th class="text-left py-3 pr-4">Order ID</th>
                        <th class="text-left py-3 pr-4">Type</th>
                        <th class="text-left py-3 pr-4 hidden sm:table-cell">Vehicle</th>
                        <th class="text-left py-3 pr-4 hidden sm:table-cell">Route</th>
                        <th class="text-left py-3 pr-4">Status</th>
                        <th class="text-right py-3">Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="order in recentOrders" :key="order.id"
                        class="border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                        <td class="py-3 pr-4"><span
                                class="font-mono font-bold text-green-600 dark:text-green-400">{{ order.tracking_code || order.id }}</span>
                        </td>
                        <td class="py-3 pr-4 text-gray-700 dark:text-gray-300">{{ order.cargoType || order.order_type }}</td>
                        <td
                            class="py-3 pr-4 text-gray-700 dark:text-gray-300 hidden sm:table-cell uppercase text-xs">
                            {{ order.vehicleType || order.vehicle_type }}</td>
                        <td
                            class="py-3 pr-4 text-gray-500 dark:text-gray-400 hidden sm:table-cell truncate max-w-[150px]">
                            {{ (order.pickup || order.pickup_addr)?.split(',')[0] }} → {{ (order.destination || order.delivery_addr)?.split(',')[0] }}</td>
                        <td class="py-3 pr-4"><span class="px-2 py-1 rounded-full text-[10px] font-bold uppercase"
                                :class="statusBadge(order.ui_status || order.status)">{{ (order.ui_status || order.status).replace('-', ' ') }}</span></td>
                        <td class="py-3 text-right font-bold text-gray-900 dark:text-white font-mono">₹{{
                            Number(order.cost?.total || order.total_amount || 0).toLocaleString() }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { individualDashboardPageKey } from './individualDashboardPageContext'

const { recentOrders, statusBadge } = inject(individualDashboardPageKey)
</script>
