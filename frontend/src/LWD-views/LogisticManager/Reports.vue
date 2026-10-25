<template>
    <div class="h-full flex flex-col space-y-6">
        <!-- Header & Control Bar -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shrink-0">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">analytics</span> Reports & Command Center
                </h2>
                <p class="text-xs text-gray-500 font-mono mt-1">
                    Live Operational Intelligence • {{ store.activeWarehouseName }}
                </p>
            </div>

            <div class="flex flex-wrap gap-2 items-center">
                <!-- AI Query Bar -->
                <div class="relative group mr-2">
                    <input v-model="aiQuery" @keyup.enter="handleAiQuery" :disabled="aiThinking" type="text"
                        placeholder="Ask AI: 'Show me top spending vendors...'"
                        class="pl-10 pr-10 py-2 bg-white dark:bg-white/5 border border-purple-200 dark:border-purple-500/30 rounded-full text-sm w-64 focus:w-80 transition-all outline-none focus:ring-2 focus:ring-purple-500/50 shadow-sm disabled:opacity-60">
                    <span v-if="!aiThinking"
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-purple-500">auto_awesome</span>
                    <span v-else
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-purple-500 animate-spin">progress_activity</span>
                    <button @click="handleAiQuery" :disabled="aiThinking || !aiQuery"
                        class="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full bg-purple-500 text-white disabled:opacity-40 hover:bg-purple-600 transition-colors">
                        <span class="material-symbols-outlined text-[14px]">send</span>
                    </button>
                </div>

                <select v-model="timeRange"
                    class="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50 text-gray-700 dark:text-gray-200 cursor-pointer">
                    <option value="today" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Today (Live)</option>
                    <option value="7d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 7 Days</option>
                    <option value="30d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 30 Days</option>
                    <option value="ytd" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Year to Date</option>
                </select>

                <button @click="downloadCurrentView"
                    class="bg-white hover:bg-gray-50 dark:bg-white/10 dark:hover:bg-white/20 text-gray-700 dark:text-white font-bold px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all border border-gray-200 dark:border-white/10">
                    <span class="material-symbols-outlined">download</span> Export View
                </button>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div
            class="flex gap-1 overflow-x-auto pb-2 shrink-0 border-b border-gray-200 dark:border-white/10 no-scrollbar">
            <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
                class="px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all flex items-center gap-2"
                :class="activeTab === tab.id ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
                <span class="material-symbols-outlined text-[18px]">{{ tab.icon }}</span>
                {{ tab.label }}
            </button>
        </div>

        <!-- Main Content Area -->
        <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10">

            <ControlTowerTab />

            <FinancialsTab />

            <AttendanceTab />

            <WorkforceTab />

            <AssetsTab />

            <ClaimsModal />

            <ReturnsTab />

            <RestockModal />

            <SecurityAuditTab />

            <ReportHistoryTab />

        </div>

        <InvestmentModal />

        <!-- Notification Toast -->
        <div v-if="notification" class="fixed bottom-6 right-6 z-50 animate-fade-in-up transition-all cursor-pointer"
            @click="notification = null">
            <div class="px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 border backdrop-blur-md"
                :class="notification.type === 'success' ? 'bg-green-50/90 dark:bg-green-900/90 border-green-200 dark:border-green-700 text-green-800 dark:text-green-100' : 'bg-blue-50/90 dark:bg-blue-900/90 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-100'">
                <span class="material-symbols-outlined text-2xl">{{ notification.type === 'success' ? 'check_circle' :
                    'info' }}</span>
                <div>
                    <h4 class="font-bold text-sm uppercase tracking-wide opacity-80 mb-0.5">{{ notification.type }}</h4>
                    <span class="font-bold text-sm block leading-tight">{{ notification.msg }}</span>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import ControlTowerTab from './reports/ControlTowerTab.vue'
import FinancialsTab from './reports/FinancialsTab.vue'
import AttendanceTab from './reports/AttendanceTab.vue'
import WorkforceTab from './reports/WorkforceTab.vue'
import AssetsTab from './reports/AssetsTab.vue'
import ClaimsModal from './reports/ClaimsModal.vue'
import ReturnsTab from './reports/ReturnsTab.vue'
import RestockModal from './reports/RestockModal.vue'
import SecurityAuditTab from './reports/SecurityAuditTab.vue'
import ReportHistoryTab from './reports/ReportHistoryTab.vue'
import InvestmentModal from './reports/InvestmentModal.vue'
import { reportsPageKey } from './reports/reportsPageContext'
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js'
import {
    chartOptions,
    doughnutOptions,
    dwellTimeChart,
    fuelAnomalyText as describeFuelAnomaly,
    fuelAuditChart,
    hubEfficiencyChart,
    paymentReconChart,
    procurementCapitalChart,
    revenueStreamChart,
    rmaReasonsChart,
    rmaVsOrdersChart,
    safetyIncidentChart,
    shiftEfficiencyChart,
    slaChart,
    vendorLeadTimeChart,
    workforceChart,
} from './reports/reportCharts'
import { attendanceCounts, downloadCsv, exportRows, loggedInOn, userLeave } from './reports/reportRows'
import { useRestockReview } from './reports/useRestockReview'
import { useCapitalInvestment } from './reports/useCapitalInvestment'

