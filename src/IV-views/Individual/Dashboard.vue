<template>
    <!-- Loading State -->
    <div v-if="store.dashboardLoading" class="space-y-6 sm:space-y-8 animate-pulse">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
            <div v-for="i in 3" :key="i" class="glass-panel p-4 md:p-6 rounded-xl h-32 bg-gray-200 dark:bg-gray-800"></div>
        </div>
        <div class="glass-panel p-5 md:p-6 rounded-xl h-64 bg-gray-200 dark:bg-gray-800"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="store.dashboardError" class="glass-panel p-8 rounded-xl text-center">
        <span class="material-symbols-outlined text-6xl text-red-500 mb-4">error</span>
        <h3 class="font-bold text-xl text-gray-900 dark:text-white mb-2">Unable to Load Dashboard</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">{{ store.dashboardError }}</p>

        <!-- Show login prompt if authentication error -->
        <div v-if="store.dashboardError.includes('credentials') || store.dashboardError.includes('Unauthorized')" class="space-y-3">
            <p class="text-sm text-amber-600 dark:text-amber-400">You need to login to access the dashboard.</p>
            <div class="flex gap-3 justify-center">
                <router-link to="/login"
                    class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold transition-colors">
                    Go to Login
                </router-link>
                <button @click="refreshDashboard"
                    class="px-6 py-2 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 rounded-lg font-bold transition-colors">
                    Try Again
                </button>
            </div>
        </div>

        <!-- Generic error -->
        <button v-else @click="refreshDashboard"
            class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold transition-colors">
            Try Again
        </button>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-6 sm:space-y-8">
        <!-- Stats Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Active Orders</div>
                    <span class="material-symbols-outlined text-blue-400 text-[20px]">local_shipping</span>
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ stats.active_orders || 0 }}</div>
                <div class="text-amber-500 text-xs mt-1">{{ stats.pending_orders || 0 }} pending</div>
            </div>
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Total Spent</div>
                    <span class="material-symbols-outlined text-purple-400 text-[20px]">payments</span>
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">₹{{ (stats.total_spent || 0).toLocaleString() }}</div>
                <div class="text-gray-500 text-xs mt-1">All-time</div>
            </div>
            <router-link to="/individual/wallet" class="glass-panel p-5 rounded-xl hover:border-green-500/30 transition-all cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Wallet Balance</div>
                    <span class="material-symbols-outlined text-green-400 text-[20px]">account_balance_wallet</span>
                </div>
                <div class="text-3xl font-bold text-green-500">₹{{ walletBalance.toLocaleString() }}</div>
                <div class="text-gray-500 text-xs mt-1">Available credit</div>
            </router-link>
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Completed</div>
                    <span class="material-symbols-outlined text-green-400 text-[20px]">verified</span>
                </div>
                <div class="text-3xl font-bold text-green-500">{{ stats.delivered_orders || 0 }}</div>
                <div class="text-green-500 text-xs mt-1">Successful moves</div>
            </div>
        </div>

        <!-- Active Moves Status -->
        <div v-if="activeMoves.length" class="space-y-6">
            <div v-for="move in activeMoves" :key="move.id" class="grid grid-cols-1 xl:grid-cols-3 gap-6 items-stretch">
            <div class="xl:col-span-2 glass-panel p-5 md:p-6 rounded-xl flex flex-col h-full">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg mb-4 flex items-center gap-2 shrink-0">
                    <span class="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span> Active Move Status
                </h3>
                <div class="flex flex-col md:flex-row gap-6 flex-1">
                    <div class="flex-none w-full md:w-64 rounded-xl h-48 md:h-auto relative shadow-inner overflow-hidden" style="min-height:192px">
                        <!-- Live Leaflet map when driver GPS is available -->
                        <template v-if="(move.uiStatus === 'in-transit' || move.uiStatus === 'dispatched') && trackingDriver?.latitude">
                            <l-map :zoom="14" :center="[trackingDriver.latitude, trackingDriver.longitude]" :use-global-leaflet="false" class="w-full h-full" style="z-index:0">
                                <l-tile-layer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" layer-type="base" name="CartoDB Voyager"></l-tile-layer>
                                <l-marker :lat-lng="[trackingDriver.latitude, trackingDriver.longitude]">
                                    <l-popup>
                                        <div class="text-xs p-1">
                                            <div class="font-bold flex items-center gap-1 mb-1">
                                                <span class="material-symbols-outlined text-[14px] text-green-500">local_shipping</span>
                                                {{ trackingDriver.driver_name || move.driverName }}
                                            </div>
                                            <div class="text-gray-500 uppercase text-[9px] font-bold bg-gray-100 rounded px-1.5 py-0.5 inline-block">{{ trackingDriver.status || 'In Transit' }}</div>
                                        </div>
                                    </l-popup>
                                </l-marker>
                            </l-map>
                        </template>
                        <!-- Map centered on pickup while awaiting driver GPS -->
                        <template v-else-if="(move.uiStatus === 'in-transit' || move.uiStatus === 'dispatched') && geocodedOrigin">
                            <l-map :zoom="13" :center="[geocodedOrigin.lat, geocodedOrigin.lng]" :use-global-leaflet="false" class="w-full h-full" style="z-index:0">
                                <l-tile-layer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" layer-type="base" name="CartoDB Voyager"></l-tile-layer>
                                <l-marker :lat-lng="[geocodedOrigin.lat, geocodedOrigin.lng]">
                                    <l-popup><div class="text-xs p-1 font-bold">Pickup<br/><span class="font-normal text-gray-500">{{ move.pickup }}</span></div></l-popup>
                                </l-marker>
                                <l-marker v-if="geocodedDestination" :lat-lng="[geocodedDestination.lat, geocodedDestination.lng]">
                                    <l-popup><div class="text-xs p-1 font-bold">Destination<br/><span class="font-normal text-gray-500">{{ move.destination }}</span></div></l-popup>
                                </l-marker>
                            </l-map>
                            <!-- Locating driver badge overlay -->
                            <div class="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 bg-white/90 dark:bg-black/80 backdrop-blur-sm rounded-lg z-10">
                                <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                                <span class="text-[10px] font-bold text-gray-600 dark:text-gray-300">Locating driver...</span>
                            </div>
                        </template>
                        <!-- Fallback: no GPS and geocoding still loading -->
                        <div v-else-if="move.uiStatus === 'in-transit' || move.uiStatus === 'dispatched'" class="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 flex flex-col items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-4xl text-green-500 animate-pulse">my_location</span>
                            <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">Locating driver...</div>
                        </div>
                        <!-- Static placeholder for pending/other statuses -->
                        <div v-else class="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-800 dark:to-gray-900 flex items-center justify-center">
                            <span class="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-600">map</span>
                        </div>
                        <!-- ETA and Track Live overlays (always visible) -->
                        <div class="absolute bottom-2 left-2 px-3 py-1 bg-white/90 dark:bg-black/80 backdrop-blur-sm text-xs font-bold rounded-lg text-green-600 dark:text-green-400 z-10">
                            ETA: {{ move.eta }}</div>
                        <router-link :to="'/individual/tracking?orderId=' + move.id" class="absolute bottom-2 right-2 px-3 py-1 bg-green-600 text-white text-xs font-bold rounded-lg hover:bg-green-700 transition-colors z-10">Track Live</router-link>
                    </div>
                    <div class="flex-1 space-y-4">
                        <div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold mb-1">Current
                                Status</div>
                            <div class="text-xl font-bold" :class="move.uiStatus === 'in-transit' ? 'text-green-600 dark:text-green-400' : move.uiStatus === 'dispatched' ? 'text-blue-600 dark:text-blue-400' : 'text-green-600 dark:text-green-400'">{{ move.statusLabel }}</div>
                            <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden mt-2">
                                <div class="bg-green-500 h-full rounded-full transition-all"
                                    :style="{ width: move.progress + '%' }"></div>
                            </div>
                        </div>
                        <div
                            class="flex items-center gap-4 bg-gray-50 dark:bg-white/5 p-3 rounded-xl border border-gray-100 dark:border-white/5">
                            <div
                                class="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white font-bold text-sm shadow-lg">
                                {{ move.driverInitials }}</div>
                            <div>
                                <div class="font-bold text-gray-900 dark:text-white text-sm">{{ move.driverName
                                }}</div>
                                <div class="text-xs text-gray-500">Driver {{ move.driverRating ? `(${move.driverRating} ★)` : '' }} · {{
                                    move.vehicleType?.toUpperCase() }}</div>
                            </div>
                            <a :href="'tel:' + move.driverPhone"
                                class="ml-auto px-4 py-2 rounded-lg bg-green-50 dark:bg-green-500/10 hover:bg-green-100 dark:hover:bg-green-500/20 text-green-700 dark:text-green-400 font-bold text-sm flex items-center gap-2 transition-colors border border-green-200 dark:border-green-500/20">
                                <span class="material-symbols-outlined text-sm">call</span>
                                {{ move.driverPhone }}
                            </a>
                        </div>

                        <!-- OTP Section — only for Small Package / Parcel deliveries -->
                        <div v-if="!move.isHouseShift && move.serviceOtp"
                            class="flex items-center justify-between bg-blue-50/50 dark:bg-blue-500/5 p-3 border border-blue-100 dark:border-blue-500/10 rounded-xl">
                            <div class="flex items-center gap-3">
                                <span class="material-symbols-outlined text-blue-500">dialpad</span>
                                <div class="text-sm">
                                    <div class="text-gray-900 dark:text-blue-100 font-bold">Delivery OTP</div>
                                    <div class="text-[10px] text-gray-500 dark:text-blue-300/70 uppercase">Share with
                                        the driver on delivery</div>
                                </div>
                            </div>
                            <div
                                class="font-mono text-2xl font-black text-blue-600 dark:text-blue-400 tracking-[0.25em] bg-white dark:bg-black/20 px-4 py-1.5 rounded-lg shadow-inner">
                                {{ move.serviceOtp }}
                            </div>
                        </div>

                        <!-- House Shift — sign-off reminder instead of OTP -->
                        <div v-else-if="move.isHouseShift"
                            class="flex items-center gap-3 bg-purple-50/50 dark:bg-purple-500/5 p-3 border border-purple-100 dark:border-purple-500/15 rounded-xl">
                            <span class="material-symbols-outlined text-purple-500">draw</span>
                            <div class="text-sm">
                                <div class="text-gray-900 dark:text-purple-100 font-bold">Sign-off at Destination</div>
                                <div class="text-[10px] text-gray-500 dark:text-purple-300/70 uppercase">Driver will ask
                                    for your signature once unloading is complete</div>
                            </div>
                        </div>

                        <div
                            class="grid grid-cols-3 gap-3 text-xs bg-gray-50 dark:bg-black/20 p-3 rounded-xl border border-gray-100 dark:border-white/5 mt-auto">
                            <div><span class="text-gray-500 block mb-0.5">Assigned Labor</span> <span
                                    class="text-gray-900 dark:text-white font-bold">{{ move.laborCount }}
                                    Helpers</span></div>
                            <div><span class="text-gray-500 block mb-0.5">Order ID</span> <span
                                    class="font-mono font-bold text-green-600 dark:text-green-400">{{ move.id
                                    }}</span></div>
                            <div><span class="text-gray-500 block mb-0.5">Service Block</span> <span
                                    class="text-purple-600 dark:text-purple-400 font-bold">{{
                                        move.serviceTimeBlock }}</span></div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Cost Summary -->
            <div class="glass-panel p-5 md:p-6 rounded-xl flex flex-col h-full">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg mb-4">Cost Summary</h3>
                <div class="space-y-3 text-sm flex-1">
                    <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Base
                            Transport</span><span class="font-bold text-gray-900 dark:text-white font-mono">₹{{
                                move.cost.base.toLocaleString() }}</span></div>
                    <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Vehicle</span><span
                            class="font-bold text-gray-900 dark:text-white font-mono">₹{{ (move.cost.vehicle ||
                                0).toLocaleString() }}</span></div>
                    <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Labor (×{{
                        move.laborCount }})</span><span
                            class="font-bold text-gray-900 dark:text-white font-mono">₹{{
                                move.cost.labor.toLocaleString() }}</span></div>
                    <div class="flex justify-between"><span
                            class="text-gray-500 dark:text-gray-400">Materials</span><span
                            class="font-bold text-gray-900 dark:text-white font-mono">₹{{
                                move.cost.materials.toLocaleString() }}</span></div>
                    <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Packing</span><span
                            class="font-bold text-gray-900 dark:text-white font-mono">₹{{
                                move.cost.packing.toLocaleString() }}</span></div>

                    <div class="border-t border-gray-100 dark:border-white/5 pt-2 mt-2"></div>

                    <div class="flex justify-between"><span
                            class="text-gray-500 dark:text-gray-400 flex items-center gap-1"><span
                                class="material-symbols-outlined text-[14px]">confirmation_number</span> Platform
                            Fee</span><span
                            class="font-bold text-gray-900 dark:text-white font-mono flex items-center gap-1"><span
                                class="text-[10px] text-gray-400 line-through mr-1"
                                v-if="move.cost.platformFee > 300">₹499</span>₹{{
                                    (move.cost.platformFee || 0).toLocaleString() }}</span></div>
                    <div class="flex justify-between"><span
                            class="text-gray-500 dark:text-gray-400 flex items-center gap-1"><span
                                class="material-symbols-outlined text-[14px]">account_balance</span> Taxes (18%
                            GST)</span><span class="font-bold text-gray-900 dark:text-white font-mono">₹{{
                                (move.cost.taxes || 0).toLocaleString() }}</span></div>

                    <div
                        class="border-t border-gray-200 dark:border-white/10 pt-3 mt-3 flex justify-between items-center">
                        <span class="font-bold text-gray-900 dark:text-white">Total</span><span
                            class="text-2xl font-bold text-green-600 dark:text-green-400 font-mono">₹{{
                                move.cost.total.toLocaleString() }}</span></div>
                </div>
                <router-link to="/individual/payments"
                    class="block w-full py-2 mt-3 text-center border border-gray-200 dark:border-white/10 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors">View
                    Payments</router-link>
            </div>
        </div>
        </div>

        <!-- Charts -->
        <div v-if="stats.total_orders > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="glass-panel p-5 md:p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Monthly Spending</h3>
                <div class="h-56">
                    <Bar :data="barChartData" :options="chartOptions" />
                </div>
            </div>
            <div class="glass-panel p-5 md:p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Move Status Distribution</h3>
                <div class="h-56 flex items-center justify-center">
                    <Doughnut :data="doughnutData" :options="doughnutOptions" />
                </div>
            </div>
        </div>

        <!-- Recent Orders -->
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

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ stats.total_orders || 0 }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Moves</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ stats.active_orders || 0 }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Active</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ stats.pending_orders || 0 }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Pending</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">₹{{
                    Number(stats.total_spent || 0).toLocaleString() }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Spent</div>
            </div>
        </div>

        <!-- Empty State (No Orders) -->
        <div v-if="stats.total_orders === 0" class="glass-panel p-8 md:p-12 rounded-xl text-center mt-8">
            <span class="material-symbols-outlined text-6xl text-gray-400 dark:text-gray-600 mb-4">local_shipping</span>
            <h3 class="font-bold text-xl text-gray-900 dark:text-white mb-2">No Moves Yet</h3>
            <p class="text-gray-500 dark:text-gray-400 mb-6">Start your first move by booking a service or getting a quote.</p>
            <div class="flex gap-4 justify-center flex-wrap">
                <router-link to="/individual/book-move"
                    class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold transition-colors">
                    Book a Move
                </router-link>
                <router-link to="/individual/quotes"
                    class="px-6 py-2 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 rounded-lg font-bold transition-colors">
                    Get Quote
                </router-link>
            </div>
        </div>

        <!-- Refresh Indicator -->
        <div class="text-center text-xs text-gray-400 dark:text-gray-600">
            <button @click="refreshDashboard" class="hover:text-green-500 transition-colors flex items-center gap-1 mx-auto">
                <span class="material-symbols-outlined text-sm">refresh</span>
                Last updated: {{ lastRefreshTime }}
            </button>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import apiClient from '@/config/api'
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const store = useIndividualStore()
const lastRefreshTime = ref('')
const walletBalance = computed(() => Number(store.walletBalance || 0))
let autoRefreshInterval = null

