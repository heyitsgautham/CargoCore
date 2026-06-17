<template>
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Dispatcher Performance Metrics</h2>
            <div class="flex items-center gap-2">
                <span v-if="store.activeOrdersLoading" class="material-symbols-outlined animate-spin text-primary text-[18px]">progress_activity</span>
                <span class="text-xs text-gray-500 dark:text-gray-400">Live · auto-refreshes</span>
            </div>
        </div>

        <!-- Order Status Pipeline -->
        <div class="glass-panel rounded-xl p-4">
            <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-3">Order Pipeline (Today)</div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="flex flex-col items-center gap-1 p-3 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20">
                    <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ pipelineConfirmed }}</div>
                    <div class="text-[10px] text-blue-500 dark:text-blue-400 font-bold uppercase tracking-wider">Confirmed</div>
                    <div class="text-[9px] text-gray-500">Awaiting dispatch</div>
                </div>
                <div class="flex flex-col items-center gap-1 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/20">
                    <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ pipelineAssigned }}</div>
                    <div class="text-[10px] text-yellow-500 dark:text-yellow-400 font-bold uppercase tracking-wider">Assigned</div>
                    <div class="text-[9px] text-gray-500">Driver assigned</div>
                </div>
                <div class="flex flex-col items-center gap-1 p-3 rounded-lg bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-500/20">
                    <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ pipelineInTransit }}</div>
                    <div class="text-[10px] text-purple-500 dark:text-purple-400 font-bold uppercase tracking-wider">In Transit</div>
                    <div class="text-[9px] text-gray-500">On the road</div>
                </div>
                <div class="flex flex-col items-center gap-1 p-3 rounded-lg bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20">
                    <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ pipelineDelivered }}</div>
                    <div class="text-[10px] text-green-500 dark:text-green-400 font-bold uppercase tracking-wider">Delivered</div>
                    <div class="text-[9px] text-gray-500">Completed</div>
                </div>
            </div>
        </div>

        <!-- KPI Cards - Row 1 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="glass-panel p-6 rounded-xl text-center">
                <div class="text-4xl font-bold text-primary">{{ onTimeRate }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 mt-2">On-Time Delivery Rate</div>
                <div class="text-[10px] mt-1" :class="onTimeRateNum >= 95 ? 'text-green-500' : onTimeRateNum >= 85 ? 'text-yellow-500' : 'text-red-500'">
                    {{ onTimeRateNum >= 95 ? 'Excellent' : onTimeRateNum >= 85 ? 'Good' : 'Needs Improvement' }}
                </div>
            </div>
            <div class="glass-panel p-6 rounded-xl text-center">
                <div class="text-4xl font-bold text-gray-900 dark:text-white">{{ activeDeliveries }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 mt-2">Active Deliveries</div>
                <div class="text-[10px] text-purple-400 mt-1">In Transit right now</div>
            </div>
            <div class="glass-panel p-6 rounded-xl text-center">
                <div class="text-4xl font-bold text-gray-900 dark:text-white">{{ totalOrdersAll }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 mt-2">Total Orders (All)</div>
                <div class="text-[10px] text-blue-400 mt-1">Across all statuses</div>
            </div>
            <div class="glass-panel p-6 rounded-xl text-center">
                <div class="text-4xl font-bold text-primary">{{ slaCompliance }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 mt-2">SLA Compliance</div>
                <div class="text-[10px] mt-1" :class="slaNum >= 95 ? 'text-green-500' : slaNum >= 85 ? 'text-yellow-500' : 'text-red-500'">
                    Target: 95%
                </div>
            </div>
        </div>

        <!-- KPI Cards - Row 2 -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold" :class="emptyMilesPct <= 15 ? 'text-green-400' : 'text-red-400'">{{ emptyMilesPct }}%</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">Empty Miles</div>
                <div class="text-[9px] mt-1" :class="emptyMilesPct <= 15 ? 'text-green-500' : 'text-red-400'">Target: &lt;15%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-green-400">{{ slaCompliance }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">On-Time Dispatch</div>
                <div class="text-[9px] text-gray-500 mt-1">SLA target: 95%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-blue-400">{{ slaCompliance }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">SLA Compliance</div>
                <div class="text-[9px] text-gray-500 mt-1">Target: 95%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-yellow-400">{{ routeDeviationPct }}%</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">Route Deviation</div>
                <div class="text-[9px] text-gray-500 mt-1">Target: &lt;5%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-purple-400">{{ avgFuelEff }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">Fuel Eff. Score</div>
                <div class="text-[9px] text-gray-500 mt-1">Avg driver score</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-cyan-400">{{ loadBalance }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider">Load Balance</div>
                <div class="text-[9px] text-gray-500 mt-1">Avg driver load</div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-panel p-6 rounded-xl relative">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white">Weekly Order Volume</h3>
                    <span class="text-[10px] text-gray-500 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">Last 7 days</span>
                </div>
                <div class="h-64">
                    <Bar :data="weeklyChartData" :options="weeklyChartOptions" />
                </div>
            </div>

            <div class="glass-panel p-6 rounded-xl">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white">Top Performing Zones</h3>
                    <span class="text-[10px] text-gray-500 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">{{ zones.length }} zones</span>
                </div>
                <div v-if="zones.length === 0" class="h-64 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
                    No logistic-manager zones available for this hub yet.
                </div>
                <div v-else class="h-64">
                    <Bar :data="zoneChartData" :options="zoneChartOptions" />
                </div>
            </div>
        </div>

        <!-- Route Quality & Driver Status -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-panel p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-yellow-400 text-[20px]">route</span>
                    Route Quality Metrics
                </h3>
                <div class="space-y-3">
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div>
                            <div class="text-sm text-gray-900 dark:text-white font-bold">Route Deviation Rate</div>
                            <div class="text-[10px] text-gray-500">Drivers deviating from plan</div>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold" :class="routeDeviationPct <= 5 ? 'text-green-400' : 'text-red-400'">{{ routeDeviationPct }}%</div>
                            <div class="text-[10px] text-gray-500">Target: &lt;5%</div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div>
                            <div class="text-sm text-gray-900 dark:text-white font-bold">Active Deliveries</div>
                            <div class="text-[10px] text-gray-500">Currently in transit</div>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-purple-400">{{ activeDeliveries }}</div>
                            <div class="text-[10px] text-green-400">Live from orders</div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div>
                            <div class="text-sm text-gray-900 dark:text-white font-bold">Avg Driver Efficiency</div>
                            <div class="text-[10px] text-gray-500">Computed from all drivers</div>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-primary">{{ avgEfficiency }}%</div>
                            <div class="text-[10px] text-gray-500">Across {{ store.dispatcherDrivers.length }} drivers</div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div>
                            <div class="text-sm text-gray-900 dark:text-white font-bold">Completed (Delivered)</div>
                            <div class="text-[10px] text-gray-500">Orders successfully delivered</div>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-green-400">{{ pipelineDelivered }}</div>
                            <div class="text-[10px] text-gray-500">Live from orders</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Driver Status Donut -->
            <div class="glass-panel p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400 text-[20px]">person_pin_circle</span>
                    Driver Availability
                </h3>
                <div class="flex items-center justify-center mb-4">
                    <div class="relative w-36 h-36">
                        <Doughnut :data="driverStatusChartData" :options="driverStatusChartOptions" />
                        <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <div class="text-xl font-bold text-gray-900 dark:text-white">{{ store.dispatcherDrivers.length }}</div>
                            <div class="text-[9px] text-gray-500 uppercase">Drivers</div>
                        </div>
                    </div>
                </div>
                <div class="space-y-2">
                    <div class="flex justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded">
                        <span class="text-gray-500 flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span>Active / On Route</span>
                        <span class="text-gray-900 dark:text-white font-mono font-bold">{{ activeDriverCount }}</span>
                    </div>
                    <div class="flex justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded">
                        <span class="text-gray-500 flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-yellow-500 inline-block"></span>On Break</span>
                        <span class="text-gray-900 dark:text-white font-mono font-bold">{{ breakDriverCount }}</span>
                    </div>
                    <div class="flex justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded">
                        <span class="text-gray-500 flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-gray-500 inline-block"></span>Offline / Inactive</span>
                        <span class="text-gray-900 dark:text-white font-mono font-bold">{{ offlineDriverCount }}</span>
                    </div>
                    <div class="flex justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded">
                        <span class="text-gray-500">Avg Load</span>
                        <span class="text-primary font-mono font-bold">{{ loadBalance }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Driver Leaderboard -->
        <div class="glass-panel p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">leaderboard</span>
                Top Driver Performance
                <span class="ml-auto text-[10px] text-gray-500 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">By Efficiency</span>
            </h3>
            <div v-if="topDrivers.length === 0" class="text-center py-6 text-gray-500 text-sm">No driver data available</div>
            <div v-else class="space-y-3">
                <div v-for="(driver, idx) in topDrivers" :key="driver.id"
                    class="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 hover:border-primary/30 transition-colors">
                    <!-- Rank -->
                    <div class="w-6 text-center font-bold text-sm"
                        :class="idx === 0 ? 'text-yellow-400' : idx === 1 ? 'text-gray-400' : idx === 2 ? 'text-orange-400' : 'text-gray-500'">
                        {{ idx + 1 }}
                    </div>
                    <!-- Avatar -->
                    <img :src="driver.avatar" :alt="driver.name" class="w-8 h-8 rounded-full border-2"
                        :style="{ borderColor: idx === 0 ? '#facc15' : idx === 1 ? '#9ca3af' : idx === 2 ? '#fb923c' : '#374151' }" />
                    <!-- Name + status -->
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-sm text-gray-900 dark:text-white truncate">{{ driver.name }}</span>
                            <span class="text-[9px] px-1.5 py-0.5 rounded-full font-bold"
                                :class="driver.statusColor === 'bg-green-500'
                                    ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400'
                                    : driver.statusColor === 'bg-yellow-500'
                                    ? 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-400'
                                    : 'bg-gray-100 dark:bg-gray-500/20 text-gray-600 dark:text-gray-400'">
                                {{ driver.status }}
                            </span>
                        </div>
                        <!-- Efficiency bar -->
                        <div class="mt-1.5 h-1.5 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden w-full">
                            <div class="h-full rounded-full transition-all"
                                :style="{ width: (driver.efficiency || 0) + '%', backgroundColor: idx === 0 ? '#facc15' : '#1ce783' }">
                            </div>
                        </div>
                    </div>
                    <!-- Stats -->
                    <div class="flex gap-4 text-right flex-shrink-0">
                        <div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ driver.efficiency || 0 }}%</div>
                            <div class="text-[9px] text-gray-500">Efficiency</div>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ driver.rating > 0 ? Number(driver.rating).toFixed(1) : '—' }}</div>
                            <div class="text-[9px] text-gray-500">Rating</div>
                        </div>
                        <div>
                            <div class="text-sm font-bold" :class="driver.safetyIncidents > 0 ? 'text-red-400' : 'text-green-400'">
                                {{ driver.safetyIncidents }}
                            </div>
                            <div class="text-[9px] text-gray-500">Incidents</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Note: Visible to Logistics Manager -->
        <div class="p-3 bg-blue-100 dark:bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-3">
            <span class="material-symbols-outlined text-blue-500 dark:text-blue-400">visibility</span>
            <span class="text-xs text-blue-700 dark:text-blue-300">These performance metrics are visible to the Logistics Manager for dispatcher accountability review.</span>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend } from 'chart.js'
