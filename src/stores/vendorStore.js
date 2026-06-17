import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useRates } from '@/composables/useRates'
import { buildPodData } from '@/utils/pod'

const API_BASE = 'http://localhost:8000/api/v1'
const VENDOR_WALLET_TOPUP_OFFSET_KEY = 'vendor_wallet_topup_offset'

function clearLegacyWalletTopupOffset() {
    if (typeof window === 'undefined') return
    localStorage.removeItem(VENDOR_WALLET_TOPUP_OFFSET_KEY)
}

function getAuthHeaders(json = false) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    return {
        ...(json ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
}

function parseStatusKey(status) {
    const value = String(status || '').toLowerCase()
    if (['warehouse', 'awaiting_pick', 'picking', 'picked', 'packing', 'packed', 'qc_passed'].includes(value)) return 'warehouse'
    if (value.includes('transit') || value === 'assigned') return 'transit'
    if (value === 'delivered' || value === 'closed') return 'delivered'
    if (value === 'cancelled') return 'cancelled'
    if (value === 'out_for_delivery') return 'delivery'
    return 'pending'
}

function formatStatusLabel(statusKey) {
    return {
        pending: 'Pending',
        warehouse: 'In Warehouse',
        transit: 'In Transit',
        delivery: 'Out for Delivery',
        delivered: 'Delivered',
        cancelled: 'Cancelled',
    }[statusKey] || 'Pending'
}

function statusProgress(statusKey) {
    return { pending: 15, warehouse: 35, transit: 65, delivery: 85, delivered: 100, cancelled: 0 }[statusKey] || 0
}

function safeDateLabel(value, fallback = 'TBD') {
    if (!value) return fallback
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime())
        ? String(value)
        : parsed.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

function safeDateTimeLabel(value, fallback = 'TBD') {
    if (!value) return fallback
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime())
        ? String(value)
        : parsed.toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
}

function routeSummary(pickup, delivery) {
    return `${pickup || 'Origin'} → ${delivery || 'Destination'}`
}

