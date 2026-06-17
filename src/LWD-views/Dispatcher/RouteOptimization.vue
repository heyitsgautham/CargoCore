<template>
    <div class="space-y-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
                <div class="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
                    AI Trip Command
                </div>
                <h2 class="mt-3 text-2xl font-bold text-gray-900 dark:text-white">Route Optimization</h2>
                <p class="mt-1 max-w-3xl text-sm text-gray-500 dark:text-gray-400">
                    Single-trip intelligence for one-order-one-driver dispatch. Predict delay, detect route risk, and push route updates to drivers.
                </p>
            </div>
            <button @click="loadTripIntelligence" :disabled="loading"
                class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">
                <span class="material-symbols-outlined text-[18px]" :class="loading ? 'animate-spin' : ''">refresh</span>
                {{ loading ? 'Refreshing...' : 'Refresh Intelligence' }}
            </button>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div v-for="stat in summaryCards" :key="stat.label" class="rounded-2xl border p-4" :class="stat.panelClass">
                <div class="flex items-start justify-between gap-3">
                    <div>
                        <div class="text-[11px] font-bold uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400">{{ stat.label }}</div>
                        <div class="mt-2 text-3xl font-black text-gray-900 dark:text-white">{{ stat.value }}</div>
                        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ stat.detail }}</div>
                    </div>
                    <div class="flex h-11 w-11 items-center justify-center rounded-2xl" :class="stat.iconWrap">
                        <span class="material-symbols-outlined" :class="stat.iconClass">{{ stat.icon }}</span>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="loading" class="flex min-h-[18rem] items-center justify-center rounded-3xl border border-gray-200 bg-white dark:border-white/10 dark:bg-white/5">
            <div class="flex flex-col items-center gap-3">
                <span class="material-symbols-outlined animate-spin text-4xl text-primary">progress_activity</span>
                <p class="text-sm text-gray-500 dark:text-gray-400">Building trip intelligence...</p>
            </div>
        </div>

        <div v-else-if="filteredTrips.length === 0" class="rounded-3xl border border-dashed border-gray-300 bg-white p-10 text-center dark:border-white/10 dark:bg-white/5">
            <span class="material-symbols-outlined text-5xl text-gray-300 dark:text-gray-600">alt_route</span>
            <h3 class="mt-4 text-lg font-bold text-gray-900 dark:text-white">No assigned trips yet</h3>
            <p class="mx-auto mt-2 max-w-xl text-sm text-gray-500 dark:text-gray-400">
                After dispatch assigns a driver, the trip will appear here for ETA intelligence, reroute recommendations, and push-to-driver actions.
            </p>
        </div>

        <div v-else class="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr,0.9fr]">
            <div class="rounded-3xl border border-gray-200 bg-white dark:border-white/10 dark:bg-white/5">
                <div class="flex flex-col gap-4 border-b border-gray-200 p-5 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Exception Queue</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">System monitors every trip. Dispatcher steps in only on exceptions.</p>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        <button v-for="option in filterOptions" :key="option.value" @click="statusFilter = option.value"
                            class="rounded-full px-3 py-1.5 text-xs font-bold uppercase tracking-[0.18em] transition-colors"
                            :class="statusFilter === option.value ? 'bg-primary text-black' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-white/5 dark:text-gray-300 dark:hover:bg-white/10'">
                            {{ option.label }}
                        </button>
                    </div>
                </div>

                <div class="max-h-[calc(100vh-18rem)] space-y-3 overflow-y-auto p-5">
                    <button v-for="trip in filteredTrips" :key="trip.order_id" @click="selectedOrderId = String(trip.order_id)"
                        class="w-full rounded-2xl border p-4 text-left transition-all"
                        :class="selectedTrip && String(selectedTrip.order_id) === String(trip.order_id) ? 'border-primary bg-primary/5 shadow-lg shadow-primary/5' : 'border-gray-200 bg-white hover:border-primary/30 dark:border-white/10 dark:bg-black/10 dark:hover:border-primary/30'">
                        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                            <div class="min-w-0">
                                <div class="flex flex-wrap items-center gap-2">
                                    <span class="text-base font-black text-gray-900 dark:text-white">{{ trip.tracking_code }}</span>
                                    <span class="rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em]" :class="riskChipClass(trip.risk_level)">
                                        {{ trip.risk_level }}
                                    </span>
                                    <span class="rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em]" :class="statusChipClass(trip.route_status)">
                                        {{ trip.route_status }}
                                    </span>
                                </div>
                                <div class="mt-2 text-sm text-gray-600 dark:text-gray-300">
                                    <span class="font-semibold">{{ trip.driver_name || 'Driver pending' }}</span>
                                    <span class="mx-2 text-gray-300 dark:text-gray-600">•</span>
                                    <span>{{ trip.vehicle_code || 'Vehicle not linked' }}</span>
                                </div>
                                <div class="mt-3 grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
                                    <div><div class="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">ETA</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ trip.eta_label }}</div></div>
                                    <div><div class="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">Delay Risk</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ trip.delay_probability_pct }}%</div></div>
                                    <div><div class="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">Confidence</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ trip.eta_confidence }}</div></div>
                                    <div><div class="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">Alt Recovery</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ alternateRecoveryMinutes(trip) }} min</div></div>
                                </div>
                            </div>
                            <div class="min-w-[13rem] rounded-2xl border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
                                <div class="font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">Recommendation</div>
                                <div class="mt-2 leading-relaxed">{{ trip.dispatcher_recommendation }}</div>
                            </div>
                        </div>
                    </button>
                </div>
            </div>

            <div v-if="selectedTrip" class="space-y-4">
                <div class="rounded-3xl border border-gray-200 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                            <div class="text-[11px] font-bold uppercase tracking-[0.22em] text-primary">Trip Brief</div>
                            <h3 class="mt-2 text-xl font-black text-gray-900 dark:text-white">{{ selectedTrip.tracking_code }}</h3>
                            <p class="mt-2 max-w-xl text-sm text-gray-600 dark:text-gray-300">{{ selectedTrip.dispatcher_recommendation }}</p>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            <span class="rounded-full border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em]" :class="riskChipClass(selectedTrip.risk_level)">{{ selectedTrip.risk_level }}</span>
                            <span class="rounded-full border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em]" :class="selectedTrip.no_go_zone_hit ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400' : 'border-green-200 bg-green-50 text-green-700 dark:border-green-500/20 dark:bg-green-500/10 dark:text-green-400'">
                                {{ selectedTrip.no_go_zone_hit ? 'No-Go Flag' : 'Clear Corridor' }}
                            </span>
                        </div>
                    </div>
                    <div class="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
                        <div v-for="item in detailStats" :key="item.label" class="rounded-2xl border p-3" :class="item.panelClass">
                            <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">{{ item.label }}</div>
                            <div class="mt-2 text-xl font-black text-gray-900 dark:text-white">{{ item.value }}</div>
                            <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ item.detail }}</div>
                        </div>
                    </div>
                </div>

                <div class="overflow-hidden rounded-3xl border border-gray-200 bg-white dark:border-white/10 dark:bg-white/5">
                    <div class="border-b border-gray-200 p-4 dark:border-white/10">
                        <h3 class="font-bold text-gray-900 dark:text-white">Trip Corridor View</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Pickup-to-destination operational corridor.</p>
                    </div>
                    <div ref="mapContainer" class="h-72 w-full"></div>
                </div>

                <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    <div v-for="route in routeCards" :key="route.route_id" class="rounded-3xl border p-5" :class="route.recommended ? 'border-primary bg-primary/5' : 'border-gray-200 bg-white dark:border-white/10 dark:bg-white/5'">
                        <div class="flex items-start justify-between gap-3">
                            <div>
                                <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-primary">{{ route.label }}</div>
                                <div class="mt-2 text-2xl font-black text-gray-900 dark:text-white">{{ route.eta_label }}</div>
                                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ route.summary }}</div>
                            </div>
                            <span v-if="route.recommended" class="rounded-full bg-primary px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-black">Recommended</span>
                        </div>
                        <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
                            <div class="rounded-2xl border border-gray-200 bg-gray-50 p-3 dark:border-white/10 dark:bg-black/10"><div class="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">Distance</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ route.distance_km }} km</div></div>
                            <div class="rounded-2xl border border-gray-200 bg-gray-50 p-3 dark:border-white/10 dark:bg-black/10"><div class="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">ETA Delta</div><div class="mt-1 font-semibold text-gray-900 dark:text-white">{{ route.delta_minutes < 0 ? `${Math.abs(route.delta_minutes)} min faster` : route.delta_minutes > 0 ? `${route.delta_minutes} min slower` : 'Current baseline' }}</div></div>
                        </div>
                        <button @click="pushTripCommand(route.route_id)" :disabled="pushingRoute === route.route_id"
                            class="mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold transition-colors"
                            :class="route.recommended ? 'bg-primary text-black hover:bg-primary-dark' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-white/10 dark:text-white dark:hover:bg-white/20'">
                            <span class="material-symbols-outlined text-[18px]">{{ pushingRoute === route.route_id ? 'progress_activity' : 'send' }}</span>
                            {{ pushingRoute === route.route_id ? 'Pushing...' : `Push ${route.label}` }}
                        </button>
                    </div>
                </div>

                <div class="rounded-3xl border border-gray-200 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <h3 class="font-bold text-gray-900 dark:text-white">Risk Signals</h3>
                    <div class="mt-4 space-y-3">
                        <div v-for="signal in selectedTrip.signals" :key="signal.key" class="rounded-2xl border px-4 py-3" :class="signalClass(signal.severity)">
                            <div class="text-[11px] font-black uppercase tracking-[0.18em]">{{ signal.key.replaceAll('_', ' ') }}</div>
                            <div class="mt-1 text-sm">{{ signal.label }}</div>
                        </div>
                    </div>
                </div>

                <div class="rounded-3xl border border-gray-200 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <h3 class="font-bold text-gray-900 dark:text-white">Push to Driver</h3>
                    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Driver gets the route note in the assignment and navigation flow, then opens Google Maps with the updated guidance.</p>
                    <textarea v-model="dispatcherNote" rows="3"
                        class="mt-4 w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-black/10 dark:text-white"
                        placeholder="Optional custom note for the driver"></textarea>
                    <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                        <button @click="pushTripCommand('recommended')" :disabled="pushingRoute === 'recommended'" class="rounded-2xl bg-primary px-4 py-3 text-sm font-black text-black transition hover:bg-primary-dark disabled:opacity-60">{{ pushingRoute === 'recommended' ? 'Pushing...' : 'Push Recommended' }}</button>
                        <button @click="pushTripCommand('primary')" :disabled="pushingRoute === 'primary'" class="rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-bold text-gray-700 transition hover:bg-gray-50 disabled:opacity-60 dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">{{ pushingRoute === 'primary' ? 'Pushing...' : 'Keep Primary Route' }}</button>
                        <button @click="pushTripCommand('alternate')" :disabled="pushingRoute === 'alternate'" class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-bold text-amber-800 transition hover:bg-amber-100 disabled:opacity-60 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300 dark:hover:bg-amber-500/20">{{ pushingRoute === 'alternate' ? 'Pushing...' : 'Push Alternate Route' }}</button>
                    </div>
                </div>
            </div>
        </div>

        <Transition enter-active-class="transition ease-out duration-300" enter-from-class="translate-y-4 opacity-0" enter-to-class="translate-y-0 opacity-100" leave-active-class="transition ease-in duration-200" leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
            <div v-if="toastMessage" class="fixed bottom-6 right-6 z-50 rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-black shadow-2xl">{{ toastMessage }}</div>
        </Transition>
    </div>
