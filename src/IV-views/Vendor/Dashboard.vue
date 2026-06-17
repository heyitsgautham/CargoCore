<template>
    <div class="space-y-6">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Active Shipments</div>
                    <span class="material-symbols-outlined text-blue-400 text-[20px]">local_shipping</span>
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ store.activeShipments.length }}</div>
                <div class="text-amber-500 text-xs mt-1">{{ store.pendingShipments.length }} pending dispatch</div>
            </div>
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Monthly Spend</div>
                    <span class="material-symbols-outlined text-purple-400 text-[20px]">payments</span>
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ monthlySpendFormatted }}</div>
                <div class="text-gray-500 text-xs mt-1">Budget: ₹50k</div>
            </div>
            <router-link to="/vendor/wallet" class="glass-panel p-5 rounded-xl hover:border-green-500/30 transition-all cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Wallet Balance</div>
                    <span class="material-symbols-outlined text-green-400 text-[20px]">account_balance_wallet</span>
                </div>
                <div class="text-3xl font-bold text-green-500">₹{{ store.creditBalance.toLocaleString() }}</div>
                <div class="text-gray-500 text-xs mt-1">Available credit</div>
            </router-link>
            <div class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wide">Success Rate</div>
                    <span class="material-symbols-outlined text-green-400 text-[20px]">verified</span>
                </div>
                <div class="text-3xl font-bold text-green-500">{{ store.analyticsData.successRate }}%</div>
                <div class="text-green-500 text-xs mt-1">Target: 99.0%</div>
            </div>
        </div>

        <div v-if="store.overdueInvoices.length > 0" class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <span class="material-symbols-outlined text-red-400">warning</span>
            <div class="flex-1">
                <div class="font-medium text-red-600 dark:text-red-400 text-sm">{{ store.overdueInvoices.length }} overdue invoice(s) — Total due: ₹{{ store.totalOverdue.toLocaleString() }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Please settle to avoid service interruption</div>
            </div>
            <router-link to="/vendor/invoices" class="px-3 py-1.5 bg-red-500 text-white text-xs font-bold rounded-lg hover:bg-red-600 transition-colors">Pay Now</router-link>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <router-link to="/vendor/create-shipment" class="glass-panel p-6 rounded-xl hover:bg-blue-500/5 dark:hover:bg-blue-500/10 cursor-pointer transition-all border border-dashed border-gray-200 dark:border-white/20 hover:border-blue-500/50 flex flex-col items-center text-center justify-center h-44 group">
                <div class="w-14 h-14 rounded-full bg-blue-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined text-2xl text-blue-500">add_box</span>
                </div>
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Create Shipment</h3>
                <p class="text-xs text-gray-500 mt-1">Single commercial delivery</p>
            </router-link>
            <router-link to="/vendor/recurring" class="glass-panel p-6 rounded-xl hover:bg-purple-500/5 dark:hover:bg-purple-500/10 cursor-pointer transition-all border border-dashed border-gray-200 dark:border-white/20 hover:border-purple-500/50 flex flex-col items-center text-center justify-center h-44 group">
                <div class="w-14 h-14 rounded-full bg-purple-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined text-2xl text-purple-500">update</span>
                </div>
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Schedule Recurring</h3>
                <p class="text-xs text-gray-500 mt-1">Set up weekly/monthly pickups</p>
            </router-link>
            <router-link to="/vendor/bulk-upload" class="glass-panel p-6 rounded-xl hover:bg-green-500/5 dark:hover:bg-green-500/10 cursor-pointer transition-all border border-dashed border-gray-200 dark:border-white/20 hover:border-green-500/50 flex flex-col items-center text-center justify-center h-44 group">
                <div class="w-14 h-14 rounded-full bg-green-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined text-2xl text-green-500">upload_file</span>
                </div>
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Bulk Upload</h3>
                <p class="text-xs text-gray-500 mt-1">Import CSV / Excel orders</p>
            </router-link>
        </div>

        <!-- ── Charts Row ─────────────────────────────────────── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Monthly Spend Bar Chart -->
            <div class="lg:col-span-2 glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">Monthly Spend</h3>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Last 6 months — hover bars for details</p>
                    </div>
                    <select v-model="spendFilter" class="text-xs bg-gray-100 dark:bg-white/10 border border-gray-200 dark:border-transparent rounded-lg px-3 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
                        <option value="spend" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Spend (₹)</option>
                        <option value="orders" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Order Count</option>
                    </select>
                </div>
                <div class="relative h-80">
                    <Bar :data="barChartData" :options="barOptions" />
                </div>
            </div>

            <!-- Shipment Status Donut -->
            <div class="glass-panel p-5 rounded-xl flex flex-col">
                <div class="mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm">Status Breakdown</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">All-time consignments</p>
                </div>
                <div class="flex-1 flex items-center justify-center">
                    <div class="relative w-36 h-36">
                        <Doughnut :data="doughnutData" :options="doughnutOptions" />
                        <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ store.shipments.length }}</span>
                            <span class="text-[10px] text-gray-500 uppercase tracking-wide">Total</span>
                        </div>
                    </div>
                </div>
                <div class="mt-4 space-y-1.5">
                    <div v-for="l in donutLegend" :key="l.label" class="flex items-center justify-between text-xs">
                        <div class="flex items-center gap-2">
                            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{background:l.color}"></div>
                            <span class="text-gray-500">{{ l.label }}</span>
                        </div>
                        <span class="font-bold text-gray-900 dark:text-white">{{ l.count }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ── Spend Trend + On-Time KPIs ─────────────────────── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Order Volume Sparkline -->
            <div class="lg:col-span-2 glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">Order Volume Trend</h3>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Orders shipped per month</p>
                    </div>
                </div>
                <div class="relative h-72">
                    <Line :data="lineChartData" :options="lineOptions" />
                </div>
            </div>

            <!-- KPI Cards Column -->
            <div class="space-y-4">
                <div class="glass-panel p-5 rounded-xl">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">On-Time Rate</span>
                        <span class="material-symbols-outlined text-green-400 text-[18px]">schedule</span>
                    </div>
                    <div class="text-3xl font-bold text-green-500 mb-2">{{ store.analyticsData.onTime }}%</div>
                    <div class="w-full h-2 bg-gray-200 dark:bg-white/10 rounded-full">
                        <div class="h-2 bg-green-500 rounded-full transition-all" :style="{width: store.analyticsData.onTime + '%'}"></div>
                    </div>
                    <div class="text-[10px] text-green-500 mt-1">↑ 2.1% vs last period</div>
                </div>

                <div class="glass-panel p-5 rounded-xl">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Avg. Transit</span>
                        <span class="material-symbols-outlined text-blue-400 text-[18px]">route</span>
                    </div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ store.analyticsData.avgTransit }}<span class="text-base font-normal text-gray-400 ml-1">days</span></div>
                    <div class="text-[10px] text-green-500 mt-1">↓ 0.5 days improvement</div>
                </div>

                <div class="glass-panel p-5 rounded-xl">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Avg. Order Value</span>
                        <span class="material-symbols-outlined text-purple-400 text-[18px]">paid</span>
                    </div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">₹{{ store.analyticsData.costPerMile.toLocaleString() }}</div>
                    <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1">Based on live shipment totals</div>
                </div>
            </div>
        </div>

        <!-- ── Recent Consignments + Sidebar ──────────────────── -->
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div class="xl:col-span-2 glass-panel rounded-xl overflow-hidden">
                <div class="p-5 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white">Recent Consignments</h3>
                    <router-link to="/vendor/tracking" class="text-blue-500 text-xs hover:underline">View All →</router-link>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm min-w-[500px]">
                        <thead class="bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 text-xs uppercase">
                            <tr>
                                <th class="px-5 py-3">Order ID</th>
                                <th class="px-5 py-3">Destination</th>
                                <th class="px-5 py-3">Status</th>
                                <th class="px-5 py-3">ETA</th>
                                <th class="px-5 py-3 text-right">Amount</th>
                                <th class="px-5 py-3"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="s in store.shipments.slice(0,5)" :key="s.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                                <td class="px-5 py-3 font-mono text-blue-500 text-xs font-bold">{{ s.id }}</td>
                                <td class="px-5 py-3 text-gray-600 dark:text-gray-300 text-xs max-w-[120px] truncate">{{ s.destination }}</td>
                                <td class="px-5 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="statusClass(s.statusKey)">{{ s.status }}</span></td>
                                <td class="px-5 py-3 text-gray-500 dark:text-gray-400 text-xs">{{ s.eta }}</td>
                                <td class="px-5 py-3 text-right font-bold text-gray-900 dark:text-white text-xs">₹{{ s.amount.toLocaleString() }}</td>
                                <td class="px-5 py-3"><button @click="selected=s" class="text-gray-400 hover:text-blue-500 transition-colors"><span class="material-symbols-outlined text-[18px]">open_in_new</span></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="space-y-4">
                <div class="glass-panel p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Invoice Summary</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center"><span class="text-xs text-gray-600 dark:text-gray-400">Overdue</span><span class="text-sm font-bold text-red-500">₹{{ store.totalOverdue.toLocaleString() }}</span></div>
                        <div class="flex justify-between items-center"><span class="text-xs text-gray-600 dark:text-gray-400">Unpaid Invoices</span><span class="text-sm font-bold text-gray-900 dark:text-white">{{ store.totalUnpaid }}</span></div>
                        <div class="flex justify-between items-center"><span class="text-xs text-gray-600 dark:text-gray-400">Paid This Month</span><span class="text-sm font-bold text-green-500">₹{{ store.totalPaidThisMonth.toLocaleString() }}</span></div>
                    </div>
                    <router-link to="/vendor/invoices" class="mt-4 block w-full text-center py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors">Manage Invoices</router-link>
                </div>
                <div class="glass-panel p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-3">Order Lifecycle</h3>
                    <div class="space-y-2">
                        <div v-for="step in lifecycle" :key="step.label" class="flex items-center gap-3">
                            <div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" :class="step.done?'bg-green-500':'bg-gray-200 dark:bg-white/10'">
                                <span class="material-symbols-outlined text-[11px]" :class="step.done?'text-white':'text-gray-400'">{{ step.done?'check':'radio_button_unchecked' }}</span>
                            </div>
                            <span class="text-xs" :class="step.done?'text-gray-800 dark:text-gray-300 font-medium':'text-gray-400 dark:text-gray-500'">{{ step.label }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <Teleport to="body">
            <BaseModal :isOpen="!!selected" @close="selected=null">
                <template #title>Shipment — {{ selected?.id }}</template>
                <div v-if="selected" class="space-y-4">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Status</div><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="statusClass(selected.statusKey)">{{ selected.status }}</span></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">ETA</div><div class="text-sm font-bold dark:text-white">{{ selected.eta }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Route</div><div class="text-xs dark:text-gray-300">{{ selected.route }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Amount</div><div class="text-sm font-bold text-green-500">₹{{ selected.amount?.toLocaleString() }}</div></div>
                    </div>
                    <div v-if="selected.driver" class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg flex items-center gap-3">
                        <span class="material-symbols-outlined text-blue-400">person</span>
                        <div><div class="text-xs text-gray-500">Driver</div><div class="text-sm font-medium dark:text-white">{{ selected.driver }} · {{ selected.driverPhone }}</div></div>
                    </div>
                    <div v-if="selected.progress>0" class="space-y-1">
                        <div class="flex justify-between text-xs text-gray-500"><span>Progress</span><span>{{ selected.progress }}%</span></div>
                        <div class="w-full h-2 bg-gray-200 dark:bg-white/10 rounded-full"><div class="h-2 bg-blue-500 rounded-full" :style="{width:selected.progress+'%'}"></div></div>
                    </div>
                </div>
                <template #footer>
                    <div class="flex gap-3">
                        <router-link to="/vendor/tracking" @click="selected=null" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors">Track Shipment</router-link>
                        <button @click="selected=null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    </div>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import BaseModal from '@/components/BaseModal.vue'
import {
    Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement,
    LineElement, ArcElement, Tooltip, Legend, Filler
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler)

const store = useVendorStore()
const selected = ref(null)
const spendFilter = ref('spend')

// ── Theme detection (reacts to dark/light toggle) ───────────────────
const isDark = ref(document.documentElement.classList.contains('dark'))
let themeObserver = null

onMounted(() => {
    themeObserver = new MutationObserver(() => {
        isDark.value = document.documentElement.classList.contains('dark')
    })
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})
onUnmounted(() => themeObserver?.disconnect())

const tickColor  = computed(() => isDark.value ? '#9ca3af' : '#374151')
const gridColor  = computed(() => isDark.value ? 'rgba(255,255,255,0.07)' : 'rgba(107,114,128,0.15)')

const statusClass = k => ({
    pending:   'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    warehouse: 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
    transit:   'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    delivery:  'bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
    delivered: 'bg-green-500/20 text-green-600 dark:text-green-400',
    cancelled: 'bg-red-500/20 text-red-600 dark:text-red-400',
}[k] || 'bg-gray-500/20 text-gray-500')

// ── Bar Chart (Monthly Spend / Orders) ──────────────────────────────
const monthly = computed(() => store.analyticsData.monthly)
const barChartData = computed(() => ({
    labels: monthly.value.map(m => m.month),
    datasets: [{
        label: spendFilter.value === 'spend' ? 'Spend (₹)' : 'Orders',
        data: monthly.value.map(m => spendFilter.value === 'spend' ? m.spend : m.orders),
        backgroundColor: monthly.value.map((_, i) =>
            i === monthly.value.length - 1 ? 'rgba(59,130,246,0.85)' : 'rgba(59,130,246,0.30)'
        ),
        borderColor: 'rgba(59,130,246,0.85)',
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
    }]
}))
const barOptions = computed(() => ({
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => spendFilter.value === 'spend' ? `₹${ctx.parsed.y.toLocaleString()}` : `${ctx.parsed.y} orders` } } },
    scales: {
        x: { grid: { display: false }, ticks: { color: tickColor.value, font: { size: 11 } } },
        y: { grid: { color: gridColor.value }, ticks: { color: tickColor.value, font: { size: 11 }, callback: v => spendFilter.value === 'spend' ? `₹${(v/1000).toFixed(0)}k` : v } },
    }
}))