export const useVendorStore = defineStore('vendor', () => {
    const { rates } = useRates()
    const initialized = ref(false)
    const loading = ref(false)
    const error = ref('')

    const dashboard = ref(null)
    const shipments = ref([])
    const invoices = ref([])
    const damageReports = ref([])
    const recurringRules = ref([])
    const bulkUploads = ref([])
    const tickets = ref([])
    const notifications = ref([])
    const warehouses = ref([])

    const companySettings = ref({
        companyName: '',
        taxId: '',
        contactPerson: '',
        phone: '',
        email: '',
        address: '',
        logo: null,
        teamMembers: [],
        notifications: {
            email: true,
            sms: true,
            push: true,
            orderUpdates: true,
            invoiceAlerts: true,
            promotions: false,
        },
        apiKeys: [],
    })

    const packingMaterials = ref([
        { id: 1, name: 'Standard Boxes', unitPrice: 45, available: 0, icon: 'inventory_2' },
        { id: 2, name: 'Wooden Crates', unitPrice: 350, available: 0, icon: 'deployed_code' },
        { id: 3, name: 'Bubble Wrap (roll)', unitPrice: 80, available: 0, icon: 'bubble_chart' },
        { id: 4, name: 'Packing Tape (roll)', unitPrice: 25, available: 0, icon: 'straighten' },
    ])

    const walletBalance = ref(0)

    async function fetchWalletBalance() {
        try {
            const res = await fetch(`${API_BASE}/vendor/wallet`, {
                headers: getAuthHeaders(),
            })
            if (res.ok) {
                const data = await res.json()
                walletBalance.value = Number(data.balance ?? 0)
                if (dashboard.value?.stats) {
                    dashboard.value.stats.credit_balance = walletBalance.value
                }
            }
        } catch (e) { /* silent */ }
    }

    const analyticsData = computed(() => ({
        monthly: dashboard.value?.analytics?.monthly || [],
        onTime: Number(dashboard.value?.analytics?.on_time || 0),
        avgTransit: Number(dashboard.value?.analytics?.avg_transit_days || 0),
        costPerMile: Number(dashboard.value?.analytics?.avg_order_value || 0),
        successRate: Number(dashboard.value?.analytics?.success_rate || 0),
    }))

    const activeShipments = computed(() => shipments.value.filter((s) => ['warehouse', 'transit', 'delivery'].includes(s.statusKey)))
    const pendingShipments = computed(() => shipments.value.filter((s) => s.statusKey === 'pending'))
    const deliveredShipments = computed(() => shipments.value.filter((s) => s.statusKey === 'delivered'))
    const overdueInvoices = computed(() => invoices.value.filter((invoice) => invoice.status === 'Overdue'))
    const totalOverdue = computed(() => overdueInvoices.value.reduce((sum, invoice) => sum + (invoice.amount - invoice.paid), 0))
    const totalUnpaid = computed(() => invoices.value.filter((invoice) => invoice.status !== 'Paid').length)
    const totalPaidThisMonth = computed(() => invoices.value.filter((invoice) => invoice.status === 'Paid').reduce((sum, invoice) => sum + invoice.paid, 0))
    const creditBalance = computed(() => Number(walletBalance.value ?? dashboard.value?.stats?.credit_balance ?? 0))
    const shipmentsWithPod = computed(() => shipments.value.filter((shipment) => shipment.pod?.confirmed))
    const unreadNotificationsCount = computed(() => notifications.value.filter((item) => !item.read).length)

    function normalizeShipment(raw) {
        const statusKey = parseStatusKey(raw.status_key || raw.status)
        const trackingCode = raw.tracking_code || String(raw.id)
        const pickup = raw.pickup_addr || 'Origin'
        const delivery = raw.delivery_addr || 'Destination'
        const amount = Number(raw.amount ?? raw.cost?.total ?? 0)
        const delivered = statusKey === 'delivered'
        const driverName = raw.assigned_driver_name || raw.driver_name || raw.driver?.name || null
        const driverPhone = raw.assigned_driver_phone || raw.driver_phone || raw.driver?.phone || null
        const assignedVehicleCode = raw.assigned_vehicle_code || raw.vehicle_code || null

        return {
            id: trackingCode,
            backendId: raw.id,
            trackingCode,
            origin: pickup,
            destination: delivery,
            route: routeSummary(pickup, delivery),
            status: raw.status_label || formatStatusLabel(statusKey),
            statusKey,
            eta: raw.eta_label || safeDateLabel(raw.scheduled_at, safeDateLabel(raw.created_at)),
            amount,
            pallets: 0,
            weight: Number(raw.cargo_weight_kg ?? raw.weight ?? raw.total_weight ?? 0),
            volume: Number(raw.cargo_volume_m3 ?? raw.volume ?? raw.total_volume ?? 0),
            category: raw.cargo_type || 'Commercial',
            paymentMode: raw.payment_mode || 'Invoice',
            paymentStatus: raw.payment_status || 'pending',
            driver: driverName,
            driverPhone,
            customerName: raw.customer_name || null,
            customerPhone: raw.customer_phone || null,
            vehicle: assignedVehicleCode || raw.vehicle_type || null,
            progress: Number(raw.progress ?? statusProgress(statusKey)),
            deliveredAt: raw.delivered_at || null,
            pod: delivered ? buildPodData(raw, {
                timestamp: safeDateTimeLabel(raw.delivered_at || raw.scheduled_at || raw.created_at),
                location: delivery,
                signedByFallback: 'Receiver',
            }) : null,
            originAddress: pickup,
            destinationAddress: delivery,
            driverLat: raw.driver_lat || raw.driverLat || null,
            driverLng: raw.driver_lng || raw.driverLng || null,
            description: raw.cargo_type || '',
            packingRequired: Number(raw.cost?.packing || 0) > 0,
            laborRequired: Number(raw.labor_count || 0) > 0,
            laborCount: Number(raw.labor_count || 0),
            createdAt: safeDateTimeLabel(raw.created_at),
            statusHistory: (raw.status_history || []).map((item) => ({
                status: item.status,
                time: item.time,
            })),
            autoDebitNote: raw.auto_debit_note || null,
            paidAmount: Number(raw.paid_amount || 0),
            customerRating: raw.customer_rating ?? null,
            customerFeedback: raw.customer_feedback ?? null,
            declaredValue: Number(raw.declared_value || 0),
            cost: {
                base: Number(raw.cost?.base || 0),
                vehicle: Number(raw.cost?.vehicle || 0),
                labor: Number(raw.cost?.labor || 0),
                materials: Number(raw.cost?.materials || 0),
                packing: Number(raw.cost?.packing || 0),
                platformFee: Number(raw.cost?.platform_fee || 0),
                taxes: Number(raw.cost?.taxes || 0),
                total: amount,
            },
        }
    }

    function normalizeInvoice(raw) {
        return {
            id: raw.id,
            orderId: raw.tracking_code,
            backendOrderId: raw.order_id,
            date: raw.date,
            dueDate: raw.due_date,
            amount: Number(raw.amount || 0),
            paid: Number(raw.paid || 0),
            status: raw.status || 'Unpaid',
        }
    }

    function rebuildNotifications() {
        const autoDebitNotifications = shipments.value
            .filter((shipment) => shipment.autoDebitNote)
            .slice(0, 4)
            .map((shipment) => {
                const message = String(shipment.autoDebitNote || '')
                const lowered = message.toLowerCase()
                const isSkipped = lowered.includes('skipped')
                const isDebt = lowered.includes('negative') || lowered.includes('debt')
                return {
                    id: `autodebit-${shipment.id}`,
                    title: isSkipped ? 'Auto-debit skipped' : (isDebt ? 'Wallet went negative' : 'Auto-debit update'),
                    message: `${shipment.id}: ${message}`,
                    time: shipment.createdAt || shipment.eta,
                    read: false,
                    type: isSkipped ? 'warning' : (isDebt ? 'alert' : 'info'),
                }
            })

        const shipmentNotifications = shipments.value.slice(0, 4).map((shipment, index) => ({
            id: `shipment-${shipment.id}`,
            title: `Shipment ${shipment.status}`,
            message: `${shipment.id} for ${shipment.destination}`,
            time: shipment.eta || shipment.createdAt,
            read: index > 1,
            type: shipment.statusKey === 'cancelled' ? 'alert' : shipment.statusKey === 'delivered' ? 'success' : 'warning',
        }))

        const invoiceNotifications = overdueInvoices.value.slice(0, 2).map((invoice) => ({
            id: `invoice-${invoice.id}`,
            title: 'Invoice Due',
            message: `${invoice.id} is ${invoice.status.toLowerCase()}.`,
            time: invoice.dueDate,
            read: false,
            type: invoice.status === 'Overdue' ? 'alert' : 'warning',
        }))

        notifications.value = [...autoDebitNotifications, ...invoiceNotifications, ...shipmentNotifications]
    }

    async function fetchWarehouses() {
        try {
            const res = await fetch(`${API_BASE}/warehouses`, {
                headers: getAuthHeaders(),
            })
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                console.warn('[vendorStore] fetchWarehouses failed:', res.status, err.detail || '')
                return
            }
            const data = await res.json()
            warehouses.value = (Array.isArray(data) ? data : data.items || []).map(w => ({
                id: String(w.id),
                name: w.name,
                address: w.address || w.location || '',
            }))
        } catch (e) {
            console.warn('[vendorStore] fetchWarehouses error:', e)
        }
    }

    async function fetchDashboardSummary() {
        const response = await fetch(`${API_BASE}/vendor/dashboard`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load vendor dashboard.')
        }

        const data = await response.json()
        dashboard.value = data
        walletBalance.value = Number(data.stats?.credit_balance ?? 0)
        invoices.value = (data.invoices?.invoices || []).map(normalizeInvoice)
        rebuildNotifications()
        return data
    }

    async function fetchShipments() {
        const response = await fetch(`${API_BASE}/vendor/shipments`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load shipments.')
        }

        const data = await response.json()
        shipments.value = (data.shipments || []).map(normalizeShipment)
        rebuildNotifications()
        return data
    }

    async function fetchSettings() {
        const response = await fetch(`${API_BASE}/vendor/settings`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load vendor settings.')
        }

        const data = await response.json()
        companySettings.value = {
            ...companySettings.value,
            companyName: data.settings?.company_name || '',
            taxId: data.settings?.tax_id || '',
            contactPerson: data.settings?.contact_person || data.settings?.company_name || '',
            phone: data.settings?.phone || '',
            email: data.settings?.email || '',
            address: data.settings?.address || '',
            notifications: {
                email: !!data.settings?.notification_prefs?.email,
                sms: !!data.settings?.notification_prefs?.sms,
                push: !!data.settings?.notification_prefs?.push,
                orderUpdates: !!data.settings?.notification_prefs?.orderUpdates,
                invoiceAlerts: !!data.settings?.notification_prefs?.invoiceAlerts,
                promotions: !!data.settings?.notification_prefs?.promotions,
            },
        }
        return data
    }

    async function fetchDamageReports() {
        const response = await fetch(`${API_BASE}/vendor/damage-reports`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load damage reports.')
        }

        const data = await response.json()
        damageReports.value = (data.reports || []).map((report) => ({
            id: report.id,
            orderId: report.order_id,
            description: report.description,
            severity: 'Medium',
            photos: report.photos || [],
            status: report.status,
            createdAt: report.created_at,
            resolution: null,
        }))
        return data
    }

    async function fetchTeamMembers() {
        const response = await fetch(`${API_BASE}/vendor/team-members`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load team members.')
        }

        companySettings.value.teamMembers = await response.json()
        return companySettings.value.teamMembers
    }

    async function fetchApiKeys() {
        const response = await fetch(`${API_BASE}/vendor/api-keys`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load API keys.')
        }

        companySettings.value.apiKeys = await response.json()
        return companySettings.value.apiKeys
    }

    async function fetchRecurringRules() {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load recurring rules.')
        }

        const data = await response.json()
        recurringRules.value = data.map((rule) => ({
            id: rule.id,
            name: rule.name,
            description: rule.description,
            frequency: rule.frequency,
            route: rule.route,
            details: rule.details,
            nextRun: rule.next_run,
            active: !!rule.active,
        }))
        return recurringRules.value
    }

    async function fetchBulkUploads() {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load bulk uploads.')
        }

        bulkUploads.value = await response.json()
        return bulkUploads.value
    }

    async function fetchTickets() {
        const response = await fetch(`${API_BASE}/vendor/support-tickets`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load support tickets.')
        }

        const data = await response.json()
        tickets.value = data.map((ticket) => ({
            id: ticket.id,
            backendId: ticket.backend_id || ticket.id.replace(/^TK-/, '').toLowerCase(),
            subject: ticket.subject,
            description: ticket.description,
            orderId: ticket.order_id,
            created: ticket.created,
            priority: ticket.priority,
            status: ticket.status,
            replies: (ticket.replies || []).map((reply) => ({
                from: reply.from_name,
                message: reply.message,
                time: reply.time,
            })),
        }))
        return tickets.value
    }

    async function initializeVendorData(force = false) {
        if (initialized.value && !force) return
        loading.value = true
        error.value = ''
        clearLegacyWalletTopupOffset()

        try {
            await Promise.all([
                fetchDashboardSummary(),
                fetchShipments(),
                fetchSettings(),
                fetchDamageReports(),
                fetchTeamMembers(),
                fetchApiKeys(),
                fetchRecurringRules(),
                fetchBulkUploads(),
                fetchTickets(),
                fetchWarehouses(),
                fetchWalletBalance(),
                fetchNotifications(),
            ])
            initialized.value = true
        } catch (err) {
            error.value = err.message || 'Failed to initialize vendor data.'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function refreshVendorData() {
        await initializeVendorData(true)
    }

    async function createShipment(data) {
        const selectedWarehouse = data.pickupType === 'hub'
            ? warehouses.value.find((warehouse) => warehouse.name === data.pickupHub) || null
            : null
        const pickupAddr = data.pickupType === 'doorstep'
            ? [data.pickupAddress, data.pickupCity, data.pickupPincode].filter(Boolean).join(', ')
            : data.pickupHub || 'Origin Hub'

        const deliveryAddr = [data.destination, data.destinationCity, data.pincode].filter(Boolean).join(', ')
        const scheduledAt = data.pickupDate ? new Date(data.pickupDate).toISOString() : null
        const quote = data.quoteBreakdown || {}
        const total = Number(quote.total ?? data.quotedPrice ?? 0)
        const materialsAmount = 0
        const packingAmount = Number(
            quote.packingFee
            ?? (data.packingRequired ? (rates.value.customerPackingFee ?? 200) : 0)
        )
        const laborAmount = Number(
            quote.laborCharges
            ?? (data.laborRequired ? Number(data.laborCount || 0) * (rates.value.customerLaborRate ?? 250) : 0)
        )
        const baseAmount = Math.max(total - packingAmount - laborAmount, 0)

        const priorityMap = { 'Urgent': 'URGENT', 'Express': 'HIGH', 'Standard': 'NORMAL' }
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                order_type: 'VENDOR',
                warehouse_id: selectedWarehouse?.id || null,
                pickup_addr: pickupAddr,
                pickup_type: data.pickupType || 'hub',
                delivery_addr: deliveryAddr,
                cargo_type: data.description || data.category || 'Commercial Shipment',
                vehicle_type: data.category || 'commercial',
                priority: priorityMap[data.priority] || 'NORMAL',
                labor_count: Number(data.laborCount || 0),
                cargo_weight_kg: Number(data.weight || 0) || null,
                cargo_volume_m3: Number(data.volume || 0) || null,
                base_amount: baseAmount,
                vehicle_amount: 0,
                labor_amount: laborAmount,
                materials_amount: materialsAmount,
                packing_amount: packingAmount,
                platform_fee: 0,
                tax_amount: 0,
                total_amount: total,
                declared_value: Number(data.declaredValue || 0),
                payment_mode: data.paymentMode || 'Invoice',
                payment_status: 'pending',
                service_time_block: data.timeWindow || null,
                scheduled_at: scheduledAt,
                delivery_lat: data.destLat || null,
                delivery_lng: data.destLng || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create shipment.')
        }

        await refreshVendorData()
        const created = await response.json()
        const normalized = shipments.value.find((shipment) => shipment.backendId === created.id) || normalizeShipment({
            ...created,
            amount: created.total_amount,
            status_label: 'Pending',
            status_key: 'pending',
            progress: 15,
            eta_label: safeDateLabel(created.scheduled_at, safeDateLabel(created.created_at)),
            cost: {
                base: created.base_amount,
                vehicle: created.vehicle_amount,
                labor: created.labor_amount,
                materials: created.materials_amount,
                packing: created.packing_amount,
                platform_fee: created.platform_fee,
                taxes: created.tax_amount,
                total: created.total_amount,
            },
            status_history: [{ status: 'Created', time: safeDateTimeLabel(created.created_at) }],
        })

        notifications.value.unshift({
            id: `created-${normalized.id}-${Date.now()}`,
            title: 'Shipment Created',
            message: `${normalized.id} created successfully.`,
            time: 'Just now',
            read: false,
            type: 'success',
        })
        return normalized
    }

    async function updateShipmentAddress(id, newAddress) {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return false

        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ delivery_addr: newAddress }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update shipment address.')
        }

        await refreshVendorData()
        return true
    }

    async function rescheduleShipment(id, newDate) {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return false

        const parsed = new Date(newDate)
        const scheduledAt = Number.isNaN(parsed.getTime()) ? null : parsed.toISOString()
        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ scheduled_at: scheduledAt }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to reschedule shipment.')
        }

        await refreshVendorData()
        return true
    }

    async function cancelShipment(id, reason = 'Cancelled by vendor') {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return { success: false, message: 'Shipment not found.' }

        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}/cancel`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ reason }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            return { success: false, message: errData.detail || 'Failed to cancel shipment.' }
        }

        const updated = await response.json()
        await refreshVendorData()
        // Refresh wallet so balance reflects the refund immediately
        await fetchWalletBalance()
        return {
            success: true,
            walletRefund: updated.wallet_refund_amount ?? 0,
        }
    }

    async function payInvoice(id, amount, paymentMethod = 'Bank Transfer') {
        const invoice = invoices.value.find((item) => item.id === id)
        if (!invoice) return false

        // Optimistic update
        const nextPaid = Math.min(invoice.amount, invoice.paid + amount)
        const prevPaid = invoice.paid
        const prevStatus = invoice.status
        invoice.paid = nextPaid
        invoice.status = nextPaid >= invoice.amount ? 'Paid' : 'Partial'

        try {
            const res = await fetch(`${API_BASE}/vendor/invoices/${invoice.backendOrderId}/pay`, {
                method: 'POST',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ amount, payment_method: paymentMethod }),
            })
            if (!res.ok) {
                // Rollback on failure
                invoice.paid = prevPaid
                invoice.status = prevStatus
                return false
            }
            const updated = await res.json()
            invoice.paid = updated.paid ?? nextPaid
            invoice.status = updated.status ?? invoice.status
            rebuildNotifications()
            return true
        } catch {
            invoice.paid = prevPaid
            invoice.status = prevStatus
            return false
        }
    }

    function recordCODPayment(orderId, amount) {
        const invoice = invoices.value.find((item) => item.orderId === orderId)
        if (invoice) payInvoice(invoice.id, amount)
    }

    async function reportDamage(orderIdOrPayload, reportPayload) {
        const orderId = typeof orderIdOrPayload === 'object' ? orderIdOrPayload.shipmentId : orderIdOrPayload
        const payload = typeof orderIdOrPayload === 'object' ? orderIdOrPayload : reportPayload

        const shipment = shipments.value.find((item) => item.id === orderId || item.backendId === orderId)
        const response = await fetch(`${API_BASE}/vendor/damage-reports`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                order_id: shipment?.backendId || '',
                description: payload?.description || '',
                photos: payload?.photos || [],
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to submit damage report.')
        }

        await fetchDamageReports()
        return true
    }

    function calculateQuote(pallets, weight, laborCount, packingRequired, materials) {
        const base = pallets * 120 + weight * 0.08
        const labor = laborCount * 250
        const packing = packingRequired ? 200 : 0
        const materialsTotal = materials ? materials.reduce((sum, material) => sum + material.qty * material.unitPrice, 0) : 0
        const total = base + labor + packing + materialsTotal
        return {
            baseTransport: Math.round(base),
            laborCharges: labor,
            packingFee: packing,
            materialsCost: Math.round(materialsTotal),
            total: Math.round(total),
        }
    }

    async function updateCompanySettings(updates) {
        const response = await fetch(`${API_BASE}/vendor/settings`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                company_name: updates.companyName,
                tax_id: updates.taxId,
                contact_person: updates.contactPerson,
                phone: updates.phone,
                email: updates.email || companySettings.value.email,
                address: updates.address ?? companySettings.value.address,
                notification_prefs: companySettings.value.notifications,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update company settings.')
        }

        await fetchSettings()
        return true
    }

    async function addTeamMember(member) {
        const response = await fetch(`${API_BASE}/vendor/team-members`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify(member),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to add team member.')
        }

        await fetchTeamMembers()
        return response.json()
    }

    async function removeTeamMember(id) {
        const response = await fetch(`${API_BASE}/vendor/team-members/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to remove team member.')
        }

        await fetchTeamMembers()
    }

    async function generateApiKey(name) {
        const response = await fetch(`${API_BASE}/vendor/api-keys`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ name }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to generate API key.')
        }

        const key = await response.json()
        await fetchApiKeys()
        return key
    }

    async function revokeApiKey(id) {
        const response = await fetch(`${API_BASE}/vendor/api-keys/${id}/revoke`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to revoke API key.')
        }

        await fetchApiKeys()
    }

    async function addRecurringRule(rule) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                name: rule.name,
                description: rule.description || '',
                frequency: rule.frequency,
                route: rule.route,
                details: rule.details,
                next_run: rule.nextRun,
                active: rule.active ?? true,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create recurring rule.')
        }

        await fetchRecurringRules()
        return response.json()
    }

    async function updateRecurringRule(id, updates) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                name: updates.name,
                description: updates.description || '',
                frequency: updates.frequency,
                route: updates.route,
                details: updates.details,
                next_run: updates.nextRun,
                active: updates.active ?? true,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update recurring rule.')
        }

        await fetchRecurringRules()
    }

    async function toggleRecurringRule(id) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}/toggle`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to toggle recurring rule.')
        }

        await fetchRecurringRules()
    }

    async function deleteRecurringRule(id) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to delete recurring rule.')
        }

        await fetchRecurringRules()
    }

    async function createBulkOrders(rows) {
        const results = { created: 0, failed: 0 }
        for (const row of rows) {
            try {
                const declaredValue = Number(row.declared_value || row.declaredValue || 0)
                const weight = Number(row.weight_kg || row.weight || 0)
                const baseAmount = declaredValue > 0 ? Math.round(declaredValue * 0.02) : 850
                const packingAmount = Math.round(baseAmount * 0.1) || 100
                const total = baseAmount + packingAmount + Math.round((baseAmount + packingAmount) * 0.18)
                const res = await fetch(`${API_BASE}/orders`, {
                    method: 'POST',
                    headers: getAuthHeaders(true),
                    body: JSON.stringify({
                        order_type: 'VENDOR',
                        warehouse_id: null,
                        pickup_addr: row.pickup_address || row.pickupAddress || 'Origin Hub',
                        pickup_type: 'doorstep',
                        delivery_addr: row.delivery_address || row.deliveryAddress || row.destination || 'Destination',
                        cargo_type: row.cargo_type || row.item_description || 'Commercial Shipment',
                        vehicle_type: 'commercial',
                        priority: 'NORMAL',
                        labor_count: 0,
                        cargo_weight_kg: weight || null,
                        cargo_volume_m3: null,
                        base_amount: baseAmount,
                        vehicle_amount: 0,
                        labor_amount: 0,
                        materials_amount: 0,
                        packing_amount: packingAmount,
                        platform_fee: 0,
                        tax_amount: Math.round((baseAmount + packingAmount) * 0.18),
                        total_amount: total,
                        declared_value: declaredValue,
                        payment_mode: row.payment_mode || row.paymentMode || 'Invoice',
                        payment_status: 'pending',
                        service_time_block: null,
                        scheduled_at: null,
                        delivery_lat: null,
                        delivery_lng: null,
                    }),
                })
                if (res.ok) results.created++
                else results.failed++
            } catch {
                results.failed++
            }
        }
        return results
    }

    async function addBulkUpload(upload) {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                filename: upload.filename || upload.fileName || 'upload.csv',
                file_size_kb: Math.round(Number(upload.fileSizeKb || 0)),
                orders: Number(upload.orders || 0),
                status: upload.status || 'Processed',
                errors: Number(upload.errors || 0),
                scheduled_for: upload.scheduledFor || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            const detail = errData.detail
            const msg = Array.isArray(detail)
                ? detail.map(e => e.msg || JSON.stringify(e)).join(', ')
                : (typeof detail === 'string' ? detail : 'Failed to save bulk upload.')
            throw new Error(msg)
        }

        await fetchBulkUploads()
    }

    async function updateBulkUpload(id, updates) {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify(updates),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update bulk upload.')
        }

        await fetchBulkUploads()
    }

    async function addTicket(ticket) {
        const response = await fetch(`${API_BASE}/vendor/support-tickets`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                subject: ticket.subject,
                description: ticket.description || ticket.message,
                priority: ticket.priority || 'Medium',
                shipment_id: ticket.shipmentId || ticket.orderId || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create support ticket.')
        }

        await fetchTickets()
        return response.json()
    }

    async function replyTicket(ticketId, message) {
        const ticket = tickets.value.find((item) => item.id === ticketId || item.backendId === ticketId)
        const backendId = ticket?.backendId || ticketId
        const response = await fetch(`${API_BASE}/vendor/support-tickets/${backendId}/reply`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ message }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to reply to ticket.')
        }

        await fetchTickets()
    }

    async function resolveTicket(id) {
        const ticket = tickets.value.find((item) => item.id === id || item.backendId === id)
        const backendId = ticket?.backendId || id
        const response = await fetch(`${API_BASE}/vendor/support-tickets/${backendId}/resolve`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to resolve ticket.')
        }

        await fetchTickets()
    }

    async function addFunds(amount) {
        if (amount <= 0) return false
        try {
            const res = await fetch(`${API_BASE}/vendor/wallet/top-up`, {
                method: 'POST',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ amount }),
            })

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                error.value = errData.detail || 'Failed to add funds.'
                return false
            }

            clearLegacyWalletTopupOffset()
            await fetchWalletBalance()
            if (dashboard.value?.stats) {
                dashboard.value.stats.credit_balance = walletBalance.value
            }
            return true
        } catch (err) {
            error.value = err?.message || 'Failed to add funds.'
            return false
        }
    }

    async function fetchNotifications() {
        try {
            const res = await fetch(`${API_BASE}/vendor/notifications`, {
                headers: getAuthHeaders(),
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
            console.warn('[vendorStore] fetchNotifications error:', e)
        }
    }

    async function markNotificationRead(id) {
        const notification = notifications.value.find((item) => item.id === id)
        if (notification) notification.read = true
        try {
            await fetch(`${API_BASE}/vendor/notifications/${id}`, {
                method: 'PUT',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ read: true }),
            })
        } catch (e) { /* best-effort */ }
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach((item) => { item.read = true })
        try {
            await fetch(`${API_BASE}/vendor/notifications/mark-all-read`, {
                method: 'POST',
                headers: getAuthHeaders(),
            })
        } catch (e) { /* best-effort */ }
    }

    async function clearNotifications() {
        notifications.value = []
        try {
            await fetch(`${API_BASE}/vendor/notifications`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            })
        } catch (e) { /* best-effort */ }
    }

    async function submitCustomerRating(backendId, rating, feedback = null) {
        try {
            const response = await fetch(`${API_BASE}/orders/${backendId}/customer-rating`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ rating, feedback }),
            })
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit rating.' }
            }
            const updated = await response.json()
            const idx = shipments.value.findIndex(s => s.backendId === backendId)
            if (idx !== -1) {
                shipments.value[idx].customerRating = updated.customer_rating
                shipments.value[idx].customerFeedback = updated.customer_feedback
            }
            return { success: true }
        } catch {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    return {
        initialized,
        loading,
        error,
        dashboard,
        shipments,
        invoices,
        recurringRules,
        bulkUploads,
        tickets,
        analyticsData,
        packingMaterials,
        companySettings,
        damageReports,
        notifications,
        unreadNotificationsCount,
        walletBalance,
        activeShipments,
        pendingShipments,
        deliveredShipments,
        shipmentsWithPod,
        overdueInvoices,
        totalOverdue,
        totalUnpaid,
        totalPaidThisMonth,
        creditBalance,
        warehouses,
        initializeVendorData,
        refreshVendorData,
        fetchWarehouses,
        fetchDashboardSummary,
        fetchShipments,
        fetchSettings,
        fetchDamageReports,
        fetchTeamMembers,
        fetchApiKeys,
        fetchRecurringRules,
        fetchBulkUploads,
        fetchTickets,
        fetchWalletBalance,
        createShipment,
        updateShipmentAddress,
        rescheduleShipment,
        cancelShipment,
        submitCustomerRating,
        payInvoice,
        recordCODPayment,
        reportDamage,
        addTicket,
        replyTicket,
        resolveTicket,
        addRecurringRule,
        updateRecurringRule,
        toggleRecurringRule,
        deleteRecurringRule,
        createBulkOrders,
        addBulkUpload,
        updateBulkUpload,
        calculateQuote,
        updateCompanySettings,
        addTeamMember,
        removeTeamMember,
        generateApiKey,
        revokeApiKey,
        addFunds,
        fetchNotifications,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
    }
})