// Register ChartJS Components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend)

const store = useLogisticStore()
const authStore = useAuthStore()

// Poll alerts every 30s so LM sees dispatcher resolutions without manual refresh
let alertPollTimer = null

function handleGotoTab(e) {
    if (e.detail) activeTab.value = e.detail
}

onMounted(async () => {
    store.fetchAlerts()
    alertPollTimer = setInterval(() => store.fetchAlerts(), 30000)
    // Listen for tab-jump from the global emergency overlay pill
    document.addEventListener('lm:goto-tab', handleGotoTab)
    // Ensure finance summary is fresh so the capital_flow_empty alert renders correctly
    await store.initialize().catch(() => {})
    store.fetchFinanceSummary(store.activeWarehouse).catch(() => {})
})
onUnmounted(() => {
    clearInterval(alertPollTimer)
    document.removeEventListener('lm:goto-tab', handleGotoTab)
})

const financeSummary = computed(() => store.activeFinanceSummary)

// State
const activeTab = ref('control_tower')
const timeRange = ref('today')
const aiQuery = ref('')

// Tabs Structure
const tabs = [
    { id: 'control_tower', label: 'Control Tower', icon: 'cell_tower' },
    { id: 'financials', label: 'Finances', icon: 'account_balance' },
    { id: 'attendance', label: 'Attendance', icon: 'calendar_month' },
    { id: 'workforce', label: 'Workforce', icon: 'groups' },
    { id: 'assets', label: 'Inventory (Boxes/Tools)', icon: 'inventory_2' },
    { id: 'returns', label: 'Returns (RMA)', icon: 'assignment_return' },
    { id: 'security_audit', label: 'System Logs', icon: 'security' },
    { id: 'reports_history', label: 'Analytics & History', icon: 'history' }
]

const getInventoryCount = (keywords) => {
    return store.filteredInventory
        .filter(i => keywords.some(k => i.name.includes(k) || i.category.includes(k)))
        .reduce((sum, item) => sum + item.quantity, 0)
}

const aiThinking = ref(false)
const notification = ref(null)

const showNotification = (msg, type = 'success') => {
    notification.value = { msg, type }
    setTimeout(() => notification.value = null, 3000)
}

const today = () => new Date().toISOString().slice(0, 10)

const downloadReport = (id) => {
    const report = store.filteredReports.find(r => r.id === id)
    if (!report) return
    downloadCsv(`report_${id}_${today()}.csv`, [
        ['Report ID', 'Title', 'Date', 'Warehouse'],
        [report.id, report.title, report.date, store.activeWarehouseName || ''],
    ])
    showNotification(`Report #${id} Downloaded`, 'success')
}

const downloadCurrentView = () => {
    const tab = activeTab.value
    const rows = exportRows(tab, store, todayStr)
    if (rows.length <= 1) {
        showNotification('No data to export for this view', 'info')
        return
    }
    downloadCsv(`${tab}_${today()}.csv`, rows)
    showNotification(`"${tabs.find(t => t.id === tab)?.label}" exported`, 'success')
}

const handleAiQuery = async () => {
    if (!aiQuery.value) return
    aiThinking.value = true
    try {
        const response = await store.askAi(aiQuery.value)
        if (response?.text) {
            store.reportAiInsights.unshift(response.text)
        }
        aiQuery.value = ''
        showNotification('AI Analysis Added to Briefing', 'success')
    } finally {
        aiThinking.value = false
    }
}

// ── Control Tower ──────────────────────────────────────────────────────────
const avgDriverEfficiency = computed(() => {
    const drivers = store.filteredDrivers.filter(d => d.efficiency != null)
    if (!drivers.length) return 0
    return Math.round(drivers.reduce((sum, d) => sum + (d.efficiency || 0), 0) / drivers.length)
})

const vehiclesInMaintenance = computed(() =>
    store.filteredVehicles.filter(v => /maintenance|shop|repair/i.test(v.status || '') || v.issue).length
)

