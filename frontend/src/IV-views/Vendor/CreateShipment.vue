<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Shipment Management</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Create new bookings or upload bulk shipments
                </p>
            </div>
        </div>

        <!-- Tabs -->
        <div class="flex gap-2 border-b border-gray-200 dark:border-white/10">
            <button @click="activeTab = 'new'"
                :class="activeTab === 'new' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">New Booking</button>
            <button @click="activeTab = 'bulk'"
                :class="activeTab === 'bulk' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">Bulk Editor</button>
            <button @click="activeTab = 'myshipments'"
                :class="activeTab === 'myshipments' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">My Shipments <span
                    class="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/20 text-blue-500">{{
                        store.shipments.length }}</span></button>
        </div>

        <!-- NEW BOOKING TAB -->
        <div v-if="activeTab === 'new'" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 space-y-6">
                    <CategorySection />

                    <CargoDetailsSection />

                    <RouteScheduleSection />

                    <ServiceOptionsSection />

                    <PaymentSection />
                </div>

                <!-- Live Quotation Panel -->
                <LiveQuotationPanel :quote="quote" :rates="rates" :booking-notice="bookingNotice" :form-valid="formValid" :validation-errors="validationErrors" :warehouse-booking-blocked="warehouseBookingBlocked" :distance-km="distanceKm" :distance-loading="distanceLoading" @submit="submitShipment" @save-draft="saveDraft" />
            </div>
        </div>

        <!-- BULK EDITOR TAB -->
        <div v-if="activeTab === 'bulk'" class="space-y-6">
            <BulkTemplates />

            <BulkSampleTables />

            <BulkCharts />

            <BulkUploadHistory />
        </div>

        <MyShipmentsTab />

        <!-- Modals -->
        <Teleport to="body">
            <ShipmentCreatedModal />

            <!-- Razorpay Checkout for Full Payment -->
            <RazorpayCheckout
                v-model="showPayModal"
                :amount="pendingPayOrder ? pendingPayOrder.amount : 0"
                :order-id="pendingPayOrder?.id || ''"
                description="Full Payment for Shipment"
                :name="authStore.currentUser?.name || ''"
                :email="authStore.currentUser?.email || ''"
                :wallet-balance="store.walletBalance"
                @success="onRazorpaySuccess"
            />

            <EditEntryModal />

            <UploadBulkModal />
        </Teleport>

        <!-- Map Picker -->
        <MapPicker
            v-if="showMapPicker"
            :isOpen="showMapPicker"
            :title="mapPickerTitle"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />
    </div>
</template>

<script setup>
import CategorySection from './createShipment/CategorySection.vue'
import CargoDetailsSection from './createShipment/CargoDetailsSection.vue'
import RouteScheduleSection from './createShipment/RouteScheduleSection.vue'
import ServiceOptionsSection from './createShipment/ServiceOptionsSection.vue'
import PaymentSection from './createShipment/PaymentSection.vue'
import BulkTemplates from './createShipment/BulkTemplates.vue'
import BulkSampleTables from './createShipment/BulkSampleTables.vue'
import BulkCharts from './createShipment/BulkCharts.vue'
import BulkUploadHistory from './createShipment/BulkUploadHistory.vue'
import MyShipmentsTab from './createShipment/MyShipmentsTab.vue'
import ShipmentCreatedModal from './createShipment/ShipmentCreatedModal.vue'
import EditEntryModal from './createShipment/EditEntryModal.vue'
import UploadBulkModal from './createShipment/UploadBulkModal.vue'
import { createShipmentPageKey } from './createShipment/createShipmentPageContext'
import LiveQuotationPanel from './createShipment/LiveQuotationPanel.vue'
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount, defineAsyncComponent, provide } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { fetchRoadDistanceKm } from '@/composables/useOsrmDistance'
import { useRates } from '@/composables/useRates'
import { useBulkUploads } from './createShipment/useBulkUploads'
import { computeQuote, downloadTemplate, filterMyShipments, validateShipmentForm } from './createShipment/shipmentForm'

const { openSlipWithData } = useSlipPrinter()

const MapPicker = defineAsyncComponent(() => import('@/components/MapPicker.vue'))


const store = useVendorStore()
const authStore = useAuthStore()
const { rates } = useRates()
const confirmedOrder = ref(null)
const activeTab = ref('new')
const showConfirmModal = ref(false)
const showPayModal = ref(false)
const pendingPayOrder = ref(null)
const showUploadModal = ref(false)
const confirmedOrderId = ref('')
const expandedShipment = ref(null)
const shipmentSearch = ref('')
const shipmentStatusFilter = ref('all')
const isDark = ref(false)
const bookingNotice = ref('')
let themeObserver = null

