import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL, authenticatedJsonRequest, getStoredAccessToken } from '@/config/api'
import { buildPodData } from '@/utils/pod'

const API_BASE = API_BASE_URL

function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}

function driverStatusColor(status) {
    if (!status) return 'bg-gray-500'
    const s = status.toLowerCase()
    if (s === 'active' || s === 'on route' || s === 'on_route') return 'bg-green-500'
    if (s === 'idle' || s === 'on break' || s === 'on_break') return 'bg-yellow-500'
    return 'bg-gray-500'
}

function generateAvatar(name, id) {
    const seed = encodeURIComponent(name || id || 'driver')
    return `https://api.dicebear.com/7.x/initials/svg?seed=${seed}&backgroundColor=374151&textColor=ffffff`
}

function parseCoordinate(value) {
    if (value === null || value === undefined || value === '') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
}

function parseMetric(value) {
    if (value === null || value === undefined || value === '') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
}

function roundMetric(value) {
    return value === null ? null : Math.round(value * 100) / 100
}

function normalizeCargoMetric(value) {
    const rounded = roundMetric(value)
    return rounded !== null && rounded <= 0 ? null : rounded
}

function resolveCargoWeight(order) {
    return normalizeCargoMetric(
        parseMetric(order.cargo_weight_kg ?? order.weight ?? order.total_weight)
    )
}

