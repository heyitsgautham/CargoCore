<template>
    <div class="min-h-[calc(100vh-8rem)] flex flex-col gap-4 pb-6 lg:gap-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">undo</span>
            Reverse Logistics & Returns
        </h2>

        <ReturnStatsCards />

        <ReturnFilterBar />

        <ReturnClaimsList />

        <ReturnDecisionModal />

        <ReturnDetailsModal />

        <ReturnImageGallery />
    </div>
</template>

<script setup>
import ReturnStatsCards from './reverseLogistics/ReturnStatsCards.vue'
import ReturnFilterBar from './reverseLogistics/ReturnFilterBar.vue'
import ReturnClaimsList from './reverseLogistics/ReturnClaimsList.vue'
import ReturnDecisionModal from './reverseLogistics/ReturnDecisionModal.vue'
import ReturnDetailsModal from './reverseLogistics/ReturnDetailsModal.vue'
import ReturnImageGallery from './reverseLogistics/ReturnImageGallery.vue'
import {
    FINAL_DECISIONS,
    PHOTO_REVIEW_DECISIONS,
    PICKUP_DECISIONS,
    RETURN_TABS,
    decisionTitle,
    filterClaims,
    formatDateTime,
    getRowAccentClass,
    getStatusClass,
    getStatusHint,
    getStatusHintClass,
    isInProgress,
    isResolved,
    needsManagerAction,
    returnStats,
} from './reverseLogistics/returnClaims'
import { reverseLogisticsPageKey } from './reverseLogistics/reverseLogisticsPageContext'
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'

const store = useLogisticStore()
const { filteredReturns } = storeToRefs(store)
let refreshTimer = null

async function refreshReturnsView() {
    await store.refresh()
}

function handleVisibilityRefresh() {
    if (document.visibilityState === 'visible') refreshReturnsView()
}

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(() => {
        if (document.visibilityState === 'visible') refreshReturnsView()
    }, 15000)
}

function stopAutoRefresh() {
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}

onMounted(() => {
    refreshReturnsView()
    startAutoRefresh()
    window.addEventListener('focus', refreshReturnsView)
    document.addEventListener('visibilitychange', handleVisibilityRefresh)
})

onUnmounted(() => {
    stopAutoRefresh()
    window.removeEventListener('focus', refreshReturnsView)
    document.removeEventListener('visibilitychange', handleVisibilityRefresh)
})

// View state
const searchQuery = ref('')
const activeStatus = ref('All')
const showResolved = ref(false)
const showDecisionModal = ref(false)
const showDetailsModal = ref(false)
const showImageModal = ref(false)
const selectedRMA = ref(null)
const selectedImages = ref([])
const legacyFileNames = ref([])
const activeImageIndex = ref(0)
const submitting = ref(false)

// Refund state
const refundIssuing = ref(false)
const refundIssued = ref(false)
const refundError = ref('')
const issuedRefundIds = new Set()

// Decision form
const decisionForm = ref({
    action: '',
    amount: 0,
    notes: '',
    applyTransportCharge: false
})

const tabs = RETURN_TABS
const photoReviewDecisions = PHOTO_REVIEW_DECISIONS
const pickupDecisions = PICKUP_DECISIONS
const finalDecisions = FINAL_DECISIONS

// Stats
const stats = computed(() => returnStats(filteredReturns.value))
const reportedCount = computed(() => stats.value.reported)
const photoReviewCount = computed(() => stats.value.photoReview)
const pickupInspectionCount = computed(() => stats.value.pickupInspection)
const awaitingLMCount = computed(() => stats.value.awaitingLM)
const refundValue = computed(() => stats.value.refundValue)

const filteredList = computed(() => filterClaims(filteredReturns.value, activeStatus.value, searchQuery.value))
const actionRequiredList = computed(() => filteredList.value.filter(needsManagerAction))
const inProgressList = computed(() => filteredList.value.filter(isInProgress))
const resolvedList = computed(() => filteredList.value.filter(isResolved))
const decisionModalTitle = computed(() => decisionTitle(selectedRMA.value))

// Actions
const openImageGallery = (rma) => {
    selectedRMA.value = rma
    const allImages = rma.images || []
    selectedImages.value = allImages.filter(img => img && (img.startsWith('http') || img.startsWith('/') || img.startsWith('data:')))
    legacyFileNames.value = allImages.filter(img => img && !img.startsWith('http') && !img.startsWith('/') && !img.startsWith('data:'))
    activeImageIndex.value = 0
    showImageModal.value = true
}

