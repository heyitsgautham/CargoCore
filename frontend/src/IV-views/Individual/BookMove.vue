<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Book a Move</h2>

        <!-- AI Pre-fill Banner -->
        <Transition enter-active-class="transition-all duration-500" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-300" leave-to-class="opacity-0 -translate-y-2">
            <div v-if="aiPrefillApplied"
                class="flex items-center gap-3 px-4 py-3 bg-purple-50 dark:bg-purple-500/10 border border-purple-300 dark:border-purple-500/30 rounded-xl">
                <span class="material-symbols-outlined text-purple-500">psychology</span>
                <div>
                    <p class="text-sm font-bold text-purple-700 dark:text-purple-300">✨ AI Estimator pre-filled your booking!</p>
                    <p class="text-xs text-purple-600 dark:text-purple-400">Vehicle, labor count, cargo type, and volume estimate were carried in from your room scan. You can adjust anything below.</p>
                </div>
            </div>
        </Transition>

        <!-- Move Type Toggle -->

        <div class="glass-panel p-4 rounded-xl">
            <div class="flex gap-2 p-1 bg-gray-100 dark:bg-white/5 rounded-lg w-fit">
                <button @click="moveType = 'house-shift'"
                    class="px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2"
                    :class="moveType === 'house-shift' ? 'bg-green-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                    <span class="material-symbols-outlined text-lg">home</span> Complete House Shift
                </button>
                <button @click="moveType = 'small-package'"
                    class="px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2"
                    :class="moveType === 'small-package' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                    <span class="material-symbols-outlined text-lg">package_2</span> Small Package / Parcel
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main Form -->
            <div class="lg:col-span-2 space-y-6">

                <!-- ===== HOUSE SHIFT FORM ===== -->
                <template v-if="moveType === 'house-shift'">
                    <CargoTypeSection />

                    <VehicleTypeSection />

                    <RouteDetailsSection />

                    <ServiceOptionsSection />

                    <InstructionsSection />

                    <HousePaymentSection />
                </template>

                <!-- ===== SMALL PACKAGE FORM ===== -->
                <template v-else>
                    <PackageDetailsSection />

                    <PackageRouteSection />

                    <PackagePaymentSection />
                </template>
            </div>

            <!-- Price Preview Sidebar -->
            <PriceSidebar />
        </div>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl border max-w-sm"
                    :class="toast.type === 'success' ? 'bg-green-600 text-white border-green-500' : 'bg-red-600 text-white border-red-500'">
                    <span class="material-symbols-outlined">{{ toast.type === 'success' ? 'check_circle' : 'error'
                        }}</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>

        <BookingConfirmationModal />

        <!-- Razorpay Checkout -->
        <RazorpayCheckout
            v-model="showPaymentModal"
            :amount="paymentAmount"
            :description="moveType === 'house-shift' ? 'House Shift — ' + form.cargoType : 'Small Package'"
            :name="authStore.currentUser?.name || ''"
            :email="authStore.currentUser?.email || ''"
            :wallet-balance="store.walletBalance"
            @success="onRazorpaySuccess"
        />

        <!-- Map Picker Modal -->
        <MapPicker 
            :isOpen="showMapPicker" 
            :title="mapPickerTitle"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />
    </div>
</template>

<script setup>
import CargoTypeSection from './bookMove/CargoTypeSection.vue'
import VehicleTypeSection from './bookMove/VehicleTypeSection.vue'
import RouteDetailsSection from './bookMove/RouteDetailsSection.vue'
import ServiceOptionsSection from './bookMove/ServiceOptionsSection.vue'
import InstructionsSection from './bookMove/InstructionsSection.vue'
import HousePaymentSection from './bookMove/HousePaymentSection.vue'
import PackageDetailsSection from './bookMove/PackageDetailsSection.vue'
import PackageRouteSection from './bookMove/PackageRouteSection.vue'
import PackagePaymentSection from './bookMove/PackagePaymentSection.vue'
import PriceSidebar from './bookMove/PriceSidebar.vue'
import BookingConfirmationModal from './bookMove/BookingConfirmationModal.vue'
import { bookMovePageKey } from './bookMove/bookMovePageContext'
import { ref, computed, reactive, watch, onMounted, provide } from 'vue'
import { apiUrl, getStoredAccessToken } from '@/config/api'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { fetchRoadDistanceKm } from '@/composables/useOsrmDistance'
import { useRates } from '@/composables/useRates'
import MapPicker from '@/components/MapPicker.vue'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'

