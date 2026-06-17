<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Shipment Analytics</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Monitor performance, spend, and delivery metrics</p>
            </div>
            <select v-model="timePeriod" class="text-sm bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
                <option value="6m" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 6 Months</option>
                <option value="1y" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last Year</option>
            </select>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-xl">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Shipments</div>
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ store.shipments.length }}</div>
                <div class="text-[10px] text-green-500 mt-1">↑ 12% vs prev</div>
            </div>
            <div class="glass-panel p-5 rounded-xl">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">On-Time Rate</div>
                <div class="text-2xl font-bold text-green-500">{{ store.analyticsData.onTime }}%</div>
                <div class="text-[10px] text-green-500 mt-1">↑ 2.1%</div>
            </div>
            <div class="glass-panel p-5 rounded-xl">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Transit Time</div>
                <div class="text-2xl font-bold text-blue-500">{{ store.analyticsData.avgTransit }} Days</div>
                <div class="text-[10px] text-green-500 mt-1">↓ 0.5 Days</div>
            </div>
            <div class="glass-panel p-5 rounded-xl">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Order Value</div>
                <div class="text-2xl font-bold text-gray-900 dark:text-white">₹{{ store.analyticsData.costPerMile.toLocaleString() }}</div>
                <div class="text-[10px] text-gray-400 mt-1">Derived from live orders</div>
            </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Monthly Spend Chart -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Monthly Spend (₹)</h3>
                <div class="h-64">
                    <Bar :data="spendChartData" :options="barOptions" />
                </div>
            </div>

            <!-- Status Distribution -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Status Distribution</h3>
                <div class="h-64 flex items-center justify-center">
                    <div class="w-52 h-52">
                        <Doughnut :data="statusChartData" :options="doughnutOptions" />
                    </div>
                </div>
            </div>

            <!-- Delivery Trend -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Delivery Trend</h3>
                <div class="h-64">
                    <Line :data="trendChartData" :options="lineOptions" />
                </div>
            </div>

            <!-- Route Performance -->
            <div class="glass-panel p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Top Routes</h3>
                <div class="space-y-3">
                    <div v-for="(route, i) in topRoutes" :key="i" class="flex items-center gap-3">
                        <span class="text-xs font-bold text-gray-400 w-5">#{{ i + 1 }}</span>
                        <div class="flex-1">
                            <div class="flex justify-between mb-1">
                                <span class="text-xs font-bold text-gray-900 dark:text-white">{{ route.name }}</span>
                                <span class="text-xs text-gray-500">{{ route.count }} shipments</span>
                            </div>
                            <div class="h-2 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                                <div class="h-full rounded-full" :class="route.color" :style="{ width: route.pct + '%' }"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Tooltip, Legend, Filler } from 'chart.js'
ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Tooltip, Legend, Filler)

const store = useVendorStore()
const timePeriod = ref('6m')

const spendChartData = computed(() => ({
    labels: store.analyticsData.monthly.map(m => m.month),
    datasets: [{
        label: 'Spend',
        data: store.analyticsData.monthly.map(m => m.spend),
        backgroundColor: 'rgba(59,130,246,0.5)',
        borderColor: 'rgba(59,130,246,1)',
        borderWidth: 1,
        borderRadius: 6,
    }]
}))

const statusCounts = computed(() => {
    const counts = {}
    store.shipments.forEach(s => { counts[s.status] = (counts[s.status] || 0) + 1 })
    return counts
})

const statusChartData = computed(() => ({
    labels: Object.keys(statusCounts.value),
    datasets: [{
        data: Object.values(statusCounts.value),
        backgroundColor: ['#facc15', '#3b82f6', '#22c55e', '#ef4444', '#a855f7'],
        borderWidth: 0,
    }]
}))

const trendChartData = computed(() => ({
    labels: store.analyticsData.monthly.map(m => m.month),
    datasets: [{
        label: 'Deliveries',
        data: store.analyticsData.monthly.map(m => m.orders),
        borderColor: 'rgba(34,197,94,1)',
        backgroundColor: 'rgba(34,197,94,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: 'rgba(34,197,94,1)',
    }]
}))

const topRoutes = computed(() => {
    const routeCounts = new Map()
    store.shipments.forEach((shipment) => {
        const route = shipment.route || `${shipment.origin} → ${shipment.destination}`
        routeCounts.set(route, (routeCounts.get(route) || 0) + 1)
    })
    const entries = [...routeCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4)
    const maxCount = entries[0]?.[1] || 1
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-yellow-500']
    return entries.map(([name, count], index) => ({
        name,
        count,
        pct: Math.max(20, Math.round((count / maxCount) * 100)),
        color: colors[index] || 'bg-blue-500',
    }))
})

const barOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { ticks: { color: '#9ca3af' }, grid: { display: false } } } }
const doughnutOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af', boxWidth: 12, padding: 12 } } }, cutout: '60%' }
const lineOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { ticks: { color: '#9ca3af' }, grid: { display: false } } } }
</script>
