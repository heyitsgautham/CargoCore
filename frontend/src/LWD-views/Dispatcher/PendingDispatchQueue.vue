<template>
    <div class="space-y-6 min-w-0">
        <!-- Header -->
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div class="min-w-0">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Pending Dispatch Queue</h2>
                <p class="text-sm text-gray-400 mt-1">Orders marked "Ready for Dispatch" by Warehouse Manager</p>
            </div>
            <div class="flex flex-wrap items-center gap-2 xl:justify-end">
                <div class="text-[10px] text-gray-500 text-right hidden sm:block">
                    <div>Auto-refreshes every 30s</div>
                    <div v-if="lastRefreshed" class="text-gray-400">Updated {{ lastRefreshed }}</div>
                </div>
                <button @click="manualRefresh" :disabled="refreshing"
                    class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-white/10 py-2 px-3 rounded-lg transition-colors flex items-center gap-1 text-sm font-bold disabled:opacity-50">
                    <span class="material-symbols-outlined text-[18px]" :class="refreshing ? 'animate-spin' : ''">refresh</span>
                </button>
                <button @click="runGlobalFeasibilityCheck"
                    class="bg-yellow-100 dark:bg-yellow-500/15 hover:bg-yellow-200 dark:hover:bg-yellow-500/25 text-yellow-700 dark:text-yellow-400 border border-yellow-300 dark:border-yellow-500/30 py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-bold">
                    <span class="material-symbols-outlined text-[18px]">verified</span> Feasibility Check
                </button>
            </div>
        </div>

        <ReadyDispatchBanner />

        <QueueSummaryCards />

        <QueueFilters />

        <QueueOrdersTable />

        <!-- Global Feasibility Toast -->
        <Teleport to="body">
            <Transition enter-active-class="transition ease-out duration-300" enter-from-class="translate-y-4 opacity-0" enter-to-class="translate-y-0 opacity-100" leave-active-class="transition ease-in duration-200" leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="globalFeasToast" class="fixed bottom-6 right-6 z-[9999] rounded-2xl px-5 py-3 text-sm font-bold shadow-2xl flex items-center gap-2"
                    :class="globalFeasToastType === 'success' ? 'bg-primary text-black' : globalFeasToastType === 'warn' ? 'bg-yellow-400 text-black' : 'bg-red-500 text-white'">
                    <span class="material-symbols-outlined text-[18px]">{{ globalFeasToastType === 'success' ? 'verified' : 'warning' }}</span>
                    {{ globalFeasToast }}
                </div>
            </Transition>
        </Teleport>

        <FeasibilityModal />

    <!-- Assign Driver Modal -->
    <AssignConfirmModal />

    </div>
</template>

<script setup>
import ReadyDispatchBanner from './pendingQueue/ReadyDispatchBanner.vue'
import QueueSummaryCards from './pendingQueue/QueueSummaryCards.vue'
import QueueFilters from './pendingQueue/QueueFilters.vue'
import QueueOrdersTable from './pendingQueue/QueueOrdersTable.vue'
import FeasibilityModal from './pendingQueue/FeasibilityModal.vue'
import AssignConfirmModal from './pendingQueue/AssignConfirmModal.vue'
import {
    deriveFeasibility as deriveOrderFeasibility,
    evaluateDispatchFeasibility as evaluateOrderFeasibility,
    formatCapacityValue,
    formatOrderVolume,
    formatOrderWeight,
    getPriorityClass,
    getTimeRemaining,
    isDeadlineCritical,
    orderAllowsDirectVehicleSelection,
} from './pendingQueue/queueRules'
import { pendingQueuePageKey } from './pendingQueue/pendingQueuePageContext'
import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken } from '@/config/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } : { 'Content-Type': 'application/json' }
}

const store = useDispatcherStore()

function onWarehouseUpdate() {
    store.fetchOrders().catch(() => {})
}

onMounted(() => {
    store.initialize().catch(() => {})
    window.addEventListener('warehouse-orders-updated', onWarehouseUpdate)
})

onUnmounted(() => {
    window.removeEventListener('warehouse-orders-updated', onWarehouseUpdate)
})

const searchQuery = ref('')
const filterPriority = ref('')
const filterWarehouse = ref('')
const filterFeasibility = ref('')
const filterReady = ref(false)
const refreshing = ref(false)
const lastRefreshed = ref('')

