<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Operational Performance</h2>
            <div class="flex gap-3 items-center">
                <select v-model="timeRange" @change="fetchPerformance"
                    class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                    <option value="today" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">Today</option>
                    <option value="week" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">This Week</option>
                    <option value="month" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">This Month</option>
                </select>
                <button @click="exportReport"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm">
                    <span class="material-symbols-outlined text-[18px]">download</span> Export Report
                </button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading performance data...</div>
        </div>

        <template v-else>
        <!-- Primary KPI Row -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div v-for="kpi in primaryKPIs" :key="kpi.label"
                class="glass-panel p-4 rounded-xl relative overflow-hidden group hover:border-primary/20 transition-colors">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">{{ kpi.label }}</div>
                <div class="text-2xl font-bold mt-1" :class="kpi.color">{{ kpi.value }}</div>
                <div class="flex items-center gap-1 mt-1">
                    <span class="material-symbols-outlined text-[14px]"
                        :class="kpi.trend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                        {{ kpi.trend > 0 ? 'trending_up' : 'trending_down' }}
                    </span>
                    <span class="text-xs"
                        :class="kpi.trend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">{{ kpi.trendLabel }}</span>
                </div>
                <div class="absolute bottom-0 left-0 right-0 h-0.5" :class="kpi.barColor"></div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Order Status Distribution -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-blue-400">timeline</span>
                    Order Status Distribution
                </h3>
                <div class="h-60 relative">
                    <Bar :data="processingChartData" :options="processingChartOptions" />
                </div>
            </div>

            <!-- Pick Accuracy Gauge -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-green-600 dark:text-green-400">check_circle</span>
                    Order Completion Rate
                </h3>
                <div class="flex items-center justify-center gap-12 h-60">
                    <div class="relative w-40 h-40">
                        <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="42" fill="none" stroke="#1f2937" stroke-width="8" />
                            <circle cx="50" cy="50" r="42" fill="none"
                                :stroke="completionRate >= 80 ? '#10b981' : completionRate >= 60 ? '#f59e0b' : '#ef4444'"
                                stroke-width="8" stroke-linecap="round"
                                :stroke-dasharray="`${completionRate * 2.64} 264`" />
                        </svg>
                        <div class="absolute inset-0 flex flex-col items-center justify-center">
                            <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ completionRate }}%</div>
                            <div class="text-[10px] text-gray-500 uppercase">Completed</div>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <div>
                            <div class="text-sm text-gray-600 dark:text-gray-400">Total Orders</div>
                            <div class="text-xl font-bold text-gray-900 dark:text-white">{{ totalOrders }}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-600 dark:text-gray-400">Dispatched</div>
                            <div class="text-xl font-bold text-green-600 dark:text-green-400">{{ packedOrders }}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-600 dark:text-gray-400">Pending</div>
                            <div class="text-xl font-bold text-yellow-600 dark:text-yellow-400">{{ pendingOrders }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Secondary Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Labor Utilization -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-purple-400">groups</span>
                    Labor Utilization
                </h3>
                <div class="space-y-4">
                    <div v-if="laborStats.total === 0" class="text-center text-gray-500 text-sm py-4">No labour data available</div>
                    <template v-else>
                        <div v-for="stat in laborBreakdown" :key="stat.name">
                            <div class="flex justify-between text-sm mb-1">
                                <span class="text-gray-600 dark:text-gray-300">{{ stat.name }}</span>
                                <span class="font-bold"
                                    :class="stat.percent >= 70 ? 'text-green-600 dark:text-green-400' : stat.percent >= 40 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'">
                                    {{ stat.percent }}%
                                </span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                                <div class="h-full rounded-full transition-all"
                                    :class="stat.percent >= 70 ? 'bg-green-500' : stat.percent >= 40 ? 'bg-yellow-500' : 'bg-red-500'"
                                    :style="`width: ${stat.percent}%`"></div>
                            </div>
                            <div class="text-xs text-gray-500 mt-0.5">{{ stat.count }} workers</div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Order Pipeline Summary -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-yellow-600 dark:text-yellow-400">conveyor_belt</span>
                    Order Pipeline
                </h3>
                <div class="space-y-3">
                    <div v-for="stage in orderPipeline" :key="stage.label"
                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-sm font-bold text-gray-900 dark:text-white">{{ stage.label }}</span>
                            <span class="text-sm font-mono font-bold" :class="stage.color">{{ stage.count }}</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :class="stage.barColor"
                                :style="`width: ${totalOrders > 0 ? Math.min((stage.count / totalOrders) * 100, 100) : 0}%`"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Stock & Demand Health -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-teal-400">inventory</span>
                    Stock & Demand Health
                </h3>
                <div class="space-y-4">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="flex justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-400">Daily Demand Load</span>
                            <span class="font-bold text-gray-900 dark:text-white">{{ demandLoad }} orders</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div class="bg-blue-500 h-full rounded-full" :style="`width: ${Math.min((demandLoad / 60) * 100, 100)}%`"></div>
                        </div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="flex justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-400">On Hold Orders</span>
                            <span class="font-bold" :class="onHoldOrders > 5 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">{{ onHoldOrders }}</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div :class="onHoldOrders > 5 ? 'bg-red-500' : 'bg-green-500'" class="h-full rounded-full"
                                :style="`width: ${totalOrders > 0 ? Math.min((onHoldOrders / totalOrders) * 100, 100) : 0}%`"></div>
                        </div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="flex justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-400">Labor Availability</span>
                            <span class="font-bold text-green-600 dark:text-green-400">{{ laborStats.available }} / {{ laborStats.total }}</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div class="bg-green-500 h-full rounded-full"
                                :style="`width: ${laborStats.total > 0 ? (laborStats.available / laborStats.total) * 100 : 0}%`"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Daily Order Volume Chart -->
        <div class="glass-panel p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-primary">bar_chart</span>
                Order Status Breakdown
            </h3>
            <div class="h-48 relative">
                <Bar :data="demandChartData" :options="demandChartOptions" />
            </div>
        </div>
        </template>

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL } from '@/config/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const authStore = useAuthStore()
const timeRange = ref('today')
const toastMsg = ref('')
const loading = ref(false)

