<template>
    <div class="space-y-6">
        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center h-64">
            <div class="text-gray-500 dark:text-gray-400">Loading dashboard data...</div>
        </div>

        <div v-else>
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

        <!-- Charts Row -->
        <div class="glass-panel p-5 rounded-xl h-[300px] md:h-[400px] flex flex-col">
            <div class="flex justify-between items-center mb-2">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-teal-500">trending_up</span>
                    Daily Throughput (Picks per Hour)
                </h3>
            </div>
            <div class="flex-1 relative w-full h-full">
                <Line v-if="throughputChartData" :key="throughputChartKey" :data="throughputChartData" :options="lineChartOptions" />
                <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
            </div>
        </div>

        <!-- Secondary Charts Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">

            <!-- 1. Orders VS Returns (Bar) -->
            <div class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                    <span class="material-symbols-outlined text-blue-400">compare_arrows</span>
                    Orders vs Returns
                </h3>
                <div class="relative flex-1 w-full min-h-0">
                    <Bar v-if="ordersReturnsData" :data="ordersReturnsData" :options="barOptions" class="absolute inset-0 pb-2" />
                    <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
                </div>
            </div>

            <!-- 2. Stock vs Packaging (Pie) -->
            <div class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                    <span class="material-symbols-outlined text-purple-400">inventory</span>
                    Inventory Composition
                </h3>
                <div class="relative flex-1 w-full min-h-0">
                    <Pie v-if="stockPackagingData" :data="stockPackagingData" :options="pieOptions" class="absolute inset-0 pb-2" />
                    <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
                </div>
            </div>

            <!-- 3. Active Workers vs Drivers (Doughnut) -->
            <div
                class="glass-panel p-5 rounded-xl flex flex-col transition-transform hover:scale-[1.01] h-64 md:h-80 sm:col-span-2 md:col-span-1">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2 shrink-0">
                    <span class="material-symbols-outlined text-yellow-400">group</span>
                    On-Site Labor
                </h3>
                <div class="relative flex-1 w-full min-h-0">
                    <Doughnut v-if="activeStaffData" :data="activeStaffData" :options="doughnutOptions" class="absolute inset-0 pb-2" />
                    <div v-else class="flex items-center justify-center h-full text-gray-500">No data available</div>
                </div>
            </div>
        </div>

        <!-- Main Content Split -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Center: Interactive Picking Queue Table -->
            <div class="lg:col-span-2 glass-panel rounded-xl flex flex-col overflow-hidden">
                <div
                    class="p-4 border-b border-gray-100 dark:border-white/5 flex flex-wrap gap-4 justify-between items-center bg-gray-100 dark:bg-black/20">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-teal-500">list_alt</span>
                        Live Picking Queue
                    </h3>

                    <!-- Dynamic Search & Filters -->
                    <div class="flex gap-2 sm:gap-3 flex-1 justify-end flex-wrap">
                        <div class="relative w-36 sm:w-48">
                            <span
                                class="material-symbols-outlined absolute left-2 top-1.5 text-gray-500 text-[18px]">search</span>
                            <input v-model="searchQuery" type="text" placeholder="Search ID or Staff..."
                                class="w-full bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg pl-8 pr-3 py-1 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-teal-500/50 transition-colors">
                        </div>
                        <select v-model="statusFilter"
                            class="bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1 text-sm text-gray-600 dark:text-gray-300 focus:outline-none focus:border-teal-500/50 transition-colors">
                            <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Statuses</option>
                            <option value="Pending" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pending</option>
                            <option value="In Progress" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Progress</option>
                            <option value="Unassigned" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Unassigned</option>
                            <option value="Review" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Review</option>
                        </select>
                    </div>
                </div>

                <div class="flex-1 overflow-auto">
                    <table class="w-full text-left border-collapse min-w-[600px]">
                        <thead class="bg-gray-50 dark:bg-white/5 sticky top-0 z-10 backdrop-blur-md">
                            <tr class="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                                <th class="p-3 font-medium">Order ID</th>
                                <th class="p-3 font-medium">Items</th>
                                <th class="p-3 font-medium">Zone</th>
                                <th class="p-3 font-medium">Priority</th>
                                <th class="p-3 font-medium">Assigned To</th>
                                <th class="p-3 font-medium">Status / Progress</th>
                                <th class="p-3 font-medium text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody class="text-sm divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="order in filteredQueue" :key="order.id"
                                class="hover:bg-gray-50 dark:bg-white/5 transition-colors group">
                                <td class="p-3 font-mono text-teal-400">{{ order.id }}</td>
                                <td class="p-3 text-gray-600 dark:text-gray-300">{{ order.items }} items</td>
                                <td class="p-3 text-gray-600 dark:text-gray-300">
                                    <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700/50 rounded text-xs">{{ order.zone }}</span>
                                </td>
                                <td class="p-3">
                                    <span v-if="order.priority === 'High'"
                                        class="text-red-600 dark:text-red-400 text-xs font-bold bg-red-500/10 px-2 py-0.5 rounded flex items-center gap-1 w-fit">
                                        <span class="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></span> HIGH
                                    </span>
                                    <span v-else class="text-gray-600 dark:text-gray-400 text-xs">Normal</span>
                                </td>
                                <td class="p-3">
                                    <div class="flex items-center gap-2" v-if="order.assigned">
                                        <div
                                            class="w-6 h-6 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-[10px] shadow-sm">
                                            {{ order.assignedInitials }}</div>
                                        <span class="text-gray-600 dark:text-gray-300">{{ order.assigned }}</span>
                                    </div>
                                    <span v-else class="text-gray-500 italic">-- Unassigned --</span>
                                </td>
                                <td class="p-3">
                                    <div class="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                                        <div class="bg-teal-500 h-full transition-all duration-500"
                                            :class="{ 'bg-blue-400': order.status === 'Review' }"
                                            :style="`width: ${order.progress}%`"></div>
                                    </div>
                                    <div class="text-[10px] text-gray-600 dark:text-gray-400 mt-1 font-medium">
                                        <span v-if="order.status === 'Review'" class="text-blue-400">Reviewing</span>
                                        <span v-else-if="order.status === 'Unassigned'"
                                            class="text-gray-500">Waiting</span>
                                        <span v-else>{{ order.progress }}% Picked</span>
                                    </div>
                                </td>
                                <!-- Dynamic Context Menu -->
                                <td class="p-3 relative text-center">
                                    <button @click.stop="toggleActionMenu(order.id)"
                                        class="text-gray-500 hover:text-gray-900 dark:text-white p-1 rounded hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">
                                        <span class="material-symbols-outlined">more_horiz</span>
                                    </button>
                                    <div v-if="activeActionMenu === order.id"
                                        class="absolute right-8 mt-1 w-36 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl py-1 z-20 text-left">
                                        <button @click="markComplete(order)"
                                            class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-green-600 dark:text-green-400 flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[14px]">check_circle</span> Mark
                                            Complete
                                        </button>
                                        <button @click="reassign(order)"
                                            class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-blue-600 dark:text-blue-400 flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[14px]">person_add</span>
                                            Reassign
                                        </button>
                                        <button @click="toggleActionMenu(order.id)"
                                            class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[14px]">close</span> Close
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="filteredQueue.length === 0">
                                <td colspan="7" class="p-8 text-center text-gray-500">
                                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">search_off</span>
                                    <p>No matching orders found.</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Right: Labor Status & Floor Map -->
            <div class="flex flex-col gap-6">
                <!-- Labor Distribution Chart -->
                <div class="glass-panel p-5 rounded-xl flex-1 flex flex-col">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-2">Real-time Labor Status</h3>

                    <div class="flex-1 relative w-full flex justify-center items-center min-h-[160px]">
                        <Doughnut v-if="laborChartData" :data="laborChartData" :options="doughnutOptions" />
                        <div v-else class="flex items-center justify-center text-gray-500">No data available</div>
                    </div>

                    <div
                        class="mt-4 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">Efficiency Insight</div>
                        <div class="text-sm text-gray-900 dark:text-white">{{ efficiencyInsight }}</div>
                    </div>
                </div>

                <!-- Return Processing Queue (Small) -->
                <div class="glass-panel p-4 rounded-xl space-y-2 bg-gray-100 dark:bg-gray-800/20">
                    <div class="flex justify-between items-center mb-1">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">Recent Returns</h3>
                        <span class="text-xs text-gray-500">Today</span>
                    </div>
                    <div v-if="recentReturns.length === 0" class="text-xs text-gray-500 text-center py-4">
                        No recent returns
                    </div>
                    <div v-for="returnItem in recentReturns.slice(0, 3)" :key="returnItem.id"
                        class="flex items-center justify-between p-2 rounded bg-gray-100 dark:bg-black/20 text-xs text-gray-600 dark:text-gray-300">
                        <span>{{ returnItem.description }}</span>
                        <span class="font-medium" :class="returnItem.action === 'Scrap' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                            {{ returnItem.action }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        </div>

        <!-- DYNAMIC RESTOCK MODAL -->
        <Teleport to="body">
            <div v-if="showRestockModal"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
                <div
                    class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl transform transition-all">
                    <!-- Header -->
                    <div
                        class="p-5 border-b border-gray-200 dark:border-white/10 flex justify-between items-center bg-gradient-to-r from-red-500/20 to-transparent">
                        <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 text-lg">
                            <span class="material-symbols-outlined text-red-600 dark:text-red-400">warning</span>
                            Critical Restock Required
                        </h3>
                        <button @click="showRestockModal = false"
                            class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <!-- Body -->
                    <div class="p-5 max-h-[60vh] overflow-y-auto no-scrollbar">
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">The following SKUs have fallen below
                            their safety stock
                            thresholds and require immediate attention.</p>
                        <div class="space-y-3">
                            <div v-for="sku in criticalSkus" :key="sku.id"
                                class="flex justify-between items-center p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ sku.name }}</div>
                                    <div class="text-[10px] text-gray-600 dark:text-gray-400 font-mono mt-0.5">{{ sku.id
                                        }}</div>
                                </div>
                                <div class="text-right">
                                    <div class="text-sm text-red-600 dark:text-red-400 font-bold flex items-center gap-1 justify-end">
                                        {{ sku.current }} left
                                        <span class="material-symbols-outlined text-[14px]">arrow_downward</span>
                                    </div>
                                    <div class="text-[10px] text-gray-500">Min Threshold: {{ sku.min }}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div
                        class="p-4 border-t border-gray-200 dark:border-white/10 flex gap-3 bg-gray-100 dark:bg-black/20">
                        <button @click="showRestockModal = false"
                            class="flex-1 py-2.5 text-sm font-bold text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 rounded-lg transition-colors">
                            Review Later
                        </button>
                        <button @click="processRestock"
                            class="flex flex-1 py-2.5 items-center justify-center gap-2 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors shadow-lg shadow-red-500/20">
                            <span class="material-symbols-outlined text-[18px]"
                                v-if="!isProcessingRestock">shopping_cart_checkout</span>
                            <span class="material-symbols-outlined text-[18px] animate-spin" v-else>sync</span>
                            {{ isProcessingRestock ? 'Processing...' : 'Authorize Restock All' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce"
            :class="toastType === 'error' ? 'bg-red-500/90 shadow-red-500/30' : 'bg-green-500/90 shadow-green-500/30'">
            <span class="material-symbols-outlined">{{ toastType === 'error' ? 'error' : 'check_circle' }}</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Line, Doughnut, Bar, Pie } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement, Filler } from 'chart.js'
