<template>
    <div class="h-full flex flex-col space-y-6">
        <!-- Header -->
        <div class="flex flex-col gap-4 shrink-0">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary">compare_arrows</span> Comparative Viewers
                    </h2>
                    <p class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">
                        Drag and drop warehouses from the sidebar to compare performance metrics.
                    </p>
                </div>
                
                <div class="flex gap-2 items-center">
                    <select v-model="timeRange" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50 text-gray-700 dark:text-gray-200 cursor-pointer">
                        <option value="today" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Today (Live)</option>
                        <option value="7d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 7 Days</option>
                        <option value="30d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 30 Days</option>
                        <option value="ytd" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Year to Date</option>
                    </select>
                    
                    <button @click="store.comparedWarehouses = []" v-if="store.comparedWarehouses.length > 0" class="text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 font-bold px-3 py-2 border border-red-200 dark:border-red-500/30 rounded-lg bg-red-50 dark:bg-red-900/10 transition-colors">
                        Clear All
                    </button>
                </div>
            </div>

            <!-- Global Tabs (Control which section is shown in cards) -->
            <div class="flex gap-1 overflow-x-auto pb-2 border-b border-gray-200 dark:border-white/10 no-scrollbar">
                <button v-for="tab in tabs" :key="tab.id"
                    @click="activeTab = tab.id"
                    class="px-3 py-2 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-2 shrink-0"
                    :class="activeTab === tab.id ? 'bg-primary text-white shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
                    <span class="material-symbols-outlined text-[16px]">{{ tab.icon }}</span>
                    {{ tab.label }}
                </button>
            </div>
        </div>

        <!-- Drop Zone / Comparison Area -->
        <div 
            class="flex-1 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-2xl flex flex-wrap content-start items-start justify-start p-4 gap-4 overflow-x-auto min-h-[500px]"
            @dragover.prevent
            @drop="onDrop"
        >
            <div v-if="store.comparedWarehouses.length === 0" class="m-auto text-center text-gray-400">
                <span class="material-symbols-outlined text-6xl mb-2 opacity-50">move_item</span>
                <p class="text-lg font-medium">Drag warehouses here to compare</p>
                <p class="text-sm">Select warehouses from the sidebar list</p>
            </div>

            <div v-for="warehouse in store.comparedWarehouses" :key="warehouse.id" class="w-96 shrink-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg flex flex-col h-full animate-fade-in ring-1 ring-black/5">
                <!-- Warehouse Header -->
                <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5 rounded-t-xl sticky top-0 z-10 backdrop-blur-sm">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs border border-primary/20">
                            {{ warehouse.name.substring(0,2).toUpperCase() }}
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white leading-tight">{{ warehouse.name }}</h3>
                            <p class="text-[10px] text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                <span class="material-symbols-outlined text-[10px]">location_on</span>
                                {{ warehouse.location }}
                            </p>
                        </div>
                    </div>
                    <button @click="removeWarehouse(warehouse.id)" class="text-gray-400 hover:text-red-500 p-1 hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors" title="Remove">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Content Area based on Active Tab -->
                <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
                    
                    <!-- 1. Control Tower -->
                    <div v-if="activeTab === 'control_tower'" class="space-y-4 animate-fade-in">
                        <!-- KPI Grid -->
                         <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg text-center border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-bold">Orders</div>
                                <div class="text-xl font-black text-gray-900 dark:text-white">{{ getHubOrders(warehouse.id) }}</div>
                                <div class="text-[10px] text-gray-400 dark:text-gray-500 font-bold">Total transactions</div>
                            </div>
                             <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg text-center border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-bold">Efficiency</div>
                                <div class="text-xl font-black text-green-500">{{ warehouse.efficiency != null ? warehouse.efficiency + '%' : '--' }}</div>
                                <div class="text-[10px] text-gray-400 dark:text-gray-500 font-bold">Target: 95%</div>
                            </div>
                         </div>

                         <!-- Active Alerts -->
                         <div class="space-y-2">
                             <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Active Alerts</div>
                             <div v-if="getHubAlerts(warehouse.id).length > 0" class="bg-red-50 dark:bg-red-900/10 p-3 rounded-lg border border-red-100 dark:border-red-500/20 flex gap-3">
                                <span class="material-symbols-outlined text-red-500 text-[20px]">warning</span>
                                <div>
                                    <div class="text-xs font-bold text-red-700 dark:text-red-400">{{ getHubAlerts(warehouse.id)[0]?.title }}</div>
                                    <div class="text-[10px] text-red-600/80 dark:text-red-400/70 mt-1">{{ getHubAlerts(warehouse.id)[0]?.description }}</div>
                                </div>
                             </div>
                             <div v-else class="bg-green-50 dark:bg-green-900/10 p-3 rounded-lg border border-green-100 dark:border-green-500/20 text-center text-xs text-green-600 dark:text-green-400">
                                No active alerts. Operations normal.
                             </div>
                         </div>

                         <!-- System Health Chart (New) -->
                         <div class="h-32 mt-2">
                            <Line :data="getLineChartData(warehouse.id, 'System Load')" :options="miniChartOptions" />
                         </div>
                    </div>

                    <!-- 2. Financials -->
                    <div v-if="activeTab === 'financials'" class="space-y-4 animate-fade-in">
                        <div class="bg-green-50 dark:bg-green-900/10 p-4 rounded-xl border border-green-100 dark:border-green-500/20 text-center">
                            <div class="text-xs text-green-600/80 dark:text-green-400/80 uppercase font-bold mb-1">Total Revenue</div>
                            <div class="text-2xl font-black text-green-700 dark:text-green-400">₹{{ getHubRevenue(warehouse.id).toLocaleString('en-IN') }}</div>
                        </div>

                         <!-- Revenue Bar Chart (New) -->
                        <div class="h-40">
                             <Bar :data="getBarChartData(warehouse.id)" :options="miniChartOptions" />
                        </div>

                        <div class="p-3 border border-red-100 dark:border-red-500/20 bg-red-50/50 dark:bg-red-900/5 rounded-lg">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-xs font-bold text-red-600">Pending Dues</span>
                                <span class="bg-red-100 text-red-700 text-[10px] px-2 py-0.5 rounded-full font-bold">CRITICAL</span>
                            </div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white">₹{{ getHubPendingCod(warehouse.id).toLocaleString('en-IN') }}</div>
                        </div>
                    </div>

                    <!-- 3. Attendance -->
                    <div v-if="activeTab === 'attendance'" class="space-y-4 animate-fade-in">
                        <div class="flex items-center justify-between p-3 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-xl shadow-sm">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                                    <span class="material-symbols-outlined">how_to_reg</span>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold">Present</div>
                                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ warehouse.staffActive ?? '--' }}/{{ warehouse.staffTotal ?? '--' }}</div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-xs font-bold" :class="getAttendanceRate(warehouse) >= 80 ? 'text-green-500' : 'text-red-500'">
                                    {{ getAttendanceRate(warehouse) != null ? getAttendanceRate(warehouse) + '%' : '--' }}
                                </div>
                                <div class="text-[10px] text-gray-400 dark:text-gray-500">Attendance</div>
                            </div>
                        </div>

                         <div class="space-y-2">
                            <h4 class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">
                                Inactive Staff
                                <span class="ml-1 text-red-400">({{ getHubInactiveStaff(warehouse.id).length }})</span>
                            </h4>
                            <template v-if="getHubInactiveStaff(warehouse.id).length > 0">
                                <div v-for="member in getHubInactiveStaff(warehouse.id).slice(0, 3)" :key="member.id"
                                    class="p-2 flex items-center gap-2 bg-gray-50 dark:bg-white/5 rounded-lg">
                                    <span class="material-symbols-outlined text-gray-400 text-[16px]">person_off</span>
                                    <div class="flex-1 text-xs font-medium text-gray-700 dark:text-gray-300">{{ member.name }}</div>
                                    <div class="text-[10px] text-gray-500 dark:text-gray-400 font-bold">{{ member.role }}</div>
                                </div>
                            </template>
                            <div v-else class="p-2 text-center text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-100 dark:border-green-500/20">
                                All staff are active
                            </div>
                        </div>

                        <!-- Attendance Trend Chart (New) -->
                        <div class="h-32 mt-2">
                             <h4 class="text-[10px] font-bold text-gray-400 uppercase mb-2">Weekly Trend</h4>
                            <Line :data="getLineChartData(warehouse.id, 'Attendance %', 'green')" :options="miniChartOptions" />
                         </div>
                    </div>

                    <!-- 4. Workforce -->
                    <div v-if="activeTab === 'workforce'" class="space-y-4 animate-fade-in">
                         <div class="h-40 flex justify-center mb-4">
                             <Doughnut :data="getWorkforceData(warehouse.id)" :options="{ maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 } } } } }" />
                         </div>

                         <div class="grid grid-cols-2 gap-3 mb-3">
                            <div class="bg-blue-50 dark:bg-blue-900/10 p-3 rounded-lg text-center border border-blue-100 dark:border-blue-500/20">
                                <div class="text-[10px] text-blue-600/70 dark:text-blue-400/70 uppercase font-bold">Drivers</div>
                                <div class="text-xl font-black text-blue-700 dark:text-blue-400">{{ getHubDriversList(warehouse.id).length }}</div>
                                <div class="text-[10px] text-blue-500">{{ getHubDriversList(warehouse.id).filter(d => d.status === 'Active').length }} Active</div>
                            </div>
                             <div class="bg-purple-50 dark:bg-purple-900/10 p-3 rounded-lg text-center border border-purple-100 dark:border-purple-500/20">
                                <div class="text-[10px] text-purple-600/70 dark:text-purple-400/70 uppercase font-bold">Staff</div>
                                <div class="text-xl font-black text-purple-700 dark:text-purple-400">{{ getHubStaff(warehouse.id).length }}</div>
                                <div class="text-[10px] text-purple-500">{{ warehouse.staffActive ?? '--' }} Active</div>
                            </div>
                         </div>
                    </div>

                    <!-- 5. Inventory -->
                    <div v-if="activeTab === 'assets'" class="space-y-4 animate-fade-in">
                         <div class="p-4 bg-gray-50 dark:bg-white/10 border border-gray-100 dark:border-white/10 rounded-xl relative overflow-hidden">
                            <h4 class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-3">Capacity Utilization</h4>
                             <div class="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-white dark:from-white/5 to-transparent"></div>
                            <div class="flex items-center gap-4 relative z-10">
                                <!-- Simple Circle -->
                                <div class="w-16 h-16 rounded-full border-4 border-gray-200 dark:border-gray-600 flex items-center justify-center font-bold text-sm text-gray-900 dark:text-white">
                                    {{ warehouse.capacity != null ? warehouse.capacity + '%' : '--' }}
                                </div>
                                <div class="flex-1 space-y-1">
                                    <div class="flex justify-between text-xs">
                                        <span class="text-gray-500 dark:text-gray-400">Vehicles</span>
                                        <span class="font-bold text-gray-900 dark:text-white">{{ warehouse.vehiclesActive ?? '--' }}/{{ warehouse.vehiclesTotal ?? '--' }}</span>
                                    </div>
                                    <div class="flex justify-between text-xs">
                                        <span class="text-gray-500 dark:text-gray-400">Process Rate</span>
                                        <span class="font-bold text-indigo-500">{{ warehouse.processRate != null ? warehouse.processRate + '%' : '--' }}</span>
                                    </div>
                                </div>
                            </div>
                         </div>
                         <!-- Stock Trend Chart (New) -->
                         <div class="h-32">
                             <h4 class="text-[10px] font-bold text-gray-400 uppercase mb-2">Stock Trend (30 Days)</h4>
                            <Line :data="getLineChartData(warehouse.id, 'Stock', 'purple')" :options="miniChartOptions" />
                         </div>
                    </div>

                    <!-- 6. Returns -->
                    <div v-if="activeTab === 'returns'" class="space-y-4 animate-fade-in">
                         <div class="flex items-start gap-4 p-3 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-500/20 rounded-lg">
                             <h1 class="text-3xl font-bold text-red-500">{{ getHubPendingReturns(warehouse.id).length }}</h1>
                             <div>
                                 <div class="text-xs font-bold text-red-700 dark:text-red-400">Pending Returns</div>
                                 <div class="text-[10px] text-red-600/80 dark:text-red-400/80">Requires immediate inspection</div>
                             </div>
                         </div>
                         <div class="space-y-2">
                             <div class="p-2 border border-gray-200 dark:border-white/10 rounded flex justify-between items-center bg-white dark:bg-white/5">
                                 <span class="text-xs font-medium text-gray-700 dark:text-gray-200">Resolution Rate</span>
                                 <span class="text-xs font-bold text-green-500">{{ getHubReturnResolutionRate(warehouse.id) != null ? getHubReturnResolutionRate(warehouse.id) + '%' : '--' }}</span>
                             </div>
                             <div class="p-2 border border-gray-200 dark:border-white/10 rounded flex justify-between items-center bg-white dark:bg-white/5">
                                 <span class="text-xs font-medium text-gray-700 dark:text-gray-200">Avg. Processing Time</span>
                                 <span class="text-xs font-bold text-gray-900 dark:text-white">2.4 Days</span>
                             </div>
                         </div>
                         
                          <!-- Returns Chart (New) -->
                        <div class="h-40 flex justify-center mt-2 relative">
                             <Doughnut :data="getReturnReasonData(warehouse.id)" :options="{ maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 } } } } }" />
                             <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                                 <span class="text-[10px] font-bold text-gray-400 mt-8">Reasons</span>
                             </div>
                        </div>
                    </div>
                </div>

                 <!-- Footer Actions removed -->
            </div>
        </div>

        <!-- Notification Toast -->
        <div v-if="notification" class="fixed bottom-6 right-6 z-50 animate-fade-in-up transition-all cursor-pointer" @click="notification = null">
            <div class="px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 border backdrop-blur-md bg-blue-50/90 dark:bg-blue-900/90 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-100">
                <span class="material-symbols-outlined text-2xl">info</span>
                <span class="font-bold text-sm">{{ notification }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, PointElement, LineElement, ArcElement)