// ── Doughnut Chart (Status Breakdown) ───────────────────────────────
const statusCounts = computed(() => {
    const sc = { pending: 0, warehouse: 0, transit: 0, delivery: 0, delivered: 0, cancelled: 0 }
    store.shipments.forEach(s => { if (sc[s.statusKey] !== undefined) sc[s.statusKey]++ })
    return sc
})
const doughnutData = computed(() => ({
    labels: ['Pending', 'In Warehouse', 'In Transit', 'Out for Delivery', 'Delivered', 'Cancelled'],
    datasets: [{
        data: [statusCounts.value.pending, statusCounts.value.warehouse, statusCounts.value.transit, statusCounts.value.delivery, statusCounts.value.delivered, statusCounts.value.cancelled],
        backgroundColor: ['rgba(234,179,8,0.85)', 'rgba(168,85,247,0.85)', 'rgba(59,130,246,0.85)', 'rgba(99,102,241,0.85)', 'rgba(34,197,94,0.85)', 'rgba(239,68,68,0.85)'],
        borderColor: isDark.value ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.9)',
        borderWidth: 2,
        hoverOffset: 6,
    }]
}))
const doughnutOptions = computed(() => ({
    responsive: true, maintainAspectRatio: false, cutout: '72%',
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } } }
}))
const donutLegend = computed(() => [
    { label: 'Pending',          color: 'rgba(234,179,8,0.85)',   count: statusCounts.value.pending },
    { label: 'In Warehouse',     color: 'rgba(168,85,247,0.85)',  count: statusCounts.value.warehouse },
    { label: 'In Transit',       color: 'rgba(59,130,246,0.85)',  count: statusCounts.value.transit },
    { label: 'Out for Delivery', color: 'rgba(99,102,241,0.85)',  count: statusCounts.value.delivery },
    { label: 'Delivered',        color: 'rgba(34,197,94,0.85)',   count: statusCounts.value.delivered },
    { label: 'Cancelled',        color: 'rgba(239,68,68,0.85)',   count: statusCounts.value.cancelled },
])