const apiDashboard = computed(() => store.dashboardSummary)
const selectedMoveIdx = ref(0)

// Cargo types from the "Small Package / Parcel" booking mode — these use OTP delivery
const SMALL_PKG_CARGO_TYPES = new Set(['document', 'fragile item', 'soft item', 'hard item'])

function isHouseShiftOrder(move) {
    const orderType = String(move.order_type || '').toUpperCase()
    const cargoType = String(move.cargo_type || '').toLowerCase().trim()
    if (orderType === 'SERVICE_MOVE') return true
    if (orderType === 'INDIVIDUAL') return !SMALL_PKG_CARGO_TYPES.has(cargoType)
    return false
}

function mapMove(move) {
    if (!move) return null
    const driverName = move.driver?.name || 'Crew assignment pending'
    const houseShift = isHouseShiftOrder(move)
    return {
        id: move.tracking_code,
        eta: move.eta_label,
        progress: move.progress,
        statusLabel: String(move.ui_status || move.status).replace('-', ' '),
        uiStatus: move.ui_status || move.status,
        vehicleType: move.vehicle_type,
        cargoType: move.cargo_type || 'Household Goods',
        isHouseShift: houseShift,
        pickup: move.pickup_addr || '',
        destination: move.delivery_addr || '',
        laborCount: move.labor_count,
        serviceTimeBlock: move.service_time_block,
        serviceOtp: houseShift ? null : move.service_otp,
        cost: {
            base: Number(move.cost?.base || 0),
            vehicle: Number(move.cost?.vehicle || 0),
            labor: Number(move.cost?.labor || 0),
            materials: Number(move.cost?.materials || 0),
            packing: Number(move.cost?.packing || 0),
            platformFee: Number(move.cost?.platform_fee || 0),
            taxes: Number(move.cost?.taxes || 0),
            total: Number(move.cost?.total || 0),
        },
        driverName,
        driverPhone: move.driver?.phone || 'Unavailable',
        driverRating: move.driver?.rating || null,
        driverInitials: driverName === 'Crew assignment pending'
            ? 'NA'
            : driverName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(),
    }
}