import { useAuthStore } from '@/stores/authStore'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement, Filler)

const authStore = useAuthStore()
const toastMsg = ref('')
const toastType = ref('success')
const isLoading = ref(true)

// Dynamic data from API
const dashboardData = ref(null)
const readyForDispatch = ref(0)
const activeLabor = ref(0)
const totalLabor = ref(0)
const totalInventoryValue = ref(0)
const inventoryValueChangePercent = ref(0)
const pendingOrdersCount = ref(0)
const avgPickTime = ref(0)
const nextTruckMinutes = ref(0)
const criticalSkus = ref([])
const pickingQueue = ref([])
const recentReturns = ref([])
const efficiencyInsight = ref('')

// Chart data refs
const throughputChartData = ref(null)
const throughputChartKey = ref(0)
const ordersReturnsData = ref(null)
const stockPackagingData = ref(null)
const activeStaffData = ref(null)
const laborChartData = ref(null)

function showToast(msg, type = 'success') {
    toastMsg.value = msg
    toastType.value = type
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

function applyDashboardPayload(data) {
    dashboardData.value = data
    totalInventoryValue.value = data.total_inventory_value ?? 0
    inventoryValueChangePercent.value = data.inventory_value_change_percent ?? 0
    pendingOrdersCount.value = data.pending_orders_count ?? 0
    avgPickTime.value = data.avg_pick_time_minutes ?? 0
    readyForDispatch.value = data.ready_for_dispatch ?? 0
    nextTruckMinutes.value = data.next_truck_minutes ?? 0
    activeLabor.value = data.active_labor ?? 0
    totalLabor.value = data.total_labor ?? 0
    criticalSkus.value = data.critical_skus || []
    pickingQueue.value = data.picking_queue || []
    recentReturns.value = data.recent_returns || []
    efficiencyInsight.value = data.efficiency_insight || 'No activity yet for this warehouse.'
    throughputChartData.value = data.throughput_chart || null
    throughputChartKey.value++
    ordersReturnsData.value = data.orders_returns_chart || null
    stockPackagingData.value = data.stock_packaging_chart || null
    activeStaffData.value = data.active_staff_chart || null
    laborChartData.value = data.labor_distribution_chart || null
}

async function fetchDashboardFallback(warehouseId) {
    const headers = {
        'Authorization': `Bearer ${authStore.authToken}`,
        'Content-Type': 'application/json'
    }

    const [kpisRes, inventoryRes, ordersRes, labourRes] = await Promise.allSettled([
        fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/kpis`, { headers }),
        fetch('http://localhost:8000/api/v1/inventory?page=1&page_size=100', { headers }),
        fetch('http://localhost:8000/api/v1/orders?page=1&page_size=100', { headers }),
        fetch('http://localhost:8000/api/v1/labourers?page=1&page_size=100', { headers })
    ])

    let kpis = null
    let inventoryItems = []
    let warehouseOrders = []
    let labourers = []

    if (kpisRes.status === 'fulfilled' && kpisRes.value.ok) {
        kpis = await kpisRes.value.json()
    }
    if (inventoryRes.status === 'fulfilled' && inventoryRes.value.ok) {
        const data = await inventoryRes.value.json()
        inventoryItems = data.items || []
    }
    if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
        const data = await ordersRes.value.json()
            // Backend already scopes orders to this warehouse for WAREHOUSE_MANAGER role
            warehouseOrders = data.items || []
    }
    if (labourRes.status === 'fulfilled' && labourRes.value.ok) {
        const data = await labourRes.value.json()
        labourers = data.items || []
    }

    const pendingStatuses = new Set(['DRAFT', 'CONFIRMED'])
    const readyStatuses = new Set(['ASSIGNED', 'IN_TRANSIT'])
    const pendingOrders = warehouseOrders.filter(order => pendingStatuses.has(order.status))
    const readyOrders = warehouseOrders.filter(order => readyStatuses.has(order.status))
    const totalInventory = inventoryItems.reduce((sum, item) => {
        const qty = item.quantity ?? item.quantity_on_hand ?? item.stock_quantity ?? item.quantity_available ?? 0
        return sum + qty
    }, 0)
    const lowStockItems = inventoryItems.filter(item => {
        const qty = item.quantity ?? item.quantity_on_hand ?? item.stock_quantity ?? item.quantity_available ?? 0
        const threshold = item.safety_stock ?? item.minimum_stock_level ?? item.reorder_point ?? 0
        return threshold > 0 && qty <= threshold
    })

    // Build real throughput chart from order timestamps (picks per hour)
    // Dynamically cover 06:00 up to current hour so the chart always extends to now
    const now = new Date()
    const currentHour = now.getHours()
    const startHour = 6
    const endHour = Math.max(currentHour, 13) // show at least up to 13:00
    const numHours = endHour - startHour + 1
    const hourLabels = Array.from({ length: numHours }, (_, i) => {
        const h = startHour + i
        return `${String(h).padStart(2, '0')}:00`
    })
    const hourCounts = Array(numHours).fill(0)
    const today = now.toDateString()
    warehouseOrders.forEach(order => {
        const d = new Date(order.created_at || order.updated_at)
        if (d.toDateString() === today) {
            const h = d.getHours()
            if (h >= startHour && h <= endHour) hourCounts[h - startHour]++
        }
    })
    // Use total orders spread across hours if no today data
    const hasAnyHourData = hourCounts.some(c => c > 0)
    const throughputData = hasAnyHourData ? hourCounts : (() => {
        // Distribute total across business hours with a bell curve pattern
        const total = warehouseOrders.length
        const weights = hourLabels.map((_, i) => {
            // bell curve centred at ~10:00
            const x = (i - numHours * 0.4) / (numHours * 0.25)
            return Math.exp(-0.5 * x * x)
        })
        const weightSum = weights.reduce((a, b) => a + b, 0)
        return weights.map(w => Math.round(total * (w / weightSum)))
    })()

    // Orders vs Returns chart
    const orderReturnLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    const dayOrderCounts = Array(7).fill(0)
    const dayReturnCounts = Array(7).fill(0)
    warehouseOrders.forEach(order => {
        const d = new Date(order.created_at || order.updated_at)
        const day = d.getDay()
        dayOrderCounts[day === 0 ? 6 : day - 1]++
    })

    // Stock composition by category
    const categoryMap = {}
    inventoryItems.forEach(item => {
        const cat = item.category || 'General'
        categoryMap[cat] = (categoryMap[cat] || 0) + (item.quantity_on_hand || 0)
    })
    const catLabels = Object.keys(categoryMap).slice(0, 5)
    const catValues = catLabels.map(l => categoryMap[l])

    // Active staff breakdown
    const activeCount = labourers.filter(l => l.is_active).length
    const inactiveCount = labourers.length - activeCount

    return {
        total_inventory_value: totalInventory * 100,
        inventory_value_change_percent: 0,
        pending_orders_count: pendingOrders.length || kpis?.order_count || 0,
        avg_pick_time_minutes: pendingOrders.length > 0 ? 10 : 0,
        ready_for_dispatch: readyOrders.length,
        next_truck_minutes: readyOrders.length > 0 ? 15 : 0,
        active_labor: labourers.filter(item => item.is_active).length,
        total_labor: labourers.length || kpis?.labour_count || 0,
        critical_skus: lowStockItems.map(item => ({
            id: item.sku || item.id,
            name: item.name || 'Inventory Item',
            current: item.quantity ?? item.quantity_on_hand ?? item.stock_quantity ?? item.quantity_available ?? 0,
            min: item.safety_stock ?? item.minimum_stock_level ?? item.reorder_point ?? 0,
            sku: item.sku || item.id
        })),
        picking_queue: pendingOrders.map(order => ({
            id: order.tracking_code || order.id,
            order_id: order.id,
            items: order.items?.length || 0,
            zone: 'Unassigned',
            priority: order.order_type === 'EXPRESS' ? 'High' : 'Normal',
            assigned: null,
            assignedInitials: '',
            progress: 0,
            status: 'Pending',
            tracking_code: order.tracking_code || order.id
        })),
        recent_returns: [],
        throughput_chart: {
            labels: hourLabels,
            datasets: [{
                label: 'Picks / Hour',
                data: throughputData,
                borderColor: '#14b8a6',
                backgroundColor: 'rgba(20, 184, 166, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#14b8a6',
                pointRadius: 4,
            }]
        },
        orders_returns_chart: {
            labels: orderReturnLabels,
            datasets: [
                { label: 'Orders', data: dayOrderCounts, backgroundColor: 'rgba(59, 130, 246, 0.7)', borderRadius: 4 },
                { label: 'Returns', data: dayReturnCounts, backgroundColor: 'rgba(239, 68, 68, 0.7)', borderRadius: 4 },
            ]
        },
        stock_packaging_chart: catLabels.length > 0 ? {
            labels: catLabels,
            datasets: [{ data: catValues.map(v => catValues[0] > 0 ? Math.round(v / catValues.reduce((a, b) => a + b, 0) * 100) : 0), backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'] }]
        } : null,
        active_staff_chart: labourers.length > 0 ? {
            labels: ['Active', 'Inactive'],
            datasets: [{ data: [activeCount, inactiveCount], backgroundColor: ['#10b981', '#6b7280'] }]
        } : null,
        labor_distribution_chart: labourers.length > 0 ? {
            labels: ['Available', 'On Duty', 'Off Duty'],
            datasets: [{ data: [activeCount, Math.ceil(activeCount * 0.6), labourers.length - activeCount], backgroundColor: ['#10b981', '#3b82f6', '#6b7280'] }]
        } : null,
        efficiency_insight: warehouseOrders.length > 0
            ? `${warehouseOrders.filter(o => ['DELIVERED', 'CLOSED'].includes(o.status)).length} of ${warehouseOrders.length} orders completed. ${pendingOrders.length} orders pending pick.`
            : 'No orders assigned to this warehouse yet.'
    }
}

// Format currency in rupees
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value)
}

// Format large numbers (millions)
function formatLargeNumber(value) {
    if (value >= 10000000) {
        return `₹${(value / 10000000).toFixed(1)}Cr`
    } else if (value >= 100000) {
        return `₹${(value / 100000).toFixed(1)}L`
    }
    return formatCurrency(value)
}

// Fetch dashboard data from API
async function fetchDashboardData() {
    try {
        isLoading.value = true
        const warehouseId = authStore.currentUser?.warehouse_id

        if (!warehouseId) {
            console.error('No warehouse_id found for current user')
            return
        }

        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/dashboard`, {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (response.status === 404) {
            const fallbackData = await fetchDashboardFallback(warehouseId)
            applyDashboardPayload(fallbackData)
            return
        }

        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data')
        }

        const data = await response.json()
        applyDashboardPayload(data)

    } catch (error) {
        console.error('Error fetching dashboard data:', error)
        showToast('Error loading dashboard data', 'error')
    } finally {
        isLoading.value = false
    }
}

// Action: Mark order complete
async function markComplete(order) {
    try {
        const warehouseId = authStore.currentUser?.warehouse_id
        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/orders/${order.order_id}/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error('Failed to mark order complete')
        }

        // Refresh dashboard data
        await fetchDashboardData()
        showToast(`${order.id} marked complete — ready for dispatch`)
    } catch (error) {
        console.error('Error marking order complete:', error)
        showToast('Error marking order complete', 'error')
    }
    activeActionMenu.value = null
}

// Action: Reassign order
async function reassign(order) {
    try {
        const warehouseId = authStore.currentUser?.warehouse_id
        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/orders/${order.order_id}/reassign`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error('Failed to reassign order')
        }

        // Refresh dashboard data
        await fetchDashboardData()
        showToast(`${order.id} reassigned successfully`)
    } catch (error) {
        console.error('Error reassigning order:', error)
        showToast('Error reassigning order', 'error')
    }
    activeActionMenu.value = null
}

// Process restock for all critical SKUs
const isProcessingRestock = ref(false)
async function processRestock() {
    try {
        isProcessingRestock.value = true
        const warehouseId = authStore.currentUser?.warehouse_id

        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/restock`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error('Failed to process restock')
        }

        // Refresh dashboard data
        await fetchDashboardData()
        showRestockModal.value = false
        showToast('All critical SKUs restocked successfully!')
    } catch (error) {
        console.error('Error processing restock:', error)
        showToast('Error processing restock', 'error')
    } finally {
        isProcessingRestock.value = false
    }
}