// Raw performance response from the dedicated backend endpoint
const perfMetrics = ref(null)

// Helper to read substatus counts from the server's status_breakdown dict
function sub(key) {
    return perfMetrics.value?.status_breakdown?.[key] ?? 0
}

const totalOrders = computed(() => perfMetrics.value?.total_orders ?? 0)
const completionRate = computed(() => Math.round(perfMetrics.value?.completion_rate ?? 0))
const onHoldOrders = computed(() => perfMetrics.value?.on_hold_count ?? 0)
const qcPassedOrders = computed(() => perfMetrics.value?.ready_for_dispatch ?? 0)
const onDockOrders = computed(() => sub('ON_DOCK'))
const packedOrders = computed(() => perfMetrics.value?.dispatched_today ?? 0)
const pendingOrders = computed(() => sub('AWAITING_PICK'))
const packingOrders = computed(() => perfMetrics.value?.packing_active ?? 0)
const demandLoad = computed(() => totalOrders.value)

const laborStats = computed(() => {
    const lb = perfMetrics.value?.labor_breakdown ?? {}
    const active = lb.active ?? 0   // assigned to an order
    const idle = lb.idle ?? 0       // in warehouse, no order
    const off = lb.off ?? 0         // not active
    const total = active + idle + off
    return { total, available: idle, busy: active, offDuty: off }
})

const laborBreakdown = computed(() => {
    const t = laborStats.value.total
    return [
        { name: 'Available', count: laborStats.value.available, percent: t > 0 ? Math.round((laborStats.value.available / t) * 100) : 0 },
        { name: 'On Duty / Assigned', count: laborStats.value.busy, percent: t > 0 ? Math.round((laborStats.value.busy / t) * 100) : 0 },
        { name: 'Off Duty', count: laborStats.value.offDuty, percent: t > 0 ? Math.round((laborStats.value.offDuty / t) * 100) : 0 },
    ]
})

const orderPipeline = computed(() => [
    { label: 'Awaiting Pick', count: sub('AWAITING_PICK'), color: 'text-yellow-600 dark:text-yellow-400', barColor: 'bg-yellow-500' },
    { label: 'Picking', count: sub('PICKING'), color: 'text-blue-600 dark:text-blue-400', barColor: 'bg-blue-500' },
    { label: 'Picked', count: sub('PICKED'), color: 'text-cyan-600 dark:text-cyan-400', barColor: 'bg-cyan-500' },
    { label: 'Packing', count: sub('PACKING'), color: 'text-purple-600 dark:text-purple-400', barColor: 'bg-purple-500' },
    { label: 'Packed', count: sub('PACKED'), color: 'text-indigo-600 dark:text-indigo-400', barColor: 'bg-indigo-500' },
    { label: 'QC Passed', count: sub('QC_PASSED') + sub('READY_FOR_DISPATCH'), color: 'text-teal-600 dark:text-teal-400', barColor: 'bg-teal-500' },
    { label: 'On Dock', count: sub('ON_DOCK'), color: 'text-pink-600 dark:text-pink-400', barColor: 'bg-pink-500' },
    { label: 'Dispatched', count: sub('DISPATCHED'), color: 'text-green-600 dark:text-green-400', barColor: 'bg-green-500' },
    { label: 'On Hold', count: sub('ON_HOLD'), color: 'text-orange-600 dark:text-orange-400', barColor: 'bg-orange-500' },
])

