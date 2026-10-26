<template>
    <div class="space-y-6">

        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Manifest Centre</h2>
                <p class="text-sm text-gray-400 mt-0.5">Today's trip log & packing asset tracker</p>
            </div>
            <div class="flex gap-2">
                <button @click="refreshTrips" :disabled="loading"
                    class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-white/10 py-2 px-3 rounded-lg transition-colors flex items-center gap-1 text-sm font-bold disabled:opacity-50">
                    <span class="material-symbols-outlined text-[18px]" :class="loading ? 'animate-spin' : ''">refresh</span>
                </button>
                <button @click="showEOD = !showEOD"
                    class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 text-sm transition-colors">
                    <span class="material-symbols-outlined text-[18px]">summarize</span>
                    End of Day Report
                </button>
            </div>
        </div>

        <ManifestStatCards />

        <TripBoardTable />

        <TripDetailPanel />

        <EndOfDayReport />

        <!-- Toast -->
        <Teleport to="body">
            <Transition name="fade">
                <div v-if="toast"
                    class="fixed bottom-6 right-6 z-[9999] bg-green-600 text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">check_circle</span>
                    {{ toast }}
                </div>
            </Transition>
        </Teleport>

    </div>
</template>

<script setup>
import ManifestStatCards from './manifestCenter/ManifestStatCards.vue'
import TripBoardTable from './manifestCenter/TripBoardTable.vue'
import TripDetailPanel from './manifestCenter/TripDetailPanel.vue'
import EndOfDayReport from './manifestCenter/EndOfDayReport.vue'
import {
    buildLogFromOrderItems,
    fetchTripPackingItems,
    formatStatus,
    formatTime,
    freshLog,
    getStatusClass,
} from './manifestCenter/manifestItems'
import { manifestPageKey } from './manifestCenter/manifestPageContext'
import { ref, computed, nextTick, onMounted, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { API_BASE_URL as API_BASE, getStoredAccessToken } from '@/config/api'

const store = useDispatcherStore()
const { openSlipWithData, prefetchSlips } = useSlipPrinter()

// ── State ──────────────────────────────────────────────────────────────────
const loading = ref(false)
const selectedTrip = ref(null)
const detailPanel = ref(null)
const showEOD = ref(false)
const toast = ref('')
const logDirty = ref(false)
const assetNotes = ref('')
const currentAssetLog = ref([])
const assetLogs = ref({})  // { [tripId]: [...items] }
const tripItemsLoading = ref(false)

const ASSET_KEY_PREFIX = 'mc_asset_v1_'

// ── Trip data from store ───────────────────────────────────────────────────
const todayTrips = computed(() => {
    // ASSIGNED and IN_TRANSIT are always "today" — a driver is actively on them.
    // DELIVERED: filter to today so old completed jobs don't clutter the board.
    const todayStart = new Date()
    todayStart.setHours(0, 0, 0, 0)

    return store.activeOrders.filter(o => {
        if (!['ASSIGNED', 'IN_TRANSIT', 'DELIVERED'].includes(o.status)) return false
        // Active trips always show regardless of when the order was created
        if (o.status === 'ASSIGNED' || o.status === 'IN_TRANSIT') return true
        // For delivered, use deliveredAt if available, fall back to lastUpdated, then always show
        const completedDate = o.deliveredAt || o.lastUpdated
        if (!completedDate) return true
        return new Date(completedDate) >= todayStart
    })
})

const activeCount    = computed(() => todayTrips.value.filter(t => t.status === 'IN_TRANSIT').length)
const completedCount = computed(() => todayTrips.value.filter(t => t.status === 'DELIVERED').length)
const totalWeightToday = computed(() => todayTrips.value.reduce((s, t) => s + Number(t.weight || 0), 0))

const assetAlertCount = computed(() => todayTrips.value.filter(t => hasAssetLoss(t.id)).length)

const todayLabel = computed(() =>
    new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
)

// ── EOD aggregates ─────────────────────────────────────────────────────────
const eodTotalLoss = computed(() => {
    let total = 0
    for (const items of Object.values(assetLogs.value)) {
        total += items.reduce((s, i) => s + Math.max(0, (i.sentOut || 0) - (i.returned || 0)), 0)
    }
    return total
})

const eodAssetSummary = computed(() => {
    // Build summary dynamically from whatever was actually logged — no hardcoded item list
    const map = {}
    for (const items of Object.values(assetLogs.value)) {
        for (const item of items) {
            const key = item.sku || item.name
            if (!map[key]) {
                map[key] = { name: item.name, icon: item.icon || 'inventory_2', totalSent: 0, totalReturned: 0 }
            }
            map[key].totalSent     += item.sentOut  || 0
            map[key].totalReturned += item.returned || 0
        }
    }
    return Object.values(map).filter(i => i.totalSent > 0)
})

// ── Asset log helpers ──────────────────────────────────────────────────────
function getAssetLog(tripId) {
    return assetLogs.value[tripId] || null
}

function hasAssetLoss(tripId) {
    const log = assetLogs.value[tripId]
    if (!log) return false
    return log.some(i => (i.sentOut || 0) > 0 && (i.returned || 0) < (i.sentOut || 0))
}

function getTripDriverContext(trip) {
    const matchedDriver = store.dispatcherDrivers.find(driver => String(driver.id) === String(trip?.driverId || ''))
    return {
        id: trip?.driverId || matchedDriver?.id || trip?.id || '',
        name: trip?.driver || matchedDriver?.name || '—',
        phone: matchedDriver?.phone || '—',
        vehicle: trip?.vehicle || matchedDriver?.vehicle || '—',
    }
}

function getTripVehicleContext(trip) {
    const matchedVehicle = store.filteredVehicles.find(vehicle => String(vehicle.id) === String(trip?.vehicleId || ''))
    return {
        code: trip?.vehicle || matchedVehicle?.code || matchedVehicle?.licensePlate || matchedVehicle?.model || '—',
        licensePlate: matchedVehicle?.licensePlate || trip?.vehicle || '—',
        type: trip?.vehicleType || matchedVehicle?.type || matchedVehicle?.model || 'Assigned vehicle',
        vehicle_number: matchedVehicle?.vehicle_number || matchedVehicle?.code || matchedVehicle?.licensePlate || trip?.vehicle || '—',
    }
}

function getTripAssetItems(trip) {
    if (selectedTrip.value?.id === trip?.id && currentAssetLog.value.length > 0) {
        return JSON.parse(JSON.stringify(currentAssetLog.value))
    }
    const saved = getAssetLog(trip?.id)
    if (saved?.length) return JSON.parse(JSON.stringify(saved))
    return []
}

function buildTripSlipPayload(trip) {
    const driverContext = getTripDriverContext(trip)
    const vehicleContext = getTripVehicleContext(trip)
    const tripNotes = selectedTrip.value?.id === trip?.id
        ? assetNotes.value
        : (typeof window !== 'undefined'
            ? localStorage.getItem(ASSET_KEY_PREFIX + trip.id + '_notes') || ''
            : '')
    return {
        ...trip,
        orderId: trip?.id,
        trackingCode: trip?.trackingCode || trip?.id,
        driver: trip?.driver || driverContext.name,
        driverId: trip?.driverId || driverContext.id,
        driverPhone: driverContext.phone,
        driver_phone: driverContext.phone,
        vehicle: trip?.vehicle || vehicleContext.code,
        vehicleType: trip?.vehicleType || vehicleContext.type,
        licenseNo: driverContext.id ? `LIC-${String(driverContext.id).slice(0, 8).toUpperCase()}` : 'To be assigned',
        notes: tripNotes || trip?.specialInstructions || '',
        specialInstructions: trip?.specialInstructions || '',
        assetItems: getTripAssetItems(trip),
    }
}

async function openTripManifest(trip) {
    if (!trip) return
    const opened = await openSlipWithData('tripManifest', buildTripSlipPayload(trip))
    if (!opened) {
        showToast('Manifest slip could not be opened')
    }
}

async function openTripAssetKit(trip) {
    if (!trip) return
    const opened = await openSlipWithData('assetCheckout', buildTripSlipPayload(trip), getTripVehicleContext(trip))
    if (!opened) {
        showToast('Asset kit slip could not be opened')
    }
}

async function selectTrip(trip) {
    if (selectedTrip.value?.id === trip.id) {
        selectedTrip.value = null
        return
    }
    selectedTrip.value = trip
    logDirty.value = false
    assetNotes.value = localStorage.getItem(ASSET_KEY_PREFIX + trip.id + '_notes') || ''

    const existing = assetLogs.value[trip.id]
    if (existing) {
        // Restore previously saved log for this trip
        currentAssetLog.value = JSON.parse(JSON.stringify(existing))
    } else {
        // Fetch real packing items from the order and pre-fill sentOut quantities
        tripItemsLoading.value = true
        const orderItems = await fetchTripPackingItems(trip.id, store.authToken || getStoredAccessToken())
        tripItemsLoading.value = false
        currentAssetLog.value = orderItems.length > 0
            ? buildLogFromOrderItems(orderItems)
            : freshLog()
    }

    // Merge in any driver-submitted return counts
    const driverData = getDriverReturn(trip.id)
    if (driverData?.items?.length && currentAssetLog.value.length > 0) {
        driverData.items.forEach(driverItem => {
            const item = currentAssetLog.value.find(
                i => i.sku === driverItem.sku || i.name === driverItem.name
            )
            if (item && item.returned === 0) item.returned = driverItem.count || 0
        })
    }

    // Scroll the asset panel into view after it renders
    nextTick(() => {
        detailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
}

function onAssetChange() {
    logDirty.value = true
}

async function saveAssetLog() {
    if (!selectedTrip.value) return
    const snapshot = JSON.parse(JSON.stringify(currentAssetLog.value))
    assetLogs.value = { ...assetLogs.value, [selectedTrip.value.id]: snapshot }
    localStorage.setItem(ASSET_KEY_PREFIX + selectedTrip.value.id, JSON.stringify(snapshot))
    localStorage.setItem(ASSET_KEY_PREFIX + selectedTrip.value.id + '_notes', assetNotes.value)
    logDirty.value = false

    // Persist to backend and restore returned items to inventory
    try {
        const token = getStoredAccessToken()
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
        const body = JSON.stringify({
            items: snapshot.map(i => ({
                name: i.name,
                sku: i.sku || null,
                sent_out: i.sentOut || 0,
                returned: i.returned || 0,
            })),
            notes: assetNotes.value || '',
        })
        const res = await fetch(`${API_BASE}/api/v1/orders/${selectedTrip.value.id}/asset-log`, {
            method: 'POST',
            headers,
            body,
        })
        if (res.ok) {
            const result = await res.json()
            showToast(`Asset log saved — ${result.items_restored} item type(s) restored to inventory`)
        } else {
            showToast('Asset log saved locally (backend sync failed)')
        }
    } catch {
        showToast('Asset log saved locally (offline)')
    }
}

function clearAssetLog() {
    currentAssetLog.value = freshLog()
    assetNotes.value = ''
    logDirty.value = false
    if (selectedTrip.value) {
        const next = { ...assetLogs.value }
        delete next[selectedTrip.value.id]
        assetLogs.value = next
        localStorage.removeItem(ASSET_KEY_PREFIX + selectedTrip.value.id)
        localStorage.removeItem(ASSET_KEY_PREFIX + selectedTrip.value.id + '_notes')
    }
}

// ── Driver-submitted packing return (written by driver app via backend) ────
// Key matches what PackingReturn.vue saves in driver-side localStorage.
// In production this would come from the backend order's packing_return field.
// For now we check the browser localStorage in case dispatcher and driver share
// a device (rare) — the real path is backend → order detail → deliveryNotes.
const DRIVER_RETURN_KEY = 'driver_packing_return_v1_'

function getDriverReturn(tripId) {
    const trip = todayTrips.value.find(t => t.id === tripId)

    // 1. packing_return_data — stored by the new packing-return endpoint
    if (trip?.packingReturnData?.items?.length) {
        return trip.packingReturnData
    }

    // 2. Legacy: delivery_notes stored as JSON (old path)
    if (trip?.deliveryNotes) {
        try {
            const parsed = JSON.parse(trip.deliveryNotes)
            if (parsed?.items?.length) return parsed
        } catch {}
    }

    // 3. Fallback: localStorage (same-device scenario)
    try {
        const raw = localStorage.getItem(DRIVER_RETURN_KEY + tripId)
        if (raw) return JSON.parse(raw)
    } catch {}

    return null
}

function importDriverReturn(tripId) {
    const driverData = getDriverReturn(tripId)
    if (!driverData?.items?.length) return

    // Map driver counts into the "returned" column of the current asset log
    driverData.items.forEach(driverItem => {
        const item = currentAssetLog.value.find(
            i => (driverItem.sku && i.sku === driverItem.sku) || i.name === driverItem.name
        )
        if (item) item.returned = driverItem.count || 0
    })
    logDirty.value = true
    showToast('Driver counts imported as returned quantities')
}

function loadAllAssetLogs() {
    const logs = {}
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key?.startsWith(ASSET_KEY_PREFIX) && !key.endsWith('_notes')) {
            const tripId = key.replace(ASSET_KEY_PREFIX, '')
            try { logs[tripId] = JSON.parse(localStorage.getItem(key)) } catch {}
        }
    }
    assetLogs.value = logs
}

function showToast(msg) {
    toast.value = msg
    setTimeout(() => { toast.value = '' }, 2500)
}

// ── Refresh ────────────────────────────────────────────────────────────────
async function refreshTrips() {
    loading.value = true
    try {
        await store.fetchActiveOrders()
    } finally {
        loading.value = false
    }
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
    prefetchSlips(['tripManifest', 'assetCheckout']).catch(() => {})
    loadAllAssetLogs()
    await refreshTrips()
})

provide(manifestPageKey, {
    activeCount,
    assetAlertCount,
    assetNotes,
    clearAssetLog,
    completedCount,
    currentAssetLog,
    detailPanel,
    eodAssetSummary,
    eodTotalLoss,
    formatStatus,
    formatTime,
    getAssetLog,
    getDriverReturn,
    getStatusClass,
    hasAssetLoss,
    importDriverReturn,
    loading,
    logDirty,
    onAssetChange,
    openTripAssetKit,
    openTripManifest,
    saveAssetLog,
    selectTrip,
    selectedTrip,
    showEOD,
    todayLabel,
    todayTrips,
    totalWeightToday,
    tripItemsLoading,
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
