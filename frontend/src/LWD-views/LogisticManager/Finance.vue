<template>
    <div class="flex flex-col gap-4">
        <!-- Header -->
        <div class="flex justify-between items-center bg-slate-800/80 p-4 rounded-xl shadow-sm border border-white/10">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">account_balance_wallet</span>
                    Finance & Payroll
                </h2>
                <p class="text-xs text-gray-500 mt-1">Manage cash flow, reconcile COD, and process payments across all departments.</p>
            </div>
            <div class="flex gap-3">
                <div class="relative group">
                    <button @click="openPayrollModal" :disabled="!filteredUsers.some(u => u.pending_payout > 0)"
                        class="bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-emerald-400/20">
                        <span class="material-symbols-outlined">payments</span> Pay All Due
                    </button>
                    <div v-if="!filteredUsers.some(u => u.pending_payout > 0)" class="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-48 bg-black/80 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none text-center">
                        No pending payouts
                    </div>
                </div>
                <button @click="openBulkActionModal" 
                    class="bg-slate-800 hover:bg-slate-700 dark:bg-purple-600 dark:hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-slate-700 dark:border-purple-400/20">
                    <span class="material-symbols-outlined">auto_fix_high</span> Smart Bonus/Deduct
                </button>
                <button @click="openTransactionModal" 
                    class="bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-slate-700 dark:border-primary/30">
                    <span class="material-symbols-outlined">add_circle</span> New Record
                </button>
            </div>
        </div>

        <FinanceStatsCards />

        <FinanceTabs />

        <FinanceLedger />

        <BonusDeductModal />

        <PayrollModal />

        <SinglePaymentModal />

        <TransactionModal />

        <ReconcileCodModal />
    </div>
</template>

<script setup>
import FinanceStatsCards from './finance/FinanceStatsCards.vue'
import FinanceTabs from './finance/FinanceTabs.vue'
import FinanceLedger from './finance/FinanceLedger.vue'
import BonusDeductModal from './finance/BonusDeductModal.vue'
import PayrollModal from './finance/PayrollModal.vue'
import SinglePaymentModal from './finance/SinglePaymentModal.vue'
import TransactionModal from './finance/TransactionModal.vue'
import ReconcileCodModal from './finance/ReconcileCodModal.vue'
import { financePageKey } from './finance/financePageContext'
import { ref, computed, onMounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useFinanceSlips } from './finance/useFinanceSlips'

const store = useLogisticStore()
const {
    filteredTransactions,
    filteredUsers,
    filteredDrivers,
    filteredTopDrivers,
    activeFinanceSummary,
    filteredFinanceCodRecords,
    filteredFinanceStaffRecords,
    filteredFinanceDriverRecords,
    initialized,
    isLoading,
} = storeToRefs(store)

const financeLoaded = computed(() => initialized.value && !isLoading.value)
const { openSlipWithData, prefetchSlips } = useSlipPrinter()

onMounted(() => {
    store.initialize().catch(() => {})
    store.fetchFinanceSummary(store.activeWarehouse).catch(() => {})
    prefetchSlips(['bookingConfirmation', 'financeTransaction']).catch(() => {})
})

// View State
const activeTab = ref('overview') // overview, cod, staff, drivers
const searchQuery = ref('')
const expandedRow = ref(null)
const showTransactionModal = ref(false)
const reconcileModalOpen = ref(false)
const selectedItem = ref(null)
const reconcileAmount = ref(0)
const newTx = ref({ desc: '', type: 'Expense', amount: 0, hubId: null })

// Payroll Modal State
const showPayrollModal = ref(false)
const payrollProcessing = ref(false)
const payrollSuccess = ref(false)
const payrollSummary = ref({ count: 0, total: 0, pendingUsers: [] })

// Single Payment State
const showPaymentModal = ref(false)
const paymentTarget = ref(null)
const paymentProcessing = ref(false)
const paymentSuccess = ref(false)

// Bulk Action State
const showBulkActionModal = ref(false)
const bulkApplying = ref(false)
const bulkForm = ref({
    type: 'Bonus',
    amount: 0,
    reason: '',
    role: 'all',
    filterByRating: false,
    minRating: 4.5,
    filterByTrips: false,
    minTrips: 10
})

