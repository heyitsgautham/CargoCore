import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRates } from '@/composables/useRates'
import { useOrderRecords } from './individual/orderRecords'
import { useCustomerNotifications } from './individual/notifications'
import { useCustomerWallet } from './individual/wallet'
import { useDamageReports } from './individual/damageReports'
import { useCustomerOrders } from './individual/ordersApi'
import { useCustomerAccount } from './individual/account'
import { useCustomerPayments } from './individual/payments'
import { useCustomerBooking } from './individual/booking'

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
    const assignmentPreviewError = ref('')

    const savedAddresses = ref([
        { id: 1, label: 'Home', icon: 'home', address: '42, Green Park', city: 'New Delhi', state: 'Delhi', pincode: '110016', phone: '+91 0000000000' },
        { id: 2, label: 'Office', icon: 'business', address: '15, Sector 62', city: 'Noida', state: 'UP', pincode: '201301', phone: '+91 0000000000' },
        { id: 3, label: 'Parent\'s House', icon: 'family_restroom', address: '8, DLF Phase 3', city: 'Gurgaon', state: 'Haryana', pincode: '122002', phone: '+91 0000000000' },
    ])

    const userInitials = computed(() =>
        user.value.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    )

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

    function rescheduleOrder(id, newDate, newTime) {
        updateOrder(id, { date: newDate, timeWindow: newTime })
        const order = orders.value.find(o => o.id === id)
        if (order) order.transportLog.push({ event: `Rescheduled to ${newDate}`, time: new Date().toLocaleString(), icon: 'schedule', color: 'amber' })
        notifications.value.unshift({
            id: Date.now(), title: 'Rescheduled', message: `${id} moved to ${newDate}.`, time: 'Just now', read: false, icon: 'schedule',
        })
    }

    function submitRating(id, rating, feedback) {
        updateOrder(id, { rating, feedback })
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

    const { normalizeBackendOrder, applyDamageReportsToOrders } = useOrderRecords({ damageReports, orders, warehouses })

    const { fetchNotifications, markNotificationRead, markAllNotificationsRead, clearNotifications } = useCustomerNotifications({ notifications })

    const { addFunds, fetchWalletBalance } = useCustomerWallet({ pendingTransportCharge, walletBalance })

    const { fetchDamageReports, reportDamageRemote } = useDamageReports({ applyDamageReportsToOrders, damageReports, damageReportsError, damageReportsLoading })

    const {
        fetchWarehouses,
        fetchOrderAssignmentPreview,
        fetchDashboardSummary,
        fetchOrders,
        fetchTrackingOrders,
        cancelOrderRemote,
        submitCustomerRating,
        rescheduleOrderRemote,
    } = useCustomerOrders({
        applyDamageReportsToOrders,
        assignmentPreview,
        assignmentPreviewError,
        cancelOrder,
        dashboardError,
        dashboardLoading,
        dashboardSummary,
        fetchNotifications,
        fetchWalletBalance,
        normalizeBackendOrder,
        notifications,
        orders,
        ordersError,
        ordersLoading,
        rescheduleOrder,
        trackingError,
        trackingLoading,
        user,
        warehouses,
    })

    const {
        fetchProfile,
        saveProfileRemote,
        fetchSettings,
        saveSettingsRemote,
        deleteAccountRemote,
    } = useCustomerAccount({
        profileError,
        profileLoading,
        settingsError,
        settingsLoading,
        user,
    })

    const { fetchPaymentsSummary, makePayment } = useCustomerPayments({
        orders,
        payments,
        paymentsError,
        paymentsLoading,
        paymentsSummary,
        updateOrder,
    })

    const {
        resolveMaterialSku,
        createOrder,
        calculateQuote,
        fetchQuotes,
        convertQuoteToOrderRemote,
        addQuote,
        convertQuoteToOrder,
    } = useCustomerBooking({
        MATERIAL_SKU_MAP,
        assignmentPreview,
        fetchWalletBalance,
        normalizeBackendOrder,
        notifications,
        orders,
        payments,
        pendingTransportCharge,
        quotes,
        quotesError,
        quotesLoading,
        vehicleTypes,
        warehouses,
        fetchDashboardSummary,
        fetchOrders,
    })

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
        assignmentPreview, assignmentPreviewError, fetchOrderAssignmentPreview,
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
