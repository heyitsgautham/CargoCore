<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Order Status Control</h2>
                <p class="text-sm text-gray-400 mt-1">Track and control order lifecycle — Ready → Dispatched → In Transit (Completion by Driver PoD)</p>
            </div>
            <div class="flex gap-2">
                <select v-model="statusFilter" class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white text-sm">
                    <option class="bg-white dark:bg-gray-800" value="">All Statuses</option>
                    <option class="bg-white dark:bg-gray-800" value="ready">Ready for Dispatch</option>
                    <option class="bg-white dark:bg-gray-800" value="dispatched">Dispatched</option>
                    <option class="bg-white dark:bg-gray-800" value="in-transit">In Transit</option>
                    <option class="bg-white dark:bg-gray-800" value="delivered">Delivered (PoD)</option>
                </select>
                <button @click="syncStatus" class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors text-sm">
                    <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': syncing }">refresh</span> {{ syncing ? 'Syncing...' : syncDone ? '✓ Synced' : 'Sync Status' }}
                </button>
            </div>
        </div>

        <StatusPipeline />

        <SlaComplianceCards />

        <OrderStatusTable />

        <SlaAlerts />

        <!-- PoD Modal -->
        <AssignVehicleModal />

        <ProofOfDeliveryModal />

        <OrderStatusModal />
    </div>
</template>

<script setup>
import StatusPipeline from './orderStatus/StatusPipeline.vue'
import SlaComplianceCards from './orderStatus/SlaComplianceCards.vue'
import OrderStatusTable from './orderStatus/OrderStatusTable.vue'
import SlaAlerts from './orderStatus/SlaAlerts.vue'
import AssignVehicleModal from './orderStatus/AssignVehicleModal.vue'
import ProofOfDeliveryModal from './orderStatus/ProofOfDeliveryModal.vue'
import OrderStatusModal from './orderStatus/OrderStatusModal.vue'
import { toUiOrder } from './orderStatus/orderRows'
import { orderStatusPageKey } from './orderStatus/orderStatusPageContext'
import { ref, computed, watch, onMounted, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken } from '@/config/api'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useToast } from '@/composables/useToast'
import { useOrderActions } from './orderStatus/useOrderActions'
import { useStatusTransitions } from './orderStatus/useStatusTransitions'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const store = useDispatcherStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()
const toast = useToast()
onMounted(async () => {
    await store.initialize().catch(() => {})
    await store.fetchActiveOrders().catch(() => {})
})

const searchQuery = ref('')
const statusFilter = ref('')
const syncing = ref(false)
const syncDone = ref(false)
const showPoD = ref(false)
const podOrder = ref(null)
const podLoading = ref(false)
const podError = ref('')
const orderMenu = ref(null)
const showActionModal = ref(false)
const actionSubmitting = ref(false)
const actionModal = ref({
    type: 'cancel',
    order: null,
    reason: '',
    error: '',
})
const alertResolved = ref({})
const actionPending = ref({})
const transitionPending = ref({})
const bulkUpdating = ref(false)
const selectedOrderIds = ref(new Set())

// ── Assign Vehicle Modal ────────────────────────────────────────────────────
const showAssignVehicleModal = ref(false)
const assignVehicleOrder = ref(null)
const assignVehicleSelected = ref('')
const assignVehicleOptions = ref([])
const assignVehicleLoading = ref(false)
const assignVehicleSaving = ref(false)
const assignVehicleError = ref('')
const assignVehicleSuccess = ref('')

function authHeaders() {
    const token = getStoredAccessToken()
    return token
        ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
        : { 'Content-Type': 'application/json' }
}

