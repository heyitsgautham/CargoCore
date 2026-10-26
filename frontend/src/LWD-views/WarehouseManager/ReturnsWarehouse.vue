<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Returns Processing (Warehouse)</h2>
            <div class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-1 flex gap-1">
                <button
                    :class="activeTab === 'damage_review' ? 'px-4 py-1.5 bg-blue-600 rounded text-white text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'damage_review'">
                    <span class="flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">photo_camera</span>
                        Damage Review
                        <span v-if="damageReviewQueue.length > 0" class="bg-red-500 text-white text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{{ damageReviewQueue.length }}</span>
                    </span>
                </button>
                <button
                    :class="activeTab === 'processing' ? 'px-4 py-1.5 bg-primary rounded text-background-dark text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'processing'">Physical Inspection</button>
                <button
                    :class="activeTab === 'completed' ? 'px-4 py-1.5 bg-primary rounded text-background-dark text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'completed'">Completed</button>
            </div>
        </div>

        <ReturnsStats />

        <!-- Loading -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading returns data...</div>
        </div>

        <template v-else>

        <DamageReviewTab />

        <PhysicalInspectionTab />

        <CompletedReturnsTab />
        </template>

        <CustomerPhotoModal />

        <InspectionPhotoModal />

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import ReturnsStats from './returnsWarehouse/ReturnsStats.vue'
import DamageReviewTab from './returnsWarehouse/DamageReviewTab.vue'
import PhysicalInspectionTab from './returnsWarehouse/PhysicalInspectionTab.vue'
import CompletedReturnsTab from './returnsWarehouse/CompletedReturnsTab.vue'
import CustomerPhotoModal from './returnsWarehouse/CustomerPhotoModal.vue'
import InspectionPhotoModal from './returnsWarehouse/InspectionPhotoModal.vue'
import {
    getConditionClass,
    getDispositionBg,
    getDispositionColor,
    getDispositionIcon,
    getDispositionLabel,
} from './returnsWarehouse/returnLabels'
import { returnsWarehousePageKey } from './returnsWarehouse/returnsWarehousePageContext'
import { API_BASE_URL } from '@/config/api'
import { ref, computed, inject, watch, onMounted, onUnmounted, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useDamageReview } from './returnsWarehouse/useDamageReview'
import { useReturnGrading } from './returnsWarehouse/useReturnGrading'

const authStore = useAuthStore()
const openScanner = inject('openScanner')
const lastGlobalScan = inject('lastGlobalScan')

const activeTab = ref('damage_review')
const rmaId = ref('')
const itemCondition = ref('')
const conditionNotes = ref('')
const disposition = ref('')
const capturedPhoto = ref(null)  // Will hold actual photo data/blob
const toastMsg = ref('')
const completedFilter = ref('')
const showPhotoModal = ref(false)
const photoItem = ref(null)
const loading = ref(false)
const submitting = ref(false)
const submittingReview = ref(false)
const selectedOrderForReturn = ref(null)
const selectedGradingId = ref(null)   // set when editing an existing pending grading
const warehouseId = ref(null)

// Flow 2 (physical inspection) extra fields
const inspectionGenuineness = ref('')
const inspectionRecommendedOutcome = ref('')
const inspectionRemarks = ref('')

const {
    damageReviewQueue,
    selectedDamageReport,
    reviewPhotoPreview,
    damageReviewForm,
    selectDamageReport,
    submitDamageReview,
    fetchDamageReviewQueue,
} = useDamageReview({ authStore, submittingReview, toastMsg })

let refreshTimer = null

// Real data from API
const inboundReturns = ref([])       // ON_HOLD orders = items awaiting inspection
const pendingGradings = ref([])      // Pending (created but not completed) return gradings
const completedItems = ref([])       // Completed return gradings from API