const EXCLUDED_BULK_ROLES = new Set(['Logistic Manager', 'Vendor', 'Customer Support'])

const bulkCandidateUsers = computed(() => {
    const driverById = new Map(
        filteredDrivers.value.map((driver) => [String(driver.id), driver])
    )
    const driverByName = new Map(
        filteredDrivers.value.map((driver) => [String(driver.name || '').trim().toLowerCase(), driver])
    )
    const topDriverById = new Map(
        filteredTopDrivers.value.map((driver) => [String(driver.id), driver])
    )
    const topDriverByName = new Map(
        filteredTopDrivers.value.map((driver) => [String(driver.name || '').trim().toLowerCase(), driver])
    )

    return filteredUsers.value
        .filter((user) =>
            !EXCLUDED_BULK_ROLES.has(user.role) &&
            String(user.status || '').toLowerCase() === 'active'
        )
        .map((user) => {
            const normalizedName = String(user.name || '').trim().toLowerCase()
            const driverRecord = driverById.get(String(user.id)) || driverByName.get(normalizedName) || null
            const topDriverRecord = topDriverById.get(String(user.id)) || topDriverByName.get(normalizedName) || null

            const resolvedRating = driverRecord?.rating ?? topDriverRecord?.rating ?? null
            const resolvedTrips = topDriverRecord?.trips ?? null

            return {
                ...user,
                role: driverRecord ? 'Driver' : user.role,
                rating: resolvedRating == null || Number.isNaN(Number(resolvedRating)) ? null : Number(resolvedRating),
                trips: resolvedTrips == null || Number.isNaN(Number(resolvedTrips)) ? null : Number(resolvedTrips),
                avatar: user.avatar || topDriverRecord?.avatar || null,
            }
        })
})

const formatBulkRating = (rating) => (
    rating == null || Number.isNaN(Number(rating))
        ? 'N/A'
        : Number(rating).toFixed(1)
)

// Bulk Computed Logic
const bulkTargetUsers = computed(() => {
    const hasRoleFilter = bulkForm.value.role !== 'all'
    const hasRatingFilter = bulkForm.value.filterByRating
    const hasTripFilter = bulkForm.value.filterByTrips
    const performanceFilterActive = hasRatingFilter || hasTripFilter

    return bulkCandidateUsers.value.filter((user) => {
        if (hasRoleFilter && user.role !== bulkForm.value.role) return false

        // Driver performance criteria should only ever evaluate drivers.
        if (performanceFilterActive && user.role !== 'Driver') return false

        if (hasRatingFilter) {
            if (user.rating == null) return false
            if (Number(user.rating) < Number(bulkForm.value.minRating)) return false
        }

        if (hasTripFilter) {
            if (user.trips == null) return false
            if (Number(user.trips) < Number(bulkForm.value.minTrips)) return false
        }

        return true
    })
})

// Bulk Methods
const openBulkActionModal = () => {
    bulkForm.value = {
        type: 'Bonus',
        amount: 50,
        reason: 'Performance Bonus',
        role: 'Driver',
        filterByRating: true,
        minRating: 4.5,
        filterByTrips: true,
        minTrips: 10
    }
    showBulkActionModal.value = true
}

const applyBulkAction = async () => {
    if (!bulkTargetUsers.value.length || bulkApplying.value) return
    bulkApplying.value = true
    try {
        const isBonus = bulkForm.value.type === 'Bonus'
        // Use EXPENSE_BONUS so the backend's finance_service correctly debits revenue
        const txType = isBonus ? 'EXPENSE_BONUS' : 'REVENUE_ONLINE'
        const amountSign = isBonus ? -1 : 1
        const date = new Date().toISOString().split('T')[0]

        // Use allSettled so all users are processed independently
        // (one failure doesn't block the rest)
        const results = await Promise.allSettled(
            bulkTargetUsers.value.map(user =>
                store.addTransaction({
                    date,
                    desc: `Bonus – ${user.name}: ${bulkForm.value.reason || 'Performance Bonus'}`,
                    amount: bulkForm.value.amount * amountSign,
                    type: txType,
                    status: 'Completed',
                    hubId: store.activeWarehouse
                })
            )
        )

        const failed = results.filter(r => r.status === 'rejected').length
        const succeeded = results.length - failed

        // Refresh finance summary from DB so Revenue card reflects the deduction
        await store.fetchFinanceSummary(store.activeWarehouse).catch(() => {})

        showBulkActionModal.value = false

        if (failed > 0) {
            alert(`Applied to ${succeeded}/${results.length} users. ${failed} failed.`)
        }
    } catch (e) {
        alert(`Failed to apply: ${e.message || 'Unknown error'}`)
    } finally {
        bulkApplying.value = false
    }
}

