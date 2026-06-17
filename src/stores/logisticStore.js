import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authenticatedJsonRequest, getStoredAccessToken } from '@/config/api'

const CREDENTIAL_CACHE_KEY = 'logistic_manager_created_credentials'

const asArray = (value) => Array.isArray(value) ? value : []
const asStringId = (value, fallback = 'all') => value == null ? fallback : String(value)
const asWarehouseId = (value) => {
    if (value == null) return null
    const normalized = String(value)
    return normalized && normalized.toLowerCase() !== 'all' ? normalized : null
}
const financeScopeFor = (warehouseId) => warehouseId && warehouseId !== 'all' ? String(warehouseId) : 'all'

function normalizeReturnStatus(status) {
    if (status === 'Inspected') return 'Physically Inspected'
    return status
}

function deriveReturnFlowType(item) {
    const explicit = item.flow_type || item.flowType || null
    if (explicit) return explicit

    const status = normalizeReturnStatus(item.status || '')
    if (['Under Review', 'Claims Reviewed'].includes(status)) {
        return 'photo_review'
    }
    if (
        ['Pickup Requested', 'Pickup Approved', 'Pickup Rejected', 'Pickup Scheduled', 'Collected', 'At Warehouse', 'Physically Inspected'].includes(status) ||
        item.wm_disposition ||
        item.wm_graded_at ||
        item.wm_grader_name
    ) {
        return 'pickup_inspection'
    }
    return null
}

function mapReturnRecord(item) {
    const flowType = deriveReturnFlowType(item)
    return {
        id: asStringId(item.id),
        hubId: asWarehouseId(item.hub_id),
        orderId: item.order_id ? String(item.order_id) : '',
        customer: item.customer,
        reason: item.reason,
        condition: item.condition,
        status: normalizeReturnStatus(item.status),
        flow_type: flowType,
        originalPrice: item.original_price,
        refundAmount: item.refund_amount,
        images: item.images || [],
        referenceCode: item.reference_code,
        walletCredited: item.wallet_credited ?? false,
        wmDisposition: item.wm_disposition || null,
        wmGenuineness: typeof item.wm_is_genuine === 'boolean' ? item.wm_is_genuine : undefined,
        wmRecommendedSettlement: item.wm_recommended_outcome || null,
        wmRemarks: item.wm_inspection_remarks || null,
        wmActualCondition: flowType === 'pickup_inspection' ? item.condition || null : null,
        wmDamageSeverity: flowType === 'photo_review' ? item.condition || null : null,
        wmGradedAt: item.wm_graded_at || null,
        wmGraderName: item.wm_grader_name || null,
        transportChargeAmount: Number(item.transport_charge_amount || 0),
        transportChargeWalletCollected: Number(item.transport_charge_wallet_collected || 0),
        transportChargePendingAmount: Number(item.transport_charge_pending_amount || 0),
        transportChargeStatus: item.transport_charge_status || null,
        transportChargeAppliedAt: item.transport_charge_applied_at || null,
        isUrgent: item.is_urgent ?? false,
        urgentReason: item.urgent_reason || null,
    }
}

function loadCredentialCache() {
    try {
        return JSON.parse(localStorage.getItem(CREDENTIAL_CACHE_KEY) || '{}')
    } catch {
        return {}
    }
}

function persistCredentialCache(cache) {
    localStorage.setItem(CREDENTIAL_CACHE_KEY, JSON.stringify(cache))
}

function authHeaders(extra = {}) {
    const token = getStoredAccessToken()
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...extra,
    }
}

function roleLabel(role) {
    if (role === 'LOGISTIC_MANAGER') return 'Logistic Manager'
    if (role === 'WAREHOUSE_MANAGER') return 'Warehouse Manager'
    if (role === 'DISPATCHER') return 'Dispatcher'
    if (role === 'DRIVER') return 'Driver'
    if (role === 'AI_AGENT' || role === 'AI_SUPPORT' || role === 'CUSTOMER_SUPPORT') return 'Customer Support'
    if (role === 'VENDOR') return 'Vendor'
    return role || 'User'
}