// Listen for global scans
watch(lastGlobalScan, (newVal) => {
    if (newVal) {
        if (newVal === 'captured_image_data_mock' || newVal.startsWith('data:image')) {
            // Captured photo data
            capturedPhoto.value = newVal
        } else {
            rmaId.value = newVal
            const found = processingItems.value.find(p => p.rma === newVal)
            if (found) {
                selectItem(found)
                toastMsg.value = `Loaded RMA ${newVal} details.`
                setTimeout(() => { toastMsg.value = '' }, 2500)
            } else {
                selectedOrderForReturn.value = null
                selectedGradingId.value = null
            }
        }
        lastGlobalScan.value = null
    }
})

function resolveWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null
}

async function fetchWarehouseId() {
    try {
        await authStore.ensureWarehouseContext()

        const resolvedWarehouseId = resolveWarehouseId()
        if (resolvedWarehouseId) {
            warehouseId.value = resolvedWarehouseId
            return
        }

        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }
        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses?page=1&page_size=100`, { headers })
        if (!response.ok) return

        const data = await response.json()
        const warehouses = data.items || data || []
        const profile = authStore.currentUser || {}
        const linkedWarehouse = warehouses.find(warehouse =>
            warehouse.id === profile.warehouse_id || warehouse.manager_id === profile.id
        ) || null

        warehouseId.value = linkedWarehouse?.id || null
    } catch (error) {
        console.error('Error fetching warehouse ID:', error)
    }
}

function mapGradingToCompleted(g) {
    return {
        id: g.id,
        name: g.order_tracking || g.rma_code || 'Unknown',
        rma: g.rma_code,
        condition: g.item_condition,
        disposition: g.disposition,
        dispositionLabel: getDispositionLabel(g.disposition),
        hasPhoto: !!g.damage_photo_url,
        photoUrl: g.damage_photo_url,
        time: g.graded_at
            ? new Date(g.graded_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
            : '--',
    }
}

async function fetchReturns({ silent = false } = {}) {
    if (!authStore.authToken) return

    if (!silent) {
        loading.value = true
    }
    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        // ON_HOLD orders are NOT reliable as return indicators — returns are tracked via
        // the return gradings API exclusively. Keep inboundReturns empty.
        inboundReturns.value = []

        if (warehouseId.value) {
            // Fetch pending return gradings (created but not yet completed)
            const pendingRes = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns?status_filter=pending&page_size=50`,
                { headers }
            )
            if (pendingRes.ok) {
                const data = await pendingRes.json()
                pendingGradings.value = data.items || []
            }

            // Fetch completed return gradings (status_filter is the correct param name)
            const completedRes = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns?status_filter=completed&page_size=50`,
                { headers }
            )
            if (completedRes.ok) {
                const completedData = await completedRes.json()
                completedItems.value = (completedData.items || []).map(mapGradingToCompleted)
            }
        }
    } catch (error) {
        console.error('Error fetching returns:', error)
    } finally {
        if (!silent) {
            loading.value = false
        }
    }
}

async function refreshReturnsContext() {
    await fetchWarehouseId()
    await fetchDamageReviewQueue()
    if (!warehouseId.value) {
        pendingGradings.value = []
        completedItems.value = []
        inboundReturns.value = []
        return
    }
    await fetchReturns()
}

function handleVisibilityRefresh() {
    if (document.visibilityState === 'visible') {
        refreshReturnsContext()
    }
}

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(() => {
        if (document.visibilityState === 'visible') {
            fetchReturns({ silent: true })
        }
    }, 15000)
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

// Build processing queue: pending gradings first, then ON_HOLD orders not yet assigned a grading
const processingItems = computed(() => {
    const fromGradings = pendingGradings.value.map(g => ({
        id: `grading-${g.id}`,
        gradingId: g.id,
        orderId: g.order_id,
        name: g.order_tracking || g.rma_code,
        rma: g.rma_code,
        reason: g.condition_notes || 'Returned by customer',
        time: g.created_at
            ? new Date(g.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
            : '--',
        rawOrder: { id: g.order_id, tracking_code: g.order_tracking },
        // Pre-fill fields if grading already has partial data
        prefill: {
            condition: g.item_condition,
            notes: g.condition_notes,
            disposition: g.disposition,
            genuineness: g.is_genuine,
            recommendedOutcome: g.recommended_outcome,
            remarks: g.inspection_remarks,
        },
    }))

    // Only show ON_HOLD orders that don't already have a pending grading
    const gradedOrderIds = new Set(pendingGradings.value.map(g => g.order_id).filter(Boolean))
    const fromOrders = inboundReturns.value
        .filter(order => !gradedOrderIds.has(order.id))
        .map(order => ({
            id: `order-${order.id}`,
            gradingId: null,
            orderId: order.id,
            name: order.tracking_code || `Order #${order.id?.slice(0, 8)}`,
            rma: `RMA-${order.tracking_code || order.id?.slice(0, 6).toUpperCase()}`,
            reason: order.notes || order.hold_reason || 'Returned by customer',
            time: order.updated_at
                ? new Date(order.updated_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
                : '--',
            rawOrder: order,
            prefill: null,
        }))

    return [...fromGradings, ...fromOrders]
})