const store = useLogisticStore()
const timeRange = ref('today')
const activeTab = ref('control_tower')
const notification = ref(null)

// Tabs Structure (Mirrored from Reports.vue)
const tabs = [
    { id: 'control_tower', label: 'Control Tower', icon: 'cell_tower' },
    { id: 'financials', label: 'Finances', icon: 'account_balance' },
    { id: 'attendance', label: 'Attendance', icon: 'calendar_month' },
    { id: 'workforce', label: 'Workforce', icon: 'groups' },
    { id: 'assets', label: 'Inventory', icon: 'inventory_2' },
    { id: 'returns', label: 'Returns', icon: 'assignment_return' },
    // Simplified list for cards, some tabs might be merged or simplified
]

const onDrop = (event) => {
    try {
        const warehouseId = event.dataTransfer.getData('warehouseId')
        if (warehouseId) {
            const id = parseInt(warehouseId) || warehouseId
            const warehouse = store.hubs.find(h => h.id === id)
            
            // Check if already in comparision store
            if (warehouse && !store.comparedWarehouses.find(w => w.id === warehouse.id)) {
                store.comparedWarehouses.push(warehouse)
            }
        }
    } catch (e) {
        console.error("Drop failed", e)
    }
}

const removeWarehouse = (id) => {
    store.comparedWarehouses = store.comparedWarehouses.filter(w => w.id !== id)
}

