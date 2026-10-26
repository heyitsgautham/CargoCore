<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Inbound Shipments</h2>
            <div class="flex gap-2">
                <button @click="openInboundEstimator()" :disabled="loading || asns.length === 0"
                    class="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">model_training</span> AI Receive Plan
                </button>
                <button @click="showScheduleModal = true"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">calendar_today</span> Schedule Delivery
                </button>
            </div>
        </div>

        <InboundStats />

        <!-- Loading overlay for table -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400 text-sm">Loading inbound shipments...</div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <DockSchedule />

            <PendingReceipts />
        </div>

        <SlotDetailModal />

        <MismatchModal />

        <DamageModal />

        <ReceivePlanModal />

        <ScheduleModal />

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>

        <ArrivalDebitModal />

        <!-- Smart Scanner Modal for Camera -->
        <SmartScannerModal :is-open="isCameraOpen" :default-tab="'camera'" @close="isCameraOpen = false" @camera="handlePhotoCapture" />

        <ImageViewerModal />
    </div>
</template>

<script setup>
import InboundStats from './inbound/InboundStats.vue'
import DockSchedule from './inbound/DockSchedule.vue'
import PendingReceipts from './inbound/PendingReceipts.vue'
import SlotDetailModal from './inbound/SlotDetailModal.vue'
import MismatchModal from './inbound/MismatchModal.vue'
import DamageModal from './inbound/DamageModal.vue'
import ReceivePlanModal from './inbound/ReceivePlanModal.vue'
import ScheduleModal from './inbound/ScheduleModal.vue'
import ArrivalDebitModal from './inbound/ArrivalDebitModal.vue'
import ImageViewerModal from './inbound/ImageViewerModal.vue'
import {
    formatIssueStatus,
    inboundStatsFrom,
    inboundStatusClassMap,
    isAsnInPickingFlow,
    issueStatusClass,
    toDockSlot,
    toInboundRow,
} from './inbound/inboundRows'
import { inboundPageKey } from './inbound/inboundPageContext'
import { ref, computed, reactive, onMounted, onUnmounted, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import SmartScannerModal from '@/components/SmartScannerModal.vue'
import { API_BASE_URL } from '@/config/api'
import { useInboundIssues } from './inbound/useInboundIssues'
import { useReceivePlan } from './inbound/useReceivePlan'

const authStore = useAuthStore()
const showMismatchModal = ref(false)
const showDamageModal = ref(false)
const showEstimatorModal = ref(false)
const showScheduleModal = ref(false)
const showSlotDetail = ref(false)
const selectedSlot = ref(null)
const toastMsg = ref('')
const isCameraOpen = ref(false)
const damagePhoto = ref(null)
const viewerImage = ref(null)
const loading = ref(false)
const estimatorLoading = ref(false)
const estimatorPlan = ref(null)
const inboundStats = ref({
    arrivedToday: 0,
    inTransit: 0,
    mismatchesFound: 0,
    damageReports: 0,
})

// Arrive confirmation modal for auto-debit orders
const showArriveConfirmModal = ref(false)
const arriveConfirmAsn = ref(null)
const isMarkingArrived = ref(false)

const mismatchForm = reactive({ asnId: '', type: 'Quantity difference', details: '' })
const damageForm = reactive({ asnId: '', count: 0, description: '', hasPhoto: false })
const estimatorForm = reactive({ asnId: '' })
const scheduleForm = reactive({ supplier: '', qty: 0, eta: '' })

const dockSchedule = ref([])
const asns = ref([])

function authHeaders() {
    return {
        Authorization: `Bearer ${authStore.authToken}`,
        'Content-Type': 'application/json',
    }
}

// Fetch inbound shipments from backend
let inboundRefreshTimer = null
let inboundRefreshPending = false

async function fetchInboundShipments(options = {}) {
    const { silent = false } = options
    if (inboundRefreshPending) return
    inboundRefreshPending = true
    if (!silent) loading.value = true
    try {
        const warehouseId = authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            throw new Error('No warehouse assigned')
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/inbound`,
            { headers: authHeaders() }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to load inbound shipments')
        }
        const data = await res.json()
        inboundStats.value = inboundStatsFrom(data?.stats)
        asns.value = (data?.shipments || [])
            .map((shipment) => toInboundRow(shipment, warehouseId))
            .filter((shipment) => !isAsnInPickingFlow(shipment))
        dockSchedule.value = (data?.dock_schedule || []).map(toDockSlot)
        if (mismatchForm.asnId && !asns.value.some((asn) => asn.id === mismatchForm.asnId)) {
            mismatchForm.asnId = ''
        }
        if (damageForm.asnId && !asns.value.some((asn) => asn.id === damageForm.asnId)) {
            damageForm.asnId = ''
        }
        if (estimatorForm.asnId && !asns.value.some((asn) => asn.id === estimatorForm.asnId)) {
            estimatorForm.asnId = ''
            estimatorPlan.value = null
        }
    } catch (error) {
        console.error('Error fetching inbound shipments:', error)
        showToast(error.message || 'Unable to load inbound data from server')
    } finally {
        if (!silent) loading.value = false
        inboundRefreshPending = false
    }
}

function refreshInboundIfVisible() {
    if (document.visibilityState === 'visible') {
        fetchInboundShipments({ silent: true })
    }
}

onMounted(() => {
    fetchInboundShipments()
    window.addEventListener('focus', refreshInboundIfVisible)
    document.addEventListener('visibilitychange', refreshInboundIfVisible)
    inboundRefreshTimer = window.setInterval(() => {
        refreshInboundIfVisible()
    }, 15000)
})

onUnmounted(() => {
    window.removeEventListener('focus', refreshInboundIfVisible)
    document.removeEventListener('visibilitychange', refreshInboundIfVisible)
    if (inboundRefreshTimer) {
        window.clearInterval(inboundRefreshTimer)
        inboundRefreshTimer = null
    }
})

const arrivedCount = computed(() => inboundStats.value.arrivedToday)
const inTransitCount = computed(() => inboundStats.value.inTransit)
const mismatchCount = computed(() => inboundStats.value.mismatchesFound)
const damageCount = computed(() => inboundStats.value.damageReports)
const selectedEstimatorAsn = computed(() => asns.value.find((asn) => asn.id === estimatorForm.asnId) || null)
const estimatorPrimaryActionLabel = computed(() => {
    const selectedAsn = selectedEstimatorAsn.value
    if (!selectedAsn) return 'Close'
    if (selectedAsn.status === 'Receiving') return 'Complete & Move to Picking'
    if (selectedAsn.status === 'Arrived') return 'Start Receiving'
    return 'Schedule Delivery'
})

function showToast(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

const { fetchInboundReceivePlan, openInboundEstimator, handleEstimatorPrimaryAction } = useReceivePlan({
    asns,
    authHeaders,
    authStore,
    completeReceiving,
    estimatorForm,
    estimatorLoading,
    estimatorPlan,
    openScheduleFromEstimator,
    selectedEstimatorAsn,
    showEstimatorModal,
    showToast,
    startReceiving,
})

function startReceiving(asn) {
    asn.status = 'Receiving'
    asn.displayStatus = 'Receiving'
    asn.statusClass = inboundStatusClassMap.Receiving
    showToast(`Started receiving ${asn.id}`)
}

async function completeReceiving(asn) {
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot complete receiving')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/receive-inbound`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to complete receiving')
        }
        showToast(`${asn.id} received — moved to picking queue`)
        await fetchInboundShipments()
        showEstimatorModal.value = false
    } catch (e) {
        console.error(e)
        showToast(e.message || 'Failed to complete receiving')
    }
}