const store = useIndividualStore()
const { rates } = useRates()
const moveType = ref('house-shift')

// Show AI prefill banner temporarily
const aiPrefillApplied = ref(false)

const form = reactive({
    cargoType: 'Household Goods', pickup: '', destination: '', date: '',
    timeWindow: '09:00 AM - 12:00 PM', laborCount: 2, packingRequired: true, vehicleType: 'tempo',
    materials: {},
    cargoWeightKg: null, cargoVolumeM3: null,
    instructions: '', paymentMode: 'Full Payment', isDummyPayment: false, hubId: '',
})

// Coordinates from MapPicker for distance calculation
const pickupCoords = ref(null)   // { lat, lon }
const destCoords   = ref(null)   // { lat, lon }

// Road distance via OSRM (async). Falls back to Haversine × 1.35 if OSRM fails.
const distanceKm = ref(null)
const distanceLoading = ref(false)

watch([pickupCoords, destCoords], async ([p, d]) => {
    if (!p || !d) { distanceKm.value = null; return }
    distanceLoading.value = true
    distanceKm.value = await fetchRoadDistanceKm(p.lat, p.lon, d.lat, d.lon)
    distanceLoading.value = false
})

// Map picker state
const showMapPicker = ref(false)
const mapPickerType = ref('pickup') // 'pickup' or 'destination'
const mapPickerTitle = computed(() => 
    mapPickerType.value === 'pickup' ? 'Select Pickup Location' : 'Select Destination Location'
)

function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}

function handleMapSelect(data) {
    if (mapPickerType.value === 'pickup') {
        form.pickup = data.address
        pickupCoords.value = { lat: data.lat, lon: data.lon }
    } else {
        form.destination = data.address
        destCoords.value = { lat: data.lat, lon: data.lon }
    }
    showMapPicker.value = false
}

const pkg = reactive({ description: '', weight: 2.5, preferredDate: '', packageType: 'Document' })

const cargoTypes = [
    { name: 'Household Goods', icon: 'chair' }, { name: 'Furniture', icon: 'table_restaurant' },
    { name: 'Luggage / Boxes', icon: 'package_2' }, { name: 'Fragile Items', icon: 'priority_high' },
    { name: 'Mixed Items', icon: 'category' },
]

const pkgTypes = [
    { name: 'Document', icon: 'description' }, { name: 'Fragile Item', icon: 'wine_bar' },
    { name: 'Soft Item', icon: 'checkroom' }, { name: 'Hard Item', icon: 'inventory_2' },
]

const paymentModes = [
    { value: 'Full Payment', label: 'Full Payment', desc: 'Pay the full amount now' },
    { value: 'Partial', label: 'Partial Payment', desc: '50% now, rest on delivery' },
    { value: 'COD', label: 'Cash on Delivery', desc: 'Pay when delivered' },
]

const timeSlots = [
    { value: '06:00 AM - 09:00 AM', label: '6 – 9 AM', demand: 'Low Demand', demandColor: 'text-green-500', priceTag: '-5%', priceColor: 'text-green-600 dark:text-green-400', recommended: false },
    { value: '09:00 AM - 12:00 PM', label: '9 – 12 PM', demand: 'Medium', demandColor: 'text-amber-500', priceTag: 'Standard', priceColor: 'text-gray-500', recommended: false },
    { value: '12:00 PM - 03:00 PM', label: '12 – 3 PM', demand: 'Low Demand', demandColor: 'text-green-500', priceTag: '-8%', priceColor: 'text-green-600 dark:text-green-400', recommended: true },
    { value: '03:00 PM - 06:00 PM', label: '3 – 6 PM', demand: 'High Demand', demandColor: 'text-red-500', priceTag: '+10%', priceColor: 'text-red-500', recommended: false },
]