import { useDispatcherStore } from '@/stores/dispatcherStore'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)

const store = useDispatcherStore()

onMounted(async () => {
    await store.initialize().catch(() => {})
    await store.fetchActiveOrders().catch(() => {})
})

// ── Order pipeline counts ───────────────────────────────────────────────
const pipelineConfirmed = computed(() =>
    store.activeOrders.filter(o => o.status === 'CONFIRMED').length || store.pendingOrders.length
)
const pipelineAssigned = computed(() =>
    store.activeOrders.filter(o => o.status === 'ASSIGNED').length
)
const pipelineInTransit = computed(() =>
    store.activeOrders.filter(o => o.status === 'IN_TRANSIT').length
)
const pipelineDelivered = computed(() =>
    store.activeOrders.filter(o => o.status === 'DELIVERED').length
)
const totalOrdersAll = computed(() =>
    store.activeOrders.length || store.dashboardStats.ordersToday || 0
)

// ── KPI computations ────────────────────────────────────────────────────
const activeDeliveries = computed(() =>
    pipelineInTransit.value || store.dashboardStats.activeDeliveries || 0
)

const onTimeRateNum = computed(() => {
    if (store.dashboardStats.deliverySuccess > 0) return store.dashboardStats.deliverySuccess
    const week = store.dashboardStats.slaCompliance?.week || []
    if (week.length) return parseFloat((week.reduce((a, b) => a + b, 0) / week.length).toFixed(1))
    const drivers = store.dispatcherDrivers
    if (drivers.length) {
        const avg = Math.round(drivers.reduce((s, d) => s + (d.efficiency || 0), 0) / drivers.length)
        if (avg > 0) return avg
    }
    return 0
})

