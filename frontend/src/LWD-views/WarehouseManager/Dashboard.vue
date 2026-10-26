<template>
    <div class="space-y-6">
        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center h-64">
            <div class="text-gray-500 dark:text-gray-400">Loading dashboard data...</div>
        </div>

        <div v-else class="space-y-6">
            <WarehouseKpiCards />

        <WarehouseTrendChart />

        <WarehouseMiniCharts />

        <!-- Main Content Split -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <PickingQueueTable />

            <LaborFloorPanel />
        </div>
        </div>

        <RestockModal />

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
import WarehouseKpiCards from './dashboard/WarehouseKpiCards.vue'
import WarehouseTrendChart from './dashboard/WarehouseTrendChart.vue'
import WarehouseMiniCharts from './dashboard/WarehouseMiniCharts.vue'
import PickingQueueTable from './dashboard/PickingQueueTable.vue'
import LaborFloorPanel from './dashboard/LaborFloorPanel.vue'
import RestockModal from './dashboard/RestockModal.vue'
import { barOptions, doughnutOptions, lineChartOptions, pieOptions } from './dashboard/chartOptions'
import { buildFallbackDashboard } from './dashboard/dashboardFallback'
import { wmDashboardPageKey } from './dashboard/wmDashboardPageContext'
import { API_BASE_URL } from '@/config/api'
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
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
        fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/kpis`, { headers }),
        fetch(`${API_BASE_URL}/api/v1/inventory?page=1&page_size=100`, { headers }),
        fetch(`${API_BASE_URL}/api/v1/orders?page=1&page_size=100`, { headers }),
        fetch(`${API_BASE_URL}/api/v1/labourers?page=1&page_size=100`, { headers })
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

    return buildFallbackDashboard({ kpis, inventoryItems, warehouseOrders, labourers })
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

        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/dashboard`, {
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
        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/orders/${order.order_id}/complete`, {
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
        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/orders/${order.order_id}/reassign`, {
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

        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/restock`, {
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

provide(wmDashboardPageKey, {
    activeActionMenu,
    activeLabor,
    activeStaffData,
    avgPickTime,
    barOptions,
    criticalSkus,
    doughnutOptions,
    efficiencyInsight,
    filteredQueue,
    formatLargeNumber,
    inventoryValueChangePercent,
    isProcessingRestock,
    laborChartData,
    lineChartOptions,
    markComplete,
    nextTruckMinutes,
    ordersReturnsData,
    pendingOrdersCount,
    pieOptions,
    processRestock,
    readyForDispatch,
    reassign,
    recentReturns,
    searchQuery,
    showRestockModal,
    statusFilter,
    stockPackagingData,
    throughputChartData,
    throughputChartKey,
    toggleActionMenu,
    totalInventoryValue,
    totalLabor,
})
</script>