const routingPreview = computed(() => store.assignmentPreview)
const warehousePreviewError = computed(() => store.assignmentPreviewError || '')
const warehouseBookingBlocked = computed(() =>
    /No active warehouses available for assignment/i.test(warehousePreviewError.value)
)
const warehouseBookingMessage = computed(() =>
    warehouseBookingBlocked.value
        ? 'Currently no warehouse is available for booking. Please try again later or contact support.'
        : warehousePreviewError.value
)

const selectedVehicle = computed(() => store.vehicleTypes.find(v => v.key === form.vehicleType))
const serviceTimeBlock = computed(() => { const v = selectedVehicle.value; return v?.key === 'hcv' ? '4-5 hours' : v?.key === 'lcv' ? '3-4 hours' : v?.key === 'tempo' ? '2-3 hours' : '1-2 hours' })

const materialsCostTotal = computed(() => { let t = 0; for (const mat of packingCatalog.value) { t += (form.materials[mat.key] || 0) * mat.price }; return t })
// Use real distance if both locations selected, otherwise fall back to 10 km minimum
const effectiveDistanceKm = computed(() => distanceKm.value ?? 10)
const quote = computed(() => store.calculateQuote(effectiveDistanceKm.value, form.laborCount, form.packingRequired, materialsCostTotal.value, form.vehicleType, rates.value))
const totalCost = computed(() => quote.value.total)

// Small Package pricing — base by weight + per-km delivery fee (from rate governance)
const pkgBase = computed(() => Math.round((pkg.weight || 1) * (rates.value.smallPackagePerKgRate ?? 120)))
const pkgDeliveryFee = computed(() => distanceKm.value ? Math.round(distanceKm.value * (rates.value.smallPackagePerKmRate ?? 12)) : 50)
const pkgSubtotal = computed(() => pkgBase.value + pkgDeliveryFee.value)
const pkgMinimumAdjustment = computed(() => Math.max((rates.value.minimumCharge ?? 500) - pkgSubtotal.value, 0))
const pkgTotal = computed(() => pkgSubtotal.value + pkgMinimumAdjustment.value)
const carryForwardCharge = computed(() => Number(store.pendingTransportCharge || 0))
const bookingBaseTotal = computed(() => moveType.value === 'house-shift' ? totalCost.value : pkgTotal.value)
const bookingTotal = computed(() => bookingBaseTotal.value + carryForwardCharge.value)
const estimatedDelivery = computed(() => {
    if (!pkg.preferredDate) return null
    const d = new Date(pkg.preferredDate); d.setDate(d.getDate() + 2)
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
})

const toast = reactive({ show: false, message: '', type: 'success' })
function showToast(message, type = 'success') { toast.show = true; toast.message = message; toast.type = type; setTimeout(() => { toast.show = false }, 3000) }

const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()
const showConfirmModal = ref(false)
const confirmedOrderId = ref('')
const confirmedOrder = ref(null)

const showPaymentModal = ref(false)

const paymentAmount = computed(() => {
    if (form.paymentMode === 'Partial') return Math.round((bookingBaseTotal.value / 2) + carryForwardCharge.value)
    return bookingTotal.value
})

function handleBookingClick() {
    if (warehouseBookingBlocked.value) {
        showToast(warehouseBookingMessage.value, 'error')
        return
    }
    if (!form.pickup || !form.destination) { showToast('Please fill pickup and destination.', 'error'); return }
    if (moveType.value === 'house-shift' && !form.date) { showToast('Please select a date.', 'error'); return }
    if (moveType.value === 'small-package' && !pkg.preferredDate) { showToast('Please select a pickup date.', 'error'); return }

    if (form.paymentMode === 'COD') {
        confirmBooking()
    } else {
        showPaymentModal.value = true
    }
}

const razorpayMethod = ref('Online')

function onRazorpaySuccess({ payment_id, method }) {
    razorpayMethod.value = method
    showPaymentModal.value = false
    confirmBooking(payment_id, method)
}