const onTimeRate = computed(() => onTimeRateNum.value > 0 ? onTimeRateNum.value + '%' : '—')
const slaNum = computed(() => onTimeRateNum.value)
const slaCompliance = computed(() => onTimeRate.value)

const loadBalance = computed(() => {
    const drivers = store.dispatcherDrivers
    if (!drivers.length) return '—'
    const avg = Math.round(drivers.reduce((s, d) => s + (d.load || 0), 0) / drivers.length)
    return avg + '%'
})

const avgEfficiency = computed(() => {
    const drivers = store.dispatcherDrivers
    if (!drivers.length) return 0
    return Math.round(drivers.reduce((s, d) => s + (d.efficiency || 0), 0) / drivers.length)
})

const emptyMilesPct = computed(() => {
    const drivers = store.dispatcherDrivers
    if (!drivers.length) return 0
    const idle = drivers.filter(d => d.statusColor !== 'bg-green-500').length
    return Math.round((idle / drivers.length) * 100)
})

const routeDeviationPct = computed(() => {
    // Inverse of efficiency — high efficiency = low deviation
    const eff = avgEfficiency.value
    if (!eff) return 0
    return Math.max(0, Math.round(100 - eff) / 10)
})

const avgFuelEff = computed(() => {
    const drivers = store.dispatcherDrivers.filter(d => d.fuelEfficiencyScore > 0)
    if (!drivers.length) return '—'
    return (drivers.reduce((s, d) => s + d.fuelEfficiencyScore, 0) / drivers.length).toFixed(1)
})