const downloadReport = (name) => {
    notification.value = `Downloading report for ${name}...`
    setTimeout(() => {
        notification.value = `Report for ${name} downloaded successfully.`
        setTimeout(() => notification.value = null, 3000)
    }, 1500)
}

// --- Real data helpers (per hub) ---

const getHubAlerts = (hubId) => store.alerts

const getHubOrders = (hubId) =>
    store.transactions.filter(t => t.hubId === hubId && t.amount > 0).length

const getHubRevenue = (hubId) =>
    store.transactions
        .filter(t => t.hubId === hubId && t.amount > 0 && t.type !== 'CAPITAL_INVESTMENT')
        .reduce((sum, t) => sum + t.amount, 0)

const getHubPendingCod = (hubId) =>
    store.financeCodRecords
        .filter(r => r.hubId === hubId && r.status === 'Pending')
        .reduce((sum, r) => sum + Number(r.amount || 0), 0)

const getHubDriversList = (hubId) =>
    store.drivers.filter(d => d.hubId === hubId)

const getHubStaff = (hubId) =>
    store.users.filter(u => u.hubId === hubId)

const getHubInactiveStaff = (hubId) =>
    getHubStaff(hubId).filter(u => u.status !== 'Active')

const getAttendanceRate = (warehouse) => {
    if (warehouse.staffTotal == null || warehouse.staffTotal === 0) return null
    return Math.round(((warehouse.staffActive ?? 0) / warehouse.staffTotal) * 100)
}