// ── Map Picker ────────────────────────────────────────────────────────
const showMapPicker = ref(false)
const mapPickerType = ref('destination') // 'destination' | 'pickup'
const mapPickerTitle = computed(() =>
    mapPickerType.value === 'destination' ? 'Select Delivery Destination' : 'Select Pickup Location'
)
function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}
function handleMapSelect(data) {
    if (mapPickerType.value === 'destination') {
        form.destination = data.address
        form.destLat = data.lat
        form.destLng = data.lon
    } else {
        form.pickupAddress = data.address
        form.pickupLat = data.lat
        form.pickupLng = data.lon
    }
    showMapPicker.value = false
}

// Road distance via OSRM — recalculates quote whenever both coords are set
const distanceKm = ref(null)
const distanceLoading = ref(false)

const categories = [
    { value: 'commercial', label: 'Commercial (B2B)', desc: 'Standard B2B shipments', icon: 'business' },
    { value: 'palletized', label: 'Palletized', desc: 'Pallet-based cargo', icon: 'inventory_2' },
    { value: 'b2c', label: 'B2C Shipment', desc: 'Direct to Customer', icon: 'person' },
]

const handlingOptions = ['Fragile', 'Cold Storage', 'Hazardous', 'Oversize', 'High Value']

const form = reactive({
    category: 'commercial',
    description: '', hsnCode: '', palletCount: 1, weight: 100, volume: null, declaredValue: 0, insuranceRequired: 'no',
    customerName: '', customerPhone: '',
    pickupType: 'hub', pickupAddress: '', pickupCity: '', pickupPincode: '', pickupLat: null, pickupLng: null,
    handling: [], pickupHub: '', destination: '', destinationCity: '', pincode: '', destLat: null, destLng: null,
    pickupDate: '', deliveryDate: '', timeWindow: '08:00 AM - 12:00 PM', priority: 'Standard',
    packingRequired: false, laborRequired: false, laborCount: 1, paymentMode: 'Invoice',
})

watch(
    () => [form.pickupLat, form.pickupLng, form.destLat, form.destLng],
    async ([pLat, pLng, dLat, dLng]) => {
        if (!pLat || !pLng || !dLat || !dLng) { distanceKm.value = null; recalculate(); return }
        distanceLoading.value = true
        distanceKm.value = await fetchRoadDistanceKm(pLat, pLng, dLat, dLng)
        distanceLoading.value = false
        recalculate()
    }
)

const quote = ref({ baseTransport: 500, laborCharges: 0, packingFee: 0, insurance: 0, total: 500 })
const warehousePreviewError = computed(() => store.assignmentPreviewError || '')
const warehouseBookingBlocked = computed(() =>
    /No active warehouses available for assignment/i.test(warehousePreviewError.value)
)
const warehouseBookingMessage = computed(() =>
    warehouseBookingBlocked.value
        ? 'Currently no warehouse is available for booking. Please try again later or contact support.'
        : warehousePreviewError.value
)
const selectedPickupWarehouseId = computed(() =>
    store.warehouses.find((warehouse) => warehouse.name === form.pickupHub)?.id || null
)

const {
    bulkUploads,
    expandedSample,
    expandedUpload,
    expandedEntry,
    editingEntry,
    showEditModal,
    barChartData,
    barChartOptions,
    doughnutChartData,
    doughnutChartOptions,
    toggleSample,
    toggleUpload,
    toggleEntry,
    openEditModal,
    saveEdit,
    deleteUpload,
    deleteEntry,
} = useBulkUploads(isDark)

function recalculate() {
    quote.value = computeQuote(form, rates.value, distanceKm.value)
}

watch(
    () => [
        rates.value,
        distanceKm.value,
        form.category,
        form.weight,
        form.palletCount,
        form.pickupType,
        form.priority,
        form.packingRequired,
        form.laborRequired,
        form.laborCount,
        form.declaredValue,
        form.insuranceRequired,
    ],
    () => recalculate(),
    { deep: true, immediate: true }
)

const validationErrors = computed(() => validateShipmentForm(form))
const formValid = computed(() => validationErrors.value.length === 0)

const filteredShipments = computed(() => filterMyShipments(store.shipments, shipmentStatusFilter.value, shipmentSearch.value))

async function submitShipment() {
    bookingNotice.value = ''
    if (!formValid.value) return
    if (warehouseBookingBlocked.value) {
        bookingNotice.value = warehouseBookingMessage.value
        return
    }
    try {
        const s = await store.createShipment({ ...form, quotedPrice: quote.value.total, quoteBreakdown: { ...quote.value } })
        confirmedOrderId.value = s.id
        confirmedOrder.value = s
        if (form.paymentMode === 'Full Payment') {
            pendingPayOrder.value = s
            showPayModal.value = true
        } else {
            showConfirmModal.value = true
        }
    } catch (error) {
        bookingNotice.value = error?.message || 'Unable to create this shipment right now.'
    }
}