// ----------------------------------------------------
// CHART CONFIGURATIONS
// ----------------------------------------------------

// 1. Throughput Line Chart
const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0,0,0,0.8)',
            titleColor: '#fff',
            bodyColor: '#4fd1c5', // teal-400
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
            ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        },
        x: {
            grid: { display: false, drawBorder: false },
            ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
}

// 2. Labor Doughnut Chart (Bottom Right Widget)
const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                color: '#d1d5db',
                usePointStyle: true,
                boxWidth: 8,
                font: { size: 11, family: 'Inter' },
                padding: 15
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            bodyColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            callbacks: {
                label: function (context) {
                    return ` ${context.label}: ${context.raw} Staff`;
                }
            }
        }
    }
}

// 3. Orders vs Returns (Bar Chart)
const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: { color: '#d1d5db', usePointStyle: true, font: { size: 10, family: 'Inter' } }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)', titleColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, cornerRadius: 8
        }
    },
    scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } }
    }
};

// 4. Stock vs Packaging (Pie Chart)
const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'right',
            labels: { color: '#d1d5db', usePointStyle: true, font: { size: 11, family: 'Inter' }, padding: 12 }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            bodyColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            callbacks: { label: (c) => ` ${c.label}: ${c.raw}%` }
        }
    }
};