async function confirmBooking(payment_id = null, method = null) {
    try {
        const order = await store.createOrder({
            moveType: moveType.value, cargoType: moveType.value === 'house-shift' ? form.cargoType : pkg.packageType,
            pickup: form.pickup, destination: form.destination,
            date: moveType.value === 'house-shift' ? form.date : pkg.preferredDate,
            timeWindow: moveType.value === 'house-shift' ? form.timeWindow : 'Auto-Scheduled',
            laborCount: moveType.value === 'house-shift' ? form.laborCount : 0,
            packingRequired: moveType.value === 'house-shift' ? form.packingRequired : false,
            vehicleType: moveType.value === 'house-shift' ? form.vehicleType : 'mini-truck',
            materials: moveType.value === 'house-shift' ? { ...form.materials } : {},
            materialItems: moveType.value === 'house-shift'
                ? packingCatalog.value
                    .filter(m => (form.materials[m.key] || 0) > 0)
                    .map(m => ({
                        id: m.id || m.key,
                        key: m.key,
                        name: m.name,
                        sku: m.sku || '',
                        quantity: form.materials[m.key],
                    }))
                : [],
            cost: moveType.value === 'house-shift' ? { ...quote.value } : { base: pkgBase.value, labor: 0, materials: 0, packing: 0, vehicle: 0, total: pkgTotal.value },
            carryForwardChargeAmount: carryForwardCharge.value,
            paymentMode: form.paymentMode, isDummyPayment: false,
            preferredPickupDate: moveType.value === 'small-package' ? pkg.preferredDate : null,
            estimatedDelivery: moveType.value === 'small-package' ? estimatedDelivery.value : null,
            paymentStatus: form.paymentMode === 'COD' ? 'pending' : (form.paymentMode === 'Partial' ? 'partial' : 'paid'),
            paymentAmount: form.paymentMode === 'COD' ? 0 : paymentAmount.value,
            paymentRef: payment_id,
            paymentMethod: method || razorpayMethod.value || 'Online',
            packageWeight: moveType.value === 'small-package' ? pkg.weight : null,
            cargoWeightKg: moveType.value === 'house-shift' ? form.cargoWeightKg : null,
            cargoVolumeM3: moveType.value === 'house-shift' ? form.cargoVolumeM3 : null,
            warehouseId: form.hubId || null,
        })

        confirmedOrderId.value = order.id
        confirmedOrder.value = order
        showConfirmModal.value = true
        showToast('Order created successfully!', 'success')
    } catch (error) {
        console.error('Failed to create order:', error)
        const msg = error?.message || 'Failed to create order. Please try again.'
        showToast(msg.length > 80 ? msg.substring(0, 80) + '…' : msg, 'error')
    }
}

function saveQuote() {
    const total = moveType.value === 'house-shift' ? totalCost.value : pkgTotal.value
    store.addQuote({ 
        cargoType: moveType.value === 'house-shift' ? form.cargoType : pkg.packageType, 
        from: form.pickup || 'Not specified', 
        to: form.destination || 'Not specified', 
        laborCount: moveType.value === 'house-shift' ? form.laborCount : 0, 
        packing: moveType.value === 'house-shift' ? form.packingRequired : false, 
        total: total 
    })
    showToast('Quote saved successfully!')
}

function resetForm() {
    form.pickup = ''; form.destination = ''; form.date = ''; form.laborCount = 2
    form.packingRequired = true; form.cargoType = 'Household Goods'; form.vehicleType = 'tempo'
    form.cargoWeightKg = null; form.cargoVolumeM3 = null
    form.materials = {}
    form.instructions = ''; form.paymentMode = 'Full Payment'; form.isDummyPayment = false; form.hubId = ''
    pkg.description = ''; pkg.weight = 2.5; pkg.preferredDate = ''; pkg.packageType = 'Document'
    pickupCoords.value = null; destCoords.value = null
    showToast('Form reset.', 'success')
}