async function openAssignVehicle(order) {
    assignVehicleOrder.value = order
    assignVehicleSelected.value = ''
    assignVehicleError.value = ''
    assignVehicleSuccess.value = ''
    showAssignVehicleModal.value = true
    assignVehicleLoading.value = true
    try {
        // Fetch all vehicles and active orders to exclude busy vehicles
        const [vRes, aRes, tRes] = await Promise.all([
            fetch(`${API_BASE}/api/v1/logistics/vehicles`, { headers: authHeaders() }),
            fetch(`${API_BASE}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: authHeaders() }),
        ])
        const allVehicles = vRes.ok ? await vRes.json() : []
        const assigned = aRes.ok ? await aRes.json() : []
        const transit = tRes.ok ? await tRes.json() : []
        const activeOrders = [
            ...(Array.isArray(assigned) ? assigned : assigned.items || []),
            ...(Array.isArray(transit) ? transit : transit.items || []),
        ]
        // Exclude vehicles already committed to another order (not this one)
        const busyVehicleIds = new Set(
            activeOrders
                .filter(o => String(o.id) !== String(order.backendId || order.id))
                .map(o => String(o.assigned_vehicle_id))
                .filter(Boolean)
        )
        const vehicleArr = Array.isArray(allVehicles) ? allVehicles : (allVehicles.items || [])
        assignVehicleOptions.value = vehicleArr.filter(v =>
            !busyVehicleIds.has(String(v.id)) &&
            (v.status === 'Active' || v.status === 'active')
        )
    } catch (_) {
        assignVehicleOptions.value = []
    } finally {
        assignVehicleLoading.value = false
    }
}

async function confirmAssignVehicle() {
    if (!assignVehicleOrder.value || !assignVehicleSelected.value) return
    assignVehicleSaving.value = true
    assignVehicleError.value = ''
    assignVehicleSuccess.value = ''
    try {
        const orderId = assignVehicleOrder.value.backendId || assignVehicleOrder.value.id
        const body = {
            vehicle_id: assignVehicleSelected.value,
            driver_id: assignVehicleOrder.value.driverId,   // keep the existing driver
        }
        const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/assign`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        if (res.ok) {
            assignVehicleSuccess.value = '✓ Vehicle assigned successfully'
            setTimeout(async () => {
                showAssignVehicleModal.value = false
                await store.fetchActiveOrders().catch(() => {})
            }, 800)
        } else {
            const err = await res.json().catch(() => ({}))
            assignVehicleError.value = err.detail || 'Failed to assign vehicle. Please try again.'
        }
    } catch (_) {
        assignVehicleError.value = 'Network error. Please try again.'
    } finally {
        assignVehicleSaving.value = false
    }
}
const selectAllCheckbox = ref(null)

const orders = ref([])

watch(() => store.activeOrders, (list) => {
    const currentSelection = new Set(selectedOrderIds.value)
    orders.value = list.map(toUiOrder)
    const activeIds = new Set(orders.value.map(order => getOrderKey(order)))
    selectedOrderIds.value = new Set([...currentSelection].filter(id => activeIds.has(id)))
}, { immediate: true })

const readyCount = computed(() => orders.value.filter(o => o.status === 'ready').length)
const dispatchedCount = computed(() => orders.value.filter(o => o.status === 'dispatched').length)
const inTransitCount = computed(() => orders.value.filter(o => o.status === 'in-transit').length)
const deliveredCount = computed(() => orders.value.filter(o => o.status === 'delivered').length)
const overdueOrders = computed(() => orders.value.filter(o => o.etaOverdue || o.slaStatus === 'ESCALATED'))
const overdueCount = computed(() => overdueOrders.value.length)
const podPhotos = computed(() => Array.isArray(podOrder.value?.pod?.photos) ? podOrder.value.pod.photos : [])
const podPhotoCount = computed(() => podPhotos.value.length)

const statusTabs = computed(() => [
    { label: 'All', value: '', count: orders.value.length, activeClass: 'bg-white/10 text-gray-900 dark:text-white' },
    { label: 'Ready', value: 'ready', count: readyCount.value, activeClass: 'bg-yellow-500/20 text-yellow-400' },
    { label: 'Dispatched', value: 'dispatched', count: dispatchedCount.value, activeClass: 'bg-blue-500/20 text-blue-400' },
    { label: 'In Transit', value: 'in-transit', count: inTransitCount.value, activeClass: 'bg-purple-500/20 text-purple-400' },
    { label: 'Delivered', value: 'delivered', count: deliveredCount.value, activeClass: 'bg-green-500/20 text-green-400' },
])

const filteredOrders = computed(() => {
    return orders.value.filter(o => {
        if (statusFilter.value && o.status !== statusFilter.value) return false
        if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase()
            const matchesId = o.id?.toLowerCase().includes(q)
            const matchesBackendId = o.backendId?.toLowerCase().includes(q)
            const matchesDriver = o.driver?.toLowerCase().includes(q)
            if (!matchesId && !matchesBackendId && !matchesDriver) return false
        }
        return true
    })
})

const selectedOrders = computed(() => orders.value.filter(order => selectedOrderIds.value.has(getOrderKey(order))))
const selectedReadyOrders = computed(() => selectedOrders.value.filter(order => order.status === 'ready'))
const selectedDispatchableReadyOrders = computed(() => selectedReadyOrders.value.filter(order => canDispatchOrder(order)))
const selectedDispatchedOrders = computed(() => selectedOrders.value.filter(order => order.status === 'dispatched'))
const selectedTransitOrders = computed(() => selectedOrders.value.filter(order => order.status === 'in-transit'))
const visibleSelectableOrders = computed(() => filteredOrders.value.filter(order => isSelectableOrder(order)))
const allVisibleSelected = computed(() =>
    visibleSelectableOrders.value.length > 0 &&
    visibleSelectableOrders.value.every(order => selectedOrderIds.value.has(getOrderKey(order)))
)
const someVisibleSelected = computed(() =>
    visibleSelectableOrders.value.some(order => selectedOrderIds.value.has(getOrderKey(order)))
)

watch([allVisibleSelected, someVisibleSelected], ([allSelected, partiallySelected]) => {
    if (!selectAllCheckbox.value) return
    selectAllCheckbox.value.indeterminate = !allSelected && partiallySelected
})

function getOrderKey(order) {
    return String(order?.backendId || order?.id || '')
}

function clearSelection(orderIds = null) {
    if (!orderIds) {
        selectedOrderIds.value = new Set()
        return
    }
    const next = new Set(selectedOrderIds.value)
    orderIds.forEach(id => next.delete(String(id)))
    selectedOrderIds.value = next
}

function isOrderSelected(order) {
    return selectedOrderIds.value.has(getOrderKey(order))
}

function canDispatchOrder(order) {
    return order.status === 'ready' && Boolean(order.driverId)
}

function isSelectableOrder(order) {
    if (order.status === 'ready') return canDispatchOrder(order) && !isTransitionPending(order)
    return ['dispatched', 'in-transit'].includes(order.status) && !isTransitionPending(order)
}

function toggleOrderSelection(order, checked) {
    const key = getOrderKey(order)
    const next = new Set(selectedOrderIds.value)
    if (checked) next.add(key)
    else next.delete(key)
    selectedOrderIds.value = next
}

function toggleSelectAllVisible(event) {
    const checked = Boolean(event?.target?.checked)
    const next = new Set(selectedOrderIds.value)
    visibleSelectableOrders.value.forEach(order => {
        const key = getOrderKey(order)
        if (checked) next.add(key)
        else next.delete(key)
    })
    selectedOrderIds.value = next
}

function getStatusDotClass(status) {
    const map = { 'ready': 'bg-yellow-500', 'dispatched': 'bg-blue-500', 'in-transit': 'bg-purple-500 animate-pulse', 'delivered': 'bg-green-500' }
    return map[status] || 'bg-gray-500'
}

function getStatusTextClass(status) {
    const map = { 'ready': 'text-yellow-400', 'dispatched': 'text-blue-400', 'in-transit': 'text-purple-400', 'delivered': 'text-green-400' }
    return map[status] || 'text-gray-400'
}

const { isTransitionPending, updateStatus, applyBulkStatus } = useStatusTransitions({
    API_BASE,
    bulkUpdating,
    canDispatchOrder,
    clearSelection,
    getOrderKey,
    selectedDispatchableReadyOrders,
    selectedDispatchedOrders,
    selectedTransitOrders,
    store,
    toast,
    transitionPending,
})

async function syncStatus() {
    syncing.value = true
    try {
        await store.fetchActiveOrders()
    } catch (_) {}
    syncing.value = false
    syncDone.value = true
    setTimeout(() => { syncDone.value = false }, 2000)
}

async function viewPoD(order) {
    podOrder.value = order
    podError.value = ''
    podLoading.value = true
    showPoD.value = true

    try {
        const orderId = order.backendId || order.id
        if (!orderId) throw new Error('Order ID missing for POD lookup.')
        const detailedOrder = await store.fetchOrderDetail(orderId)
        podOrder.value = toUiOrder(detailedOrder)
    } catch (error) {
        podError.value = error instanceof Error ? error.message : 'Unable to load proof of delivery.'
    } finally {
        podLoading.value = false
    }
}

const {
    toggleOrderMenu,
    isActionPending,
    canCancelOrder,
    canEscalateOrder,
    hasMenuActions,
    closeActionModal,
    cancelOrder,
    escalateOrder,
    submitActionModal,
} = useOrderActions({
    API_BASE,
    actionModal,
    actionPending,
    actionSubmitting,
    orderMenu,
    orders,
    showActionModal,
    store,
    toast,
})

function resolveAlert(orderId) {
    alertResolved.value[orderId] = true
    const order = orders.value.find(o => o.id === orderId || o.backendId === orderId)
    if (order && order.status === 'ready') {
        updateStatus(order, 'dispatched')
        order.driver = 'Auto-assigned'
        order.vehicle = 'Van T-20'
    }
}

provide(orderStatusPageKey, {
    actionModal,
    actionSubmitting,
    alertResolved,
    allVisibleSelected,
    applyBulkStatus,
    assignVehicleError,
    assignVehicleLoading,
    assignVehicleOptions,
    assignVehicleOrder,
    assignVehicleSaving,
    assignVehicleSelected,
    assignVehicleSuccess,
    authStore,
    bulkUpdating,
    canCancelOrder,
    canDispatchOrder,
    canEscalateOrder,
    cancelOrder,
    clearSelection,
    closeActionModal,
    confirmAssignVehicle,
    deliveredCount,
    dispatchedCount,
    escalateOrder,
    filteredOrders,
    getStatusDotClass,
    getStatusTextClass,
    hasMenuActions,
    inTransitCount,
    isActionPending,
    isOrderSelected,
    isSelectableOrder,
    isTransitionPending,
    openAssignVehicle,
    openSlipWithData,
    orderMenu,
    orders,
    overdueCount,
    overdueOrders,
    podError,
    podLoading,
    podOrder,
    podPhotoCount,
    podPhotos,
    readyCount,
    resolveAlert,
    searchQuery,
    selectAllCheckbox,
    selectedDispatchableReadyOrders,
    selectedDispatchedOrders,
    selectedOrders,
    selectedTransitOrders,
    showActionModal,
    showAssignVehicleModal,
    showPoD,
    statusFilter,
    statusTabs,
    submitActionModal,
    toggleOrderMenu,
    toggleOrderSelection,
    toggleSelectAllVisible,
    updateStatus,
    viewPoD,
    visibleSelectableOrders,
})
</script>