// ── Line Chart (Order Volume Trend) ─────────────────────────────────
const lineChartData = computed(() => ({
    labels: monthly.value.map(m => m.month),
    datasets: [{
        label: 'Orders',
        data: monthly.value.map(m => m.orders),
        borderColor: 'rgba(99,102,241,0.9)',
        backgroundColor: isDark.value ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.06)',
        borderWidth: 2.5,
        pointBackgroundColor: 'rgba(99,102,241,1)',
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.4,
        fill: true,
    }]
}))
const lineOptions = computed(() => ({
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} orders` } } },
    scales: {
        x: { grid: { display: false }, ticks: { color: tickColor.value, font: { size: 11 } } },
        y: { grid: { color: gridColor.value }, ticks: { color: tickColor.value, font: { size: 11 } } },
    }
}))

const monthlySpendFormatted = computed(() => {
    const spend = store.dashboard?.stats?.monthly_spend ?? 0
    if (spend >= 1000000) return `₹${(spend / 1000000).toFixed(1)}M`
    if (spend >= 1000) return `₹${(spend / 1000).toFixed(1)}k`
    return `₹${spend.toLocaleString()}`
})

const LIFECYCLE_STEPS = [
    'Vendor submits booking',
    'ORDER_ID generated',
    'Manager notified',
    'Warehouse assigned',
    'Goods prepared',
    'Vehicle assigned',
    'Delivery executed',
    'Proof uploaded',
    'Invoice generated',
]
const STATUS_DONE_COUNT = { pending: 3, warehouse: 5, transit: 6, delivery: 7, delivered: 9, cancelled: 1 }

const lifecycle = computed(() => {
    const latest = store.activeShipments[0] || store.shipments[0]
    const n = latest ? (STATUS_DONE_COUNT[latest.statusKey] ?? 0) : 0
    return LIFECYCLE_STEPS.map((label, i) => ({ label, done: i < n }))
})
</script>
