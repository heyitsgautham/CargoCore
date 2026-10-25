import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { apiRequest, authHeaders } from './logistic/api'

import {
    asArray,
    asStringId,
    asWarehouseId,
    financeScopeFor,
    mapReturnRecord,
    loadCredentialCache,
} from './logistic/mappers'
import { useLogisticTasks } from './logistic/tasks'
import { useLogisticChats } from './logistic/chats'
import { useLogisticNotifications } from './logistic/notifications'
import { useLogisticAlerts } from './logistic/alerts'
import { useLogisticReturns } from './logistic/returns'
import { useLogisticFleet } from './logistic/fleet'
import { useLogisticHubs } from './logistic/hubs'
import { useLogisticUsers } from './logistic/users'
import { useLogisticZones } from './logistic/zones'

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
    const credentialCache = ref(loadCredentialCache())

    const { normalizeUserRecord, addUser, updateUser, deleteUser, toggleUserStatus, approveVendor, rejectVendor } = useLogisticUsers({ users, credentialCache, refresh })

    function hydrate(payload) {
        const stats = payload.dashboard_stats || {}

        dashboardStats.value = {
            ordersToday: stats.orders_today || 0,
            activeDeliveries: stats.active_deliveries || 0,
            processing: stats.processing || 0,
            deliverySuccess: stats.delivery_success || 0,
            revenueToday: stats.revenue_today || 0,
            ordersTrend: stats.orders_trend || 0,
            revenueTrend: stats.revenue_trend || 0,
            slaCompliance: { week: asArray(stats.sla_week), month: asArray(stats.sla_week) },
            revenue: { week: asArray(stats.revenue_week), month: asArray(stats.revenue_week) },
            orders: { week: asArray(stats.orders_week), month: asArray(stats.orders_week) },
        }

        hubs.value = asArray(payload.hubs).map((hub) => ({
            id: asStringId(hub.id),
            hubCode: hub.hub_code,
            name: hub.name,
            location: hub.location,
            address: hub.address,
            lat: hub.lat || null,
            lng: hub.lng || null,
            manager: hub.manager,
            managerInitials: hub.manager_initials,
            capacity: hub.capacity,
            efficiency: hub.efficiency,
            staffActive: hub.staff_active,
            staffTotal: hub.staff_total,
            vehiclesActive: hub.vehicles_active,
            vehiclesTotal: hub.vehicles_total,
            processRate: hub.process_rate,
            status: hub.status || 'Active',
            isActive: (hub.status || 'Active') !== 'Archived',
            statusColor: hub.status_color,
            bg: hub.bg,
        }))

        alerts.value = asArray(payload.alerts).map((alert) => ({
            id: asStringId(alert.id),
            type: alert.type,
            title: alert.title,
            description: alert.description,
            severity: alert.severity,
            icon: alert.icon || 'warning',
            timestamp: alert.timestamp,
        }))

        drivers.value = asArray(payload.drivers).map((driver) => ({
            id: asStringId(driver.id),
            hubId: asWarehouseId(driver.hub_id ?? driver.hubId),
            name: driver.name,
            status: driver.status || 'Active',
            location: driver.location || '',
            vehicle: driver.vehicle || '',
            efficiency: Number(driver.efficiency ?? 0),
            rating: Number(driver.rating ?? 0),
            safetyIncidents: Number(driver.safety_incidents ?? driver.safetyIncidents ?? 0),
            fuelEfficiencyScore: driver.fuel_efficiency_score || driver.fuelEfficiencyScore || '',
            avgSpeed: driver.avg_speed || driver.avgSpeed || '',
            phone: driver.phone || '',
            currentJob: driver.current_job || driver.currentJob || '',
            avatarColor: driver.avatar_color || driver.avatarColor || 'bg-blue-600',
            chatHistory: asArray(driver.chat_history ?? driver.chatHistory),
        }))

        topDrivers.value = asArray(payload.top_drivers).map((driver) => {
            const linkedDriver = drivers.value.find((item) =>
                item.id === asStringId(driver.id) || item.name === driver.name
            )

            return {
                id: asStringId(driver.id),
                hubId: asWarehouseId(driver.hubId ?? driver.hub_id ?? linkedDriver?.hubId),
                name: driver.name,
                rating: Number(driver.rating ?? linkedDriver?.rating ?? 0),
                trips: Number(driver.trips ?? 0),
                ontime: Number(driver.ontime ?? 0),
                avatar: driver.avatar || null,
                avatarColor: linkedDriver?.avatarColor || 'bg-blue-600',
                status: linkedDriver?.status || 'Active',
                vehicle: linkedDriver?.vehicle || '',
                currentJob: linkedDriver?.currentJob || '',
            }
        })

        vehicles.value = asArray(payload.vehicles).map((vehicle) => ({
            id: asStringId(vehicle.id),
            hubId: asWarehouseId(vehicle.hub_id ?? vehicle.hubId),
            code: vehicle.code || asStringId(vehicle.id),
            type: vehicle.type || vehicle.vehicle_type || '',
            model: vehicle.model || '',
            year: vehicle.year || null,
            licensePlate: vehicle.license_plate || vehicle.licensePlate || '',
            status: vehicle.status || 'Active',
            driver: vehicle.driver || 'Unassigned',
            fuelEfficiency: vehicle.fuel_efficiency || vehicle.fuelEfficiency || '',
            mileage: vehicle.mileage ?? 0,
            nextService: vehicle.next_service || vehicle.nextService || '',
            issue: vehicle.maintenance_issue || vehicle.issue || null,
            fuelLevelPct: vehicle.fuel_level_pct ?? vehicle.fuelLevelPct ?? null,
            rangeKm: vehicle.range_km ?? vehicle.rangeKm ?? null,
            seatCapacity: vehicle.seat_capacity ?? vehicle.seatCapacity ?? null,
            cargoCapacityTons: vehicle.cargo_capacity_tons ?? vehicle.cargoCapacityTons ?? null,
            telemetryStatus: vehicle.telemetry_status || vehicle.telemetryStatus || null,
            telemetryLastSeen: vehicle.telemetry_last_seen || vehicle.telemetryLastSeen || null,
        }))

        maintenance.value = asArray(payload.maintenance).map((item) => ({
            id: asStringId(item.id),
            hubId: asWarehouseId(item.hub_id ?? item.hubId),
            issue: item.issue || '',
            status: item.status || '',
            statusClass: item.status_class || item.statusClass || '',
        }))

        users.value = asArray(payload.users).map(normalizeUserRecord)

        returns.value = asArray(payload.returns).map(mapReturnRecord)

        equipmentLedger.value = asArray(payload.equipment_ledger).map((eq) => ({
            id: asStringId(eq.id),
            hubId: asWarehouseId(eq.hub_id),
            itemType: eq.item_type,
            issuedCount: eq.issued_count,
            returnedCount: eq.returned_count,
            referenceCode: eq.reference_code,
            status: eq.status,
        }))

        zones.value = asArray(payload.zones).map((zone) => ({
            id: asStringId(zone.id),
            hubId: asWarehouseId(zone.hub_id),
            name: zone.name,
            type: zone.type,
            radius: zone.radius,
            status: zone.status,
            color: zone.color,
            lat: zone.lat ?? null,
            lng: zone.lng ?? null,
        }))

        chats.value = asArray(payload.chats).map((chat) => ({
            id: asStringId(chat.id),
            hubId: asWarehouseId(chat.hub_id),
            name: chat.name,
            time: chat.time,
            lastMessage: chat.last_message,
            status: chat.status,
            phone: chat.phone,
            muted: chat.muted,
            messages: asArray(chat.messages),
        }))

        escalations.value = asArray(payload.escalations).map((item) => ({
            id: asStringId(item.id),
            hubId: asWarehouseId(item.hub_id),
            title: item.title,
            priority: item.priority,
            from: item.from_name,
            role: item.role,
            time: item.time,
            description: item.description,
            actionDetails: item.action_details,
            status: item.status,
        }))

        inventory.value = asArray(payload.inventory).map((item) => ({
            ...item,
            id: asStringId(item.id),
            hubId: asWarehouseId(item.hubId),
        }))

        notifications.value = asArray(payload.notifications).map((item) => ({
            id: asStringId(item.id),
            title: item.title,
            message: item.message,
            time: item.time,
            createdAt: item.created_at,
            read: item.read,
            type: item.type,
        }))

        tasks.value = asArray(payload.tasks).map((task) => ({
            id: asStringId(task.id),
            text: task.text,
            status: task.status,
            targetTime: task.target_time,
            repeat: task.repeat,
            createdAt: task.created_at,
            lastAlertTime: task.last_alert_time,
            silenced: task.silenced,
            remaining: '',
        }))

        aiSuggestionChips.value = asArray(payload.ai_suggestion_chips)
        aiMessages.value = asArray(payload.ai_messages).map((message, index) => ({
            id: message.id || `ai-${index}`,
            role: message.role,
            text: message.text,
            data: message.data || null,
            time: message.time,
        }))
        // Bootstrap correctly computes total_revenue, total_expenses, total_payroll_due, pending_cod
        financeSummary.value = payload.finance_summary || {}

        // ── Transactions (Overview tab) ────────────────────────────────────────
        transactions.value = asArray(payload.transactions).map((tx) => ({
            id: asStringId(tx.id),
            hubId: asWarehouseId(tx.hub_id),
            transactionCode: tx.transaction_code || '',
            date: tx.date,
            desc: tx.desc || tx.description || '',
            type: tx.type || tx.transaction_type || '',
            amount: Number(tx.amount ?? 0),
            status: tx.status || 'Completed',
            metadataJson: tx.metadata_json || {},
            relatedOrder: tx.related_order || null,
        }))

        financeCodRecords.value = asArray(payload.finance_cod_records).map((item) => ({ ...item, id: asStringId(item.id), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
        financeStaffRecords.value = asArray(payload.finance_staff_records).map((item) => ({ ...item, id: asStringId(item.id), userId: asStringId(item.userId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
        financeDriverRecords.value = asArray(payload.finance_driver_records).map((item) => ({ ...item, id: asStringId(item.id), userId: asStringId(item.userId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
        fleetLogs.value = payload.fleet_logs || {}
        vehicleDocuments.value = asArray(payload.vehicle_documents).map((item) => ({ ...item, id: asStringId(item.id), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
        driverDocuments.value = asArray(payload.driver_documents).map((item) => ({ ...item, id: asStringId(item.id), driverId: asStringId(item.driverId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
        reportAiInsights.value = asArray(payload.report_ai_insights)
        reportDamageClaims.value = asArray(payload.report_damage_claims)
        reportSecurityLogs.value = asArray(payload.report_security_logs)
        reportMetrics.value = payload.report_metrics || {}

        creditBalance.value = transactions.value
            .filter((item) => item.amount > 0)
            .reduce((sum, item) => sum + item.amount, 0)
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

    async function addTransaction(tx) {
        const created = await apiRequest('/logistics/transactions', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                warehouse_id: tx.hubId && tx.hubId !== 'all' ? tx.hubId : null,
                description: tx.desc,
                transaction_type: tx.type,
                amount: tx.amount,
                status: tx.status || 'Completed',
            }),
        })

        transactions.value = [{
            id: asStringId(created.id),
            hubId: asWarehouseId(created.hub_id),
            transactionCode: created.transaction_code || '',
            date: created.date,
            desc: created.desc,
            type: created.type,
            amount: created.amount,
            status: created.status,
            metadataJson: created.metadata_json || {},
            relatedOrder: created.related_order || null,
        }, ...transactions.value]

        if (created.amount > 0) {
            financeSummary.value.total_revenue = (financeSummary.value.total_revenue || 0) + created.amount
            creditBalance.value += created.amount
        } else {
            const expense = Math.abs(created.amount)
            // Only update the Expenses counter — never touch Revenue.
            // Revenue = what customers paid; Expenses = what we spent. They are separate.
            // Capital absorbs the shortfall if expenses exceed revenue.
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + expense
            financeSummary.value.capital_invested = Math.max(0, (financeSummary.value.capital_invested || 0) - expense)
        }
    }

        /**
     * Fetch live finance summary from /api/v1/finance/summary.
     * Returns real DB aggregations so revenue starts at 0 on empty DB.
     */
    async function fetchFinanceSummary(warehouseId = activeWarehouse.value) {
        try {
            const scope = financeScopeFor(warehouseId)
            const query = scope === 'all' ? '' : `?warehouse_id=${encodeURIComponent(scope)}`
            const data = await apiRequest(`/finance/summary${query}`, { headers: authHeaders() })
            financeSummary.value = {
                ...data,
                _warehouseScope: scope,
            }
            return financeSummary.value
        } catch (e) {
            console.warn('[fetchFinanceSummary] failed (non-fatal):', e)
            return financeSummary.value
        }
    }

    async function askAiDispatcher(query) {
        try {
            const payload = { message: query, context: 'dispatcher' }
            if (dispatcherAiSessionId.value) payload.session_id = dispatcherAiSessionId.value
            const response = await apiRequest('/ai/chat', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(payload),
            })
            if (response.session_id) dispatcherAiSessionId.value = response.session_id
            let text = response.message || response.reply || response.text || 'No response.'
            text = text.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            return { text }
        } catch (err) {
            return { text: 'AI engine unavailable. Please try again.' }
        }
    }

    async function askAi(query) {
        const userMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            text: query,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
        aiMessages.value.push(userMessage)

        try {
            const payload = { message: query, context: 'logistic_manager' }
            if (aiSessionId.value) {
                payload.session_id = aiSessionId.value
            }
            const response = await apiRequest('/ai/chat', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(payload),
            })
            if (response.session_id) {
                aiSessionId.value = response.session_id
            }
            
            let renderedText = response.message || response.reply || response.text || 'Process completed.'
            // Convert basic markdown to HTML for Vue v-html
            renderedText = renderedText.replace(/\n*```sql(.*?)```\n*/gs, '<br><pre class="bg-gray-800 text-green-400 p-3 text-xs rounded-xl my-2 overflow-x-auto shadow-inner">$1</pre><br>')
                .replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                .replace(/\*(.*?)\*/g, '<i>$1</i>')

            const aiMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                text: renderedText,
                data: null,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            aiMessages.value.push(aiMessage)
            return aiMessage
        } catch (err) {
            console.error('AI Query Error:', err)
            const errorMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                text: `<span class="text-red-500 font-bold">Error:</span> ${err.message || 'Could not connect to the AI engine. Please try again.'}`,
                data: null,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            aiMessages.value.push(errorMessage)
            return errorMessage
        }
    }

    const { updateReturnStatus, issueReturnRefund, scheduleReturnPickup } = useLogisticReturns({ returns, refresh })

    const { fetchAlerts, addAlert, resolveAlert } = useLogisticAlerts({ alerts, refresh, closeModal })

    const { sendMessageToDriver, updateDriverStatus, updateVehicle, addVehicle, updateVehicleStatus, addDriver } = useLogisticFleet({ drivers, vehicles, refresh })

    const { getManagerDriverThreadName, findManagerDriverThread, fetchWmChats, sendChatMessage, createChatThread, ensureManagerDriverThread, deleteChatThread, muteChatThread } = useLogisticChats({ chats })

    const { fetchTasks, createTask, deleteTask, patchTask, clearDoneTasks } = useLogisticTasks({ tasks })

    const { addHub, updateHub, archiveHub, restoreHub, deleteHub } = useLogisticHubs({ activeWarehouse, refresh })

    const { createZone, updateZone, deleteZone } = useLogisticZones({ hubs, refresh })

    function addFunds(amount) {
        if (amount > 0) creditBalance.value += amount
    }

    function markFinanceRecordPaid(collection, id) {
        const targetCollections = {
            cod: financeCodRecords.value,
            staff: financeStaffRecords.value,
            drivers: financeDriverRecords.value,
        }
        const items = targetCollections[collection]
        if (!items) return
        const item = items.find((entry) => entry.id === id)
        if (item) item.status = collection === 'cod' ? 'Completed' : 'Paid'
    }

    async function runPayroll(userPayouts) {
        // userPayouts: [{user_id, amount, record_type, name}]
        const result = await apiRequest('/finance/payroll/run', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ user_payouts: userPayouts }),
        })
        // Payroll is an outflow — only update Expenses and Capital, never Revenue.
        const total = result.total || 0
        if (total > 0) {
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + total
            financeSummary.value.capital_invested = Math.max(0, (financeSummary.value.capital_invested || 0) - total)
        }
        return result
    }

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