</template>

<script setup>
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useLogisticStore } from '@/stores/logisticStore'
import { authenticatedJsonRequest } from '@/config/api'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
    iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
    shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

const store = useDispatcherStore()
const logisticStore = useLogisticStore()
const loading = ref(true)
const statusFilter = ref('all')
const tripIntelligence = ref([])
const selectedOrderId = ref('')
const dispatcherNote = ref('')
const toastMessage = ref('')
const pushingRoute = ref('')
const filterOptions = [
    { label: 'All Trips', value: 'all' },
    { label: 'Needs Action', value: 'attention' },
    { label: 'On Track', value: 'on_track' },
]

const summaryCards = computed(() => {
    const trips = tripIntelligence.value
    const atRisk = trips.filter((trip) => trip.route_status !== 'On Track').length
    const alternateReady = trips.filter((trip) => trip.recommended_route === 'alternate').length
    const avgConfidence = trips.length
        ? Math.round((trips.filter((trip) => trip.eta_confidence === 'High').length / trips.length) * 100)
        : 0
    return [
        { label: 'Active Trips', value: trips.length, detail: 'Assigned or in-transit', icon: 'local_shipping', iconWrap: 'bg-blue-50 dark:bg-blue-500/10', iconClass: 'text-blue-600 dark:text-blue-400', panelClass: 'border-gray-200 bg-white dark:border-white/10 dark:bg-white/5' },
        { label: 'Needs Action', value: atRisk, detail: 'Delay risk, blocked, delayed', icon: 'error', iconWrap: 'bg-red-50 dark:bg-red-500/10', iconClass: 'text-red-600 dark:text-red-400', panelClass: 'border-gray-200 bg-white dark:border-white/10 dark:bg-white/5' },
        { label: 'Reroute Ready', value: alternateReady, detail: 'Alternate route recommended', icon: 'alt_route', iconWrap: 'bg-amber-50 dark:bg-amber-500/10', iconClass: 'text-amber-600 dark:text-amber-400', panelClass: 'border-gray-200 bg-white dark:border-white/10 dark:bg-white/5' },
        { label: 'High Confidence', value: `${avgConfidence}%`, detail: 'Trips with high ETA confidence', icon: 'verified', iconWrap: 'bg-green-50 dark:bg-green-500/10', iconClass: 'text-green-600 dark:text-green-400', panelClass: 'border-gray-200 bg-white dark:border-white/10 dark:bg-white/5' },
    ]
})