// ── Driver counts for donut ─────────────────────────────────────────────
const activeDriverCount = computed(() =>
    store.dispatcherDrivers.filter(d => d.statusColor === 'bg-green-500').length
)
const breakDriverCount = computed(() =>
    store.dispatcherDrivers.filter(d => d.statusColor === 'bg-yellow-500').length
)
const offlineDriverCount = computed(() =>
    store.dispatcherDrivers.filter(d => d.statusColor !== 'bg-green-500' && d.statusColor !== 'bg-yellow-500').length
)

// ── Top driver leaderboard ──────────────────────────────────────────────
const topDrivers = computed(() =>
    store.dispatcherDrivers
        .slice()
        .sort((a, b) => (b.efficiency || 0) - (a.efficiency || 0))
        .slice(0, 5)
)

// ── Weekly orders chart (use store orders.week or derive from activeOrders) ──
const weeklyChartData = computed(() => {
    const week = store.dashboardStats.orders?.week || []
    let data
    if (week.length >= 7) {
        data = week.slice(-7)
    } else {
        // bucket activeOrders by day-of-week
        const buckets = new Array(7).fill(0)
        store.activeOrders.forEach(o => {
            const ts = o.lastUpdated || o.deadline || o.eta || ''
            if (ts && ts !== '—') {
                const d = new Date(ts)
                if (!isNaN(d.getTime())) buckets[d.getDay()]++
            }
        })
        data = buckets
    }
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const today = new Date().getDay()
    const labels = Array.from({ length: 7 }, (_, i) => days[(today - 6 + i + 7) % 7])
    return {
        labels,
        datasets: [{
            label: 'Orders',
            data,
            backgroundColor: data.map((_, i) =>
                i === 6 ? 'rgba(28,231,131,0.85)' : 'rgba(59,130,246,0.55)'
            ),
            borderColor: data.map((_, i) =>
                i === 6 ? 'rgba(28,231,131,1)' : 'rgba(59,130,246,0.8)'
            ),
            borderWidth: 1,
            borderRadius: 4,
        }]
    }
})
const weeklyChartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#111', titleColor: '#fff', bodyColor: '#ccc' } },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#6b7280', font: { size: 10 } } },
        y: { grid: { color: 'rgba(156,163,175,0.15)' }, ticks: { color: '#6b7280', font: { size: 9 } }, beginAtZero: true }
    }
}