const openPayrollModal = () => {
    payrollSuccess.value = false

    // Use the finance records (same source as Payroll Due stat card) so
    // they stay in sync — users.pending_payout is always set regardless of paid status.
    const pendingStaff = filteredFinanceStaffRecords.value.filter(r => r.status === 'Pending')
    const pendingDrivers = filteredFinanceDriverRecords.value.filter(r => r.status === 'Pending')
    const allPending = [...pendingStaff, ...pendingDrivers]

    if (allPending.length === 0) return

    payrollSummary.value = {
        count: allPending.length,
        total: allPending.reduce((sum, r) => sum + (r.amount || 0), 0),
        pendingUsers: allPending.map(r => ({ ...r, name: r.name, pending_payout: r.amount }))
    }
    showPayrollModal.value = true
}

const confirmPayrollRun = async () => {
    payrollProcessing.value = true

    // Build per-user payout list for the backend
    const staffPayouts = filteredFinanceStaffRecords.value
        .filter(item => item.status === 'Pending' && item.amount > 0)
        .map(item => ({ user_id: item.userId, amount: item.amount, record_type: 'staff', name: item.name }))
    const driverPayouts = filteredFinanceDriverRecords.value
        .filter(item => item.status === 'Pending' && item.amount > 0)
        .map(item => ({ user_id: item.userId, amount: item.amount, record_type: 'driver', name: item.name }))

    try {
        await store.runPayroll([...staffPayouts, ...driverPayouts])

        // Update local record statuses so UI responds immediately without refresh
        filteredFinanceStaffRecords.value
            .filter(item => item.status === 'Pending')
            .forEach(item => store.markFinanceRecordPaid('staff', item.id))
        filteredFinanceDriverRecords.value
            .filter(item => item.status === 'Pending')
            .forEach(item => store.markFinanceRecordPaid('drivers', item.id))

        // Clear pending_payout on user objects
        payrollSummary.value.pendingUsers.forEach(u => { u.pending_payout = 0 })

        payrollSuccess.value = true
    } catch (e) {
        console.error('Payroll run failed:', e)
    } finally {
        payrollProcessing.value = false
    }
}

// Tabs Configuration
const tabs = [
    { id: 'overview', label: 'Overview', icon: 'dashboard' },
    { id: 'cod', label: 'COD Reconciliation', icon: 'payments' },
    { id: 'staff', label: 'Staff Payroll', icon: 'badge' },
    { id: 'drivers', label: 'Driver/Labor Payouts', icon: 'engineering' }
]

// Computed Data & Logic
const activeTabLabel = computed(() => {
    return tabs.find(t => t.id === activeTab.value)?.label || 'Transactions'
})

const totalRevenue = computed(() => activeFinanceSummary.value.total_revenue ??
    filteredTransactions.value
        .filter(t => t.amount > 0 && t.type !== 'CAPITAL_INVESTMENT')
        .reduce((sum, t) => sum + t.amount, 0))
const totalExpenses = computed(() => activeFinanceSummary.value.total_expenses ??
    Math.abs(filteredTransactions.value.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0)))
const totalPayrollDue = computed(() =>
    [...filteredFinanceStaffRecords.value, ...filteredFinanceDriverRecords.value]
        .filter(item => item.status === 'Pending')
        .reduce((sum, item) => sum + (item.amount || 0), 0)
)
const capitalInflow = computed(() => activeFinanceSummary.value.capital_invested ??
    filteredTransactions.value.filter(t => t.type === 'CAPITAL_INVESTMENT').reduce((sum, t) => sum + t.amount, 0))