function canStartInboundProcessing(asn) {
    return asn.status === 'Arrived' && (asn.canMoveToPicking || (!asn.mismatch && !asn.damaged))
}

function canCompleteInboundProcessing(asn) {
    return asn.status === 'Receiving' && (asn.canMoveToPicking || (!asn.mismatch && !asn.damaged))
}

function showIssueHoldState(asn) {
    return (asn.mismatch || asn.damaged) && !asn.canMoveToPicking && !asn.canGenerateTakeBack
}

function showTakeBackAction(asn) {
    return asn.canGenerateTakeBack && asn.warehouseSubstatus !== 'ON_HOLD'
}

async function generateTakeBack(asn) {
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot generate take-back')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/generate-take-back`,
            {
                method: 'POST',
                headers: authHeaders(),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to generate vendor take-back')
        }
        showToast(`Vendor take-back generated for ${asn.id}`)
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to generate vendor take-back')
    }
}

async function markArrived(asn) {
    // Show confirmation modal if auto-debit is enabled for this order
    if (asn.autoDebitEnabled && asn.isRecurring) {
        arriveConfirmAsn.value = asn
        showArriveConfirmModal.value = true
        return
    }
    await _doMarkArrived(asn)
}

async function _doMarkArrived(asn) {
    showArriveConfirmModal.value = false
    arriveConfirmAsn.value = null
    isMarkingArrived.value = true
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot mark arrival')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/mark-arrived`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to mark arrival')
        }
        const result = await res.json()
        showToast(result.message || `${asn.id} marked as arrived`)
        await fetchInboundShipments()
    } catch (e) {
        console.error(e)
        showToast(e.message || 'Failed to mark arrival')
    } finally {
        isMarkingArrived.value = false
    }
}

