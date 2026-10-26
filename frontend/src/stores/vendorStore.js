import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useRates } from '@/composables/useRates'
import { normalizeInvoice } from './vendor/payloads'
import { API_BASE, clearLegacyWalletTopupOffset, getAuthHeaders } from './vendor/api'
import { useVendorNotifications } from './vendor/notifications'
import { useVendorBilling } from './vendor/billing'
import { useVendorShipments } from './vendor/shipments'
import { useVendorCompany } from './vendor/company'
import { useRecurringRules } from './vendor/recurring'
import { useVendorBulkUploads } from './vendor/bulkUploads'
import { useVendorSupport } from './vendor/support'

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
    const assignmentPreview = ref(null)
    const assignmentPreviewError = ref('')

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

    const {
        rebuildNotifications,
        fetchNotifications,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
    } = useVendorNotifications({ notifications, overdueInvoices, shipments })

    const { fetchWalletBalance, addFunds, payInvoice, recordCODPayment } = useVendorBilling({
        dashboard,
        error,
        invoices,
        rebuildNotifications,
        walletBalance,
    })

    const {
        fetchWarehouses,
        fetchOrderAssignmentPreview,
        fetchShipments,
        createShipment,
        updateShipmentAddress,
        rescheduleShipment,
        cancelShipment,
        reportDamage,
        fetchDamageReports,
        submitCustomerRating,
        calculateQuote,
    } = useVendorShipments({
        assignmentPreview,
        assignmentPreviewError,
        damageReports,
        fetchWalletBalance,
        notifications,
        rates,
        rebuildNotifications,
        refreshVendorData,
        shipments,
        warehouses,
    })

    const {
        fetchSettings,
        updateCompanySettings,
        fetchTeamMembers,
        addTeamMember,
        removeTeamMember,
        fetchApiKeys,
        generateApiKey,
        revokeApiKey,
    } = useVendorCompany({ companySettings })

    const {
        fetchRecurringRules,
        estimateRecurringCost,
        addRecurringRule,
        updateRecurringRule,
        toggleRecurringRule,
        deleteRecurringRule,
    } = useRecurringRules({ recurringRules })

    const { fetchBulkUploads, createBulkOrders, addBulkUpload, updateBulkUpload } = useVendorBulkUploads({ bulkUploads })

    const { fetchTickets, addTicket, replyTicket, resolveTicket } = useVendorSupport({ tickets })

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
        assignmentPreview,
        assignmentPreviewError,
        initializeVendorData,
        refreshVendorData,
        fetchWarehouses,
        fetchOrderAssignmentPreview,
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
        estimateRecurringCost,
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
