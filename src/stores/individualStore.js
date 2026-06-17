import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiUrl } from '@/config/api'
import { useRates } from '@/composables/useRates'
import { buildPodData } from '@/utils/pod'

let orderCounter = 3050

function generateOrderId() {
    orderCounter++
    return `MOV-${orderCounter}`
}

export const useIndividualStore = defineStore('individual', () => {
    const { rates } = useRates()
    const authUser = typeof window !== 'undefined'
        ? JSON.parse(localStorage.getItem('auth_user') || 'null')
        : null

    // ─── User Profile ────────────────────────────────────────────
    const user = ref({
        name: authUser?.name || 'Alex Johnson',
        avatar: null,
        email: authUser?.email || 'alex.johnson@email.com',
        phone: authUser?.phone || '',
        joiningDate: authUser?.created_at || new Date().toISOString(),
        tier: 'Gold Member',
        address: authUser?.address || '',
        language: authUser?.preferred_language || 'en',
        currency: authUser?.preferred_currency || 'INR',
        paymentDefault: authUser?.default_payment_method || 'Full Payment',
        notificationsEnabled: true,
        smsAlerts: true,
        notificationPrefs: {
            push: true,
            sms: true,
            email: true,
            geofence: true,
            promo: false,
        },
        privacyPrefs: {
            location: true,
            analytics: true,
            marketing: false,
        },
    })
    const dashboardSummary = ref(null)
    // ─── AI Estimator Pre-fill ────────────────────────────────────
    const aiPrefill = ref(null)   // { vehicleType, laborCount, cargoType, packingRequired, boxes, bubbleWrap }
    function setAiPrefill(data) { aiPrefill.value = data }
    function clearAiPrefill()   { aiPrefill.value = null }
    const dashboardLoading = ref(false)

    const dashboardError = ref('')
    const quotesLoading = ref(false)
    const quotesError = ref('')
    const trackingLoading = ref(false)
    const trackingError = ref('')
    const profileLoading = ref(false)
    const profileError = ref('')
    const paymentsLoading = ref(false)
    const paymentsError = ref('')
    const damageReportsLoading = ref(false)
    const damageReportsError = ref('')
    const settingsLoading = ref(false)
    const settingsError = ref('')
    const ordersLoading = ref(false)
    const ordersError = ref('')
    const paymentsSummary = ref(null)
    const warehouses = ref([])
    const assignmentPreview = ref(null)

    const savedAddresses = ref([
        { id: 1, label: 'Home', icon: 'home', address: '42, Green Park', city: 'New Delhi', state: 'Delhi', pincode: '110016', phone: '+91 0000000000' },
        { id: 2, label: 'Office', icon: 'business', address: '15, Sector 62', city: 'Noida', state: 'UP', pincode: '201301', phone: '+91 0000000000' },
        { id: 3, label: 'Parent\'s House', icon: 'family_restroom', address: '8, DLF Phase 3', city: 'Gurgaon', state: 'Haryana', pincode: '122002', phone: '+91 0000000000' },
    ])

    const userInitials = computed(() =>
        user.value.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    )

    function normalizeLanguageSetting(value) {
        const normalized = String(value || '').trim().toLowerCase()
        const aliases = {
            en: 'en',
            english: 'en',
            hi: 'hi',
            hindi: 'hi',
            ta: 'ta',
            tamil: 'ta',
            te: 'te',
            telugu: 'te',
            bn: 'bn',
            bengali: 'bn',
            mr: 'mr',
            marathi: 'mr',
        }
        return aliases[normalized] || 'en'
    }

    function normalizeCurrencySetting(value) {
        const normalized = String(value || '').trim().toUpperCase()
        if (normalized.includes('USD')) return 'USD'
        if (normalized.includes('EUR')) return 'EUR'
        return 'INR'
    }

    function normalizePaymentSetting(value) {
        const normalized = String(value || '').trim().toLowerCase()
        if (normalized.includes('partial')) return 'Partial'
        if (normalized.includes('cash') || normalized === 'cod') return 'COD'
        return 'Full Payment'
    }

    function normalizeCustomerSettings(settings = {}) {
        return {
            language: normalizeLanguageSetting(settings.language),
            currency: normalizeCurrencySetting(settings.currency),
            default_payment: normalizePaymentSetting(settings.default_payment),
            notification_prefs: {
                push: settings.notification_prefs?.push ?? true,
                sms: settings.notification_prefs?.sms ?? true,
                email: settings.notification_prefs?.email ?? true,
                geofence: settings.notification_prefs?.geofence ?? true,
                promo: settings.notification_prefs?.promo ?? false,
            },
            privacy_prefs: {
                location: settings.privacy_prefs?.location ?? true,
                analytics: settings.privacy_prefs?.analytics ?? true,
                marketing: settings.privacy_prefs?.marketing ?? false,
            },
        }
    }

    function syncStoredAuthUser(patch = {}) {
        if (typeof window === 'undefined') return
        const authData = JSON.parse(localStorage.getItem('auth_user') || 'null') || {}
        localStorage.setItem('auth_user', JSON.stringify({
            ...authData,
            ...patch,
        }))
    }

    function applyCustomerSettings(settings = {}) {
        const normalized = normalizeCustomerSettings(settings)
        user.value = {
            ...user.value,
            language: normalized.language,
            currency: normalized.currency,
            paymentDefault: normalized.default_payment,
            notificationsEnabled: !!normalized.notification_prefs.push,
            smsAlerts: !!normalized.notification_prefs.sms,
            notificationPrefs: normalized.notification_prefs,
            privacyPrefs: normalized.privacy_prefs,
        }
        syncStoredAuthUser({
            preferred_language: normalized.language,
            preferred_currency: normalized.currency,
            default_payment_method: normalized.default_payment,
            notifications_push: normalized.notification_prefs.push,
            notifications_sms: normalized.notification_prefs.sms,
            notifications_email: normalized.notification_prefs.email,
            notifications_geofence: normalized.notification_prefs.geofence,
            notifications_promo: normalized.notification_prefs.promo,
            privacy_location: normalized.privacy_prefs.location,
            privacy_analytics: normalized.privacy_prefs.analytics,
            privacy_marketing: normalized.privacy_prefs.marketing,
        })
        return normalized
    }

    // ─── Vehicle Fleet Catalog ──────────────────────────────────
    const vehicleTypes = ref([
        { key: 'mini-truck', name: 'Mini Truck', icon: 'local_shipping', capacity: '500 kg / 1 BHK', seats: 2, priceMultiplier: 1.0, desc: 'Ideal for small moves & packages' },
        { key: 'tempo', name: 'Tempo', icon: 'airport_shuttle', capacity: '1.5 Ton / 2 BHK', seats: 3, priceMultiplier: 1.4, desc: 'Best for 1-2 BHK apartments' },
        { key: 'lcv', name: 'LCV (Eicher)', icon: 'fire_truck', capacity: '3 Ton / 3 BHK', seats: 4, priceMultiplier: 2.0, desc: 'Large apartments & offices' },
        { key: 'hcv', name: 'HCV (Container)', icon: 'rv_hookup', capacity: '7+ Ton / Villa', seats: 6, priceMultiplier: 3.2, desc: 'Full villa / warehouse shift' },
    ])

    // ─── Orders ──────────────────────────────────────────────────
    const orders = ref([])

    const activeOrders = computed(() => orders.value.filter(o => o.status === 'in-transit' || o.status === 'dispatched'))
    const pendingOrders = computed(() => orders.value.filter(o => o.status === 'pending'))
    const deliveredOrders = computed(() => orders.value.filter(o => o.status === 'delivered'))
    const cancelledOrders = computed(() => orders.value.filter(o => o.status === 'cancelled'))
    const totalSpent = computed(() => orders.value.filter(o => o.paymentStatus === 'paid').reduce((s, o) => s + o.cost.total, 0))

    const walletBalance = ref(0)
    const pendingTransportCharge = ref(0)
    async function addFunds(amount) {
        const topUpAmount = Number(amount || 0)
        if (!(topUpAmount > 0)) return false

        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/wallet/top-up'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ amount: topUpAmount }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || 'Failed to top up wallet')
            }

            const data = await res.json()
            walletBalance.value = Number(data.balance ?? walletBalance.value + topUpAmount)
            return true
        } catch (error) {
            console.error('Failed to add wallet funds:', error)
            return false
        }
    }
    async function fetchWalletBalance() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/wallet'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (res.ok) {
                const data = await res.json()
                walletBalance.value = data.balance ?? 0
                pendingTransportCharge.value = data.pending_transport_charge ?? 0
            }
        } catch (e) { /* silent */ }
    }

    // ─── Monthly Spending (for chart) ────────────────────────────
    const monthlySpending = ref([
        { month: 'Oct', amount: 4200 },
        { month: 'Nov', amount: 7800 },
        { month: 'Dec', amount: 3500 },
        { month: 'Jan', amount: 12400 },
        { month: 'Feb', amount: 13400 },
        { month: 'Mar', amount: 9950 },
    ])

    // ─── Quotes ──────────────────────────────────────────────────
    const quotes = ref([])

    // ─── Payments ────────────────────────────────────────────────
    const payments = ref([])

    // ─── Damage Reports ──────────────────────────────────────────
    const damageReports = ref([])

    // ─── Notifications ───────────────────────────────────────────
    const notifications = ref([])

    const unreadNotificationsCount = computed(() => notifications.value.filter(n => !n.read).length)

    async function fetchNotifications() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/notifications'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) return
            const data = await res.json()
            notifications.value = (Array.isArray(data) ? data : []).map((item) => ({
                id: item.id,
                title: item.title,
                message: item.message,
                time: item.time,
                read: item.read,
                type: item.type,
            }))
        } catch (e) {
            console.warn('[individualStore] fetchNotifications error:', e)
        }
    }

    async function fetchWarehouses() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/warehouses?page=1&page_size=100'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || 'Failed to load hubs')
            }
            const data = await res.json()
            warehouses.value = (Array.isArray(data) ? data : data.items || []).map((warehouse) => ({
                id: String(warehouse.id),
                name: warehouse.name,
                address: warehouse.address || '',
            }))
            return warehouses.value
        } catch (error) {
            console.warn('[individualStore] fetchWarehouses failed:', error)
            return warehouses.value
        }
    }

    async function fetchOrderAssignmentPreview(warehouseId = null) {
        try {
            const token = localStorage.getItem('auth_token')
            const query = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''
            const res = await fetch(apiUrl(`api/v1/orders/assignment-preview${query}`), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || 'Failed to resolve assignment preview')
            }
            const data = await res.json()
            assignmentPreview.value = {
                ...data,
                warehouse_id: String(data.warehouse_id),
            }
            return assignmentPreview.value
        } catch (error) {
            console.warn('[individualStore] fetchOrderAssignmentPreview failed:', error)
            return assignmentPreview.value
        }
    }

    function normalizeBackendStatus(status) {
        const value = String(status || '').toUpperCase()
        if (value === 'DRAFT' || value === 'CONFIRMED') return 'pending'
        if (value === 'ASSIGNED') return 'dispatched'
        if (value === 'IN_TRANSIT') return 'in-transit'
        if (value === 'DELIVERED' || value === 'CLOSED') return 'delivered'
        if (value === 'CANCELLED') return 'cancelled'
        return value.toLowerCase()
    }

    function normalizeBackendOrder(order) {
        const status = normalizeBackendStatus(order.status)
        const warehouseSubstatus = order.warehouse_substatus || ''
        const warehouseId = order.warehouse_id ? String(order.warehouse_id) : null
        const warehouseName = order.warehouse_name
            || (warehouseId ? warehouses.value.find((warehouse) => warehouse.id === warehouseId)?.name : null)
            || null
        const warehouseAddress = order.warehouse_address
            || (warehouseId ? warehouses.value.find((warehouse) => warehouse.id === warehouseId)?.address : null)
            || null

        // Build transport log with warehouse operations
        const transportLog = buildTransportLog(order, status, warehouseSubstatus)

        return {
            id: order.tracking_code || String(order.id),
            backendId: order.id,
            trackingCode: order.tracking_code,
            status,
            rawStatus: order.status,
            warehouseId,
            warehouseName,
            warehouseAddress,
            warehouseSubstatus,
            moveType: String(order.order_type || '').toUpperCase() === 'INDIVIDUAL' ? 'house-shift' : 'small-package',
            cargoType: order.cargo_type || (String(order.order_type || '').toUpperCase() === 'INDIVIDUAL' ? 'Household Goods' : (order.order_type || 'Order')),
            pickup: order.pickup_addr,
            destination: order.delivery_addr,
            date: order.scheduled_at ? new Date(order.scheduled_at).toLocaleDateString('en-CA') : new Date(order.created_at).toLocaleDateString('en-CA'),
            timeWindow: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
            laborCount: order.labor_count || 0,
            packingRequired: Number(order.packing_amount || 0) > 0,
            vehicleType: order.vehicle_type || String(order.order_type || 'move').toLowerCase(),
            cargoWeightKg: Number(order.cargo_weight_kg ?? order.weight ?? order.total_weight ?? 0),
            cargoVolumeM3: Number(order.cargo_volume_m3 ?? order.volume ?? order.total_volume ?? 0),
            materials: {},
            cost: {
                base: Number(order.base_amount || 0),
                labor: Number(order.labor_amount || 0),
                materials: Number(order.materials_amount || 0),
                packing: Number(order.packing_amount || 0),
                vehicle: Number(order.vehicle_amount || 0),
                platformFee: Number(order.platform_fee || 0),
                taxes: Number(order.tax_amount || 0),
                carryForward: Number(order.carry_forward_charge_amount || 0),
                total: Number(order.total_amount || 0),
            },
            driver: order.assigned_driver_name || order.driver || null,
            customerName: order.customer_name || null,
            customerPhone: order.customer_phone || null,
            eta: order.scheduled_at ? new Date(order.scheduled_at).toLocaleString() : 'TBD',
            progress: status === 'delivered' ? 100 : status === 'in-transit' ? 65 : status === 'dispatched' ? 40 : 0,
            paymentMode: order.payment_mode || 'Pending',
            paymentStatus: order.payment_status || (status === 'delivered' ? 'paid' : 'pending'),
            paidAmount: Number(order.paid_amount || 0),
            isDummyPayment: false,
            rating: null,
            feedback: '',
            customerRating: order.customer_rating ?? null,
            customerFeedback: order.customer_feedback ?? null,
            createdAt: order.created_at,
            deliveredAt: order.delivered_at || null,
            declaredValue: Number(order.declared_value || 0),
            serviceTimeBlock: order.service_time_block || 'TBD',
            dwellTime: { loading: 0, unloading: 0, total: 0 },
            beforeAfterPhotos: {},
            crewCheckin: null,
            transportLog,
            pod: status === 'delivered' ? buildPodData(order, {
                timestamp: order.delivered_at
                    ? new Date(order.delivered_at).toLocaleString()
                    : (order.created_at ? new Date(order.created_at).toLocaleString() : 'Delivered'),
                location: order.delivery_addr || '—',
                signedByFallback: 'Receiver',
            }) : null,
            cancellation: order.cancel_reason ? { reason: order.cancel_reason, fee: 0, date: new Date().toISOString() } : null,
            hasDamageReport: false,
            damageReportId: '',
            damageReportStatus: '',
            damageRefundAmount: null,
            damageCondition: null,
        }
    }

    function applyDamageReportsToOrders() {
        if (!orders.value.length) return

        const latestReportByOrderId = new Map()
        for (const report of damageReports.value) {
            const orderId = String(report.orderId || '')
            if (!orderId) continue

            const existing = latestReportByOrderId.get(orderId)
            if (!existing || new Date(report.createdAt || 0) > new Date(existing.createdAt || 0)) {
                latestReportByOrderId.set(orderId, report)
            }
        }

        orders.value = orders.value.map((order) => {
            const linkedReport = latestReportByOrderId.get(String(order.backendId || ''))
            if (!linkedReport) {
                return {
                    ...order,
                    hasDamageReport: false,
                    damageReportId: '',
                    damageReportStatus: '',
                    damageRefundAmount: null,
                    damageCondition: null,
                }
            }

            return {
                ...order,
                hasDamageReport: true,
                damageReportId: linkedReport.id,
                damageReportStatus: linkedReport.status || 'reported',
                damageRefundAmount: linkedReport.refundAmount ?? null,
                damageCondition: linkedReport.condition ?? null,
            }
        })
    }

    // Build transport log with warehouse operations
    function buildTransportLog(order, status, warehouseSubstatus) {
        const log = []
        const createdTime = order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'

        // Direct transport orders (packing_amount == 0) skip all warehouse steps —
        // the driver goes straight to the customer's location.
        const isDirectTransport = Number(order.packing_amount ?? 0) === 0

        // Order created
        log.push({ event: 'Order created', time: createdTime, icon: 'receipt_long', color: 'blue' })

        // Order confirmed
        if (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status)) {
            log.push({ event: 'Order confirmed', time: createdTime, icon: 'check_circle', color: 'green' })
        }

        if (isDirectTransport) {
            // ── Direct transport path: no warehouse steps ──────────────────────
            if (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status)) {
                log.push({
                    event: 'Driver assigned',
                    description: 'A driver has been assigned and will head directly to your pickup location.',
                    time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Assigned',
                    icon: 'person_pin_circle',
                    color: 'blue'
                })
            }

            if (status === 'in-transit') {
                log.push({
                    event: 'Driver en route to pickup',
                    description: 'Your driver is on the way to collect your items.',
                    time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'On the way',
                    icon: 'local_shipping',
                    color: 'green'
                })
            }
        } else {
            // ── Full warehouse path ────────────────────────────────────────────

            // Backfill: confirmed orders with no substatus still show as queued
            let ws = warehouseSubstatus
            if (!ws && (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status))) {
                ws = 'AWAITING_PICK'
            }

            // Queued / Awaiting Pick
            if (['AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Queued for Picking',
                    description: "Orders that are queued up and ready, but no one has started picking them yet.",
                    time: order.created_at ? new Date(order.created_at).toLocaleString() : 'Ready',
                    icon: 'hourglass_empty',
                    color: 'amber'
                })
            }

            // On Hold
            if (ws === 'ON_HOLD') {
                log.push({
                    event: 'Order On Hold',
                    description: "Orders that are blocked. Usually, this means they don't have enough labourers assigned to them yet.",
                    time: new Date().toLocaleString(),
                    icon: 'pause_circle',
                    color: 'red'
                })
            }

            // Picking started
            if (['PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Picking started',
                    description: "Orders currently being gathered by your staff from the warehouse shelves.",
                    time: order.picking_started_at ? new Date(order.picking_started_at).toLocaleString() : 'In progress',
                    icon: 'shopping_basket',
                    color: 'blue'
                })
            }

            // Picking completed (Picked)
            if (['PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Picking completed',
                    description: "Orders where all items are gathered and are waiting to be boxed.",
                    time: order.picking_completed_at ? new Date(order.picking_completed_at).toLocaleString() : 'Completed',
                    icon: 'inventory_2',
                    color: 'cyan'
                })
            }

            // Packing started
            if (['PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Packing started',
                    description: "Orders currently at a packing station, being boxed and prepped for dispatch.",
                    time: order.packing_started_at ? new Date(order.packing_started_at).toLocaleString() : 'In progress',
                    icon: 'package_2',
                    color: 'amber'
                })
            }

            // Packing completed
            if (['PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Packing completed',
                    time: order.packing_completed_at ? new Date(order.packing_completed_at).toLocaleString() : 'Completed',
                    icon: 'deployed_code',
                    color: 'green'
                })
            }

            // Quality check passed
            if (['QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Quality check passed',
                    time: order.qc_passed_at ? new Date(order.qc_passed_at).toLocaleString() : 'Verified',
                    icon: 'verified',
                    color: 'green'
                })
            }

            // Ready for dispatch
            if (['READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws) || status === 'dispatched' || status === 'in-transit') {
                log.push({
                    event: 'Ready for dispatch',
                    time: order.dispatch_ready_at ? new Date(order.dispatch_ready_at).toLocaleString() : 'Ready',
                    icon: 'local_shipping',
                    color: 'blue'
                })
            }

            // Dispatched from warehouse (truck left the dock, driver not yet assigned)
            if (['ON_DOCK', 'DISPATCHED'].includes(ws)) {
                log.push({
                    event: 'Dispatched from warehouse',
                    description: 'Your shipment has left the warehouse and is awaiting driver assignment.',
                    time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Dispatched',
                    icon: 'output',
                    color: 'blue'
                })
            }

            // Driver assigned (dispatcher assigned a driver + vehicle)
            if (status === 'dispatched' || status === 'in-transit') {
                log.push({
                    event: 'Driver assigned',
                    description: 'A driver and vehicle have been assigned to your shipment.',
                    time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Assigned',
                    icon: 'person_pin_circle',
                    color: 'blue'
                })
            }

            // Shipment in transit (vehicle is on the road)
            if (status === 'in-transit') {
                log.push({
                    event: 'Shipment in transit',
                    description: 'Your shipment is on its way to the destination.',
                    time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'On the way',
                    icon: 'local_shipping',
                    color: 'green'
                })
            }
        }

        // Delivered (same for both paths)
        if (status === 'delivered') {
            log.push({
                event: 'Delivery completed',
                time: order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Delivered',
                icon: 'where_to_vote',
                color: 'green'
            })
        }

        // Cancelled (same for both paths)
        if (status === 'cancelled') {
            const cancelReason = order.cancel_reason || 'Order was cancelled'
            log.push({
                event: 'Order Cancelled',
                description: cancelReason,
                time: order.updated_at ? new Date(order.updated_at).toLocaleString() : new Date().toLocaleString(),
                icon: 'cancel',
                color: 'red'
            })
        }

        return log
    }

    function normalizeTrackingOrder(order) {
        const status = order.ui_status || normalizeBackendStatus(order.status)
        const warehouseSubstatus = order.warehouse_substatus || ''

        // Enrich order with warehouse timestamps for buildTransportLog
        const enriched = {
            ...order,
            picking_started_at: order.picking_started_at || null,
            picking_completed_at: order.picking_completed_at || null,
            packing_started_at: order.packing_started_at || null,
            packing_completed_at: order.packing_completed_at || null,
            qc_passed_at: order.qc_passed_at || null,
            dispatched_at: order.dispatched_at || null,
        }

        // Always rebuild transport log locally so warehouse steps always appear correctly.
        const transportLog = buildTransportLog(enriched, status, warehouseSubstatus)

        return {
            id: order.tracking_code || String(order.id),
            backendId: order.id,
            trackingCode: order.tracking_code,
            status,
            rawStatus: order.status,
            warehouseId: order.warehouse_id ? String(order.warehouse_id) : null,
            warehouseName: order.warehouse_name || null,
            warehouseAddress: order.warehouse_address || null,
            warehouseLat: order.warehouse_lat ?? null,
            warehouseLng: order.warehouse_lng ?? null,
            warehouseSubstatus,
            moveType: 'house-shift',
            cargoType: order.cargo_type || 'Household Goods',
            pickup: order.pickup_addr,
            destination: order.delivery_addr,
            date: order.scheduled_at ? new Date(order.scheduled_at).toLocaleDateString('en-CA') : new Date(order.created_at).toLocaleDateString('en-CA'),
            timeWindow: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
            laborCount: order.labor_count || 0,
            packingRequired: false,
            vehicleType: order.vehicle_type || 'assigned',
            materials: {},
            cost: {
                base: Number(order.base_amount || 0),
                labor: Number(order.labor_amount || 0),
                materials: Number(order.materials_amount || 0),
                packing: Number(order.packing_amount || 0),
                vehicle: Number(order.vehicle_amount || 0),
                platformFee: Number(order.platform_fee || 0),
                taxes: Number(order.tax_amount || 0),
                total: Number(order.total_amount || 0),
            },
            driver: order.assigned_driver_name || order.driver || null,
            customerName: order.customer_name || null,
            customerPhone: order.customer_phone || null,
            eta: order.eta_label || 'TBD',
            progress: order.progress ?? 0,
            paymentMode: order.payment_mode || 'Pending',
            paymentStatus: order.payment_status || (status === 'delivered' ? 'paid' : 'pending'),
            paidAmount: Number(order.paid_amount || 0),
            isDummyPayment: false,
            rating: null,
            feedback: '',
            customerRating: order.customer_rating ?? null,
            customerFeedback: order.customer_feedback ?? null,
            createdAt: order.created_at,
            deliveredAt: order.delivered_at || null,
            declaredValue: Number(order.declared_value || 0),
            serviceTimeBlock: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
            dwellTime: { loading: 0, unloading: 0, total: 0 },
            beforeAfterPhotos: {},
            crewCheckin: order.crew_checkin || null,
            transportLog,
            picking_started_at: enriched.picking_started_at,
            picking_completed_at: enriched.picking_completed_at,
            packing_started_at: enriched.packing_started_at,
            packing_completed_at: enriched.packing_completed_at,
            qc_passed_at: enriched.qc_passed_at,
            dispatched_at: enriched.dispatched_at,
            pod: status === 'delivered' ? buildPodData(order, {
                timestamp: order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Delivered',
                location: order.delivery_addr || '—',
                signedByFallback: 'Receiver',
            }) : null,
            cancellation: order.cancel_reason
                ? { reason: order.cancel_reason, fee: order.cancellation_fee || 0, date: order.updated_at || new Date().toISOString() }
                : null,
        }
    }

    function mapQuote(quote) {
        return {
            id: quote.id,
            cargoType: quote.cargo_type,
            from: quote.from_location,
            to: quote.to_location,
            laborCount: quote.labor_count,
            packing: quote.packing,
            total: quote.total,
            date: quote.date,
            status: quote.status,
        }
    }

    async function fetchDashboardSummary() {
        dashboardLoading.value = true
        dashboardError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/dashboard'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                dashboardError.value = errData.detail || 'Failed to load dashboard data.'
                return { success: false, message: dashboardError.value }
            }

            const data = await response.json()
            dashboardSummary.value = data
            user.value = {
                ...user.value,
                name: data.profile?.name || user.value.name,
                email: data.profile?.email || user.value.email,
                phone: data.profile?.phone || user.value.phone,
                joiningDate: data.profile?.created_at || user.value.joiningDate,
            }

            // Load notifications in parallel with dashboard (best-effort)
            fetchNotifications().catch(() => {})

            return { success: true, data }
        } catch (error) {
            dashboardError.value = 'Error connecting to the server.'
            return { success: false, message: dashboardError.value }
        } finally {
            dashboardLoading.value = false
        }
    }

    async function fetchOrders(status = null) {
        ordersLoading.value = true
        ordersError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const params = new URLSearchParams({ page: '1', page_size: '50' })
            if (status && status !== 'all') {
                const backendStatusMap = {
                    pending: 'CONFIRMED',
                    dispatched: 'ASSIGNED',
                    'in-transit': 'IN_TRANSIT',
                    delivered: 'DELIVERED',
                    cancelled: 'CANCELLED',
                }
                const backendStatus = backendStatusMap[status]
                if (backendStatus) params.set('status_filter', backendStatus)
            }

            const response = await fetch(apiUrl(`api/v1/orders?${params.toString()}`), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                ordersError.value = errData.detail || 'Failed to load orders.'
                return { success: false, message: ordersError.value }
            }

            const data = await response.json()
            orders.value = (data.items || []).map(normalizeBackendOrder)
            applyDamageReportsToOrders()
            return { success: true, data: orders.value }
        } catch (error) {
            ordersError.value = 'Error connecting to the server.'
            return { success: false, message: ordersError.value }
        } finally {
            ordersLoading.value = false
        }
    }

    async function fetchTrackingOrders() {
        trackingLoading.value = true
        trackingError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/tracking'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                trackingError.value = errData.detail || 'Failed to load tracking data.'
                return { success: false, message: trackingError.value }
            }

            const data = await response.json()
            orders.value = (data.orders || []).map(normalizeTrackingOrder)
            return { success: true, data: orders.value }
        } catch (error) {
            trackingError.value = 'Error connecting to the server.'
            return { success: false, message: trackingError.value }
        } finally {
            trackingLoading.value = false
        }
    }

    async function fetchProfile() {
        profileLoading.value = true
        profileError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/profile'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                profileError.value = errData.detail || 'Failed to load profile.'
                return { success: false, message: profileError.value }
            }

            const data = await response.json()
            user.value = {
                ...user.value,
                name: data.profile?.name || user.value.name,
                email: data.profile?.email || user.value.email,
                phone: data.profile?.phone || user.value.phone,
                joiningDate: data.profile?.created_at || user.value.joiningDate,
                altPhone: data.alt_phone || '',
                address: data.address || '',
                language: data.language || user.value.language,
                paymentDefault: data.default_payment || user.value.paymentDefault,
                notificationsEnabled: !!data.notification_prefs?.push,
                smsAlerts: !!data.notification_prefs?.sms,
            }
            return { success: true, data: user.value }
        } catch (error) {
            profileError.value = 'Error connecting to the server.'
            return { success: false, message: profileError.value }
        } finally {
            profileLoading.value = false
        }
    }

    async function saveProfileRemote(updates) {
        profileLoading.value = true
        profileError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/auth/me'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({
                    name: updates.name,
                    phone: updates.phone,
                    date_of_birth: updates.dob,
                    address: updates.address,
                }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                profileError.value = errData.detail || 'Failed to update profile.'
                return { success: false, message: profileError.value }
            }

            const data = await response.json()
            user.value = {
                ...user.value,
                name: data.name || user.value.name,
                email: data.email || user.value.email,
                phone: data.phone || user.value.phone,
                dob: updates.dob ?? user.value.dob,
                address: updates.address ?? user.value.address,
            }

            if (typeof window !== 'undefined') {
                const authData = JSON.parse(localStorage.getItem('auth_user') || 'null') || {}
                localStorage.setItem('auth_user', JSON.stringify({
                    ...authData,
                    name: user.value.name,
                    email: user.value.email,
                    phone: user.value.phone,
                    role: authData.role || 'INDIVIDUAL',
                }))
            }

            return { success: true, data: user.value }
        } catch (error) {
            profileError.value = 'Error connecting to the server.'
            return { success: false, message: profileError.value }
        } finally {
            profileLoading.value = false
        }
    }

    async function fetchPaymentsSummary() {
        paymentsLoading.value = true
        paymentsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/payments'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                paymentsError.value = errData.detail || 'Failed to load payments.'
                return { success: false, message: paymentsError.value }
            }

            const data = await response.json()
            paymentsSummary.value = data
            payments.value = (data.records || []).map((record) => ({
                id: record.id,
                orderId: record.tracking_code,
                amount: record.amount,
                mode: record.mode,
                status: record.status,
                date: record.created_at,
                isDummy: false,
            }))
            return { success: true, data }
        } catch (error) {
            paymentsError.value = 'Error connecting to the server.'
            return { success: false, message: paymentsError.value }
        } finally {
            paymentsLoading.value = false
        }
    }

    async function fetchQuotes() {
        quotesLoading.value = true
        quotesError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/quotes'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                quotesError.value = errData.detail || 'Failed to load quotes.'
                return { success: false, message: quotesError.value }
            }

            const data = await response.json()
            quotes.value = (data.quotes || []).map(mapQuote)
            return { success: true, data: quotes.value }
        } catch (error) {
            quotesError.value = 'Error connecting to the server.'
            return { success: false, message: quotesError.value }
        } finally {
            quotesLoading.value = false
        }
    }

    async function convertQuoteToOrderRemote(quoteId) {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/customer/quotes/${quoteId}/convert`), {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to convert quote.' }
            }

            await fetchQuotes()
            await fetchOrders()
            const data = await response.json()
            return { success: true, data }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    async function fetchDamageReports() {
        damageReportsLoading.value = true
        damageReportsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/damage-reports'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                damageReportsError.value = errData.detail || 'Failed to load damage reports.'
                return { success: false, message: damageReportsError.value }
            }

            const data = await response.json()
            damageReports.value = (data.reports || []).map((report) => ({
                id: report.id,
                orderId: report.order_id,
                description: report.description,
                photos: report.photos || [],
                flow_type: report.flow_type ?? null,
                status: report.status,
                qrCode: report.qr_code,
                createdAt: report.created_at,
                refundAmount: report.refund_amount ?? null,
                condition: report.condition ?? null,
            }))
            applyDamageReportsToOrders()
            return { success: true, data: damageReports.value }
        } catch (error) {
            damageReportsError.value = 'Error connecting to the server.'
            return { success: false, message: damageReportsError.value }
        } finally {
            damageReportsLoading.value = false
        }
    }

    async function reportDamageRemote(orderId, description, photos, resolutionType = 'photo_review') {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/damage-reports'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({
                    order_id: orderId,
                    description,
                    photos,
                    resolution_type: resolutionType,
                }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit damage report.' }
            }

            await fetchDamageReports()
            return { success: true }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    async function fetchSettings() {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/settings'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to load settings.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json()
            const normalizedSettings = applyCustomerSettings(data.settings)
            return { success: true, data: normalizedSettings }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    async function saveSettingsRemote(settings) {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/settings'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(settings),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to save settings.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json()
            const normalizedSettings = applyCustomerSettings(data.settings)
            return { success: true, data: normalizedSettings }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    async function deleteAccountRemote() {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/account'), {
                method: 'DELETE',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to delete account.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json().catch(() => ({}))
            return { success: true, message: data.message || 'Account deleted successfully.' }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    // ─── Materials Catalog ───────────────────────────────────────
    // Icon mapping for material names
    const materialIcons = {
        'box': 'inventory_2',
        'bubbleWrap': 'bubble_chart',
        'crate': 'deployed_code',
        'foamSheet': 'layers',
        'tape': 'straighten',
        'blanket': 'bed',
        'wardrobeBox': 'checkroom',
        'palletWrap': 'deployed_code',
        'default': 'package_2'
    }

    const MATERIAL_SKU_MAP = {
        box: 'PKG-CARTON',
        boxes: 'PKG-CARTON',
        carton: 'PKG-CARTON',
        cartons: 'PKG-CARTON',
        bubbleWrap: 'PKG-BUBBLE-WRAP',
        bubble: 'PKG-BUBBLE-WRAP',
        wrap: 'PKG-BUBBLE-WRAP',
        crate: 'PKG-PLASTIC-CRATE',
        crates: 'PKG-PLASTIC-CRATE',
        plasticCrates: 'PKG-PLASTIC-CRATE',
        blanket: 'PKG-BLANKET',
        blankets: 'PKG-BLANKET',
        wardrobeBox: 'PKG-WARDROBE-BOX',
        wardrobeBoxes: 'PKG-WARDROBE-BOX',
        tape: 'PKG-TAPE',
        foamSheet: 'FOAM-SHEET',
        foam: 'FOAM-SHEET',
    }

    function fallbackPackingSku(name = '') {
        return String(name || '')
            .trim()
            .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
            .toUpperCase()
            .replace(/[^A-Z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')
            .substring(0, 10)
    }

    function resolveMaterialSku(material = {}) {
        const explicitSku = String(material.sku || '').trim()
        if (explicitSku) return explicitSku

        const key = String(material.key || material.id || '').trim()
        if (MATERIAL_SKU_MAP[key]) return MATERIAL_SKU_MAP[key]

        return fallbackPackingSku(material.name || key)
    }

    const materialsCatalog = computed(() => {
        const materials = rates.value.materials

        // If materials is an array (new format), use it directly
        if (Array.isArray(materials)) {
            return materials.map(m => ({
                key: m.id,
                name: m.name,
                sku: resolveMaterialSku({ key: m.id, name: m.name, sku: m.sku }),
                price: m.rate,
                icon: materialIcons[m.id] || materialIcons.default,
                unit: m.unit || 'pcs'
            }))
        }

        // Fallback for old object format
        return [
            { key: 'boxes', name: 'Carton Boxes (Large)', price: materials?.box ?? 50, icon: 'inventory_2', unit: 'pcs' },
            { key: 'bubbleWrap', name: 'Bubble Wrap Rolls', price: materials?.bubbleWrap ?? 20, icon: 'bubble_chart', unit: 'rolls' },
            { key: 'plasticCrates', name: 'Plastic Crates', price: materials?.crate ?? 200, icon: 'deployed_code', unit: 'pcs' },
        ]
    })

    // ─── Actions ─────────────────────────────────────────────────

    async function createOrder(data) {
        const vehicle = vehicleTypes.value.find(v => v.key === data.vehicleType) || vehicleTypes.value[0]
        const totalAmount = Number(data.cost?.total || 0)
        const carryForwardChargeAmount = Number(data.carryForwardChargeAmount || 0)
        const payableBookingTotal = totalAmount + carryForwardChargeAmount
        const initialPaymentAmount = data.paymentMode === 'COD'
            ? 0
            : Math.min(Number(data.paymentAmount || 0), payableBookingTotal)
        const isWalletPayment = typeof (data.paymentMethod || '') === 'string' && (data.paymentMethod || '').toLowerCase().includes('wallet')

        // Prepare order data for backend API
        const orderPayload = {
            order_type: 'INDIVIDUAL',
            warehouse_id: data.warehouseId || null,
            pickup_addr: data.pickup || '',
            delivery_addr: data.destination || '',
            cargo_weight_kg: Number(data.packageWeight || data.cargoWeightKg || 0) || null,
            cargo_volume_m3: Number(data.cargoVolumeM3 || 0) || null,
            cargo_type: data.cargoType || null,
            vehicle_type: data.vehicleType || null,
            labor_count: data.laborCount || 0,
            base_amount: data.cost?.base || 0,
            vehicle_amount: data.cost?.vehicle || 0,
            labor_amount: data.cost?.labor || 0,
            materials_amount: data.cost?.materials || 0,
            packing_amount: data.cost?.packing || 0,
            platform_fee: data.cost?.platformFee || 0,
            tax_amount: data.cost?.taxes || 0,
            total_amount: totalAmount,
            payment_mode: data.paymentMode || null,
            payment_status: 'pending',
            initial_payment_amount: initialPaymentAmount,
            initial_payment_ref: data.paymentRef || null,
            initial_payment_mode: initialPaymentAmount > 0 ? (isWalletPayment ? 'WALLET' : 'ONLINE') : null,
            initial_payment_method: initialPaymentAmount > 0 ? (data.paymentMethod || 'Online') : null,
            service_time_block: data.moveType === 'small-package' ? '30 min' : '2-3 hours',
            scheduled_at: data.date ? new Date(data.date).toISOString() : null,
        }

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/orders'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(orderPayload),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `Server error ${response.status}: Failed to create order`)
            }

            const backendOrder = await response.json()
            const resolvedWarehouseId = backendOrder.warehouse_id ? String(backendOrder.warehouse_id) : (data.warehouseId || null)
            const resolvedWarehouse = resolvedWarehouseId
                ? warehouses.value.find((warehouse) => warehouse.id === resolvedWarehouseId)
                : null

            // Submit packing materials as OrderItems (so warehouse inventory deduction works during packing)
            // Prefer pre-resolved materialItems (sku + qty) passed directly from the booking form.
            // Only fall back to the old MATERIAL_SKU_MAP lookup when materialItems is not provided.
            const directItems = (data.materialItems || [])
                .map(i => ({ ...i, sku: resolveMaterialSku(i) }))
                .filter(i => i.sku && i.quantity > 0)

            let resolvedItems = null
            if (directItems.length > 0) {
                // Catalog-resolved: already have correct SKUs from the real WM inventory
                resolvedItems = directItems.map(i => ({ sku: i.sku, quantity: i.quantity, box_count: null, estimated_volume: null }))
            } else {
                // Legacy fallback: map old form.materials keys via MATERIAL_SKU_MAP
                const rawMaterialItems = Object.entries(data.materials || {})
                    .filter(([, qty]) => qty > 0)
                    .map(([key, qty]) => ({ key, qty, sku: resolveMaterialSku({ key }) }))
                    .filter(({ sku }) => sku)
                if (rawMaterialItems.length > 0) {
                    resolvedItems = rawMaterialItems.map(({ sku, qty }) => ({ sku, quantity: qty, box_count: null, estimated_volume: null }))
                }
            }

            if (resolvedItems && resolvedItems.length > 0) {
                try {
                    const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
                    const itemsRes = await fetch(apiUrl(`api/v1/orders/${backendOrder.id}/items`), {
                        method: 'POST',
                        headers,
                        body: JSON.stringify(resolvedItems),
                    })
                    if (!itemsRes.ok) {
                        const errBody = await itemsRes.json().catch(() => ({}))
                        console.error('Failed to attach packing material items:', itemsRes.status, errBody)
                    }
                } catch (itemErr) {
                    console.error('Could not attach packing material items to order:', itemErr)
                }
            }

            const normalizedOrder = normalizeBackendOrder({
                ...backendOrder,
                warehouse_name: resolvedWarehouse?.name || assignmentPreview.value?.warehouse_name || null,
                warehouse_address: resolvedWarehouse?.address || assignmentPreview.value?.warehouse_address || null,
            })
            if (Number(backendOrder.carry_forward_charge_amount || 0) > 0) {
                pendingTransportCharge.value = 0
            }

            // Add to local state immediately for instant UI feedback
            orders.value.unshift(normalizedOrder)

            if (initialPaymentAmount > 0) {
                payments.value.unshift({
                    id: data.paymentRef || (`PAY-${800 + payments.value.length + 1}`),
                    orderId: normalizedOrder.id,
                    amount: initialPaymentAmount,
                    mode: data.paymentMethod || 'Online',
                    status: 'completed',
                    date: new Date().toISOString(),
                    isDummy: false,
                })
            }

            // Add notification
            notifications.value.unshift({
                id: Date.now(),
                title: 'Order Created',
                message: `${normalizedOrder.trackingCode} booked — ${vehicle.name} assigned.`,
                time: 'Just now',
                read: false,
                icon: 'check_circle',
            })

            // Refresh dashboard summary so recent orders list is up to date
            fetchDashboardSummary()
            // Refresh wallet balance if paid via Cargo Core Wallet so UI reflects deduction
            if (isWalletPayment && initialPaymentAmount > 0) fetchWalletBalance()

            return normalizedOrder
        } catch (error) {
            console.error('Failed to create order:', error)
            // Re-throw so the UI (BookMove.vue) can show the real error to the user
            // instead of silently creating a local-only order that disappears on refresh
            throw error
        }
    }


    function updateOrder(id, updates) {
        const idx = orders.value.findIndex(o => o.id === id)
        if (idx !== -1) Object.assign(orders.value[idx], updates)
    }

    function cancelOrder(id) {
        const order = orders.value.find(o => o.id === id || o.backendId === id)
        if (!order) return null
        let fee = 0
        let reason = ''
        if (order.status === 'pending') {
            fee = 0; reason = 'Cancelled before dispatch — No fee'
        } else if (order.status === 'dispatched') {
            fee = Math.round(order.cost.total * 0.05); reason = 'Cancelled after driver assigned — 5% fee'
        } else if (order.status === 'in-transit' && order.progress < 30) {
            fee = Math.round(order.cost.total * 0.10); reason = 'Cancelled after dispatch — 10% fee'
        } else if (order.status === 'in-transit') {
            fee = Math.round(order.cost.total * 0.25); reason = 'Cancelled mid-transit — 25% fee'
        }
        order.status = 'cancelled'
        order.cancellation = { reason, fee, date: new Date().toISOString() }
        order.transportLog.push({ event: `Cancelled — ${reason}`, time: new Date().toLocaleString(), icon: 'cancel', color: 'red' })
        notifications.value.unshift({
            id: Date.now(), title: 'Order Cancelled', message: `${id} has been cancelled.`, time: 'Just now', read: false, icon: 'cancel'
        })
        return order
    }

    async function cancelOrderRemote(id, reason = 'Cancelled by customer') {
        const order = orders.value.find(o => o.id === id || o.backendId === id)
        if (!order?.backendId) {
            const local = cancelOrder(id)
            return { success: !!local, order: local }
        }

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/orders/${order.backendId}/cancel`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ reason }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to cancel order.' }
            }

            const updated = await response.json()
            const normalized = normalizeBackendOrder(updated)
            const index = orders.value.findIndex(o => o.backendId === updated.id)
            if (index >= 0) orders.value[index] = normalized
            // Refresh wallet so balance reflects the refund immediately
            await fetchWalletBalance()
            // Re-fetch tracking orders so Tracking.vue shows updated status + cancel log entry
            fetchTrackingOrders().catch(() => {})
            return {
                success: true,
                order: normalized,
                walletRefund: updated.wallet_refund_amount ?? 0,
            }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    async function submitCustomerRating(backendId, rating, feedback = null) {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/orders/${backendId}/customer-rating`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ rating, feedback }),
            })
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit rating.' }
            }
            const updated = await response.json()
            const idx = orders.value.findIndex(o => o.backendId === backendId)
            if (idx !== -1) {
                orders.value[idx].customerRating = updated.customer_rating
                orders.value[idx].customerFeedback = updated.customer_feedback
            }
            return { success: true }
        } catch {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    function rescheduleOrder(id, newDate, newTime) {
        updateOrder(id, { date: newDate, timeWindow: newTime })
        const order = orders.value.find(o => o.id === id)
        if (order) order.transportLog.push({ event: `Rescheduled to ${newDate}`, time: new Date().toLocaleString(), icon: 'schedule', color: 'amber' })
        notifications.value.unshift({
            id: Date.now(), title: 'Rescheduled', message: `${id} moved to ${newDate}.`, time: 'Just now', read: false, icon: 'schedule',
        })
    }

    async function rescheduleOrderRemote(id, newDate, newTime) {
        const order = orders.value.find(o => o.id === id || o.backendId === id)
        if (!order?.backendId) {
            rescheduleOrder(id, newDate, newTime)
            return { success: true }
        }

        try {
            const token = localStorage.getItem('auth_token')
            const scheduled_at = newDate ? new Date(newDate).toISOString() : null
            const response = await fetch(apiUrl(`api/v1/orders/${order.backendId}`), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ scheduled_at }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to reschedule order.' }
            }

            const updated = await response.json()
            const normalized = normalizeBackendOrder(updated)
            const index = orders.value.findIndex(o => o.backendId === updated.id)
            if (index >= 0) orders.value[index] = normalized
            notifications.value.unshift({
                id: Date.now(), title: 'Rescheduled', message: `${normalized.id} moved to ${newDate}.`, time: 'Just now', read: false, icon: 'schedule',
            })
            return { success: true, order: normalized }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    function submitRating(id, rating, feedback) {
        updateOrder(id, { rating, feedback })
    }

    function addQuote(data) {
        const q = { id: `QT-${500 + quotes.value.length + 1}`, ...data, date: new Date().toISOString().split('T')[0], status: 'active' }
        quotes.value.unshift(q)
        return q
    }

    async function convertQuoteToOrder(quoteId) {
        const q = quotes.value.find(q => q.id === quoteId)
        if (!q) return null
        q.status = 'converted'
        return await createOrder({
            cargoType: q.cargoType, pickup: q.from, destination: q.to,
            laborCount: q.laborCount, packingRequired: q.packing,
            materials: {}, cost: { base: Math.round(q.total * 0.45), labor: Math.round(q.total * 0.2), materials: Math.round(q.total * 0.1), packing: Math.round(q.total * 0.1), vehicle: Math.round(q.total * 0.15), total: q.total },
            date: new Date().toISOString().split('T')[0], timeWindow: '10:00 AM - 12:00 PM',
            paymentMode: 'Full Payment', vehicleType: 'tempo',
        })
    }

    async function makePayment(orderId, amount, mode, isDummy = false, paymentRef = null) {
        const p = {
            id: `PAY-${800 + payments.value.length + 1}`, orderId, amount, mode,
            status: isDummy ? 'simulated' : 'completed',
            date: new Date().toISOString(), isDummy,
        }
        payments.value.unshift(p)
        updateOrder(orderId, { paymentStatus: isDummy ? 'simulated' : 'paid', paymentMode: mode, isDummyPayment: isDummy })

        // Persist to backend if real payment (not simulated)
        if (!isDummy) {
            const order = orders.value.find(o => o.id === orderId || o.trackingCode === orderId)
            const backendId = order?.backendId
            if (backendId) {
                try {
                    const token = localStorage.getItem('auth_token')
                    const isWalletPayment = typeof mode === 'string' && mode.toLowerCase().includes('wallet')
                    if (isWalletPayment) {
                        await fetch(apiUrl(`api/v1/orders/${backendId}/wallet-pay`), {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                            body: JSON.stringify({ amount }),
                        })
                    } else {
                        await fetch(apiUrl(`api/v1/orders/${backendId}/pay`), {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                            body: JSON.stringify({
                                payment_ref: paymentRef,
                                payment_mode: 'ONLINE',
                                payment_method: mode,
                                amount,
                            }),
                        })
                    }
                } catch (e) {
                    console.warn('[makePayment] Backend /pay call failed (non-fatal):', e)
                }
            }
        }
        return p
    }

    function reportDamage(orderId, description, photos) {
        const report = {
            id: `DMG-${100 + damageReports.value.length + 1}`,
            orderId, description, photos: photos || [],
            status: 'reported', qrCode: `QR-${Date.now()}`,
            createdAt: new Date().toISOString(),
        }
        damageReports.value.unshift(report)
        notifications.value.unshift({
            id: Date.now(), title: 'Damage Reported', message: `Report ${report.id} submitted for ${orderId}.`, time: 'Just now', read: false, icon: 'report',
        })
        return report
    }

    function calculateQuote(distance, laborCount, packingRequired, materialsCost, vehicleKey, ratesOverride = {}) {
        const individualDistanceRates = ratesOverride.individualDistanceRates || {}
        const perKmRates = {
            'mini-truck': individualDistanceRates.miniTruck ?? 18,
            'tempo': individualDistanceRates.tempo ?? 25,
            'lcv': individualDistanceRates.lcv ?? 35,
            'hcv': individualDistanceRates.hcv ?? 50,
        }
        const vehicle = vehicleTypes.value.find(v => v.key === vehicleKey) || vehicleTypes.value[0]
        const perKm = perKmRates[vehicleKey] || 25

        const bookingFee = ratesOverride.individualBookingFee ?? 300
        const laborRate = ratesOverride.individualLaborRate ?? 800
        const packingPct = (ratesOverride.individualPackingPct ?? 20) / 100
        const minimumCharge = ratesOverride.minimumCharge ?? 500

        const distCharge = Math.round(distance * perKm)                 // distance charge
        const base = Math.max(bookingFee + distCharge, minimumCharge)   // total base fare
        const labor = laborCount * laborRate
        const packing = packingRequired ? Math.round(base * packingPct) : 0
        const vehicleCost = Math.round(distCharge * (vehicle.priceMultiplier - 1) * 0.4)
        const matCost = materialsCost || 0
        const subtotal = base + labor + packing + vehicleCost + matCost
        const platformFee = 249
        const taxes = Math.round(subtotal * 0.18)
        return { base, labor, packing, materials: matCost, vehicle: vehicleCost, platformFee, taxes, total: subtotal + platformFee + taxes }
    }

    async function markNotificationRead(id) {
        const n = notifications.value.find(n => n.id === id)
        if (n) n.read = true
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl(`api/v1/customer/notifications/${id}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ read: true }),
            })
        } catch (e) { /* best-effort */ }
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach(n => { n.read = true })
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl('api/v1/customer/notifications/mark-all-read'), {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
        } catch (e) { /* best-effort */ }
    }

    async function clearNotifications() {
        notifications.value = []
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl('api/v1/customer/notifications'), {
                method: 'DELETE',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
        } catch (e) { /* best-effort */ }
    }

    function updateProfile(updates) {
        Object.assign(user.value, updates)
    }

    function saveAddress(addressData) {
        if (addressData.id) {
            const idx = savedAddresses.value.findIndex(a => a.id === addressData.id)
            if (idx !== -1) savedAddresses.value[idx] = { ...savedAddresses.value[idx], ...addressData }
        } else {
            savedAddresses.value.push({ ...addressData, id: Date.now() })
        }
    }

    function deleteAddress(id) {
        savedAddresses.value = savedAddresses.value.filter(a => a.id !== id)
    }

    return {
        dashboardSummary, dashboardLoading, dashboardError, fetchDashboardSummary,
        quotesLoading, quotesError, fetchQuotes, convertQuoteToOrderRemote,
        trackingLoading, trackingError, fetchTrackingOrders,
        profileLoading, profileError, fetchProfile, saveProfileRemote,
        paymentsLoading, paymentsError, paymentsSummary, fetchPaymentsSummary,
        damageReportsLoading, damageReportsError, fetchDamageReports, reportDamageRemote,
        settingsLoading, settingsError, fetchSettings, saveSettingsRemote, deleteAccountRemote,
        ordersLoading, ordersError, fetchOrders, cancelOrderRemote,
        user, userInitials,
        warehouses, fetchWarehouses,
        assignmentPreview, fetchOrderAssignmentPreview,
        orders, activeOrders, pendingOrders, deliveredOrders, cancelledOrders, totalSpent,
        walletBalance, addFunds, fetchWalletBalance,
        pendingTransportCharge,
        monthlySpending, vehicleTypes,
        quotes, payments, damageReports,
        notifications, unreadNotificationsCount, fetchNotifications,
        materialsCatalog,
        createOrder, updateOrder, cancelOrder, rescheduleOrder, rescheduleOrderRemote, submitRating, submitCustomerRating,
        addQuote, convertQuoteToOrder, makePayment, reportDamage, calculateQuote,
        markNotificationRead, markAllNotificationsRead, clearNotifications,
        updateProfile, savedAddresses, saveAddress, deleteAddress,
        aiPrefill, setAiPrefill, clearAiPrefill
    }
})