const forwardToWM = async (rma) => {
    await store.updateReturnStatus(rma.id, 'Under Review', { notes: 'Forwarded to WM for damage review' })
}

const openLMDecisionModal = (rma) => {
    selectedRMA.value = rma
    decisionForm.value = { action: '', amount: rma.originalPrice || 0, notes: '', applyTransportCharge: false }
    showDecisionModal.value = true
}

const openDetails = (rma) => {
    selectedRMA.value = rma
    const needsDecision =
        (rma.flow_type === 'photo_review' && rma.status === 'Claims Reviewed') ||
        (rma.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested', 'Physically Inspected'].includes(rma.status || 'Reported'))
    if (needsDecision) {
        openLMDecisionModal(rma)
    } else {
        openDetailsReadOnly(rma)
    }
}

const openDetailsReadOnly = (rma) => {
    selectedRMA.value = rma
    refundIssued.value = Boolean(rma.walletCredited || issuedRefundIds.has(rma.id))
    refundIssuing.value = false
    refundError.value = ''
    showDetailsModal.value = true
}

const submitDecision = async () => {
    if (!selectedRMA.value || !decisionForm.value.action || submitting.value) return
    submitting.value = true

    try {
        const rma = selectedRMA.value
        const action = decisionForm.value.action

        // Map action to new status
        let newStatus
        if (action === 'Full Refund') newStatus = 'Approved'
        else if (action === 'Partial Refund') newStatus = 'Partially Approved'
        else if (action === 'Reject Claim') newStatus = 'Rejected'
        else if (action === 'Need More Evidence') newStatus = 'Under Review'
        else if (action === 'Approve Pickup') newStatus = 'Pickup Approved'
        else if (action === 'Reject Pickup Request') newStatus = 'Pickup Rejected'
        else if (action === 'Ask for More Evidence') newStatus = 'Under Review'
        else newStatus = action

        await store.updateReturnStatus(rma.id, newStatus, {
            refundAmount: ['Full Refund', 'Partial Refund'].includes(action) ? decisionForm.value.amount : 0,
            notes: decisionForm.value.notes,
            applyTransportCharge: decisionForm.value.applyTransportCharge || false,
        })

        // Add refund transaction if applicable
        if (['Full Refund', 'Partial Refund'].includes(action) && decisionForm.value.amount > 0) {
            await store.addTransaction({
                id: Date.now(),
                date: new Date().toISOString().split('T')[0],
                desc: `Refund for ${rma.id}`,
                amount: -decisionForm.value.amount,
                type: 'Expense',
                status: 'Completed',
                hubId: store.activeWarehouse
            })
        }

        // Auto-schedule driver pickup when LM approves pickup
        if (action === 'Approve Pickup') {
            try {
                await store.scheduleReturnPickup(rma.id)
            } catch (e) {
                console.warn('Could not auto-schedule pickup:', e?.message)
            }
        }

        showDecisionModal.value = false
    } finally {
        submitting.value = false
    }
}

const handleIssueRefund = async () => {
    if (!selectedRMA.value || refundIssuing.value || refundIssued.value) return
    refundIssuing.value = true
    refundError.value = ''
    try {
        const result = await store.issueReturnRefund(selectedRMA.value.id)
        issuedRefundIds.add(selectedRMA.value.id)
        refundIssued.value = true
        selectedRMA.value = { ...selectedRMA.value, status: 'Refunded', walletCredited: true }
        if (result && !result.credited) {
            refundError.value = 'Note: refund was already issued previously.'
        }
    } catch (e) {
        refundError.value = e?.message || 'Failed to issue refund. Please try again.'
    } finally {
        refundIssuing.value = false
    }
}

provide(reverseLogisticsPageKey, {
    actionRequiredList,
    activeImageIndex,
    activeStatus,
    awaitingLMCount,
    decisionForm,
    decisionModalTitle,
    filteredList,
    finalDecisions,
    formatDateTime,
    forwardToWM,
    getRowAccentClass,
    getStatusClass,
    getStatusHint,
    getStatusHintClass,
    handleIssueRefund,
    inProgressList,
    legacyFileNames,
    openDetails,
    openDetailsReadOnly,
    openImageGallery,
    openLMDecisionModal,
    photoReviewCount,
    photoReviewDecisions,
    pickupDecisions,
    pickupInspectionCount,
    refundError,
    refundIssued,
    refundIssuing,
    refundValue,
    reportedCount,
    resolvedList,
    searchQuery,
    selectedImages,
    selectedRMA,
    showDecisionModal,
    showDetailsModal,
    showImageModal,
    showResolved,
    submitDecision,
    submitting,
    tabs,
})
</script>