const getHubReturns = (hubId) =>
    store.returns.filter(r => r.hubId === hubId)

const getHubPendingReturns = (hubId) => {
    const pending = ['Pending', 'Pickup Requested', 'Pickup Approved', 'Pickup Scheduled',
                     'Collected', 'At Warehouse', 'Under Review', 'Physically Inspected']
    return getHubReturns(hubId).filter(r => pending.includes(r.status))
}

const getHubReturnResolutionRate = (hubId) => {
    const all = getHubReturns(hubId)
    if (!all.length) return null
    const resolved = all.filter(r => ['Resolved', 'Completed', 'Closed'].includes(r.status)).length
    return Math.round((resolved / all.length) * 100)
}

// --- Chart data using real store data ---

const getLineChartData = (hubId, label, color = 'blue') => {
    const week = store.dashboardStats.slaCompliance?.week || []
    const data = week.length >= 5
        ? week.slice(-5).map(v => Math.round(Number(v) || 0))
        : [0, 0, 0, 0, 0]
    return {
        labels: ['M', 'T', 'W', 'T', 'F'],
        datasets: [{
            label,
            data,
            borderColor: color === 'purple' ? '#8b5cf6' : color === 'green' ? '#10b981' : '#3b82f6',
            backgroundColor: color === 'purple' ? 'rgba(139, 92, 246, 0.1)' : color === 'green' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 2
        }]
    }
}