const filteredCompleted = computed(() => {
    if (!completedFilter.value) return completedItems.value
    return completedItems.value.filter(i => i.disposition === completedFilter.value)
})

function selectItem(item) {
    rmaId.value = item.rma
    selectedOrderForReturn.value = item.rawOrder
    selectedGradingId.value = item.gradingId || null
    if (item.prefill) {
        itemCondition.value = item.prefill.condition || ''
        conditionNotes.value = item.prefill.notes || ''
        disposition.value = item.prefill.disposition || ''
        inspectionGenuineness.value = typeof item.prefill.genuineness === 'boolean' ? item.prefill.genuineness : ''
        inspectionRecommendedOutcome.value = item.prefill.recommendedOutcome || ''
        inspectionRemarks.value = item.prefill.remarks || ''
    } else {
        itemCondition.value = ''
        conditionNotes.value = ''
        disposition.value = ''
        inspectionGenuineness.value = ''
        inspectionRecommendedOutcome.value = ''
        inspectionRemarks.value = ''
    }
}

const { submitReturn } = useReturnGrading({
    authStore,
    capturedPhoto,
    completedItems,
    conditionNotes,
    disposition,
    inboundReturns,
    inspectionGenuineness,
    inspectionRecommendedOutcome,
    inspectionRemarks,
    itemCondition,
    mapGradingToCompleted,
    pendingGradings,
    rmaId,
    selectedGradingId,
    selectedOrderForReturn,
    submitting,
    toastMsg,
    warehouseId,
})

watch(
    () => [authStore.currentWarehouse?.id, authStore.currentUser?.warehouse_id],
    async ([currentWarehouseId, currentUserWarehouseId], [prevCurrentWarehouseId, prevCurrentUserWarehouseId]) => {
        if (
            currentWarehouseId === prevCurrentWarehouseId
            && currentUserWarehouseId === prevCurrentUserWarehouseId
        ) {
            return
        }
        await refreshReturnsContext()
    }
)

onMounted(async () => {
    await refreshReturnsContext()
    startAutoRefresh()
    window.addEventListener('focus', refreshReturnsContext)
    document.addEventListener('visibilitychange', handleVisibilityRefresh)
})

onUnmounted(() => {
    stopAutoRefresh()
    window.removeEventListener('focus', refreshReturnsContext)
    document.removeEventListener('visibilitychange', handleVisibilityRefresh)
})

provide(returnsWarehousePageKey, {
    activeTab,
    capturedPhoto,
    completedFilter,
    completedItems,
    conditionNotes,
    damageReviewForm,
    damageReviewQueue,
    disposition,
    filteredCompleted,
    getConditionClass,
    getDispositionBg,
    getDispositionColor,
    getDispositionIcon,
    inspectionGenuineness,
    inspectionRecommendedOutcome,
    inspectionRemarks,
    itemCondition,
    loading,
    openScanner,
    photoItem,
    processingItems,
    reviewPhotoPreview,
    rmaId,
    selectDamageReport,
    selectItem,
    selectedDamageReport,
    selectedOrderForReturn,
    showPhotoModal,
    submitDamageReview,
    submitReturn,
    submitting,
    submittingReview,
})
</script>