const filteredTrips = computed(() => {
    if (statusFilter.value === 'attention') return tripIntelligence.value.filter((trip) => trip.route_status !== 'On Track')
    if (statusFilter.value === 'on_track') return tripIntelligence.value.filter((trip) => trip.route_status === 'On Track')
    return tripIntelligence.value
})

const selectedTrip = computed(() =>
    filteredTrips.value.find((trip) => String(trip.order_id) === String(selectedOrderId.value))
    || filteredTrips.value[0]
    || null
)

const selectedOrder = computed(() =>
    store.activeOrders.find((order) => String(order.id) === String(selectedTrip.value?.order_id))
    || null
)

const detailStats = computed(() => {
    if (!selectedTrip.value) return []
    return [
        { label: 'Trip ETA', value: selectedTrip.value.eta_label, detail: `${selectedTrip.value.eta_minutes} min projected`, panelClass: 'border-gray-200 bg-gray-50 dark:border-white/10 dark:bg-black/10' },
        { label: 'Delay Probability', value: `${selectedTrip.value.delay_probability_pct}%`, detail: 'Risk engine output', panelClass: 'border-gray-200 bg-gray-50 dark:border-white/10 dark:bg-black/10' },
        { label: 'ETA Confidence', value: selectedTrip.value.eta_confidence, detail: 'Estimate quality', panelClass: 'border-gray-200 bg-gray-50 dark:border-white/10 dark:bg-black/10' },
        { label: 'Distance', value: `${selectedTrip.value.planned_distance_km} km`, detail: 'Operational trip distance', panelClass: 'border-gray-200 bg-gray-50 dark:border-white/10 dark:bg-black/10' },
    ]
})