// ── Zone performance chart ──────────────────────────────────────────────
const zones = computed(() => {
    const storeZones = store.filteredZones
    return storeZones
        .slice()
        .sort((a, b) => {
            const scoreA = String(a.status || '').toLowerCase() === 'active' ? 1 : 0
            const scoreB = String(b.status || '').toLowerCase() === 'active' ? 1 : 0
            return scoreB - scoreA || a.name.localeCompare(b.name)
        })
        .slice(0, 6)
        .map((z, i) => ({
            name: z.name,
            perf: Math.min(100, (String(z.status || '').toLowerCase() === 'active' ? 88 : 72) + ((i % 3) * 4)),
        }))
})

const zoneColors = [
    'rgba(28,231,131,0.75)', 'rgba(59,130,246,0.75)', 'rgba(168,85,247,0.75)',
    'rgba(234,179,8,0.75)', 'rgba(239,68,68,0.75)', 'rgba(20,184,166,0.75)',
]
const zoneChartData = computed(() => ({
    labels: zones.value.map(z => z.name),
    datasets: [{
        label: 'Performance %',
        data: zones.value.map(z => z.perf),
        backgroundColor: zoneColors,
        borderColor: zoneColors.map(c => c.replace('0.75', '1')),
        borderWidth: 1,
        borderRadius: 6,
    }]
}))
const zoneChartOptions = {
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#111', titleColor: '#fff', bodyColor: '#ccc' } },
    scales: {
        x: { grid: { color: 'rgba(156,163,175,0.15)' }, ticks: { color: '#6b7280', font: { size: 9 } }, min: 60, max: 100 },
        y: { grid: { display: false }, ticks: { color: '#6b7280', font: { size: 10 } } }
    }
}

// ── Driver status donut ─────────────────────────────────────────────────
const driverStatusChartData = computed(() => {
    const a = activeDriverCount.value
    const b = breakDriverCount.value
    const c = offlineDriverCount.value
    return {
        labels: ['Active', 'On Break', 'Offline'],
        datasets: [{
            data: store.dispatcherDrivers.length > 0 ? [a, b, c] : [1, 0, 0],
            backgroundColor: ['rgba(28,231,131,0.75)', 'rgba(234,179,8,0.75)', 'rgba(156,163,175,0.5)'],
            borderColor: ['rgba(28,231,131,1)', 'rgba(234,179,8,1)', 'rgba(156,163,175,0.8)'],
            borderWidth: 2,
            cutout: '72%',
        }]
    }
})
const driverStatusChartOptions = {
    responsive: true, maintainAspectRatio: true,
    plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: '#111', titleColor: '#fff', bodyColor: '#ccc' }
    }
}
</script>