async function onRazorpaySuccess({ method, amount }) {
    showPayModal.value = false
    if (pendingPayOrder.value) {
        const invoice = store.invoices.find(inv => inv.orderId === pendingPayOrder.value.id)
        if (invoice) {
            await store.payInvoice(invoice.id, amount, method)
        }
        pendingPayOrder.value = null
    }
    showConfirmModal.value = true
}

function saveDraft() {
    const tooltip = document.createElement('div')
    tooltip.className = 'fixed bottom-4 right-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    tooltip.textContent = 'Draft saved locally'
    document.body.appendChild(tooltip)
    setTimeout(() => tooltip.remove(), 2500)
}

function resetForm() {
    Object.assign(form, {
        category: 'commercial', description: '', hsnCode: '', palletCount: 1, weight: 100, volume: null, declaredValue: 0, insuranceRequired: 'no', customerName: '', customerPhone: '',
        pickupType: 'hub', pickupAddress: '', pickupCity: '', pickupPincode: '',
        handling: [], pickupHub: store.warehouses[0]?.name || '', destination: '', destinationCity: '', pincode: '', pickupDate: '', deliveryDate: '', timeWindow: '08:00 AM - 12:00 PM', priority: 'Standard', packingRequired: false, laborRequired: false, laborCount: 1, paymentMode: 'Invoice'
    })
    recalculate()
}


function openShipmentEdit(ship) {
    editingEntry.value = JSON.parse(JSON.stringify({
        orderId: ship.id,
        date: ship.createdAt,
        category: ship.category,
        description: ship.description,
        hsnCode: '',
        palletCount: ship.pallets,
        weight: ship.weight,
        declaredValue: ship.amount,
        insuranceRequired: 'No',
        pickupHub: ship.origin,
        destinationCity: ship.destination,
        pincode: '',
        pickupDate: '',
        priority: 'Standard',
        paymentMode: ship.paymentMode,
        packingRequired: ship.packingRequired,
        laborRequired: ship.laborRequired,
        laborCount: ship.laborCount,
        _isStoreShipment: true,
    }))
    showEditModal.value = true
}

function deleteShipment(id) {
    if (!confirm('Delete this shipment? This cannot be undone.')) return
    store.shipments.splice(store.shipments.findIndex(s => s.id === id), 1)
    const tooltip = document.createElement('div')
    tooltip.className = 'fixed top-4 right-4 z-[9999] bg-red-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    tooltip.textContent = `Shipment ${id} deleted`
    document.body.appendChild(tooltip)
    setTimeout(() => tooltip.remove(), 2500)
}


// Auto-select first warehouse once loaded
watch(() => store.warehouses, (list) => {
    if (!form.pickupHub && list.length) form.pickupHub = list[0].name
}, { immediate: true })

watch(
    () => [form.pickupType, selectedPickupWarehouseId.value],
    async ([pickupType, warehouseId]) => {
        await store.fetchOrderAssignmentPreview(pickupType === 'hub' ? warehouseId : null)
    },
    { immediate: true }
)

onMounted(async () => {
    if (typeof document !== 'undefined') {
        isDark.value = document.documentElement.classList.contains('dark')
    }

    if (typeof document !== 'undefined' && typeof MutationObserver !== 'undefined') {
        themeObserver = new MutationObserver(() => {
            isDark.value = document.documentElement.classList.contains('dark')
        })
        themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    }

    // Always re-fetch warehouses when page loads so new hubs are visible immediately
    await store.fetchWarehouses()
    await store.fetchOrderAssignmentPreview(selectedPickupWarehouseId.value)
})

onBeforeUnmount(() => {
    themeObserver?.disconnect()
    themeObserver = null
})

recalculate()

provide(createShipmentPageKey, {
    activeTab,
    authStore,
    barChartData,
    barChartOptions,
    bulkUploads,
    categories,
    confirmedOrder,
    confirmedOrderId,
    deleteEntry,
    deleteShipment,
    deleteUpload,
    doughnutChartData,
    doughnutChartOptions,
    downloadTemplate,
    editingEntry,
    expandedEntry,
    expandedSample,
    expandedShipment,
    expandedUpload,
    filteredShipments,
    form,
    handlingOptions,
    openEditModal,
    openMapPicker,
    openShipmentEdit,
    openSlipWithData,
    rates,
    recalculate,
    resetForm,
    saveEdit,
    shipmentSearch,
    shipmentStatusFilter,
    showConfirmModal,
    showEditModal,
    showUploadModal,
    store,
    toggleEntry,
    toggleSample,
    toggleUpload,
    warehouseBookingBlocked,
    warehouseBookingMessage,
})
</script>