const routeCards = computed(() => selectedTrip.value ? [selectedTrip.value.primary_route, selectedTrip.value.alternate_route] : [])

function alternateRecoveryMinutes(trip) {
    return Math.max(0, -(trip?.alternate_route?.delta_minutes || 0))
}

function riskChipClass(level) {
    if (level === 'CRITICAL' || level === 'HIGH') return 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400'
    if (level === 'MEDIUM') return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400'
    return 'border-green-200 bg-green-50 text-green-700 dark:border-green-500/20 dark:bg-green-500/10 dark:text-green-400'
}

function statusChipClass(status) {
    if (status === 'On Track') return 'border-green-200 bg-green-50 text-green-700 dark:border-green-500/20 dark:bg-green-500/10 dark:text-green-400'
    if (status === 'Delay Risk') return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400'
    return 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400'
}

function signalClass(severity) {
    if (severity === 'high') return 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300'
    if (severity === 'medium') return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300'
    return 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-300'
}

function showToast(message) {
    toastMessage.value = message
    window.clearTimeout(showToast._timer)
    showToast._timer = window.setTimeout(() => { toastMessage.value = '' }, 3200)
}

async function loadTripIntelligence() {
    loading.value = true
    try {
        await store.initialize().catch(() => {})
        await store.fetchActiveOrders().catch(() => {})
        const data = await authenticatedJsonRequest('api/v1/orders/trip-intelligence?statuses=ASSIGNED,IN_TRANSIT')
        tripIntelligence.value = Array.isArray(data) ? data : []
        if (!selectedOrderId.value && tripIntelligence.value[0]) selectedOrderId.value = String(tripIntelligence.value[0].order_id)
    } catch (error) {
        console.error('Failed to load trip intelligence', error)
        showToast('Could not load trip intelligence')
    } finally {
        loading.value = false
    }
}