const primaryKPIs = computed(() => [
    {
        label: 'Total Orders', value: String(totalOrders.value),
        color: 'text-gray-900 dark:text-white', trend: 1, trendLabel: `in ${timeRange.value}`, barColor: 'bg-gray-400'
    },
    {
        label: 'Completion Rate', value: `${completionRate.value}%`,
        color: completionRate.value >= 70 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
        trend: completionRate.value >= 70 ? 1 : -1, trendLabel: 'dispatched/total', barColor: 'bg-green-500'
    },
    {
        label: 'On Hold', value: String(onHoldOrders.value),
        color: onHoldOrders.value > 5 ? 'text-red-600 dark:text-red-400' : 'text-yellow-600 dark:text-yellow-400',
        trend: onHoldOrders.value <= 5 ? 1 : -1, trendLabel: 'orders paused', barColor: 'bg-yellow-500'
    },
    {
        label: 'Labor Total', value: String(laborStats.value.total),
        color: 'text-blue-600 dark:text-blue-400', trend: 1, trendLabel: 'on roster', barColor: 'bg-blue-500'
    },
    {
        label: 'QC Passed', value: String(qcPassedOrders.value),
        color: 'text-teal-600 dark:text-teal-400', trend: 1, trendLabel: 'ready for dispatch', barColor: 'bg-teal-500'
    },
    {
        label: 'On Dock', value: String(onDockOrders.value),
        color: 'text-pink-600 dark:text-pink-400', trend: 1, trendLabel: 'loading', barColor: 'bg-pink-500'
    },
])

async function fetchPerformance() {
    loading.value = true
    try {
        const warehouseId = authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            console.warn('No warehouse_id — cannot fetch performance metrics')
            return
        }
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/performance?time_range=${timeRange.value}`,
            { headers }
        )
        if (res.ok) {
            const data = await res.json()
            perfMetrics.value = data.metrics
        } else {
            console.error('Performance fetch failed:', res.status, await res.text())
        }
    } catch (error) {
        console.error('Error fetching performance data:', error)
    } finally {
        loading.value = false
    }
}

function showToast(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

function exportReport() {
    const rows = [
        ['Metric', 'Value'],
        ...primaryKPIs.value.map(k => [k.label, k.value]),
        [],
        ['Pipeline Stage', 'Order Count'],
        ...orderPipeline.value.map(s => [s.label, s.count]),
        [],
        ['Labour', 'Count'],
        ['Available', laborStats.value.available],
        ['On Duty / Assigned', laborStats.value.busy],
        ['Off Duty', laborStats.value.offDuty],
        ['Total', laborStats.value.total],
    ]
    const csv = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `performance_${timeRange.value}_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showToast(`Performance report (${timeRange.value}) exported`)
}

// Charts
const processingChartData = computed(() => ({
    labels: ['Awaiting', 'Picking', 'Picked', 'Packing', 'Packed', 'QC Passed', 'On Dock', 'Dispatched'],
    datasets: [{
        label: 'Orders',
        data: [
            sub('AWAITING_PICK'),
            sub('PICKING'),
            sub('PICKED'),
            packingOrders.value,
            sub('PACKED'),
            qcPassedOrders.value,
            onDockOrders.value,
            sub('DISPATCHED'),
        ],
        backgroundColor: [
            'rgba(245, 158, 11, 0.7)',
            'rgba(59, 130, 246, 0.7)',
            'rgba(6, 182, 212, 0.7)',
            'rgba(139, 92, 246, 0.7)',
            'rgba(99, 102, 241, 0.7)',
            'rgba(20, 184, 166, 0.7)',
            'rgba(236, 72, 153, 0.7)',
            'rgba(34, 197, 94, 0.7)',
        ],
        borderRadius: 6,
        borderSkipped: false,
    }]
}))

const processingChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 12,
            cornerRadius: 8,
            callbacks: { label: (ctx) => `${ctx.parsed.y} orders` }
        }
    },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 11 } } },
        y: { min: 0, grid: { color: 'rgba(156,163,175,0.1)' }, ticks: { color: '#9ca3af', font: { size: 11 }, stepSize: 1 } }
    }
}

const demandChartData = computed(() => ({
    labels: orderPipeline.value.map(s => s.label),
    datasets: [{
        label: 'Orders',
        data: orderPipeline.value.map(s => s.count),
        backgroundColor: (ctx) => {
            const chart = ctx.chart
            const { ctx: canvasCtx, chartArea } = chart
            if (!chartArea) return 'rgba(68, 233, 150, 0.6)'
            const gradient = canvasCtx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top)
            gradient.addColorStop(0, 'rgba(68, 233, 150, 0.3)')
            gradient.addColorStop(1, 'rgba(68, 233, 150, 0.9)')
            return gradient
        },
        borderColor: 'rgb(68, 233, 150)',
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
    }]
}))

const demandChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 12,
            cornerRadius: 8,
            callbacks: { label: (ctx) => `${ctx.parsed.y} orders` }
        }
    },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } },
        y: { min: 0, grid: { color: 'rgba(156,163,175,0.1)' }, ticks: { color: '#9ca3af', font: { size: 11 }, stepSize: 1 } }
    }
}

onMounted(async () => {
    await authStore.ensureWarehouseContext()
    await fetchPerformance()
})
</script>