const {
    submitMismatch,
    submitDamage,
    openDamageCamera,
    handlePhotoCapture,
    retakeDamagePhoto,
} = useInboundIssues({
    asns,
    authHeaders,
    authStore,
    damageForm,
    damagePhoto,
    fetchInboundShipments,
    isCameraOpen,
    mismatchForm,
    showDamageModal,
    showMismatchModal,
    showToast,
})

function viewImage(imageSrc) {
    viewerImage.value = imageSrc
}

function openScheduleFromEstimator() {
    const selectedAsn = asns.value.find((asn) => asn.id === estimatorForm.asnId)
    if (selectedAsn) {
        scheduleForm.supplier = selectedAsn.supplier
        scheduleForm.qty = selectedAsn.expected || 0
    }
    showEstimatorModal.value = false
    showScheduleModal.value = true
}

async function scheduleDelivery() {
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!warehouseId) {
        showToast('No warehouse assigned')
        return
    }
    const scheduledAt = scheduleForm.eta ? new Date(scheduleForm.eta) : null
    if (!scheduleForm.supplier.trim()) {
        showToast('Enter supplier name')
        return
    }
    if (!scheduleForm.qty || scheduleForm.qty < 1) {
        showToast('Enter expected quantity')
        return
    }
    if (!scheduledAt || Number.isNaN(scheduledAt.getTime())) {
        showToast('Choose a valid delivery time')
        return
    }
    try {
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/inbound/schedule`,
            {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    supplier_name: scheduleForm.supplier.trim(),
                    expected_qty: scheduleForm.qty,
                    scheduled_at: scheduledAt.toISOString(),
                }),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to schedule delivery')
        }
        showScheduleModal.value = false
        scheduleForm.supplier = ''
        scheduleForm.qty = 0
        scheduleForm.eta = ''
        showToast('Delivery scheduled successfully')
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to schedule delivery')
    }
}

provide(inboundPageKey, {
    _doMarkArrived,
    arriveConfirmAsn,
    arrivedCount,
    asns,
    canCompleteInboundProcessing,
    canStartInboundProcessing,
    completeReceiving,
    damageCount,
    damageForm,
    damagePhoto,
    dockSchedule,
    estimatorForm,
    estimatorLoading,
    estimatorPlan,
    estimatorPrimaryActionLabel,
    fetchInboundReceivePlan,
    formatIssueStatus,
    generateTakeBack,
    handleEstimatorPrimaryAction,
    inTransitCount,
    isMarkingArrived,
    issueStatusClass,
    loading,
    markArrived,
    mismatchCount,
    mismatchForm,
    openDamageCamera,
    openInboundEstimator,
    retakeDamagePhoto,
    scheduleDelivery,
    scheduleForm,
    selectedSlot,
    showArriveConfirmModal,
    showDamageModal,
    showEstimatorModal,
    showIssueHoldState,
    showMismatchModal,
    showScheduleModal,
    showSlotDetail,
    showTakeBackAction,
    startReceiving,
    submitDamage,
    submitMismatch,
    viewImage,
    viewerImage,
})
</script>
