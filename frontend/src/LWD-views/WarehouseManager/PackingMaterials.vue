<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Packing Materials & Returnable Assets</h2>
                <div class="flex items-center gap-1.5 mt-0.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                    <span class="text-xs text-green-600 dark:text-green-400 font-medium">Live · auto-refreshes every 30s</span>
                </div>
            </div>
            <div class="flex gap-2">
                <button @click="showIssueModal = true"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">output</span> Issue to Order
                </button>
                <button @click="showRestockModal = true"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">add</span> Request Restock
                </button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading packing materials...</div>
        </div>

        <template v-else>
        <MaterialStockCards />

        <MaterialsWorkspace />
        </template>

        <IssueMaterialsModal />

        <RestockMaterialsModal />

        <!-- Toasts -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
        <div v-if="errorMsg"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">error</span>
            <div class="font-bold">{{ errorMsg }}</div>
        </div>
        <div v-if="escalateMsg"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">arrow_upward</span>
            <div>
                <div class="font-bold">Escalated to Logistics Manager!</div>
                <div class="text-xs opacity-80">{{ escalateMsg }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import MaterialStockCards from './packingMaterials/MaterialStockCards.vue'
import MaterialsWorkspace from './packingMaterials/MaterialsWorkspace.vue'
import IssueMaterialsModal from './packingMaterials/IssueMaterialsModal.vue'
import RestockMaterialsModal from './packingMaterials/RestockMaterialsModal.vue'
import {
    getEmoji,
    mergeIssuanceLogs,
    normalizeIssuanceLog,
    readCachedIssuanceLogs,
    writeCachedIssuanceLogs,
} from './packingMaterials/materialRecords'
import { packingMaterialsPageKey } from './packingMaterials/packingMaterialsPageContext'
import { ref, computed, reactive, onMounted, onUnmounted, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import { getEffectiveWarehouseSubstatus } from '@/utils/warehouseOrderState'
import { useIssueOrderSelection } from './packingMaterials/useIssueOrderSelection'
import { useIssueSubmit } from './packingMaterials/useIssueSubmit'
import { useRestockRequest } from './packingMaterials/useRestockRequest'

const authStore = useAuthStore()

const logTab = ref('issued')
const showIssueModal = ref(false)
const showRestockModal = ref(false)
const toastMsg = ref('')
const escalateMsg = ref('')
const errorMsg = ref('')
const loading = ref(false)
const issuingMaterials = ref(false)
const restocking = ref(false)

const issueForm = reactive({ orderId: '', issuedToLabourerId: '', items: {} })
const restockForm = reactive({})
const selectedOrderDetails = ref(null)
const recommendedMaterials = ref([])

// Live data
const allInventory = ref([])
const activeOrders = ref([])
const labourers = ref([])
const issuanceLogs = ref([])
const returnableAssets = ref([])
const ELIGIBLE_ISSUANCE_SUBSTATUSES = new Set(['ON_HOLD', 'AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING'])

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
}

// Filter inventory to packing-related items (category or name match)
const packingItems = computed(() => {
    const packingKeywords = ['pack', 'wrap', 'box', 'carton', 'tape', 'label', 'blanket', 'crate', 'film', 'pallet', 'protector', 'bag', 'rope', 'bubble', 'foam', 'sheet']
    const items = allInventory.value.filter(item => {
        const text = ((item.name || '') + (item.category || '') + (item.product_category || '')).toLowerCase()
        return packingKeywords.some(kw => text.includes(kw))
    })
    // If no matches, show all inventory
    const source = items.length > 0 ? items : allInventory.value.slice(0, 12)
    return source.map(item => {
        const stock = item.quantity_on_hand || item.quantity || item.stock_quantity || item.quantity_available || 0
        const threshold = item.safety_stock || item.minimum_stock_level || item.reorder_point || Math.max(10, Math.floor(stock * 0.3))
        const max = item.max_capacity || item.maximum_stock || Math.max(stock * 2, threshold * 3, 1)
        return {
            id: item.id,
            sku: item.sku || item.id?.slice(0, 8).toUpperCase(),
            name: item.name || item.product_name || 'Item',
            emoji: getEmoji(item.name, item.category),
            stock,
            max,
            threshold,
            unit: item.unit || item.unit_of_measure || 'pcs',
        }
    })
})

const lowStockItems = computed(() => {
    const items = packingItems.value.filter(i => i.stock <= i.threshold)
    items.forEach(i => { if (!restockForm[i.id]) restockForm[i.id] = i.threshold * 2 })
    return items
})

const filteredLog = computed(() => issuanceLogs.value.filter(l => l.type === logTab.value))

// Tracking codes of orders that have already had materials issued
const issuedOrderTrackingCodes = computed(() => {
    return new Set(
        issuanceLogs.value
            .filter(l => l.type === 'issued')
            .map(l => l.orderId)
            .filter(id => id && id !== 'N/A')
    )
})

// Only show orders that haven't had materials issued yet
const ordersAvailableForIssuance = computed(() => {
    const warehouseId = getWarehouseId()
    return activeOrders.value.filter(order => {
        const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
        const needsPackingMaterials = Number(order.materials_amount ?? 0) > 0
        const notIssuedYet = !issuedOrderTrackingCodes.value.has(order.tracking_code)
        return ELIGIBLE_ISSUANCE_SUBSTATUSES.has(substatus) && needsPackingMaterials && notIssuedYet
    })
})

// Filter laborers by availability status
const availableLabourers = computed(() => {
    return labourers.value.filter(l => l.status === 'AVAILABLE')
})

const orderAssignedLabourers = computed(() => {
    return labourers.value.filter(l => l.status === 'ASSIGNED' && l.assigned_order_tracking === issueForm.orderId)
})

const issuableLabourers = computed(() => {
    const byId = new Map()
    for (const labourer of orderAssignedLabourers.value) byId.set(String(labourer.id), labourer)
    for (const labourer of availableLabourers.value) byId.set(String(labourer.id), labourer)
    return [...byId.values()]
})

const selectedIssuingLabourer = computed(() => {
    const selectedId = String(issueForm.issuedToLabourerId || '')
    if (!selectedId) return null
    return issuableLabourers.value.find(labourer => String(labourer.id) === selectedId) || null
})

function labourerIssueLabel(labourer) {
    if (labourer.assigned_order_tracking === issueForm.orderId) return 'Assigned to this order'
    return labourer.role || labourer.designation || 'Available Labourer'
}

function issuableItemsForSelectedOrder() {
    const byId = new Map(packingItems.value.map(item => [String(item.id), item]))
    for (const item of recommendedMaterials.value) {
        byId.set(String(item.id), item)
    }
    return [...byId.values()]
}

// Validation: check if any item qty exceeds available stock
const issueValidationErrors = computed(() => {
    const errors = []
    for (const item of issuableItemsForSelectedOrder()) {
        const qty = issueForm.items[item.id]
        if (qty && qty > 0 && qty > item.stock) {
            errors.push(`${item.name}: requested ${qty}, only ${item.stock} available`)
        }
    }
    return errors
})

const canSubmitIssue = computed(() => {
    if (!issueForm.orderId || !issueForm.issuedToLabourerId) return false
    if (issueValidationErrors.value.length > 0) return false
    // At least one item must be issued
    const hasItems = issuableItemsForSelectedOrder().some(item => {
        const qty = issueForm.items[item.id]
        return qty && qty > 0
    })
    return hasItems
})

const { onOrderSelected, applyRecommendedQuantities, closeIssueModal } = useIssueOrderSelection({
    activeOrders,
    allInventory,
    authStore,
    issueForm,
    packingItems,
    recommendedMaterials,
    selectedOrderDetails,
    showIssueModal,
    showSuccess,
})

async function fetchData() {
    loading.value = true
    try {
        await authStore.ensureWarehouseContext()
        const warehouseId = getWarehouseId()
        const cachedIssuanceLogs = readCachedIssuanceLogs(warehouseId)
        issuanceLogs.value = cachedIssuanceLogs
        
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        const [inventoryRes, ordersRes, labourRes, movementsRes, returnsRes] = await Promise.allSettled([
            fetch(apiUrl(`api/v1/inventory?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            fetch(apiUrl('api/v1/orders?page=1&page_size=100'), { headers }),
            fetch(apiUrl(`api/v1/labourers?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            fetch(apiUrl(`api/v1/inventory/movements?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            warehouseId ? fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/returns?page=1&page_size=20`), { headers }) : Promise.resolve({ ok: false })
        ])

        if (inventoryRes.status === 'fulfilled' && inventoryRes.value.ok) {
            const data = await inventoryRes.value.json()
            allInventory.value = data.items || data || []
        }

        if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
            const data = await ordersRes.value.json()
            activeOrders.value = (data.items || []).filter(order => {
                const sameWarehouse = warehouseId ? order.warehouse_id === warehouseId : true
                return sameWarehouse && ['CONFIRMED', 'ASSIGNED', 'IN_TRANSIT'].includes(order.status)
            })
        }

        if (labourRes.status === 'fulfilled' && labourRes.value.ok) {
            const data = await labourRes.value.json()
            labourers.value = data.items || []
        }

        // Load issuance logs from inventory movements (ISSUE, PACK, RESERVED types)
        if (movementsRes.status === 'fulfilled') {
            if (movementsRes.value.ok) {
                const data = await movementsRes.value.json()
                const movements = Array.isArray(data) ? data : (data.items || [])
                const movementLogs = movements
                    .filter(m => {
                        const t = (m.movement_type || '').toUpperCase()
                        return t === 'ISSUE' || t === 'RESERVED' || t === 'PACK'
                    })
                    .map(m => normalizeIssuanceLog(m))

                issuanceLogs.value = mergeIssuanceLogs(movementLogs, cachedIssuanceLogs)
                writeCachedIssuanceLogs(warehouseId, issuanceLogs.value)
            } else {
                const errorText = await movementsRes.value.text()
                console.error('Failed to load movements:', errorText)
                if (cachedIssuanceLogs.length === 0) {
                    showError('Failed to load issuance logs. Please check your permissions.')
                }
            }
        } else if (movementsRes.status === 'rejected') {
            console.error('Error loading movements:', movementsRes.reason)
            if (cachedIssuanceLogs.length === 0) {
                showError('Error loading issuance logs. Please try again.')
            }
        }

        // Load returnable assets from returns endpoint
        if (returnsRes.status === 'fulfilled' && returnsRes.value && returnsRes.value.ok) {
            const data = await returnsRes.value.json()
            returnableAssets.value = (data.items || []).map(r => ({
                id: r.id,
                name: r.rma_code || 'Return Item',
                orderId: r.order_tracking || r.order_id?.slice(0, 8) || 'N/A',
                qty: 1,
                returned: r.status === 'COMPLETED' ? 1 : 0,
                missing: 0,
                status: r.status === 'COMPLETED' ? 'Returned' : (r.status === 'PENDING' ? 'Pending' : r.status),
                statusClass: r.status === 'COMPLETED'
                    ? 'bg-green-500/10 text-green-500 border-green-500/20'
                    : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
                flagged: false,
                gradeId: r.id
            }))
        }

    } catch (error) {
        console.error('Error fetching packing materials:', error)
    } finally {
        loading.value = false
    }
}

function showSuccess(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

function showError(msg) {
    errorMsg.value = msg
    setTimeout(() => { errorMsg.value = '' }, 3500)
}

async function verifyReturn(asset) {
    if (asset.status === 'Returned') return

    const warehouseId = getWarehouseId()
    if (!warehouseId || !asset.gradeId) {
        showError('Cannot verify return - missing warehouse')
        return
    }

    try {
        const response = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/returns/${asset.gradeId}/complete`), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (response.ok || response.status === 404) {
            asset.returned = asset.qty
            asset.missing = 0
            asset.status = 'Returned'
            asset.statusClass = 'bg-green-500/10 text-green-500 border-green-500/20'
            showSuccess(`${asset.name} return verified for ${asset.orderId}`)
        } else {
            showError('Failed to verify return')
        }
    } catch (error) {
        console.error('Error verifying return:', error)
        showError('Error verifying return')
    }
}

function flagAsset(asset) {
    asset.flagged = !asset.flagged
    if (asset.flagged) showSuccess(`${asset.name} flagged — notified Logistics Manager`)
}

const { submitIssue } = useIssueSubmit({
    activeOrders,
    allInventory,
    authStore,
    canSubmitIssue,
    closeIssueModal,
    getWarehouseId,
    issuableItemsForSelectedOrder,
    issuanceLogs,
    issueForm,
    issueValidationErrors,
    issuingMaterials,
    labourers,
    selectedIssuingLabourer,
    showError,
    showSuccess,
})

const { submitRestock, escalateRestock } = useRestockRequest({
    allInventory,
    authStore,
    escalateMsg,
    lowStockItems,
    restockForm,
    restocking,
    showError,
    showRestockModal,
    showSuccess,
})

const AUTO_REFRESH_INTERVAL_MS = 30_000
let autoRefreshTimer = null

async function silentRefreshInventory() {
    const warehouseId = getWarehouseId()
    const headers = {
        'Authorization': `Bearer ${authStore.authToken}`,
        'Content-Type': 'application/json'
    }
    try {
        const res = await fetch(apiUrl(`api/v1/inventory?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers })
        if (res.ok) {
            const data = await res.json()
            allInventory.value = data.items || data || []
        }
    } catch { /* silent — don't interrupt user */ }
}

onMounted(() => {
    fetchData()
    autoRefreshTimer = setInterval(silentRefreshInventory, AUTO_REFRESH_INTERVAL_MS)
})

onUnmounted(() => {
    clearInterval(autoRefreshTimer)
})

provide(packingMaterialsPageKey, {
    applyRecommendedQuantities,
    canSubmitIssue,
    closeIssueModal,
    escalateRestock,
    filteredLog,
    flagAsset,
    getWarehouseId,
    issuableLabourers,
    issueForm,
    issuingMaterials,
    labourerIssueLabel,
    logTab,
    lowStockItems,
    onOrderSelected,
    ordersAvailableForIssuance,
    packingItems,
    recommendedMaterials,
    restockForm,
    restocking,
    returnableAssets,
    selectedOrderDetails,
    showIssueModal,
    showRestockModal,
    submitIssue,
    submitRestock,
    verifyReturn,
})
</script>