async function pushTripCommand(route) {
    if (!selectedTrip.value) return
    pushingRoute.value = route
    try {
        const response = await authenticatedJsonRequest(`api/v1/orders/${selectedTrip.value.order_id}/trip-intelligence/push`, {
            method: 'POST',
            body: JSON.stringify({
                selected_route: route,
                dispatcher_note: dispatcherNote.value?.trim() || undefined,
            }),
        })
        showToast(response?.message || 'Trip command pushed to driver')
        await loadTripIntelligence()
    } catch (error) {
        console.error('Failed to push trip command', error)
        showToast('Could not push route update')
    } finally {
        pushingRoute.value = ''
    }
}

const mapContainer = ref(null)
let mapInstance = null
let mapLayers = []

function clearMap() {
    mapLayers.forEach((layer) => layer.remove())
    mapLayers = []
}

function ensureMap() {
    if (mapInstance || !mapContainer.value) return
    mapInstance = L.map(mapContainer.value, { zoomControl: true }).setView([12.9716, 77.5946], 11)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(mapInstance)
}

function drawSelectedTrip() {
    if (!mapInstance) return
    clearMap()

    const pickup = selectedOrder.value?.pickupLat != null && selectedOrder.value?.pickupLng != null
        ? [selectedOrder.value.pickupLat, selectedOrder.value.pickupLng]
        : null
    const delivery = selectedOrder.value?.deliveryLat != null && selectedOrder.value?.deliveryLng != null
        ? [selectedOrder.value.deliveryLat, selectedOrder.value.deliveryLng]
        : null

    if (!pickup && !delivery) {
        const hub = logisticStore.activeWarehouse && store.hubs.find((item) => item.id === logisticStore.activeWarehouse)
        const coords = Array.isArray(hub?.coordinates)
            ? hub.coordinates
            : typeof hub?.coordinates === 'string'
                ? hub.coordinates.split(',').map(Number)
                : [12.9716, 77.5946]
        mapInstance.setView(coords, 11)
        return
    }

    const bounds = []
    if (pickup) {
        mapLayers.push(L.marker(pickup).bindPopup(`<b>Pickup</b><br>${selectedTrip.value?.pickup_addr || 'Pickup location'}`).addTo(mapInstance))
        bounds.push(pickup)
    }
    if (delivery) {
        mapLayers.push(L.marker(delivery).bindPopup(`<b>Destination</b><br>${selectedTrip.value?.delivery_addr || 'Destination'}`).addTo(mapInstance))
        bounds.push(delivery)
    }
    if (pickup && delivery) {
        mapLayers.push(L.polyline([pickup, delivery], {
            color: selectedTrip.value?.recommended_route === 'alternate' ? '#f59e0b' : '#1CE783',
            weight: 4,
            opacity: 0.85,
            dashArray: selectedTrip.value?.no_go_zone_hit ? '12 10' : undefined,
        }).addTo(mapInstance))
    }

    if (bounds.length === 1) mapInstance.setView(bounds[0], 12)
    if (bounds.length > 1) mapInstance.fitBounds(L.latLngBounds(bounds).pad(0.2))
}

watch(selectedTrip, async (trip) => {
    if (!trip) return
    dispatcherNote.value = trip.driver_message || ''
    await nextTick()
    ensureMap()
    drawSelectedTrip()
}, { immediate: true })

watch(selectedOrder, () => {
    drawSelectedTrip()
})

onMounted(async () => {
    await loadTripIntelligence()
    await nextTick()
    ensureMap()
    drawSelectedTrip()
})

onBeforeUnmount(() => {
    if (mapInstance) {
        mapInstance.remove()
        mapInstance = null
    }
})
</script>