function roleApiValue(role) {
    const normalized = String(role || 'DRIVER')
        .trim()
        .replace(/\s+/g, '_')
        .replace(/-/g, '_')
        .toUpperCase()

    if (normalized === 'CUSTOMER_SUPPORT' || normalized === 'AI_SUPPORT') {
        return 'AI_AGENT'
    }

    return normalized
}

async function apiRequest(path, options = {}) {
    return authenticatedJsonRequest(`api/v1${path}`, options)
}

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

    function normalizeUserRecord(user) {
        const cachedCredentials = credentialCache.value[String(user.email || '').toLowerCase()] || null
        return {
            id: asStringId(user.id),
            hubId: asWarehouseId(user.hub_id ?? user.warehouse_id),
            name: user.name,
            email: user.email,
            role: roleLabel(user.role),
            status: user.status || (user.is_active ? 'Active' : 'Inactive'),
            lastLogin: user.last_login || '',
            username: user.username,
            password: cachedCredentials?.password || '',
            pending_payout: user.pending_payout ?? 0,
            mobile: user.mobile ?? user.phone,
            mobileVerified: user.mobile_verified ?? Boolean(user.phone || user.mobile),
            emailVerified: user.email_verified ?? true,
            avatar: user.avatar,
            approvalStatus: user.approval_status || 'APPROVED',
            approvalNote: user.approval_note || '',
            approvalReviewedAt: user.approval_reviewed_at || '',
            companyName: user.company_name || '',
            taxId: user.tax_id || '',
            contactPerson: user.contact_person || '',
            businessEmail: user.business_email || '',
            businessPhone: user.business_phone || '',
            submittedAt: user.submitted_at || user.created_at || '',
        }
    }

    function upsertUserRecord(user) {
        const mappedUser = normalizeUserRecord(user)
        const existingIndex = users.value.findIndex((item) => item.id === mappedUser.id)
        const existingUser = existingIndex === -1 ? null : users.value[existingIndex]
        const mergedUser = existingUser ? {
            ...existingUser,
            ...mappedUser,
            avatar: mappedUser.avatar || existingUser.avatar,
            lastLogin: mappedUser.lastLogin || existingUser.lastLogin,
            pending_payout: user.pending_payout ?? existingUser.pending_payout,
            submittedAt: mappedUser.submittedAt || existingUser.submittedAt,
        } : mappedUser
        if (existingIndex === -1) {
            users.value.unshift(mergedUser)
        } else {
            users.value.splice(existingIndex, 1, mergedUser)
        }
        return mergedUser
    }

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
            status: hub.status,
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
            location: alert.location,
            recommendation: alert.recommendation,
            ...(alert.impact || {}),
        }))

        drivers.value = asArray(payload.drivers).map((driver) => ({
            id: asStringId(driver.id),
            hubId: asWarehouseId(driver.hub_id),
            name: driver.name,
            status: driver.status,
            location: driver.location,
            vehicle: driver.vehicle,
            efficiency: driver.efficiency,
            rating: driver.rating,
            safetyIncidents: driver.safety_incidents,
            fuelEfficiencyScore: driver.fuel_efficiency_score,
            avgSpeed: driver.avg_speed,
            phone: driver.phone,
            currentJob: driver.current_job,
            avatarColor: driver.avatar_color || 'bg-gray-700',
            chatHistory: driver.chat_history || [],
        }))

        topDrivers.value = asArray(payload.top_drivers).map((driver) => ({
            ...driver,
            id: asStringId(driver.id),
            hubId: asWarehouseId(driver.hubId),
        }))

        vehicles.value = asArray(payload.vehicles).map((vehicle) => ({
            id: asStringId(vehicle.id),
            hubId: asWarehouseId(vehicle.hub_id),
            type: vehicle.type,
            code: vehicle.code,
            model: vehicle.model,
            year: vehicle.year,
            licensePlate: vehicle.license_plate,
            status: vehicle.status,
            driver: vehicle.driver,
            fuelEfficiency: vehicle.fuel_efficiency,
            mileage: vehicle.mileage,
            nextService: vehicle.next_service,
            issue: vehicle.maintenance_issue,
        }))

        maintenance.value = asArray(payload.maintenance).map((item) => ({
            id: asStringId(item.id),
            hubId: asWarehouseId(item.hub_id),
            issue: item.issue,
            status: item.status,
            statusClass: item.status_class,
        }))

        transactions.value = asArray(payload.transactions).map((tx) => ({
            id: asStringId(tx.id),
            hubId: asWarehouseId(tx.hub_id),
            transactionCode: tx.transaction_code || '',
            date: tx.date,
            desc: tx.desc,
            type: tx.type,
            amount: tx.amount,
            status: tx.status,
            metadataJson: tx.metadata_json || {},
            relatedOrder: tx.related_order || null,
        }))

        reports.value = asArray(payload.reports).map((report) => ({
            id: asStringId(report.id),
            hubId: asWarehouseId(report.hub_id),
            title: report.title,
            date: report.date,
            icon: report.icon,
            color: report.color,
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

    async function markNotificationRead(id) {
        await apiRequest(`/logistics/notifications/${id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ read: true }),
        })
        const item = notifications.value.find((entry) => entry.id === id)
        if (item) item.read = true
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach((item) => { item.read = true })
        await apiRequest('/logistics/notifications/mark-all-read', { method: 'POST', headers: authHeaders() }).catch(() => {})
    }

    async function clearNotifications() {
        await apiRequest('/logistics/notifications', { method: 'DELETE', headers: authHeaders() })
        notifications.value = []
    }

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
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + Math.abs(created.amount)
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

    async function updateReturnStatus(rmaId, newStatus, details = {}) {
        const updatedReturn = await apiRequest(`/logistics/returns/${rmaId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                status: newStatus,
                refund_amount: details.refundAmount ?? null,
                condition: details.condition ?? null,
                notes: details.notes ?? null,
                apply_transport_charge: details.applyTransportCharge ?? false,
            }),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            const previous = returns.value[existingIndex]
            returns.value.splice(existingIndex, 1, {
                ...previous,
                ...mapReturnRecord(updatedReturn),
                wmDisposition: updatedReturn.wm_disposition ?? previous.wmDisposition ?? null,
                wmGenuineness: typeof updatedReturn.wm_is_genuine === 'boolean' ? updatedReturn.wm_is_genuine : previous.wmGenuineness,
                wmRecommendedSettlement: updatedReturn.wm_recommended_outcome ?? previous.wmRecommendedSettlement ?? null,
                wmRemarks: updatedReturn.wm_inspection_remarks ?? previous.wmRemarks ?? null,
                wmActualCondition: updatedReturn.condition ?? previous.wmActualCondition ?? null,
                wmDamageSeverity: updatedReturn.condition ?? previous.wmDamageSeverity ?? null,
                wmGradedAt: updatedReturn.wm_graded_at ?? previous.wmGradedAt ?? null,
                wmGraderName: updatedReturn.wm_grader_name ?? previous.wmGraderName ?? null,
                transportChargeAmount: Number(updatedReturn.transport_charge_amount ?? previous.transportChargeAmount ?? 0),
                transportChargeWalletCollected: Number(updatedReturn.transport_charge_wallet_collected ?? previous.transportChargeWalletCollected ?? 0),
                transportChargePendingAmount: Number(updatedReturn.transport_charge_pending_amount ?? previous.transportChargePendingAmount ?? 0),
                transportChargeStatus: updatedReturn.transport_charge_status ?? previous.transportChargeStatus ?? null,
                transportChargeAppliedAt: updatedReturn.transport_charge_applied_at ?? previous.transportChargeAppliedAt ?? null,
                notes: details.notes ?? previous.notes ?? '',
            })
        } else {
            await refresh()
        }
        return updatedReturn
    }

    async function issueReturnRefund(rmaId) {
        const result = await apiRequest(`/logistics/returns/${rmaId}/issue-refund`, {
            method: 'POST',
            headers: authHeaders(),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            returns.value.splice(existingIndex, 1, {
                ...returns.value[existingIndex],
                status: 'Refunded',
                walletCredited: true,
            })
        }
        return result
    }

    async function scheduleReturnPickup(rmaId) {
        const updatedCase = await apiRequest(`/logistics/returns/${rmaId}/schedule-pickup`, {
            method: 'POST',
            headers: authHeaders(),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            returns.value.splice(existingIndex, 1, {
                ...returns.value[existingIndex],
                ...mapReturnRecord(updatedCase),
                status: normalizeReturnStatus(updatedCase.status || 'Pickup Scheduled'),
            })
        }
        return updatedCase
    }

    async function fetchAlerts() {
        try {
            const data = await apiRequest('/logistics/alerts', { headers: authHeaders() })
            if (Array.isArray(data)) {
                alerts.value = data.map(alert => ({
                    id: String(alert.id),
                    type: alert.type,
                    title: alert.title,
                    description: alert.description,
                    severity: alert.severity,
                    icon: alert.icon || 'warning',
                    timestamp: alert.timestamp,
                    location: alert.location,
                    recommendation: alert.recommendation,
                    ...(alert.impact || {}),
                }))
            }
        } catch (_) {}
    }

    async function addAlert(alert) {
        await apiRequest('/logistics/alerts', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(alert),
        })
        await refresh()
    }

    async function resolveAlert(id) {
        await apiRequest(`/logistics/alerts/${id}/resolve`, {
            method: 'POST',
            headers: authHeaders(),
        })
        alerts.value = alerts.value.filter((item) => item.id !== id)
        closeModal()
    }

    async function sendMessageToDriver(driverId, text) {
        const driver = drivers.value.find((item) => item.id === String(driverId))
        if (!driver) return
        driver.chatHistory.push({
            id: Date.now(),
            text,
            sender: 'dispatch',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        })
    }

    function getManagerDriverThreadName(driverOrName) {
        const rawName = typeof driverOrName === 'string'
            ? driverOrName
            : driverOrName?.name
        const safeName = String(rawName || '').trim()
        return safeName || 'Unknown Driver'
    }

    function findManagerDriverThread(driver) {
        if (!driver) return null
        const threadName = getManagerDriverThreadName(driver)
        // Match by exact name OR the legacy "LM Driver: X" format
        return chats.value.find(
            (chat) => chat.name === threadName || chat.name === `LM Driver: ${threadName}`
        ) || null
    }

    async function fetchWmChats() {
        const data = await apiRequest('/logistics/chats', { headers: authHeaders() })
        chats.value = (Array.isArray(data) ? data : []).map((item) => ({
            id: String(item.id),
            hubId: asWarehouseId(item.hub_id),
            name: item.name,
            time: item.time || '',
            lastMessage: item.last_message || '',
            status: item.status || 'Offline',
            phone: item.phone || null,
            muted: item.muted || false,
            messages: (item.messages || []).map((m) => ({
                id: String(m.id),
                text: m.text,
                sender: m.sender,
                time: m.time,
            })),
        }))
        return chats.value
    }

    async function sendChatMessage(threadId, text) {
        const updated = await apiRequest(`/logistics/chats/${threadId}/messages`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ text, sender: 'me' }),
        })
        const mappedMessages = (updated.messages || []).map((m) => ({
            id: String(m.id),
            text: m.text,
            sender: m.sender,
            time: m.time,
        }))
        // Sync local state
        const idx = chats.value.findIndex((c) => c.id === String(threadId))
        if (idx !== -1) {
            chats.value[idx].messages = mappedMessages
            chats.value[idx].lastMessage = updated.last_message || text
            chats.value[idx].time = updated.time || 'Just now'
        }
        return { messages: mappedMessages }
    }

    async function createChatThread(name, phone = null, warehouseId = null) {
        const created = await apiRequest('/logistics/chats', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ name, phone, warehouse_id: warehouseId }),
        })
        const mappedThread = {
            id: String(created.id),
            hubId: asWarehouseId(created.hub_id),
            name: created.name,
            time: created.time || 'Just now',
            lastMessage: created.last_message || '',
            status: created.status || 'Online',
            phone: created.phone || null,
            muted: false,
            messages: (created.messages || []).map((m) => ({
                id: String(m.id),
                text: m.text,
                sender: m.sender,
                time: m.time,
            })),
        }
        const existingIdx = chats.value.findIndex((chat) => chat.id === String(created.id))
        if (existingIdx !== -1) {
            chats.value[existingIdx] = mappedThread
        } else {
            chats.value.unshift(mappedThread)
        }
        return mappedThread
    }

    async function ensureManagerDriverThread(driver) {
        if (!driver?.name) throw new Error('Driver context is required')

        const existing = findManagerDriverThread(driver)
        if (existing) return existing

        const created = await createChatThread(
            getManagerDriverThreadName(driver),
            driver.phone || null,
            driver.hubId || driver.warehouseId || null,
        )
        return created
    }

    async function deleteChatThread(threadId) {
        await apiRequest(`/logistics/chats/${threadId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        chats.value = chats.value.filter((c) => c.id !== String(threadId))
    }

    async function muteChatThread(threadId, muted) {
        const updated = await apiRequest(`/logistics/chats/${threadId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ muted }),
        })
        const chat = chats.value.find((c) => c.id === String(threadId))
        if (chat) chat.muted = updated.muted
    }

    function taskFromApi(item) {
        return {
            id: String(item.id),
            text: item.text,
            status: item.status || 'To Do',
            targetTime: item.target_time ? new Date(item.target_time).getTime() : null,
            repeat: item.repeat || 'none',
            createdAt: item.created_at ? new Date(item.created_at).getTime() : Date.now(),
            lastAlertTime: item.last_alert_time ? new Date(item.last_alert_time).getTime() : null,
            silenced: item.silenced || false,
            remaining: '',
        }
    }

    async function fetchTasks() {
        const data = await apiRequest('/logistics/tasks', { headers: authHeaders() })
        tasks.value = asArray(data).map(taskFromApi)
    }

    async function createTask(payload) {
        const body = {
            text: payload.text,
            status: payload.status || 'To Do',
            target_time: payload.targetTime ? new Date(payload.targetTime).toISOString() : null,
            repeat: payload.repeat || 'none',
        }
        const data = await apiRequest('/logistics/tasks', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        tasks.value.unshift(taskFromApi(data))
    }

    async function deleteTask(id) {
        await apiRequest(`/logistics/tasks/${id}`, { method: 'DELETE', headers: authHeaders() })
        tasks.value = tasks.value.filter((t) => t.id !== String(id))
    }

    async function patchTask(id, updates) {
        const body = {}
        if (updates.status !== undefined) body.status = updates.status
        if (updates.silenced !== undefined) body.silenced = updates.silenced
        if (updates.text !== undefined) body.text = updates.text
        if (updates.targetTime !== undefined) body.target_time = updates.targetTime ? new Date(updates.targetTime).toISOString() : null
        if (updates.repeat !== undefined) body.repeat = updates.repeat
        if (updates.lastAlertTime !== undefined) body.last_alert_time = updates.lastAlertTime ? new Date(updates.lastAlertTime).toISOString() : null
        const data = await apiRequest(`/logistics/tasks/${id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        const t = tasks.value.find((t) => t.id === String(id))
        if (t && data) Object.assign(t, taskFromApi(data))
    }

    async function clearDoneTasks() {
        const doneIds = tasks.value.filter((t) => t.status === 'Done').map((t) => t.id)
        tasks.value = tasks.value.filter((t) => t.status !== 'Done')
        await Promise.all(doneIds.map((id) => apiRequest(`/logistics/tasks/${id}`, { method: 'DELETE', headers: authHeaders() }).catch(() => {})))
    }

    async function fetchNotifications() {
        const data = await apiRequest('/logistics/notifications', { headers: authHeaders() })
        notifications.value = asArray(data).map((item) => ({
            id: asStringId(item.id),
            title: item.title,
            message: item.message,
            time: item.time,
            read: item.read,
            type: item.type,
        }))
    }

    async function sendBroadcast(payload) {
        return await apiRequest('/logistics/notifications/broadcast', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload),
        })
    }

    async function updateDriverStatus(driverId, newStatus) {
        try {
            await apiRequest(`/logistics/drivers/${driverId}`, {
                method: 'PUT',
                headers: authHeaders(),
                body: JSON.stringify({ status: newStatus }),
            })
            await refresh()
        } catch (e) {
            // Fallback to local update if API fails
            const driver = drivers.value.find((item) => item.id === String(driverId))
            if (driver) driver.status = newStatus
        }
    }

    async function updateVehicle(vehicleId, fields) {
        await apiRequest(`/logistics/vehicles/${vehicleId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(fields),
        })
        await refresh()
    }

    async function addVehicle(vehicleData) {
        try {
            await apiRequest('/logistics/vehicles', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    code: vehicleData.id,
                    vehicle_type: vehicleData.type,
                    warehouse_id: vehicleData.hubId && vehicleData.hubId !== 'all' ? vehicleData.hubId : null,
                    assigned_driver_id: vehicleData.driverId || null,
                    model: vehicleData.model,
                    year: vehicleData.year || new Date().getFullYear(),
                    license_plate: vehicleData.licensePlate,
                    status: vehicleData.status || 'Active',
                    fuel_efficiency: vehicleData.fuelEfficiency || 'Pending Calibration',
                    mileage: vehicleData.mileage || 0,
                    maintenance_issue: vehicleData.issue || null,
                }),
            })
            await refresh()
        } catch (e) {
            console.warn("Backend /vehicles not implemented, mocking local state", e)
            vehicles.value.push({
                id: vehicleData.id,
                hubId: vehicleData.hubId && vehicleData.hubId !== 'all' ? String(vehicleData.hubId) : null,
                type: vehicleData.type,
                code: vehicleData.id,
                model: vehicleData.model,
                year: vehicleData.year || new Date().getFullYear(),
                licensePlate: vehicleData.licensePlate,
                status: 'Active',
                driver: vehicleData.driver || 'Unassigned',
                fuelEfficiency: '10.5 mpg',
                mileage: '0 mi',
                nextService: '3 Months',
                issue: 'None'
            })
        }
    }

    async function updateVehicleStatus(vehicleId, newStatus) {
        await apiRequest(`/logistics/vehicles/${vehicleId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ status: newStatus }),
        })
        await refresh()
    }

    async function addDriver(driverData) {
        await apiRequest('/logistics/drivers', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: driverData.name,
                email: driverData.email,
                phone: driverData.phone || null,
                warehouse_id: driverData.warehouse_id && driverData.warehouse_id !== 'all' ? driverData.warehouse_id : null,
                status: driverData.status || 'Active',
                current_location: driverData.current_location || null,
            }),
        })
        await refresh()
    }

    async function addHub(hubData) {
        await apiRequest('/warehouses', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: hubData.name,
                address: hubData.location,
                capacity_limit: hubData.capacity || 1000,
                hub_status: hubData.status || null,
            }),
        })
        await refresh()
    }

    async function updateHub(hubData) {
        await apiRequest(`/warehouses/${hubData.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: hubData.name,
                address: hubData.location,
                capacity_limit: hubData.capacity || 1000,
                is_active: hubData.status !== 'Inactive',
                hub_status: hubData.status || null,
            }),
        })
        await refresh()
    }

    async function deleteHub(hubId) {
        await apiRequest(`/warehouses/${hubId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        if (activeWarehouse.value === String(hubId)) activeWarehouse.value = 'all'
        await refresh()
    }

    async function addUser(userData) {
        const created = await apiRequest('/users', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: userData.name,
                username: userData.username || null,
                email: userData.email,
                phone: userData.mobile || userData.phone || null,
                password: userData.password || '12345678',
                role: roleApiValue(userData.role),
                warehouse_id: userData.hubId && userData.hubId !== 'all' ? userData.hubId : null,
            }),
        })

        if (userData.email && userData.password) {
            credentialCache.value[String(userData.email).toLowerCase()] = {
                username: created?.username || userData.username || '',
                password: userData.password,
            }
            persistCredentialCache(credentialCache.value)
        }

        await refresh()
        return created
    }

    async function updateUser(email, updates) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        const updated = await apiRequest(`/users/${user.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: updates.name,
                phone: updates.mobile || updates.phone || null,
                is_active: updates.status ? updates.status === 'Active' : undefined,
            }),
        })
        upsertUserRecord(updated)
    }

    async function deleteUser(email) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        await apiRequest(`/users/${user.id}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        delete credentialCache.value[String(email).toLowerCase()]
        persistCredentialCache(credentialCache.value)
        await refresh()
    }

    async function toggleUserStatus(email) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        const updated = await apiRequest(`/users/${user.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ is_active: user.status !== 'Active' }),
        })
        upsertUserRecord(updated)
    }

    async function approveVendor(userId, note = '') {
        const updated = await apiRequest(`/users/${userId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                approval_status: 'APPROVED',
                approval_note: note || null,
                is_active: true,
            }),
        })
        return upsertUserRecord(updated)
    }

    async function rejectVendor(userId, note = '') {
        const updated = await apiRequest(`/users/${userId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                approval_status: 'REJECTED',
                approval_note: note || null,
                is_active: false,
            }),
        })
        return upsertUserRecord(updated)
    }

    async function createZone(zoneData) {
        // Ensure we have a valid warehouse_id (required, cannot be null)
        const warehouseId = zoneData.hubId && zoneData.hubId !== 'all'
            ? zoneData.hubId
            : (hubs.value[0]?.id || null)

        if (!warehouseId) {
            throw new Error('A warehouse must be selected to create a zone')
        }

        const created = await apiRequest('/logistics/zones', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                warehouse_id: warehouseId,
                name: zoneData.name,
                zone_type: zoneData.type,
                radius_km: parseFloat(zoneData.radius) || 1.0,
                status: zoneData.status || 'Active',
                color_token: zoneData.color || 'blue',
                lat: zoneData.lat ?? null,
                lng: zoneData.lng ?? null,
            }),
        })
        await refresh()
        return created
    }

    async function updateZone(zoneId, zoneData) {
        await apiRequest(`/logistics/zones/${zoneId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: zoneData.name,
                zone_type: zoneData.type,
                radius_km: parseFloat(zoneData.radius) || 1.0,
                status: zoneData.status || 'Active',
                color_token: zoneData.color || 'blue',
                lat: zoneData.lat ?? null,
                lng: zoneData.lng ?? null,
            }),
        })
        await refresh()
    }

    async function deleteZone(zoneId) {
        await apiRequest(`/logistics/zones/${zoneId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        await refresh()
    }

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
        // Deduct total paid from revenue (payroll is an outflow)
        const total = result.total || 0
        if (total > 0) {
            financeSummary.value.total_revenue = Math.max(0, (financeSummary.value.total_revenue || 0) - total)
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + total
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
        reportAiInsights,
        reportMetrics,
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