const getBarChartData = (hubId) => {
    const txns = store.transactions.filter(t => t.hubId === hubId && t.amount > 0 && t.type !== 'CAPITAL_INVESTMENT')
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const now = new Date()
    const last4 = Array.from({ length: 4 }, (_, i) => {
        const d = new Date(now.getFullYear(), now.getMonth() - 3 + i, 1)
        return { label: monthNames[d.getMonth()], month: d.getMonth(), year: d.getFullYear() }
    })
    const data = last4.map(({ month, year }) =>
        txns.filter(t => { const d = new Date(t.date); return d.getMonth() === month && d.getFullYear() === year })
            .reduce((sum, t) => sum + t.amount, 0)
    )
    return {
        labels: last4.map(m => m.label),
        datasets: [{ label: 'Revenue', data, backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'], borderRadius: 4 }]
    }
}

const getWorkforceData = (hubId) => {
    const hubDrivers = getHubDriversList(hubId)
    const hubStaff = getHubStaff(hubId)
    const adminCount = hubStaff.filter(u =>
        ['Logistic Manager', 'Warehouse Manager', 'Dispatcher'].some(r => u.role?.includes(r))
    ).length
    const warehouseCount = Math.max(0, hubStaff.length - hubDrivers.length - adminCount)
    return {
        labels: ['Warehouse', 'Drivers', 'Admin'],
        datasets: [{
            data: [warehouseCount, hubDrivers.length, adminCount],
            backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981'],
            borderWidth: 0
        }]
    }
}

const getReturnReasonData = (hubId) => {
    const hubReturns = getHubReturns(hubId)
    const reasons = { 'Damaged': 0, 'Wrong Item': 0, 'Other': 0 }
    hubReturns.forEach(r => {
        const reason = (r.reason || '').toLowerCase()
        if (reason.includes('damage')) reasons['Damaged']++
        else if (reason.includes('wrong')) reasons['Wrong Item']++
        else reasons['Other']++
    })
    return {
        labels: Object.keys(reasons),
        datasets: [{ data: Object.values(reasons), backgroundColor: ['#ef4444', '#f59e0b', '#9ca3af'], borderWidth: 0 }]
    }
}

const miniChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
    },
    scales: {
        x: { 
            display: true,
            grid: { display: false },
            ticks: { font: { size: 10 } }
        },
        y: { 
            display: true,
            ticks: { font: { size: 10 } }
        }
    }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.3);
    border-radius: 20px;
}
</style>