async function manualRefresh() {
    refreshing.value = true
    try {
        await store.fetchOrders()
        const now = new Date()
        lastRefreshed.value = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`
    } finally {
        refreshing.value = false
    }
}
const showFeasibilityModal = ref(false)
const feasCheckOrder = ref(null)
const feasibilityToast = ref('')
const showAssignConfirm = ref(false)
const assignConfirmOrder = ref(null)
const assignDriverId = ref('')
const assignVehicleId = ref('')
const assignDrivers = ref([])
const assignVehicles = ref([])
const assignDriversLoading = ref(false)
const assignVehiclesLoading = ref(false)
const isAssigning = ref(false)
const assignError = ref('')
const assignSuccess = ref('')
const globalFeasToast = ref('')
const globalFeasToastType = ref('success')

function showGlobalFeasToast(message, type = 'success') {
    globalFeasToast.value = message
    globalFeasToastType.value = type
    window.clearTimeout(showGlobalFeasToast._timer)
    showGlobalFeasToast._timer = window.setTimeout(() => { globalFeasToast.value = '' }, 3200)
}

const warehouses = computed(() => store.hubs.map(h => h.name))

const pendingOrders = ref([])
const FEASIBILITY_STORAGE_KEY = 'cc_dispatcher_pending_queue_feasibility_v1'

function loadFeasibilityOverrides() {
    if (typeof window === 'undefined') return {}
    try {
        const raw = window.localStorage.getItem(FEASIBILITY_STORAGE_KEY)
        const parsed = raw ? JSON.parse(raw) : {}
        return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (_) {
        return {}
    }
}

const feasibilityOverrides = ref(loadFeasibilityOverrides())

function persistFeasibilityOverrides() {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(FEASIBILITY_STORAGE_KEY, JSON.stringify(feasibilityOverrides.value))
}

function saveFeasibilityOverride(orderId, feasibility, failReason = '') {
    feasibilityOverrides.value = {
        ...feasibilityOverrides.value,
        [String(orderId)]: {
            feasibility,
            failReason,
            updatedAt: new Date().toISOString(),
        },
    }
    persistFeasibilityOverrides()
}

function clearFeasibilityOverride(orderId) {
    const next = { ...feasibilityOverrides.value }
    delete next[String(orderId)]
    feasibilityOverrides.value = next
    persistFeasibilityOverrides()
}

const availableDriversCount = computed(() => store.dispatcherDrivers.filter(driver => {
    const status = String(driver.status || '').toLowerCase()
    return !driver.suspended
        && !driver.maintenance
        && (driver.activeOrders?.length || 0) === 0
        && ['active', 'idle', 'on break', 'on_break'].includes(status)
}).length)

function evaluateDispatchFeasibility(order) {
    return evaluateOrderFeasibility(order, availableDriversCount.value)
}

function deriveFeasibility(order) {
    return deriveOrderFeasibility(order, feasibilityOverrides.value)
}

function hydratePendingOrders(list) {
    pendingOrders.value = list.map(order => {
        const next = { ...order }
        const feasibilityState = deriveFeasibility(next)
        next.feasibility = feasibilityState.feasibility
        next.failReason = feasibilityState.failReason
        return next
    })
}

function applyFeasibilityState(order, feasibility, failReason = '') {
    if (!order) return
    order.feasibility = feasibility
    order.failReason = failReason
    saveFeasibilityOverride(order.id, feasibility, failReason)
}

watch(
    () => [store.pendingOrders, feasibilityOverrides.value],
    ([list]) => {
        hydratePendingOrders(list || [])
    },
    { immediate: true, deep: true }
)

const urgentCount = computed(() => pendingOrders.value.filter(o => o.priority === 'URGENT').length)
const highCount = computed(() => pendingOrders.value.filter(o => o.priority === 'HIGH').length)
const totalWeight = computed(() => pendingOrders.value.reduce((sum, o) => sum + Number(o.weight || 0), 0))
const feasibleCount = computed(() => pendingOrders.value.filter(o => o.feasibility === 'feasible').length)
const readyCount = computed(() => pendingOrders.value.filter(o => o.readyForDispatch).length)

const filteredOrders = computed(() => {
    const list = pendingOrders.value.filter(o => {
        if (filterReady.value && (!o.readyForDispatch || o.loadingInProgress)) return false
        if (searchQuery.value && !o.id.toLowerCase().includes(searchQuery.value.toLowerCase()) && !o.warehouse.toLowerCase().includes(searchQuery.value.toLowerCase())) return false
        if (filterPriority.value && o.priority !== filterPriority.value) return false
        if (filterWarehouse.value && o.warehouse !== filterWarehouse.value) return false
        if (filterFeasibility.value && o.feasibility !== filterFeasibility.value) return false
        return true
    })
    // Ready-for-dispatch orders float to the top
    return [...list].sort((a, b) => (b.readyForDispatch ? 1 : 0) - (a.readyForDispatch ? 1 : 0))
})

function runFeasibilityCheck(order) {
    const next = evaluateDispatchFeasibility(order)
    order.feasibility = next.feasibility
    order.failReason = next.failReason
    feasCheckOrder.value = order
    feasibilityToast.value = ''
    showFeasibilityModal.value = true
}

function runGlobalFeasibilityCheck() {
    pendingOrders.value.forEach(o => {
        const next = evaluateDispatchFeasibility(o)
        o.feasibility = next.feasibility
        o.failReason = next.failReason
    })
    const feasible = pendingOrders.value.filter(o => o.feasibility === 'feasible').length
    const infeasible = pendingOrders.value.filter(o => o.feasibility === 'infeasible').length
    const unchecked = pendingOrders.value.filter(o => o.feasibility === 'unchecked').length
    const total = pendingOrders.value.length
    if (total === 0) {
        showGlobalFeasToast('No pending orders to check', 'warn')
    } else if (infeasible === 0 && unchecked === 0) {
        showGlobalFeasToast(`All ${feasible} order${feasible > 1 ? 's' : ''} feasible`, 'success')
    } else if (feasible === 0 && unchecked === 0) {
        showGlobalFeasToast(`${infeasible} order${infeasible > 1 ? 's' : ''} not feasible`, 'error')
    } else {
        const parts = []
        if (feasible) parts.push(`${feasible} feasible`)
        if (infeasible) parts.push(`${infeasible} blocked`)
        if (unchecked) parts.push(`${unchecked} unchecked`)
        showGlobalFeasToast(parts.join(' · '), infeasible > 0 ? 'warn' : 'success')
    }
}

function approveAndAssign() {
    if (feasCheckOrder.value) {
        clearFeasibilityOverride(feasCheckOrder.value.id)
        const next = deriveFeasibility(feasCheckOrder.value)
        feasCheckOrder.value.feasibility = next.feasibility
        feasCheckOrder.value.failReason = next.failReason
        feasibilityToast.value = `✓ ${feasCheckOrder.value.id} — Assigned to next available driver`
        setTimeout(() => {
            const idx = pendingOrders.value.findIndex(o => o.id === feasCheckOrder.value.id)
            if (idx > -1) pendingOrders.value.splice(idx, 1)
            showFeasibilityModal.value = false
        }, 1200)
    }
}

function holdFeasOrder() {
    if (feasCheckOrder.value) {
        applyFeasibilityState(feasCheckOrder.value, 'infeasible', 'On Hold')
        feasibilityToast.value = `⏸ ${feasCheckOrder.value.id} — Hold placed`
        setTimeout(() => { showFeasibilityModal.value = false }, 1000)
    }
}

function escalateFeasOrder() {
    if (feasCheckOrder.value) {
        feasibilityToast.value = `⬆ ${feasCheckOrder.value.id} — Escalated to Manager`
        setTimeout(() => { showFeasibilityModal.value = false }, 1000)
    }
}

async function assignDriver(order) {
    assignConfirmOrder.value = order
    assignDriverId.value = ''
    assignVehicleId.value = ''
    assignError.value = ''
    assignSuccess.value = ''
    showAssignConfirm.value = true
    // Fetch drivers, vehicles, and active orders to filter out busy ones
    assignDriversLoading.value = true
    assignVehiclesLoading.value = true
    try {
        const warehouseId = assignConfirmOrder.value?.warehouseId
        const fetches = [
            fetch(`${API_BASE}/api/v1/logistics/drivers`, { headers: authHeaders() }),
            fetch(`${API_BASE}/api/v1/logistics/vehicles`, { headers: authHeaders() }),
            fetch(`${API_BASE}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: authHeaders() }),
        ]
        if (warehouseId) {
            fetches.push(fetch(`${API_BASE}/api/v1/warehouses/${warehouseId}/operations/loading-docks`, { headers: authHeaders() }))
        }
        const [dRes, vRes, aRes, tRes, docksRes] = await Promise.all(fetches)
        const allDrivers = dRes.ok ? await dRes.json() : []
        const allVehicles = vRes.ok ? await vRes.json() : []
        const assignedOrders = aRes.ok ? await aRes.json() : []
        const transitOrders = tRes.ok ? await tRes.json() : []
        const activeOrders = [...(Array.isArray(assignedOrders) ? assignedOrders : assignedOrders.items || []), ...(Array.isArray(transitOrders) ? transitOrders : transitOrders.items || [])]

        // Drivers already on an active order OR suspended/off-duty
        const busyDriverIds = new Set(activeOrders.map(o => String(o.assigned_driver_id)).filter(Boolean))
        assignDrivers.value = allDrivers.filter(d => {
            const status = (d.status || '').toLowerCase()
            return !busyDriverIds.has(String(d.id)) &&
                !store.isDriverSuspended(String(d.id)) &&
                status !== 'suspended' &&
                status !== 'off-duty'  // driver has ended their shift — not available
        })

        // Vehicle already assigned to this order (set by warehouse at loading dock)
        const preAssignedVehicleId = assignConfirmOrder.value?.vehicleId
            ? String(assignConfirmOrder.value.vehicleId) : null

        // Collect vehicles on occupied docks (still loading, not yet released)
        const docksData = docksRes?.ok ? await docksRes.json() : null
        const dockedVehicleIds = new Set(
            (docksData?.items || [])
                .filter(d => d.status === 'OCCUPIED' && d.assigned_vehicle_id)
                .map(d => String(d.assigned_vehicle_id))
        )

        // Vehicles already committed to another ASSIGNED/IN_TRANSIT order — exclude these
        const busyVehicleIds = new Set(activeOrders.map(o => String(o.assigned_vehicle_id)).filter(Boolean))

        // If warehouse already picked a vehicle for this order, show ONLY that vehicle (locked)
        const vehicleArr = Array.isArray(allVehicles) ? allVehicles : (allVehicles.items || [])
        let dispatchable
        if (preAssignedVehicleId) {
            // Warehouse pre-selected via loading dock — restrict to just that vehicle
            const v = vehicleArr.find(v => String(v.id) === preAssignedVehicleId)
            dispatchable = v ? [v] : []
            assignVehicleId.value = preAssignedVehicleId
        } else if (orderAllowsDirectVehicleSelection(assignConfirmOrder.value)) {
            // Service moves and return pickups can be dispatched directly by the dispatcher.
            dispatchable = vehicleArr.filter(v => !busyVehicleIds.has(String(v.id)) && !dockedVehicleIds.has(String(v.id)))
        } else {
            // No vehicle assigned by warehouse (small parcel / no loading dock) —
            // dispatcher cannot select a vehicle; WM must assign one via loading dock
            dispatchable = []
        }

        assignVehicles.value = dispatchable
    } catch (_) {
        assignDrivers.value = []
        assignVehicles.value = []
    } finally {
        assignDriversLoading.value = false
        assignVehiclesLoading.value = false
    }
}

