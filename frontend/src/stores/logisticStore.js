import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { apiRequest, authHeaders } from './logistic/api'

import {
    asWarehouseId,
    financeScopeFor,
} from './logistic/mappers'
import { mapBootstrap } from './logistic/bootstrapMapping'
import { useLogisticTasks } from './logistic/tasks'
import { useLogisticChats } from './logistic/chats'
import { useLogisticNotifications } from './logistic/notifications'
import { useLogisticAlerts } from './logistic/alerts'
import { useLogisticReturns } from './logistic/returns'
import { useLogisticFleet } from './logistic/fleet'
import { useLogisticHubs } from './logistic/hubs'
import { useLogisticUsers } from './logistic/users'
import { useLogisticZones } from './logistic/zones'
import { useLogisticFinance } from './logistic/finance'
import { useLogisticAssistant } from './logistic/assistant'

export const useLogisticStore = defineStore('logistic', () => {
    const initialized = ref(false)
    const isLoading = ref(false)
    const error = ref('')

    const activeWarehouse = ref('all')
    const activeModal = ref(null)
    const selectedItem = ref(null)
    const comparedWarehouses = ref([])
    const searchQuery = ref('')
    const isSearchOpen = ref(false)

    const dashboardStats = ref({
        ordersToday: 0,
        activeDeliveries: 0,
        processing: 0,
        deliverySuccess: 0,
        revenueToday: 0,
        ordersTrend: 0,
        revenueTrend: 0,
        slaCompliance: { week: [] },
        revenue: { week: [] },
        orders: { week: [] },
    })

    const hubs = ref([])
    const alerts = ref([])
    const drivers = ref([])
    const topDrivers = ref([])
    const vehicles = ref([])
    const maintenance = ref([])
    const transactions = ref([])
    const reports = ref([])
    const users = ref([])
    const returns = ref([])
    const zones = ref([])
    const chats = ref([])
    const escalations = ref([])
    const inventory = ref([])
    const notifications = ref([])
    const tasks = ref([])
    const creditBalance = ref(0)
    const pinnedHubs = ref([])
    const aiSuggestionChips = ref([])
    const aiMessages = ref([])
    const aiSessionId = ref(null)
    const dispatcherAiSessionId = ref(null) // separate session for dispatcher role
    const financeSummary = ref({})
    const financeCodRecords = ref([])
    const financeStaffRecords = ref([])
    const financeDriverRecords = ref([])
    const fleetLogs = ref({})
    const vehicleDocuments = ref([])
    const driverDocuments = ref([])
    const reportDamageClaims = ref([])
    const reportSecurityLogs = ref([])
    const reportMetrics = ref({})
    const equipmentLedger = ref([])
    const reportAiInsights = ref([])

    const { normalizeUserRecord, addUser, updateUser, deleteUser, toggleUserStatus, approveVendor, rejectVendor, lastCreatedCredentials, clearCreatedCredentials } = useLogisticUsers({ users, refresh })

    function hydrate(payload) {
        const fields = {
            dashboardStats,
            hubs,
            alerts,
            drivers,
            topDrivers,
            vehicles,
            maintenance,
            users,
            returns,
            equipmentLedger,
            zones,
            chats,
            escalations,
            inventory,
            notifications,
            tasks,
            aiSuggestionChips,
            aiMessages,
            financeSummary,
            transactions,
            reports,
            financeCodRecords,
            financeStaffRecords,
            financeDriverRecords,
            fleetLogs,
            vehicleDocuments,
            driverDocuments,
            reportAiInsights,
            reportDamageClaims,
            reportSecurityLogs,
            reportMetrics,
            creditBalance,
        }
        for (const [key, value] of Object.entries(mapBootstrap(payload, normalizeUserRecord))) {
            fields[key].value = value
        }
    }

    async function refresh() {
        const payload = await apiRequest('/logistics/bootstrap', { headers: authHeaders() })
        hydrate(payload)
        initialized.value = true
        await fetchFinanceSummary(activeWarehouse.value)
    }

    async function initialize(force = false) {
        if (initialized.value && !force) return
        isLoading.value = true
        error.value = ''
        try {
            await refresh()
        } catch (err) {
            error.value = err.message || 'Failed to load logistics data'
            throw err
        } finally {
            isLoading.value = false
        }
    }

    const activeWarehouseName = computed(() => {
        if (activeWarehouse.value === 'all') return 'All Warehouses'
        const hub = hubs.value.find((item) => item.id === activeWarehouse.value)
        return hub ? hub.name : 'Unknown Hub'
    })
    const activeHubs = computed(() => hubs.value.filter((hub) => hub.isActive !== false && hub.status !== 'Archived'))

    const unreadNotificationsCount = computed(() => notifications.value.filter((item) => !item.read).length)
    const filterByWarehouse = (items) => (
        activeWarehouse.value === 'all'
            ? items
            : items.filter((item) => asWarehouseId(item?.hubId) === activeWarehouse.value)
    )

    const filteredDrivers = computed(() => {
        let result = filterByWarehouse(drivers.value)
        if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase()
            result = result.filter((item) => item.name.toLowerCase().includes(q) || item.id.toLowerCase().includes(q))
        }
        return result
    })

    const filteredTopDrivers = computed(() => filterByWarehouse(topDrivers.value))
    const filteredVehicles = computed(() => filterByWarehouse(vehicles.value))
    const filteredMaintenance = computed(() => filterByWarehouse(maintenance.value))
    const filteredTransactions = computed(() => filterByWarehouse(transactions.value))
    const filteredReports = computed(() => filterByWarehouse(reports.value))
    const filteredUsers = computed(() => filterByWarehouse(users.value))
    const filteredReturns = computed(() => filterByWarehouse(returns.value))
    const filteredZones = computed(() => filterByWarehouse(zones.value))
    const filteredChats = computed(() => {
        const all = filterByWarehouse(chats.value)
        // Deduplicate: if a "LM Driver: X" legacy thread exists alongside a plain "X"
        // thread, hide the legacy one to avoid duplicate entries in the sidebar.
        const plainNames = new Set(
            all.filter((c) => !c.name.startsWith('LM Driver: ')).map((c) => c.name)
        )
        return all.filter(
            (c) => !c.name.startsWith('LM Driver: ') || !plainNames.has(c.name.slice('LM Driver: '.length))
        )
    })
    const filteredEscalations = computed(() =>
        filterByWarehouse(escalations.value).filter((item) => item.status === 'OPEN')
    )
    const filteredInventory = computed(() => filterByWarehouse(inventory.value))
    const filteredFinanceCodRecords = computed(() => filterByWarehouse(financeCodRecords.value))
    const filteredFinanceStaffRecords = computed(() => filterByWarehouse(financeStaffRecords.value))
    const filteredFinanceDriverRecords = computed(() => filterByWarehouse(financeDriverRecords.value))
    const filteredVehicleDocuments = computed(() => filterByWarehouse(vehicleDocuments.value))
    const filteredDriverDocuments = computed(() => filterByWarehouse(driverDocuments.value))
    const filteredDamageClaims = computed(() => reportDamageClaims.value)
    const filteredSecurityLogs = computed(() => reportSecurityLogs.value)
    const activeFinanceSummary = computed(() => {
        const scope = financeScopeFor(activeWarehouse.value)
        const summaryMatchesScope = (financeSummary.value?._warehouseScope || 'all') === scope
        const fallbackRevenue = filteredTransactions.value
            .filter((item) => item.amount > 0 && item.type !== 'CAPITAL_INVESTMENT')
            .reduce((sum, item) => sum + item.amount, 0)
        const fallbackExpenses = Math.abs(
            filteredTransactions.value
                .filter((item) => item.amount < 0 && item.type !== 'REVENUE_REFUND')
                .reduce((sum, item) => sum + item.amount, 0)
        )
        const fallbackPendingCod = filteredFinanceCodRecords.value
            .filter((item) => item.status === 'Pending')
            .reduce((sum, item) => sum + (item.amount || 0), 0)
        const fallbackPayrollDue = [...filteredFinanceStaffRecords.value, ...filteredFinanceDriverRecords.value]
            .filter((item) => item.status === 'Pending')
            .reduce((sum, item) => sum + (item.amount || 0), 0)
        const fallbackProcurement = filteredTransactions.value
            .filter((item) => item.type === 'EXPENSE_PROCUREMENT')
            .reduce((sum, item) => sum + Math.abs(item.amount || 0), 0)
        const fallbackCapital = filteredTransactions.value
            .filter((item) => item.type === 'CAPITAL_INVESTMENT')
            .reduce((sum, item) => sum + (item.amount || 0), 0)

        return {
            ...(summaryMatchesScope ? financeSummary.value : {}),
            total_revenue: summaryMatchesScope && financeSummary.value?.total_revenue != null ? financeSummary.value.total_revenue : fallbackRevenue,
            total_expenses: summaryMatchesScope && financeSummary.value?.total_expenses != null ? financeSummary.value.total_expenses : fallbackExpenses,
            pending_cod: summaryMatchesScope && financeSummary.value?.pending_cod != null ? financeSummary.value.pending_cod : fallbackPendingCod,
            total_payroll_due: summaryMatchesScope && financeSummary.value?.total_payroll_due != null ? financeSummary.value.total_payroll_due : fallbackPayrollDue,
            procurement_expenses: summaryMatchesScope && financeSummary.value?.procurement_expenses != null ? financeSummary.value.procurement_expenses : fallbackProcurement,
            capital_invested: summaryMatchesScope && financeSummary.value?.capital_invested != null ? financeSummary.value.capital_invested : fallbackCapital,
            // capital_flow_empty:
            // 1. Trust backend flag when available (most accurate)
            // 2. Fall back to local computation ONLY after store is initialized
            //    (prevents false-positive flash before data loads)
            capital_flow_empty: (() => {
                // Backend confirmed it
                if (summaryMatchesScope && financeSummary.value?.capital_flow_empty === true) return true
                // Backend confirmed it's NOT empty
                if (summaryMatchesScope && financeSummary.value?.capital_flow_empty === false) return false
                // No backend data yet — only use local fallback AFTER full init (no flash)
                if (!initialized.value || isLoading.value) return false
                // Alert when revenue is drained to 0 (capital still may cover, but warn now)
                return fallbackRevenue <= 0
            })(),
        }
    })

    function openModal(name, data = null) {
        activeModal.value = name
        selectedItem.value = data
        isSearchOpen.value = false
    }

    function closeModal() {
        activeModal.value = null
        selectedItem.value = null
    }

    function setWarehouse(id) {
        activeWarehouse.value = String(id)
        if (activeModal.value === 'warehouse-select') closeModal()
        if (initialized.value) {
            fetchFinanceSummary(activeWarehouse.value).catch(() => {})
        }
    }

    function togglePin(hub) {
        const exists = pinnedHubs.value.find((item) => item.id === hub.id)
        pinnedHubs.value = exists ? pinnedHubs.value.filter((item) => item.id !== hub.id) : [...pinnedHubs.value, { id: hub.id, name: hub.name }]
    }

    const { fetchNotifications, markNotificationRead, markAllNotificationsRead, clearNotifications, sendBroadcast } = useLogisticNotifications({ notifications })

    function toggleSearch() {
        isSearchOpen.value = !isSearchOpen.value
        if (!isSearchOpen.value) searchQuery.value = ''
    }

        /**
     * Fetch live finance summary from /api/v1/finance/summary.
     * Returns real DB aggregations so revenue starts at 0 on empty DB.
     */
    const { updateReturnStatus, issueReturnRefund, scheduleReturnPickup } = useLogisticReturns({ returns, refresh })

    const { fetchAlerts, addAlert, resolveAlert } = useLogisticAlerts({ alerts, refresh, closeModal })

    const { sendMessageToDriver, updateDriverStatus, updateVehicle, addVehicle, updateVehicleStatus, addDriver } = useLogisticFleet({ drivers, vehicles, refresh })

    const { getManagerDriverThreadName, findManagerDriverThread, fetchWmChats, sendChatMessage, createChatThread, ensureManagerDriverThread, deleteChatThread, muteChatThread } = useLogisticChats({ chats })

    const { fetchTasks, createTask, deleteTask, patchTask, clearDoneTasks } = useLogisticTasks({ tasks })

    const { addHub, updateHub, archiveHub, restoreHub, deleteHub } = useLogisticHubs({ activeWarehouse, refresh })

    const { createZone, updateZone, deleteZone } = useLogisticZones({ hubs, refresh })

    async function uploadDocument(payload) {
        await apiRequest('/logistics/documents', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload),
        })
        await refresh()
    }

    async function updateDocumentStatus(docId, newStatus, notes = null) {
        await apiRequest(`/logistics/documents/${docId}/status`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ status: newStatus, notes }),
        })
        await refresh()
    }

    const {
        addTransaction,
        fetchFinanceSummary,
        addFunds,
        markFinanceRecordPaid,
        runPayroll,
    } = useLogisticFinance({
        activeWarehouse,
        creditBalance,
        financeCodRecords,
        financeDriverRecords,
        financeStaffRecords,
        financeSummary,
        transactions,
    })

    const { askAiDispatcher, askAi } = useLogisticAssistant({ aiMessages, aiSessionId, dispatcherAiSessionId })

    return {
        initialized,
        isLoading,
        error,
        activeWarehouse,
        activeModal,
        selectedItem,
        comparedWarehouses,
        dashboardStats,
        alerts,
        drivers,
        topDrivers,
        vehicles,
        maintenance,
        transactions,
        users,
        returns,
        zones,
        chats,
        inventory,
        reports,
        hubs,
        pinnedHubs,
        searchQuery,
        isSearchOpen,
        notifications,
        tasks,
        creditBalance,
        escalations,
        aiSuggestionChips,
        aiMessages,
        financeSummary,
        activeFinanceSummary,
        financeCodRecords,
        financeStaffRecords,
        financeDriverRecords,
        fleetLogs,
        vehicleDocuments,
        driverDocuments,
        reportAiInsights,
        reportDamageClaims,
        reportSecurityLogs,
        reportMetrics,
        initialize,
        refresh,
        addFunds,
        activeWarehouseName,
        activeHubs,
        unreadNotificationsCount,
        filteredDrivers,
        filteredTopDrivers,
        filteredVehicles,
        filteredMaintenance,
        filteredTransactions,
        filteredReports,
        filteredUsers,
        filteredReturns,
        filteredZones,
        filteredChats,
        filteredEscalations,
        warehouseManagerUsers: computed(() =>
            users.value.filter((u) => u.role === 'Warehouse Manager')
        ),
        filteredInventory,
        filteredFinanceCodRecords,
        filteredFinanceStaffRecords,
        filteredFinanceDriverRecords,
        filteredVehicleDocuments,
        filteredDriverDocuments,
        filteredDamageClaims,
        filteredSecurityLogs,
        equipmentLedger,
        openModal,
        closeModal,
        addTransaction,
        fetchFinanceSummary,
        askAi,
        askAiDispatcher,
        updateReturnStatus,
        issueReturnRefund,
        scheduleReturnPickup,
        addAlert,
        fetchAlerts,
        resolveAlert,
        setWarehouse,
        togglePin,
        fetchNotifications,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
        toggleSearch,
        fetchTasks,
        createTask,
        deleteTask,
        patchTask,
        clearDoneTasks,
        fetchWmChats,
        sendMessageToDriver,
        sendChatMessage,
        createChatThread,
        getManagerDriverThreadName,
        findManagerDriverThread,
        ensureManagerDriverThread,
        deleteChatThread,
        muteChatThread,
        sendBroadcast,

        updateDriverStatus,
        addVehicle,
        updateVehicleStatus,
        updateVehicle,
        addDriver,
        addHub,
        updateHub,
        archiveHub,
        restoreHub,
        deleteHub,
        addUser,
        lastCreatedCredentials,
        clearCreatedCredentials,
        updateUser,
        deleteUser,
        toggleUserStatus,
        approveVendor,
        rejectVendor,
        createZone,
        updateZone,
        deleteZone,
        markFinanceRecordPaid,
        runPayroll,
        uploadDocument,
        updateDocumentStatus,
    }
})