// ----------------------------------------------------
// RESTOCK MODAL LOGIC
// ----------------------------------------------------
const showRestockModal = ref(false)

// ----------------------------------------------------
// INTERACTIVE PICKING QUEUE LOGIC
// ----------------------------------------------------
const searchQuery = ref('')
const statusFilter = ref('')
const activeActionMenu = ref(null)

const filteredQueue = computed(() => {
    return pickingQueue.value.filter(order => {
        // Search by Order ID or Assigned Worker Name
        const matchesSearch = !searchQuery.value ||
            order.id.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
            (order.assigned && order.assigned.toLowerCase().includes(searchQuery.value.toLowerCase()))

        // Filter by Dropdown Status
        const matchesStatus = !statusFilter.value || order.status === statusFilter.value

        // Remove globally completed ones from the active queue
        return matchesSearch && matchesStatus && order.status !== 'Completed'
    })
})

// --- Menu Actions ---
const toggleActionMenu = (id) => {
    activeActionMenu.value = activeActionMenu.value === id ? null : id
}

// Click-outside directive logic to close menus gracefully
const closeMenu = (e) => {
    if (!e.target.closest('.relative')) {
        activeActionMenu.value = null
    }
}

let pollInterval = null

onMounted(() => {
    fetchDashboardData()
    document.addEventListener('click', closeMenu)
    // Refresh dashboard data (including throughput chart) every 30 seconds
    pollInterval = setInterval(fetchDashboardData, 30000)
})

onUnmounted(() => {
    document.removeEventListener('click', closeMenu)
    if (pollInterval) clearInterval(pollInterval)
})
</script>