const totalOrders = computed(() => store.dashboardStats.ordersToday || 0)
const completedOrders = computed(() => Math.floor(totalOrders.value * (store.dashboardStats.deliverySuccess / 100)))
const completionRate = computed(() => Math.round((completedOrders.value / totalOrders.value) * 100))

const crisisAlerts = computed(() => (store.alerts || []).map(a => ({ ...a, desc: a.description })))
const aiInsights = computed(() => store.reportAiInsights || [])
const reportMetrics = computed(() => store.reportMetrics || {})

// ── Attendance (presence = logged in today) ────────────────────────────────
const todayStr = today()
const loginedToday = (user) => loggedInOn(user, todayStr)
const attendance = computed(() => attendanceCounts(store.filteredUsers, todayStr))
const attendancePresentCount = computed(() => attendance.value.present)
const attendanceOnLeaveCount = computed(() => attendance.value.onLeave)
const attendanceUnplannedCount = computed(() => attendance.value.unplanned)
const attendancePresentPct = computed(() => attendance.value.presentPct)

// ── Charts ─────────────────────────────────────────────────────────────────
const revenueStreamData = computed(() => revenueStreamChart(store.filteredTransactions))
const paymentReconData = computed(() => paymentReconChart(reportMetrics.value))
const fuelAuditData = computed(() => fuelAuditChart(reportMetrics.value))
const fuelAnomalyText = computed(() => describeFuelAnomaly(store.filteredTransactions))
const procurementCapitalData = computed(() => procurementCapitalChart(financeSummary.value))
const workforceData = computed(() => workforceChart(reportMetrics.value))
const vendorLeadTimeData = computed(() => vendorLeadTimeChart(reportMetrics.value))
const safetyIncidentData = computed(() => safetyIncidentChart(reportMetrics.value))
const shiftEfficiencyData = computed(() => shiftEfficiencyChart(reportMetrics.value))
const dwellTimeData = computed(() => dwellTimeChart(reportMetrics.value))
const rmaVsOrdersData = computed(() => rmaVsOrdersChart(reportMetrics.value))
const rmaReasonsData = computed(() => rmaReasonsChart(reportMetrics.value, store.filteredReturns))
const analyticsSLAData = computed(() => slaChart(store.dashboardStats))
const analyticsHubData = computed(() => hubEfficiencyChart(store.hubs))

// ── Damage claims ──────────────────────────────────────────────────────────
const claimsModalOpen = ref(false)
const selectedClaim = ref(null)
const damageClaims = computed(() => store.filteredDamageClaims || [])

const openClaimModal = (claim) => {
    selectedClaim.value = claim
    claimsModalOpen.value = true
}

const resolveClaim = (decision) => {
    if (!selectedClaim.value) return
    showNotification(`Claim resolved: ${decision}. Notification sent to reporter.`, 'success')
    selectedClaim.value.status = 'Resolved'
    claimsModalOpen.value = false
    selectedClaim.value = null
}

// ── Restock review and capital investment ──────────────────────────────────
const { restockModalOpen, restockItems, escalatedRestockCount, openRestockModal, resolveRestock } =
    useRestockReview({ store, authStore, showNotification })
const { investmentModalOpen, investmentSubmitting, investmentForm, submitInvestment } =
    useCapitalInvestment({ store, authStore, showNotification })

const capitalTransactions = computed(() =>
    (store.filteredTransactions || []).filter(tx => tx.type === 'CAPITAL_INVESTMENT')
)


provide(reportsPageKey, {
    activeTab,
    aiInsights,
    aiThinking,
    analyticsHubData,
    analyticsSLAData,
    attendanceOnLeaveCount,
    attendancePresentCount,
    attendancePresentPct,
    attendanceUnplannedCount,
    avgDriverEfficiency,
    capitalTransactions,
    chartOptions,
    claimsModalOpen,
    completedOrders,
    completionRate,
    crisisAlerts,
    damageClaims,
    doughnutOptions,
    downloadReport,
    dwellTimeData,
    escalatedRestockCount,
    financeSummary,
    fuelAnomalyText,
    fuelAuditData,
    getInventoryCount,
    investmentForm,
    investmentModalOpen,
    investmentSubmitting,
    loginedToday,
    openClaimModal,
    openRestockModal,
    paymentReconData,
    procurementCapitalData,
    resolveClaim,
    resolveRestock,
    restockItems,
    restockModalOpen,
    revenueStreamData,
    rmaReasonsData,
    rmaVsOrdersData,
    safetyIncidentData,
    selectedClaim,
    shiftEfficiencyData,
    store,
    submitInvestment,
    totalOrders,
    userLeave,
    vehiclesInMaintenance,
    vendorLeadTimeData,
    workforceData,
})
</script>

<style scoped src="./reports/Reports.css"></style>