async function confirmAssign() {
    if (!assignConfirmOrder.value || !assignDriverId.value) return
    isAssigning.value = true
    assignError.value = ''
    assignSuccess.value = ''
    try {
        const body = { driver_id: assignDriverId.value }
        if (assignVehicleId.value) body.vehicle_id = assignVehicleId.value
        const res = await fetch(`${API_BASE}/api/v1/orders/${assignConfirmOrder.value.id}/assign`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        if (res.ok) {
            assignSuccess.value = `✓ Order assigned successfully`
            setTimeout(() => {
                clearFeasibilityOverride(assignConfirmOrder.value.id)
                const idx = pendingOrders.value.findIndex(o => o.id === assignConfirmOrder.value.id)
                if (idx > -1) pendingOrders.value.splice(idx, 1)
                showAssignConfirm.value = false
                store.fetchOrders().catch(() => {})
            }, 900)
        } else {
            const err = await res.json().catch(() => ({}))
            assignError.value = err.detail || 'Assignment failed. Please try again.'
        }
    } catch (_) {
        assignError.value = 'Network error. Please try again.'
    } finally {
        isAssigning.value = false
    }
}

function escalateOrder(order) {
    order.priority = order.priority === 'URGENT' ? 'NORMAL' : 'URGENT'
}

function holdOrder(order) {
    applyFeasibilityState(order, 'infeasible', 'On Hold')
}

provide(pendingQueuePageKey, {
    approveAndAssign,
    assignConfirmOrder,
    assignDriver,
    assignDriverId,
    assignDrivers,
    assignDriversLoading,
    assignError,
    assignSuccess,
    assignVehicleId,
    assignVehicles,
    assignVehiclesLoading,
    confirmAssign,
    escalateFeasOrder,
    escalateOrder,
    feasCheckOrder,
    feasibilityToast,
    feasibleCount,
    filterFeasibility,
    filterPriority,
    filterReady,
    filterWarehouse,
    filteredOrders,
    formatCapacityValue,
    formatOrderVolume,
    formatOrderWeight,
    getPriorityClass,
    getTimeRemaining,
    highCount,
    holdFeasOrder,
    holdOrder,
    isAssigning,
    isDeadlineCritical,
    orderAllowsDirectVehicleSelection,
    pendingOrders,
    readyCount,
    runFeasibilityCheck,
    searchQuery,
    showAssignConfirm,
    showFeasibilityModal,
    totalWeight,
    urgentCount,
    warehouses,
})
</script>