const pendingCOD = computed(() => filteredFinanceCodRecords.value
    .filter(item => item.status === 'Pending')
    .reduce((sum, item) => sum + (item.amount || 0), 0))

const reconcileDiff = computed(() => {
    if(!selectedItem.value) return 0
    return reconcileAmount.value - selectedItem.value.amount
})

const filteredItems = computed(() => {
    let items = []
    
    if (activeTab.value === 'overview') {
        items = filteredTransactions.value
    } else if (activeTab.value === 'cod') {
        items = filteredFinanceCodRecords.value
    } else if (activeTab.value === 'staff') {
        items = filteredFinanceStaffRecords.value
    } else if (activeTab.value === 'drivers') {
        items = filteredFinanceDriverRecords.value
    }

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        items = items.filter(i => 
            (i.desc && i.desc.toLowerCase().includes(q)) || 
            (i.name && i.name.toLowerCase().includes(q)) ||
            (i.id && i.id.toLowerCase().includes(q))
        )
    }
    return items
})

// Actions
const toggleRow = (id) => {
    expandedRow.value = expandedRow.value === id ? null : id
}

const openTransactionModal = () => {
    newTx.value = { desc: '', type: 'Expense', amount: 0, hubId: store.activeWarehouse }
    showTransactionModal.value = true
}

const addTransaction = async () => {
    let finalAmount = Math.abs(newTx.value.amount)
    if (newTx.value.type !== 'Incoming') finalAmount = -finalAmount

    await store.addTransaction({
        hubId: newTx.value.hubId || store.activeWarehouse,
        desc: newTx.value.desc,
        type: newTx.value.type,
        amount: finalAmount,
        status: 'Completed'
    })
    showTransactionModal.value = false
}

const openReconcileModal = (item) => {
    selectedItem.value = item
    reconcileAmount.value = item.amount
    reconcileModalOpen.value = true
}

const confirmReconciliation = () => {
    store.markFinanceRecordPaid('cod', selectedItem.value.id)
    reconcileModalOpen.value = false
}

const payUser = (item) => {
    paymentTarget.value = item
    showPaymentModal.value = true
    paymentSuccess.value = false
    paymentProcessing.value = false
}

const confirmSinglePayment = async () => {
    paymentProcessing.value = true
    
    // Simulate transaction
    await new Promise(resolve => setTimeout(resolve, 1500))

    await store.addTransaction({
        hubId: store.activeWarehouse,
        date: new Date().toLocaleDateString(),
        desc: `Payout to ${paymentTarget.value.name}`,
        type: 'Expense',
        amount: -paymentTarget.value.amount,
        status: 'Completed'
    })

    store.markFinanceRecordPaid(activeTab.value === 'staff' ? 'staff' : 'drivers', paymentTarget.value.id)
    const targetUser = filteredUsers.value.find((user) => user.id === paymentTarget.value.userId)
    if (targetUser) targetUser.pending_payout = 0

    paymentProcessing.value = false
    paymentSuccess.value = true

    // Auto close
    setTimeout(() => {
        showPaymentModal.value = false
        paymentSuccess.value = false
        paymentTarget.value = null
    }, 2000)
}

const { downloadSlip, txTypeLabel } = useFinanceSlips({ activeTab, filteredTransactions, openSlipWithData })

provide(financePageKey, {
    activeTab,
    activeTabLabel,
    addTransaction,
    applyBulkAction,
    bulkApplying,
    bulkForm,
    bulkTargetUsers,
    capitalInflow,
    confirmPayrollRun,
    confirmReconciliation,
    confirmSinglePayment,
    downloadSlip,
    expandedRow,
    filteredItems,
    financeLoaded,
    formatBulkRating,
    newTx,
    openReconcileModal,
    payUser,
    paymentProcessing,
    paymentSuccess,
    paymentTarget,
    payrollProcessing,
    payrollSuccess,
    payrollSummary,
    pendingCOD,
    reconcileAmount,
    reconcileDiff,
    reconcileModalOpen,
    searchQuery,
    selectedItem,
    showBulkActionModal,
    showPaymentModal,
    showPayrollModal,
    showTransactionModal,
    tabs,
    toggleRow,
    totalExpenses,
    totalPayrollDue,
    totalRevenue,
    txTypeLabel,
})
</script>
