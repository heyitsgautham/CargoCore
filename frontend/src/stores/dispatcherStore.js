import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { driverStatusColor, generateAvatar } from './dispatcher/orderMetrics'
import { useDispatchDrivers } from './dispatcher/drivers'
import { useDispatchOrderMapping } from './dispatcher/orderMapping'
import { useDispatchOrders } from './dispatcher/orders'
import { useDispatchAlerts } from './dispatcher/alerts'
import { useDispatchManifests } from './dispatcher/manifests'
import { useDispatchComms } from './dispatcher/comms'

export const useDispatcherStore = defineStore('dispatcher', () => {
    const ls = useLogisticStore()
    const authStore = useAuthStore()

    // Pending orders fetched from backend
    const pendingOrders = ref([])
    const ordersLoading = ref(false)

    // Vehicles fetched directly (DISPATCHER can't access /logistics/bootstrap)
    const _vehicles = ref([])
    const vehiclesLoading = ref(false)

    // Active orders (ASSIGNED / IN_TRANSIT) for Order Status Control
    const activeOrders = ref([])
    const activeOrdersLoading = ref(false)

    // Drivers fetched directly — dispatcher has access to /logistics/drivers
    const _drivers = ref([])
    const driversLoading = ref(false)

    // Chats fetched directly — bypasses bootstrap for DISPATCHER role
    const _chats = ref([])
    const chatsLoading = ref(false)

    // Zones fetched directly — dispatch should see manager-created zones without bootstrap access
    const _zones = ref([])
    const zonesLoaded = ref(false)

    // All contactable users (DRIVER + WAREHOUSE_MANAGER) from backend
    const _contacts = ref([])

    // Local suspend overrides are only a fallback while the backend update is in flight.
    // The persisted driver profile status is the source of truth across dispatcher/LM views.
    const _suspendedIds = ref(new Set(JSON.parse(localStorage.getItem('cc_dispatcher_suspended') || '[]')))

    let _pollInterval = null

    async function initialize() {
        try {
            await ls.initialize()
        } catch (_) {
            // /logistics/bootstrap requires LOGISTIC_MANAGER role — skip gracefully for DISPATCHER
        }
        await Promise.all([fetchOrders(), fetchDrivers(), fetchVehicles(), fetchActiveOrders(), fetchChats(), fetchContacts(), fetchAlerts(), fetchZones(), fetchManifests()])
        // React to warehouse marking orders ready (same-tab event)
        if (typeof window !== 'undefined') {
            window.removeEventListener('warehouse-orders-updated', fetchOrders)
            window.addEventListener('warehouse-orders-updated', fetchOrders)
        }
        // Poll every 30 seconds to pick up cross-tab/cross-user updates
        if (!_pollInterval) {
            _pollInterval = setInterval(() => {
                fetchOrders().catch(() => {})
                fetchActiveOrders().catch(() => {})
                fetchAlerts().catch(() => {}) // Also poll alerts for crisis updates
            }, 30_000)
        }
    }

    const READY_STATUSES = ['QC_PASSED', 'READY_FOR_DISPATCH', 'DISPATCHED', 'qc_passed', 'ready_for_dispatch', 'dispatched']
    const LOADING_STATUSES = ['ON_DOCK', 'on_dock']

    // ── Dispatcher-shaped drivers ──────────────────────────────────────────
    // Use directly fetched drivers (_drivers) so DISPATCHER role works without bootstrap access
    const dispatcherDrivers = computed(() => {
        const source = _drivers.value.length > 0 ? _drivers.value : ls.filteredDrivers
        const now = Date.now()
        const todayMidnight = new Date(); todayMidnight.setHours(0, 0, 0, 0)
        const todayMs = todayMidnight.getTime()

        return source.map((d) => {
            const driverId = String(d.id)
            // Only ASSIGNED + IN_TRANSIT orders count as active for this driver
            const driverOrders = activeOrders.value.filter(o =>
                o.driverId === driverId &&
                (o.status === 'ASSIGNED' || o.status === 'IN_TRANSIT')
            )
            const assignedCount = driverOrders.length

            // ── Current Load ────────────────────────────────────────────────
            // Real: total cargo weight from active orders. Fall back to efficiency_score
            // when no orders are assigned (driver is standing by).
            const totalWeightKg = driverOrders.reduce((sum, o) => sum + Number(o.weight || 0), 0)
            const weightBasedLoad = totalWeightKg > 0
                ? Math.min(100, Math.round(totalWeightKg / 10))   // 1000 kg = 100%
                : assignedCount > 0
                    ? Math.min(100, assignedCount * 20)             // each order ≈ 20% load
                    : (d.efficiency ?? 0)                           // standby: use efficiency score

            // ── HOS (Hours of Service) ───────────────────────────────────────
            // Real: time elapsed since the driver's earliest active order was created today.
            // If no active orders → 0h (not on shift).
            const orderTimestamps = driverOrders
                .map(o => {
                    const ts = o.lastUpdated && o.lastUpdated !== '—' ? new Date(o.lastUpdated).getTime() : 0
                    return ts > todayMs ? ts : 0
                })
                .filter(Boolean)
            const shiftStartMs = orderTimestamps.length > 0 ? Math.min(...orderTimestamps) : null
            const hosHours = shiftStartMs
                ? parseFloat(((now - shiftStartMs) / 3_600_000).toFixed(1))
                : 0
            const maxHours = 10  // standard HOS limit
            const hosPct = Math.min(100, (hosHours / maxHours) * 100)
            const breakDue = hosHours > 0 && hosPct >= 75
            const breakDueIn = breakDue
                ? `${parseFloat(((maxHours - hosHours))).toFixed(1)}h`
                : null

            const locallySuspended = _suspendedIds.value.has(driverId)
            const isSuspended = locallySuspended || d.status === 'Suspended'
            const effectiveStatus = isSuspended ? 'Suspended' : (d.status || 'Active')
            const color = isSuspended ? 'bg-red-500' : driverStatusColor(d.status)

            // Vehicle: resolve the actual plate/code from the vehicles list.
            // If driver has active orders, resolve from the order's vehicleId;
            // otherwise show the vehicle stored on the driver profile.
            let activeVehicle = ''
            if (driverOrders.length > 0) {
                const orderVehicleId = driverOrders[0].vehicleId
                const orderVehicleRecord = orderVehicleId
                    ? _vehicles.value.find(v => String(v.id) === String(orderVehicleId))
                        || ls.filteredVehicles.find(v => String(v.id) === String(orderVehicleId))
                    : null
                const resolvedCode = orderVehicleRecord
                    ? (orderVehicleRecord.license_plate || orderVehicleRecord.licensePlate || orderVehicleRecord.code || orderVehicleRecord.model || '')
                    : ''
                // Use resolved code; fall back to whatever mapOrder already set
                activeVehicle = resolvedCode ||
                    (driverOrders[0].vehicle && driverOrders[0].vehicle !== '—' && !driverOrders[0].vehicle.startsWith('Vehicle ') ? driverOrders[0].vehicle : '') ||
                    d.vehicle || ''
            } else {
                activeVehicle = d.vehicle || ''
            }

            return {
                ...d,
                avatar: generateAvatar(d.name, d.id),
                statusColor: color,
                vehicle: activeVehicle,
                // Current Load — real cargo/order weight
                load: weightBasedLoad,
                totalWeightKg,
                // HOS — computed from active order timestamps
                hours: hosHours,
                maxHours,
                hosPct,
                // Shift stats — real counts
                stops: assignedCount,
                activeOrders: driverOrders,
                // Auth / suspend
                authorized: !isSuspended,
                licenseValid: true,
                suspended: isSuspended,
                maintenance: d.status === 'Maintenance',
                breakDue,
                breakDueIn,
                status: effectiveStatus,
                statusClass: isSuspended
                    ? 'bg-red-100 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-300 dark:border-red-500/20'
                    : color === 'bg-green-500'
                    ? 'bg-green-100 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/20'
                    : color === 'bg-yellow-500'
                    ? 'bg-yellow-100 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-500/20'
                    : 'bg-gray-100 dark:bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-500/20',
            }
        })
    })

    const slaProjection = computed(() => {
        const moving = activeOrders.value.filter(o =>
            o.status === 'IN_TRANSIT' || o.status === 'ASSIGNED' || o.status === 'DELIVERED'
        ).length
        const pending = pendingOrders.value.length
        const total = moving + pending
        if (!total) return { pct: 100, delta: 8 }
        const pct = Math.min(100, Math.round((moving / total) * 100))
        return { pct, delta: pct - 92 }
    })

    // ── Communication contacts — users (DRIVER + WH_MGR) merged with thread data ──
    const dispatcherContacts = computed(() => {
        // Primary: user-based contacts from /dispatch-contacts (always includes all contactable users)
        if (_contacts.value.length > 0) {
            return _contacts.value.map(c => ({
                id: String(c.user_id),
                threadId: c.thread_id ? String(c.thread_id) : null,
                name: c.name,
                role: c.role,
                type: c.role === 'WAREHOUSE_MANAGER' ? 'warehouse' : 'driver',
                online: (c.thread_status || '').toLowerCase() === 'online',
                lastMessage: c.last_message || 'No messages yet',
                avatar: generateAvatar(c.name, String(c.user_id)),
                status: c.thread_status || 'Offline',
                phone: c.phone || '',
                email: c.email || '',
                unread: 0,
                messages: (c.messages || []).map(m => ({
                    id: String(m.id),
                    from: m.sender || 'driver',
                    text: m.text || '',
                    time: m.time || '',
                    type: 'text',
                })),
            }))
        }

        // Fallback: chat threads if contacts not loaded yet
        const source = _chats.value.length > 0 ? _chats.value : ls.chats
        if (source.length > 0) {
            return source.map(c => ({
                id: String(c.id),
                threadId: String(c.id),
                name: c.name,
                role: 'DRIVER',
                type: 'driver',
                online: (c.status || '').toLowerCase() === 'online',
                lastMessage: c.last_message || c.lastMessage || '',
                avatar: generateAvatar(c.name, String(c.id)),
                status: c.status || 'Offline',
                phone: c.phone || '',
                unread: 0,
                messages: (c.messages || []).map(m => ({
                    id: String(m.id || Date.now()),
                    from: m.sender || 'driver',
                    text: m.text || '',
                    time: m.time || '',
                    type: 'text',
                })),
            }))
        }

        // Last fallback: driver profiles
        return (_drivers.value.length > 0 ? _drivers.value : ls.filteredDrivers).slice(0, 8).map(d => ({
            id: d.id,
            threadId: null,
            name: d.name,
            role: 'DRIVER',
            type: 'driver',
            online: d.status === 'Active' || d.status === 'On Route',
            lastMessage: 'No messages yet',
            avatar: generateAvatar(d.name, d.id),
            status: d.status || 'Offline',
            phone: d.phone || '',
            unread: 0,
            messages: [],
        }))
    })

    // ── Crisis/disruptions — fetched directly (DISPATCHER can't use bootstrap) ──
    const _alerts = ref([])
    const _alertsLoaded = ref(false)

    const activeCrises = computed(() => {
        const source = _alertsLoaded.value ? _alerts.value : ls.alerts
        return source
            .filter(a => a.is_active !== false && (a.severity === 'high' || a.severity === 'critical' || a.severity === 'medium'))
            .map(a => {
                // Parse location coordinates if available (format: "lat, lng")
                let lat = null, lng = null
                if (a.location && a.location.includes(',')) {
                    const [latStr, lngStr] = a.location.split(',').map(s => s.trim())
                    const parsedLat = parseFloat(latStr)
                    const parsedLng = parseFloat(lngStr)
                    if (!isNaN(parsedLat) && !isNaN(parsedLng)) {
                        lat = parsedLat
                        lng = parsedLng
                    }
                }
                // Extract driver info from impact_json if available
                const impact = a.impact || {}
                return {
                    id: a.id,
                    level: a.severity === 'critical' ? 'CRITICAL' : a.severity === 'high' ? 'HIGH' : 'MEDIUM',
                    title: a.title,
                    timeAgo: a.timestamp || 'Recent',
                    description: a.description || '',
                    affectedOrders: typeof impact === 'number' ? impact : 0,
                    actions: ['Reroute', 'Notify Drivers', 'Escalate'],
                    driver: impact.driver_name || a.location || '',
                    driverId: impact.driver_id || null,
                    alertType: a.type || impact.alert_type || 'unknown',
                    lat,
                    lng,
                    icon: a.icon || 'warning',
                    recommendation: a.recommendation || '',
                }
            })
    })

    const disruptions = computed(() => {
        const source = _alerts.value.length > 0 ? _alerts.value : ls.alerts
        return source
            .filter(a => a.severity !== 'high' && a.severity !== 'critical')
            .map(a => ({
                id: a.id,
                severity: a.severity || 'medium',
                icon: a.icon || 'warning',
                title: a.title,
                detail: a.description || a.recommendation || '',
                affected: 0,
                rerouted: false,
                etaUpdated: false,
            }))
    })

    // ── Pass-throughs from logisticStore ──────────────────────────────────
    const isLoading = computed(() => ls.isLoading || ordersLoading.value)
    const dashboardStats = computed(() => ls.dashboardStats)
    const hubs = computed(() => ls.hubs)
    // Prefer directly fetched vehicles (works for DISPATCHER role); fall back to logistic store bootstrap data
    const filteredVehicles = computed(() =>
        _vehicles.value.length > 0
            ? _vehicles.value.map(v => ({
                id: String(v.id),
                code: v.code || '',
                licensePlate: v.license_plate || v.licensePlate || '',
                model: v.model || '',
                status: v.status || '',
                type: v.type || v.vehicle_type || '',
                seatCapacity: v.seat_capacity ?? v.seatCapacity ?? null,
                cargoCapacityTons: v.cargo_capacity_tons ?? v.cargoCapacityTons ?? null,
                // Required for driver-based vehicle lookup fallback in resolveVehicleCode
                driverId: v.assigned_driver_id ? String(v.assigned_driver_id) : null,
            }))
            : ls.filteredVehicles
    )
    const filteredChats = computed(() => ls.filteredChats)
    const filteredEscalations = computed(() => ls.filteredEscalations)
    const filteredZones = computed(() => {
        if (!zonesLoaded.value) return ls.filteredZones
        const activeWarehouse = String(ls.activeWarehouse || 'all')
        if (activeWarehouse !== 'all') {
            const scopedZones = _zones.value.filter((zone) => zone.hubId === activeWarehouse)
            if (scopedZones.length) return scopedZones
        }

        const assignedWarehouseId = authStore.currentUser?.warehouse_id
            ? String(authStore.currentUser.warehouse_id)
            : null
        if (assignedWarehouseId) {
            const assignedZones = _zones.value.filter((zone) => zone.hubId === assignedWarehouseId)
            if (assignedZones.length) return assignedZones
        }

        return _zones.value
    })
    const notifications = computed(() => ls.notifications)
    const unreadNotificationsCount = computed(() => ls.unreadNotificationsCount)

    async function askAi(query) {
        return ls.askAiDispatcher(query)
    }

    async function sendMessageToDriver(driverId, text) {
        return ls.sendMessageToDriver(driverId, text)
    }

    // ── Manifests ─────────────────────────────────────────────────────────────
    const manifests = ref([])
    const manifestsLoading = ref(false)

    function markNotificationRead(id) { return ls.markNotificationRead(id) }
    function markAllNotificationsRead() { return ls.markAllNotificationsRead() }
    function clearNotifications() { return ls.clearNotifications() }

    const {
        fetchDrivers,
        toggleDriverSuspend,
        isDriverSuspended,
    } = useDispatchDrivers({ _drivers, _suspendedIds, driversLoading, ls })

    const { mapOrder } = useDispatchOrderMapping({
        LOADING_STATUSES,
        READY_STATUSES,
        _vehicles,
        ls,
    })

    const {
        fetchOrders,
        fetchActiveOrders,
        fetchOrderDetail,
        fetchClusters,
        assignOrder,
        batchAssignOrders,
    } = useDispatchOrders({
        activeOrders,
        activeOrdersLoading,
        mapOrder,
        ordersLoading,
        pendingOrders,
    })

    const { fetchAlerts, createAlert, resolveAlert } = useDispatchAlerts({ _alerts, _alertsLoaded, ls })

    const { fetchManifests, saveManifest, pushManifestToDriver } = useDispatchManifests({ manifests, manifestsLoading })

    const {
        fetchChats,
        fetchZones,
        fetchVehicles,
        fetchContacts,
        sendDispatchMessage,
        createChatForContact,
    } = useDispatchComms({
        _chats,
        _contacts,
        _vehicles,
        _zones,
        chatsLoading,
        vehiclesLoading,
        zonesLoaded,
    })

    return {
        // State
        pendingOrders,
        activeOrders,
        ordersLoading,
        activeOrdersLoading,
        isLoading,
        manifests,
        manifestsLoading,
        // Computed
        dispatcherDrivers,
        slaProjection,
        dispatcherContacts,
        activeCrises,
        disruptions,
        dashboardStats,
        hubs,
        filteredVehicles,
        filteredChats,
        filteredEscalations,
        filteredZones,
        notifications,
        unreadNotificationsCount,
        // Actions
        initialize,
        fetchOrders,
        fetchDrivers,
        fetchVehicles,
        fetchActiveOrders,
        fetchOrderDetail,
        fetchChats,
        fetchContacts,
        fetchAlerts,
        fetchZones,
        fetchClusters,
        assignOrder,
        batchAssignOrders,
        askAi,
        sendMessageToDriver,
        sendDispatchMessage,
        createChatForContact,
        createAlert,
        resolveAlert,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
        fetchManifests,
        saveManifest,
        pushManifestToDriver,
        toggleDriverSuspend,
        isDriverSuspended,
        suspendedDriverIds: _suspendedIds,
    }
})