watch(
    () => store.aiPrefill,
    (prefill) => {
        if (!prefill) return
        moveType.value = 'house-shift'
        form.vehicleType = prefill.vehicleType || form.vehicleType
        form.laborCount = Number(prefill.laborCount || form.laborCount)
        form.cargoType = prefill.cargoType || form.cargoType
        form.packingRequired = Boolean(prefill.packingRequired)
        if (prefill.estimatedVolumeM3 !== null && prefill.estimatedVolumeM3 !== undefined) {
            const normalizedVolume = Number(prefill.estimatedVolumeM3)
            form.cargoVolumeM3 = Number.isFinite(normalizedVolume) && normalizedVolume > 0
                ? normalizedVolume
                : form.cargoVolumeM3
        }
        aiPrefillApplied.value = true
        window.setTimeout(() => {
            aiPrefillApplied.value = false
        }, 5000)
        store.clearAiPrefill()
    },
    { deep: true }
)

watch(() => form.hubId, async (hubId) => {
    const preview = await store.fetchOrderAssignmentPreview(hubId || null).catch(() => null)
    form.materials = {}
    await fetchPackingCatalog(hubId || preview?.warehouse_id || null)
})

// Packing materials — fetched from real WM inventory so customer sees exact same items
const packingCatalog = ref([])
const packingCatalogLoading = ref(false)

const MATERIAL_ICONS = { box: 'inventory_2', carton: 'inventory_2', wrap: 'bubble_chart', bubble: 'bubble_chart', tape: 'straighten', blanket: 'bedding', crate: 'deployed_code', pallet: 'pallet', bag: 'shopping_bag', foam: 'layers', sheet: 'layers', default: 'package_2' }

function iconForItem(name) {
    const lower = (name || '').toLowerCase()
    for (const [kw, icon] of Object.entries(MATERIAL_ICONS)) {
        if (lower.includes(kw)) return icon
    }
    return MATERIAL_ICONS.default
}

async function fetchPackingCatalog(warehouseId = null) {
    packingCatalogLoading.value = true
    try {
        const token = getStoredAccessToken()
        const query = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''
        const res = await fetch(apiUrl(`api/v1/inventory/packing-catalog${query}`), {
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
        })
        if (res.ok) {
            const items = await res.json()
            packingCatalog.value = items.map(item => {
                // Price: inventory selling_price → matched rates catalog → fallback 50
                const ratesMat = rates.value.materials?.find?.(m =>
                    (item.name || '').toLowerCase().includes(m.id.toLowerCase()) ||
                    (item.sku || '').toLowerCase().includes(m.id.toLowerCase())
                )
                const price = (item.selling_price && item.selling_price > 0)
                    ? item.selling_price
                    : (ratesMat?.rate || 50)
                return {
                    key: item.id,
                    name: item.name,
                    sku: item.sku,
                    price,
                    unit: item.unit || ratesMat?.unit || 'pcs',
                    stock: item.stock,
                    icon: iconForItem(item.name)
                }
            })
        }
    } catch (e) {
        // silently fall back below
    }
    // Fallback to rates catalog if inventory unavailable
    if (packingCatalog.value.length === 0) {
        packingCatalog.value = store.materialsCatalog
    }
    packingCatalogLoading.value = false
}

onMounted(async () => {
    await store.fetchWarehouses()
    const preview = await store.fetchOrderAssignmentPreview(form.hubId || null)
    await store.fetchWalletBalance()
    await fetchPackingCatalog(form.hubId || preview?.warehouse_id || null)
})

provide(bookMovePageKey, {
    authStore,
    bookingTotal,
    cargoTypes,
    carryForwardCharge,
    confirmedOrder,
    confirmedOrderId,
    distanceKm,
    estimatedDelivery,
    form,
    handleBookingClick,
    materialsCostTotal,
    moveType,
    openMapPicker,
    openSlipWithData,
    packingCatalog,
    packingCatalogLoading,
    paymentModes,
    pkg,
    pkgBase,
    pkgDeliveryFee,
    pkgMinimumAdjustment,
    pkgTypes,
    quote,
    rates,
    resetForm,
    routingPreview,
    saveQuote,
    selectedVehicle,
    serviceTimeBlock,
    showConfirmModal,
    store,
    timeSlots,
    warehouseBookingBlocked,
    warehouseBookingMessage,
})
</script>