function resolveCargoVolume(order) {
    const direct = parseMetric(order.cargo_volume_m3 ?? order.volume ?? order.total_volume)
    if (direct !== null) return normalizeCargoMetric(direct)

    const items = Array.isArray(order.items) ? order.items : []
    const estimatedVolume = items.reduce((sum, item) => sum + Number(item?.estimated_volume || 0), 0)
    return estimatedVolume > 0 ? normalizeCargoMetric(estimatedVolume) : null
}

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

    function _persistSuspended() {
        localStorage.setItem('cc_dispatcher_suspended', JSON.stringify([..._suspendedIds.value]))
    }

    function _setLocalSuspended(driverId, suspended) {
        const id = String(driverId)
        if (suspended) {
            _suspendedIds.value.add(id)
        } else {
            _suspendedIds.value.delete(id)
        }
        _suspendedIds.value = new Set(_suspendedIds.value)
        _persistSuspended()
    }

    function _updateLocalDriverStatus(driverId, status) {
        const id = String(driverId)
        const update = (driver) => String(driver.id) === id ? { ...driver, status } : driver
        _drivers.value = _drivers.value.map(update)

        if (Array.isArray(ls.drivers)) {
            const idx = ls.drivers.findIndex((driver) => String(driver.id) === id)
            if (idx !== -1) ls.drivers.splice(idx, 1, { ...ls.drivers[idx], status })
        }
    }

    async function _persistDriverStatus(driverId, status) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/drivers/${driverId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ status }),
        })
        if (!res.ok) return false

        const updated = normalizeDriver(await res.json())
        const idx = _drivers.value.findIndex((driver) => String(driver.id) === String(driverId))
        if (idx === -1) {
            _drivers.value.unshift(updated)
        } else {
            _drivers.value[idx] = { ..._drivers.value[idx], ...updated }
        }
        return true
    }

    async function _syncLocalSuspensionsToBackend() {
        const pendingIds = [..._suspendedIds.value]
            .filter((id) => _drivers.value.some((driver) => String(driver.id) === String(id)))
            .filter((id) => !_drivers.value.some((driver) =>
                String(driver.id) === String(id) && String(driver.status || '').toLowerCase() === 'suspended'
            ))
        if (!pendingIds.length) return

        const syncedIds = []
        await Promise.all(pendingIds.map(async (id) => {
            try {
                if (await _persistDriverStatus(id, 'Suspended')) syncedIds.push(id)
            } catch (_) {}
        }))
        syncedIds.forEach((id) => _setLocalSuspended(id, false))
    }

    async function toggleDriverSuspend(driverId) {
        const id = String(driverId)
        const wasSuspended = isDriverSuspended(id)
        const nextSuspended = !wasSuspended
        const nextStatus = nextSuspended ? 'Suspended' : 'Active'

        _setLocalSuspended(id, nextSuspended)
        _updateLocalDriverStatus(id, nextStatus)

        try {
            const saved = await _persistDriverStatus(id, nextStatus)
            if (saved) {
                _setLocalSuspended(id, false)
                await fetchDrivers()
            } else {
                _setLocalSuspended(id, wasSuspended)
                _updateLocalDriverStatus(id, wasSuspended ? 'Suspended' : 'Active')
            }
        } catch (_) {
            _setLocalSuspended(id, wasSuspended)
            _updateLocalDriverStatus(id, wasSuspended ? 'Suspended' : 'Active')
        }
    }

    function isDriverSuspended(driverId) {
        const id = String(driverId)
        return _suspendedIds.value.has(id)
            || _drivers.value.some((driver) => String(driver.id) === id && String(driver.status || '').toLowerCase() === 'suspended')
            || ls.filteredDrivers.some((driver) => String(driver.id) === id && String(driver.status || '').toLowerCase() === 'suspended')
    }

    let _pollInterval = null

    function normalizeDriver(d) {
        return {
            id: String(d.id || ''),
            hubId: String(d.hub_id || ''),
            name: d.name || '',
            status: d.status || 'Active',
            location: d.location || d.current_location || '',
            vehicle: d.vehicle || '',
            efficiency: d.efficiency ?? d.efficiency_score ?? 0,
            rating: d.rating ?? 0,
            safetyIncidents: d.safety_incidents ?? d.safetyIncidents ?? 0,
            fuelEfficiencyScore: d.fuel_efficiency_score ?? d.fuelEfficiencyScore ?? 0,
            avgSpeed: Number(d.avg_speed ?? d.avgSpeed ?? 0) || 0,
            phone: d.phone || '',
            currentJob: d.current_job ?? d.currentJob ?? '',
            avatarColor: d.avatar_color ?? d.avatarColor ?? 'bg-gray-700',
            chatHistory: d.chat_history ?? d.chatHistory ?? [],
        }
    }

    function normalizeZone(z) {
        return {
            id: String(z.id || ''),
            hubId: z.hub_id || z.hubId ? String(z.hub_id || z.hubId) : null,
            name: z.name || '',
            type: z.type || z.zone_type || '',
            radius: z.radius ?? z.radius_km ?? null,
            status: z.status || 'Active',
            color: z.color || z.color_token || '',
            lat: z.lat ?? null,
            lng: z.lng ?? null,
        }
    }

    async function fetchDrivers() {
        driversLoading.value = true
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/drivers', {
                headers: { ...authHeaders() },
            })
            const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
            _drivers.value = items.map(normalizeDriver)
            await _syncLocalSuspensionsToBackend()
        } catch (_) {
        } finally {
            driversLoading.value = false
        }
    }

    async function fetchChats() {
        chatsLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/chats`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _chats.value = await res.json()
            }
        } catch (_) {
        } finally {
            chatsLoading.value = false
        }
    }

    async function fetchZones() {
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/zones', {
                headers: authHeaders(),
            })
            _zones.value = (Array.isArray(data) ? data : []).map(normalizeZone)
            zonesLoaded.value = true
        } catch (_) {
        }
    }

    async function fetchVehicles() {
        vehiclesLoading.value = true
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/vehicles', {
                headers: { ...authHeaders() },
            })
            _vehicles.value = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
        } catch (_) {
        } finally {
            vehiclesLoading.value = false
        }
    }

    async function fetchContacts() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/dispatch-contacts`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _contacts.value = await res.json()
            }
        } catch (_) {}
    }

    async function sendDispatchMessage(threadId, text) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/chats/${threadId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ text, sender: 'Dispatcher' }),
        })
        if (!res.ok) return null
        const updated = await res.json()
        // Sync into _chats
        const idx = _chats.value.findIndex((c) => String(c.id) === String(threadId))
        if (idx !== -1) _chats.value[idx] = updated
        else _chats.value.unshift(updated)
        return updated
    }

    async function createChatForContact(name, phone = null) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/chats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ name, phone }),
        })
        if (!res.ok) return null
        const thread = await res.json()
        _chats.value.unshift(thread)
        return thread
    }

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

    function resolveDriverName(driverId) {
        if (!driverId) return null
        const id = String(driverId)
        // Check filtered drivers first, then all drivers from logistic store
        const driver = ls.filteredDrivers.find(d => d.id === id)
        return driver ? driver.name : null
    }

    function resolveVehicleCode(vehicleId) {
        if (!vehicleId) return null
        const id = String(vehicleId)
        const vehicle = ls.filteredVehicles.find(v => v.id === id)
        if (vehicle) return vehicle.code || vehicle.licensePlate || vehicle.model || null
        return null
    }

    function mapOrder(o) {
        const substatus = o.warehouse_substatus || ''
        const isEscalated = o.escalated === true || String(o.escalation_status || '').toUpperCase() === 'OPEN'
        const weight = resolveCargoWeight(o)
        const volume = resolveCargoVolume(o)
        // Prefer server-resolved names, fall back to local store lookup
        const driverName = o.assigned_driver_name || resolveDriverName(o.assigned_driver_id)
        const vehicleCode = o.assigned_vehicle_code || resolveVehicleCode(o.assigned_vehicle_id)
        const deliveryAddr =
            o.unloading_addr ||
            o.unloading_address ||
            o.destination ||
            o.delivery_addr ||
            ''
        const deliveryLat = parseCoordinate(
            o.delivery_lat ??
            o.destination_lat ??
            o.unloading_lat ??
            o.drop_lat ??
            o.dest_lat ??
            o.destLat ??
            o.destinationLat
        )
        const deliveryLng = parseCoordinate(
            o.delivery_lng ??
            o.destination_lng ??
            o.unloading_lng ??
            o.drop_lng ??
            o.dest_lng ??
            o.destLng ??
            o.destinationLng
        )
        const pickupLat = parseCoordinate(
            o.pickup_lat ??
            o.origin_lat ??
            o.loading_lat ??
            o.source_lat ??
            o.pickupLat ??
            o.originLat
        )
        const pickupLng = parseCoordinate(
            o.pickup_lng ??
            o.origin_lng ??
            o.loading_lng ??
            o.source_lng ??
            o.pickupLng ??
            o.originLng
        )
        const podTimeLabel = o.delivered_at
            ? new Date(o.delivered_at).toLocaleString()
            : (o.created_at ? new Date(o.created_at).toLocaleString() : 'Delivered')
        const pod = o.status === 'DELIVERED'
            ? buildPodData(o, {
                timestamp: podTimeLabel,
                location: deliveryAddr || '—',
                signedByFallback: 'Receiver',
            })
            : null
        return {
            id: String(o.id || ''),
            trackingCode: o.tracking_code || '',
            warehouse: o.pickup_addr || o.warehouse_id || 'Hub',
            weight: weight ?? 0,
            hasWeight: weight !== null,
            volume: volume ?? 0,
            hasVolume: volume !== null,
            laborCount: o.labor_count || 0,
            priority: o.priority || 'NORMAL',
            deadline: o.scheduled_at || o.delivery_deadline || '',
            specialInstructions: o.notes || o.special_instructions || '',
            feasibility: o.feasibility || 'unchecked',
            failReason: o.fail_reason || '',
            selected: false,
            // warehouse readiness
            warehouseSubstatus: substatus,
            readyForDispatch: READY_STATUSES.includes(substatus),
            loadingInProgress: LOADING_STATUSES.includes(substatus),
            // for OrderStatusControl
            status: o.status || 'CONFIRMED',
            statusLabel: o.status || 'Confirmed',
            driver: driverName || (o.assigned_driver_id ? 'Driver ' + String(o.assigned_driver_id).slice(0, 6) : 'Unassigned'),
            driverId: o.assigned_driver_id ? String(o.assigned_driver_id) : null,
            vehicle: vehicleCode || (o.assigned_vehicle_id ? 'Vehicle ' + String(o.assigned_vehicle_id).slice(0, 6) : '—'),
            vehicleId: o.assigned_vehicle_id ? String(o.assigned_vehicle_id) : null,
            eta: o.scheduled_at || '—',
            etaOverdue: false,
            slaStatus: isEscalated ? 'ESCALATED' : 'On Track',
            slaClass: isEscalated ? 'bg-red-500/20 text-red-400' : 'text-green-400',
            lastUpdated: o.delivered_at || o.arrived_at || o.scheduled_at || o.created_at || '—',
            type: o.order_type || o.cargo_type || 'Standard',
            hub: o.pickup_addr || '',
            cargoType: o.cargo_type || '',
            vehicleType: o.vehicle_type || '',
            totalAmount: o.total_amount || 0,
            warehouseId: o.warehouse_id || null,
            customerName: o.customer_name || null,
            customerPhone: o.customer_phone || null,
            createdAt: o.created_at || null,
            deliveredAt: o.delivered_at || null,
            deliveryNotes: o.delivery_notes || null,
            packingReturnData: o.packing_return_data || null,
            escalated: isEscalated,
            escalationId: o.escalation_id ? String(o.escalation_id) : null,
            escalationStatus: o.escalation_status || null,
            pod,
            // Map coordinates for visualization
            pickupAddr: o.pickup_addr || '',
            pickupLat,
            pickupLng,
            deliveryAddr,
            deliveryLat,
            deliveryLng,
        }
    }

    async function fetchOrders() {
        ordersLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders?status_filter=CONFIRMED&page_size=100`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const data = await res.json()
                const items = Array.isArray(data) ? data : (data.items || data.orders || [])
                pendingOrders.value = items.map(mapOrder)
            }
        } catch (_) {
        } finally {
            ordersLoading.value = false
        }
    }

    async function fetchActiveOrders() {
        activeOrdersLoading.value = true
        try {
            const [cRes, aRes, tRes, dRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/orders?status_filter=CONFIRMED&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
                fetch(`${API_BASE}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
                fetch(`${API_BASE}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
                fetch(`${API_BASE}/api/v1/orders?status_filter=DELIVERED&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
            ])
            const confirmed = cRes.ok ? (await cRes.json()) : []
            const assigned = aRes.ok ? (await aRes.json()) : []
            const inTransit = tRes.ok ? (await tRes.json()) : []
            const delivered = dRes.ok ? (await dRes.json()) : []
            const confirmedItems = Array.isArray(confirmed) ? confirmed : (confirmed.items || [])
            const assignedItems = Array.isArray(assigned) ? assigned : (assigned.items || [])
            const inTransitItems = Array.isArray(inTransit) ? inTransit : (inTransit.items || [])
            const deliveredItems = Array.isArray(delivered) ? delivered : (delivered.items || [])
            const allItems = [...confirmedItems, ...assignedItems, ...inTransitItems, ...deliveredItems]
            console.log('📦 fetchActiveOrders: Received', allItems.length, 'orders')
            if (allItems.length > 0) {
                console.log('Sample raw order:', allItems[0])
            }
            activeOrders.value = allItems.map(o => mapOrder(o))
            console.log('📦 After mapping:', activeOrders.value.length, 'orders')
            const withCoords = activeOrders.value.filter(o => o.deliveryLat && o.deliveryLng)
            console.log('📦 Orders with delivery coords:', withCoords.length)
            if (withCoords.length > 0) {
                console.log('Sample mapped order with coords:', withCoords[0])
            }
        } catch (_) {
        } finally {
            activeOrdersLoading.value = false
        }
    }

    async function fetchOrderDetail(orderId) {
        const data = await authenticatedJsonRequest(`api/v1/orders/${orderId}`, {
            headers: { ...authHeaders() },
        })
        return mapOrder(data)
    }

    // ── Dispatcher-shaped drivers ──────────────────────────────────────────
    // Use directly fetched drivers (_drivers) so DISPATCHER role works without bootstrap access
    const dispatcherDrivers = computed(() => {
        const source = _drivers.value.length > 0 ? _drivers.value : ls.filteredDrivers
        const now = Date.now()
        const todayMidnight = new Date(); todayMidnight.setHours(0, 0, 0, 0)
        const todayMs = todayMidnight.getTime()

        return source.map((d) => {
            const driverId = String(d.id)
            const driverOrders = activeOrders.value.filter(o => o.driverId === driverId)
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

            return {
                ...d,
                avatar: generateAvatar(d.name, d.id),
                statusColor: color,
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

    async function fetchAlerts() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _alerts.value = await res.json()
                _alertsLoaded.value = true
            }
        } catch (_) {}
    }

    async function createAlert(payload) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(payload),
            })
            if (res.ok) {
                await fetchAlerts()
                return await res.json()
            }
        } catch (_) {}
        return null
    }

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

    async function fetchClusters(radiusKm = 5.0) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders/cluster?radius_km=${radiusKm}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) return await res.json()
            return { clusters: [], unbatched: [], total_orders: 0, estimated_miles_saved_pct: 0, avg_efficiency_pct: 0 }
        } catch (_) {
            return { clusters: [], unbatched: [], total_orders: 0, estimated_miles_saved_pct: 0, avg_efficiency_pct: 0 }
        }
    }

    async function assignOrder(orderId, driverId, vehicleId = null) {
        const body = { driver_id: driverId }
        if (vehicleId) body.vehicle_id = vehicleId
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(body),
            })
            if (res.ok) {
                await fetchOrders()
                await fetchActiveOrders()
            }
            return res.ok
        } catch (_) {
            return false
        }
    }

    async function batchAssignOrders(assignments) {
        const res = await fetch(`${API_BASE}/api/v1/orders/batch-assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ assignments }),
        })
        if (!res.ok) throw new Error('Batch assign failed')
        await fetchOrders()
        return await res.json()
    }

    async function askAi(query) {
        return ls.askAiDispatcher(query)
    }

    async function sendMessageToDriver(driverId, text) {
        return ls.sendMessageToDriver(driverId, text)
    }

    async function resolveAlert(id) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts/${id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _alerts.value = _alerts.value.filter(a => String(a.id) !== String(id))
            }
        } catch (_) {
            ls.resolveAlert(id).catch(() => {})
        }
    }

    // ── Manifests ─────────────────────────────────────────────────────────────
    const manifests = ref([])
    const manifestsLoading = ref(false)

    function _mapManifest(m) {
        const statusClass =
            m.status === 'Dispatched'
                ? 'bg-green-500/10 text-green-500 border-green-500/20'
                : m.status === 'Draft'
                ? 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
        return {
            id: m.route_id,
            backendId: String(m.id),
            driver: m.driver_name,
            vehicle: m.vehicle_code || 'Auto-assigned',
            hub: m.hub_name || '—',
            orders: m.orders_count,
            weight: m.total_weight,
            totalDistance: m.total_distance,
            stopCount: m.stop_count,
            totalVolume: m.total_volume,
            estDuration: m.est_duration || '—',
            status: m.status,
            statusClass,
            fragileCount: m.fragile_count,
            perishableCount: 0,
            codCount: m.cod_count,
            crew: (m.crew_list || []).map(c => ({ name: c.name, role: c.role })),
            stops: [],
            pushed: m.pushed,
            printed: false,
        }
    }

    async function fetchManifests() {
        manifestsLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const data = await res.json()
                manifests.value = data.map(_mapManifest)
            }
        } catch (_) {
        } finally {
            manifestsLoading.value = false
        }
    }

    async function saveManifest(payload) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(payload),
            })
            if (res.ok) {
                const created = await res.json()
                manifests.value.unshift(_mapManifest(created))
                return _mapManifest(created)
            }
        } catch (_) {}
        return null
    }

    async function pushManifestToDriver(backendId) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests/${backendId}/push`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const updated = await res.json()
                const idx = manifests.value.findIndex(m => m.backendId === backendId)
                if (idx !== -1) manifests.value[idx] = _mapManifest(updated)
                return true
            }
        } catch (_) {}
        return false
    }

    function markNotificationRead(id) { return ls.markNotificationRead(id) }
    function markAllNotificationsRead() { return ls.markAllNotificationsRead() }
    function clearNotifications() { return ls.clearNotifications() }

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