const activeMoves = computed(() => {
    const moves = apiDashboard.value?.active_moves || []
    if (moves.length) return moves.map(mapMove)
    const single = apiDashboard.value?.active_move
    return single ? [mapMove(single)] : []
})

const activeMove = computed(() => activeMoves.value[selectedMoveIdx.value] || activeMoves.value[0] || null)
const recentOrders = computed(() => apiDashboard.value?.recent_orders || [])

// Live vehicle tracking for in-transit/dispatched orders
const trackingDriver = ref(null)
let trackingInterval = null

async function fetchDriverLocation(orderId) {
    if (!orderId) return
    try {
        const response = await apiClient.get(`/tracking/orders/${orderId}/driver`)
        trackingDriver.value = response.data || null
    } catch {
        trackingDriver.value = null
    }
}

// Geocoded pickup/destination for map fallback when driver GPS is unavailable
const geocodedOrigin = ref(null)
const geocodedDestination = ref(null)

async function geocodeAddress(address) {
    if (!address) return null
    try {
        const encoded = encodeURIComponent(address)
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encoded}&format=json&limit=1`, {
            headers: { 'Accept-Language': 'en', 'User-Agent': 'CargoCore/1.0' }
        })
        const data = await res.json()
        if (data?.[0]) return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) }
    } catch { /* ignore */ }
    return null
}

watch(activeMoves, async (moves) => {
    const liveMove = moves.find(m => m.uiStatus === 'in-transit' || m.uiStatus === 'dispatched')
    if (liveMove) {
        fetchDriverLocation(liveMove.id)
        if (!trackingInterval) {
            trackingInterval = setInterval(() => fetchDriverLocation(liveMove.id), 10000)
        }
        // Geocode pickup and destination for the map fallback
        if (!geocodedOrigin.value && liveMove.pickup) {
            geocodedOrigin.value = await geocodeAddress(liveMove.pickup)
        }
        if (!geocodedDestination.value && liveMove.destination) {
            geocodedDestination.value = await geocodeAddress(liveMove.destination)
        }
    } else {
        clearInterval(trackingInterval)
        trackingInterval = null
        trackingDriver.value = null
        geocodedOrigin.value = null
        geocodedDestination.value = null
    }
}, { immediate: true })
const stats = computed(() => apiDashboard.value?.stats || {
    total_orders: 0,
    active_orders: 0,
    pending_orders: 0,
    delivered_orders: 0,
    cancelled_orders: 0,
    total_spent: 0,
})

async function refreshDashboard() {
    await store.fetchDashboardSummary()
    updateRefreshTime()
}

async function fetchWalletBalance() {
    await store.fetchWalletBalance()
}

function updateRefreshTime() {
    const now = new Date()
    lastRefreshTime.value = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
    await Promise.all([
        refreshDashboard(),
        fetchWalletBalance()
    ])

    // Auto-refresh every 30 seconds if there are active moves
    autoRefreshInterval = setInterval(() => {
        if (activeMoves.value.length) {
            store.fetchDashboardSummary()
            updateRefreshTime()
        }
    }, 30000)
})

onUnmounted(() => {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval)
    if (trackingInterval) clearInterval(trackingInterval)
})

function statusBadge(st) {
    return { 'delivered': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', 'in-transit': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'dispatched': 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400', 'pending': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', 'cancelled': 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400' }[st] || ''
}

const barChartData = computed(() => {
    const monthlyActivity = apiDashboard.value?.monthly_activity || []
    return {
        labels: monthlyActivity.length > 0 ? monthlyActivity.map((m) => m.month) : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Orders',
            data: monthlyActivity.length > 0 ? monthlyActivity.map((m) => m.count) : [0, 0, 0, 0, 0, 0],
            backgroundColor: ['#22c55e33', '#22c55e33', '#22c55e33', '#22c55e66', '#22c55e99', '#22c55e'],
            borderColor: '#22c55e',
            borderWidth: 1,
            borderRadius: 6,
        }],
    }
})

const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
        y: {
            ticks: {
                callback: (value) => String(value),
                color: '#9ca3af',
                font: { size: 10 }
            },
            grid: { color: '#e5e7eb22' }
        },
        x: { ticks: { color: '#9ca3af', font: { size: 10 } }, grid: { display: false } },
    },
}

const doughnutData = computed(() => {
    const delivered = stats.value.delivered_orders || 0
    const active = stats.value.active_orders || 0
    const pending = stats.value.pending_orders || 0
    const cancelled = stats.value.cancelled_orders || 0

    // If all are zero, show a placeholder
    const hasData = delivered + active + pending + cancelled > 0

    return {
        labels: ['Delivered', 'In Transit', 'Pending', 'Cancelled'],
        datasets: [{
            data: hasData ? [delivered, active, pending, cancelled] : [1, 0, 0, 0],
            backgroundColor: hasData ? ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444'] : ['#e5e7eb'],
            borderWidth: 0,
        }],
    }
})

const doughnutOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'right', labels: { color: '#9ca3af', font: { size: 11 }, boxWidth: 12, padding: 16 } } },
    cutout: '65%',
}
</script>
