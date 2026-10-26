<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-green-500">gps_fixed</span> Real-Time Tracking
        </h2>

        <OrderSelector />

        <div v-if="activeMove && activeMove.status !== 'cancelled'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Map Area -->
            <div class="lg:col-span-2 space-y-4">
                <LiveMapPanel />

                <DwellTimeCard />

                <TransportLogCard />
            </div>

            <!-- Details Sidebar -->
            <div class="space-y-4">
                <DriverCard />

                <VehicleInfoCard />

                <BeforeAfterPhotos />

                <ServiceChecklist />

                <GeofenceAlertButton />

                <DeliverySlips />
            </div>
        </div>

        <!-- Cancelled Order View -->
        <div v-else-if="activeMove && activeMove.status === 'cancelled'" class="space-y-4">
            <!-- Cancellation Banner -->
            <div class="glass-panel p-6 rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50/50 dark:bg-red-500/5">
                <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-red-500 text-3xl">cancel</span>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-lg font-bold text-red-700 dark:text-red-400 mb-1">Order Cancelled</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400">{{ activeMove.cancellation?.reason || 'This order was cancelled.' }}</p>
                        <div class="flex items-center gap-3 mt-2 flex-wrap">
                            <span class="text-xs font-mono text-gray-500 dark:text-gray-400">{{ activeMove.id }}</span>
                            <span v-if="activeMove.cancellation?.fee > 0" class="text-xs font-bold text-red-600 dark:text-red-400">
                                Cancellation fee: ₹{{ activeMove.cancellation.fee.toLocaleString('en-IN') }}
                            </span>
                            <span v-else class="text-xs text-green-600 dark:text-green-400 font-medium">No cancellation fee</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Transport Log for cancelled order -->
            <div class="glass-panel p-4 sm:p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-500 text-lg">timeline</span> Transport Log
                </h3>
                <div class="relative pl-8">
                    <div class="absolute left-[11px] top-2 bottom-0 w-[2px] bg-gradient-to-b from-green-500 via-blue-500 to-red-400"></div>
                    <div v-for="(log, i) in activeMove.transportLog" :key="i" class="relative pb-5 last:pb-0 group">
                        <div class="absolute -left-8 top-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] shadow-md"
                            :style="{ backgroundColor: logColor(log.color) }">
                            <span class="material-symbols-outlined text-[12px]">{{ log.icon }}</span>
                        </div>
                        <div class="p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ log.event }}</span>
                            </div>
                            <div v-if="log.description" class="text-[11px] text-gray-600 dark:text-gray-400 mt-1 leading-snug">{{ log.description }}</div>
                            <div class="text-[10px] text-gray-500 dark:text-gray-500 font-mono mt-0.5">{{ log.time }}</div>
                        </div>
                    </div>
                    <div v-if="!activeMove.transportLog?.length" class="text-center py-4 text-gray-400 text-sm">
                        No transport events recorded.
                    </div>
                </div>
            </div>

            <router-link to="/individual/book-move"
                class="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded-xl transition-colors">
                <span class="material-symbols-outlined text-sm">add_circle</span> Book a New Move
            </router-link>
        </div>

        <div v-else class="glass-panel p-12 rounded-xl text-center text-gray-500 dark:text-gray-400">
            <span class="material-symbols-outlined text-5xl block mb-3">location_off</span>
            <p class="font-medium text-lg">No active move to track.</p>
            <router-link to="/individual/book-move"
                class="text-green-600 dark:text-green-400 text-sm font-bold hover:underline mt-2 inline-block">Book a
                Move →</router-link>
        </div>
        
        <DriverCallModal />

        <DriverChatModal />
    </div>
</template>

<script setup>
import OrderSelector from './tracking/OrderSelector.vue'
import LiveMapPanel from './tracking/LiveMapPanel.vue'
import DwellTimeCard from './tracking/DwellTimeCard.vue'
import TransportLogCard from './tracking/TransportLogCard.vue'
import DriverCard from './tracking/DriverCard.vue'
import VehicleInfoCard from './tracking/VehicleInfoCard.vue'
import BeforeAfterPhotos from './tracking/BeforeAfterPhotos.vue'
import ServiceChecklist from './tracking/ServiceChecklist.vue'
import GeofenceAlertButton from './tracking/GeofenceAlertButton.vue'
import DeliverySlips from './tracking/DeliverySlips.vue'
import DriverCallModal from './tracking/DriverCallModal.vue'
import DriverChatModal from './tracking/DriverChatModal.vue'
import { customerTrackingPageKey } from './tracking/customerTrackingPageContext'
import { ref, computed, watch, nextTick, onMounted, onActivated, onUnmounted, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { paddedCornerPairs } from '@/utils/mapBounds'
import {
    MAP_FIT_PADDING_TOP_LEFT,
    MAP_FIT_PADDING_BOTTOM_RIGHT,
    warehouseIcon,
    pickupIcon,
    destIcon,
    driverIcon,
    buildRouteBundle,
    getCachedRouteData,
    getRouteFocusSettings,
    ensureRouteData,
    warmDisplayOrderMapData,
} from './tracking/routeData'
import { useGeofenceAlert } from './tracking/useGeofenceAlert'
import { useDriverChat } from './tracking/useDriverChat'
import { useRouteSummary } from './tracking/useRouteSummary'

// Fix Leaflet icons issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

const route = useRoute()
const store = useIndividualStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()

const allOrders = computed(() => store.orders)

const displayOrders = computed(() => {
    if (route.query.orderId) {
        return allOrders.value.filter(o => o.id === route.query.orderId)
    }
    return allOrders.value
})

const selectedOrderId = ref(route.query.orderId || (allOrders.value.length > 0 ? allOrders.value[0].id : null))
const activeMove = computed(() => {
    return allOrders.value.find(o => o.id === selectedOrderId.value) || allOrders.value[0] || null
})
const shouldPollLiveTracking = computed(() => !['delivered', 'cancelled'].includes(activeMove.value?.status || ''))

// ─── Real-Time Tracking Integration ───
const { driver: trackingDriver } = useRealTimeTracking(selectedOrderId, {
    mode: 'single',
    enabled: shouldPollLiveTracking,
})

// ─── Route Blueprint State ───
const mapRef = ref(null)
const mapPanelRef = ref(null)
const warehouseCoords = ref(null) // [lat, lng]
const routeCoords = ref([])       // [[lat,lng],...] full route polyline
const warehouseToPickupCoords = ref([])
const pickupToDestCoords = ref([])
const pickupCoords = ref(null)    // [lat, lng]
const destCoords = ref(null)      // [lat, lng]
const routeLoading = ref(false)
const mapFocusFlash = ref(false)
const routeFocusMode = ref('instant')
let routeRequestToken = 0
let mapFocusFlashTimer = null
function requestSmoothMapFocus() {
    routeFocusMode.value = 'smooth'
    mapFocusFlash.value = true

    clearTimeout(mapFocusFlashTimer)
    mapFocusFlashTimer = setTimeout(() => {
        mapFocusFlash.value = false
    }, 1400)
}

async function fitMapToRoute(coords, { animate = false } = {}) {
    await nextTick()
    const leaflet = mapRef.value?.leafletObject
    if (!leaflet || !coords?.length) return

    leaflet.invalidateSize?.()
    leaflet.stop?.()

    if (coords.length === 1) {
        if (animate && leaflet.flyTo) {
            leaflet.flyTo(coords[0], 10, { animate: true, duration: 0.72, easeLinearity: 0.2 })
        } else {
            leaflet.setView(coords[0], 10)
        }
        return
    }

    const { maxZoom, duration, padFactor } = getRouteFocusSettings(coords)
    const bounds = paddedCornerPairs(coords, padFactor)
    if (animate && leaflet.flyToBounds) {
        leaflet.flyToBounds(bounds, {
            paddingTopLeft: MAP_FIT_PADDING_TOP_LEFT,
            paddingBottomRight: MAP_FIT_PADDING_BOTTOM_RIGHT,
            maxZoom,
            duration,
            easeLinearity: 0.18
        })
        return
    }

    leaflet.fitBounds(bounds, {
        paddingTopLeft: MAP_FIT_PADDING_TOP_LEFT,
        paddingBottomRight: MAP_FIT_PADDING_BOTTOM_RIGHT,
        maxZoom
    })
}

function applyRouteToMap(data) {
    const bundle = buildRouteBundle(data)
    warehouseCoords.value = bundle.warehouse
    pickupCoords.value = bundle.pickup
    destCoords.value = bundle.dest
    warehouseToPickupCoords.value = bundle.warehouseToPickup
    pickupToDestCoords.value = bundle.pickupToDest
    routeCoords.value = bundle.coords
}

function clearRouteFromMap() {
    warehouseCoords.value = null
    pickupCoords.value = null
    destCoords.value = null
    warehouseToPickupCoords.value = []
    pickupToDestCoords.value = []
    routeCoords.value = []
}

async function loadRouteForOrder(order) {
    if (!order) return
    const requestToken = ++routeRequestToken
    const shouldAnimate = routeFocusMode.value === 'smooth'
    routeFocusMode.value = 'instant'
    const cached = getCachedRouteData(order.id)
    const hasCachedRoute = Boolean(
        cached?.warehouse
        || cached?.pickup
        || cached?.dest
        || cached?.warehouseToPickup?.length
        || cached?.pickupToDest?.length
        || cached?.coords?.length
    )

    if (hasCachedRoute) {
        applyRouteToMap(cached)
        await fitMapToRoute(routeCoords.value, { animate: shouldAnimate })
    }

    routeLoading.value = true
    if (!hasCachedRoute) {
        clearRouteFromMap()
    }

    try {
        const resolved = await ensureRouteData(order, { allowGeometry: true })
        if (requestToken !== routeRequestToken) return

        applyRouteToMap(resolved)

        if (!hasCachedRoute) {
            await fitMapToRoute(routeCoords.value, { animate: shouldAnimate })
        }
    } finally {
        if (requestToken === routeRequestToken) {
            routeLoading.value = false
        }
    }
}

function getRouteCenter(coords) {
    if (!Array.isArray(coords) || !coords.length) return null
    if (coords.length === 1) return coords[0]
    const center = L.latLngBounds(coords).getCenter()
    return [center.lat, center.lng]
}

const mapCenter = computed(() => {
    const order = activeMove.value
    if (order?.status === 'delivered') {
        const deliveredCenter = getRouteCenter(routeCoords.value)
        if (deliveredCenter) return deliveredCenter
    }
    if (trackingDriver.value?.latitude && trackingDriver.value?.longitude) {
        return [trackingDriver.value.latitude, trackingDriver.value.longitude]
    }
    const routeCenter = getRouteCenter(routeCoords.value)
    if (routeCenter) return routeCenter
    if (warehouseCoords.value) return warehouseCoords.value
    if (pickupCoords.value) return pickupCoords.value
    if (destCoords.value) return destCoords.value
    return [19.0760, 72.8777]
})
const zoom = ref(13)

watch(() => route.query.orderId, (newId) => {
    if (newId) {
        requestSmoothMapFocus()
        selectedOrderId.value = newId
    } else if (!selectedOrderId.value && allOrders.value.length > 0) {
        selectedOrderId.value = allOrders.value[0].id
    }
}, { immediate: true })

watch(() => displayOrders.value.map(order => `${order.id}:${order.status}`).join('|'), () => {
    warmDisplayOrderMapData(displayOrders.value)
}, { immediate: false })

const activeRouteSignature = computed(() => {
    if (!activeMove.value) return ''
    return [
        activeMove.value.id,
        activeMove.value.warehouseId || '',
        activeMove.value.warehouseName || '',
        activeMove.value.warehouseAddress || '',
        activeMove.value.warehouseLat ?? '',
        activeMove.value.warehouseLng ?? '',
        activeMove.value.pickup,
        activeMove.value.destination,
        activeMove.value.status,
    ].join('|')
})

watch(activeRouteSignature, () => {
    if (activeMove.value && activeMove.value.status !== 'cancelled') {
        loadRouteForOrder(activeMove.value)
    }
}, { immediate: false })

function selectOrder(id) {
    requestSmoothMapFocus()

    if (selectedOrderId.value === id) {
        const currentCoords = routeCoords.value.length
            ? routeCoords.value
            : buildRouteBundle({
                warehouse: warehouseCoords.value,
                pickup: pickupCoords.value,
                dest: destCoords.value,
                warehouseToPickup: warehouseToPickupCoords.value,
                pickupToDest: pickupToDestCoords.value,
            }).coords
        fitMapToRoute(currentCoords, { animate: true })
        return
    }

    selectedOrderId.value = id
    // We don't push the route query here if they are in 'all orders' mode
    // because doing so would filter the list down to 1 item inside displayOrders.
    // So we just update the local state.
}
const { geofenceAlert, geofenceLoading, geofenceError, toggleGeofence } = useGeofenceAlert({ activeMove, authStore })

const {
    logColor,
    isWarehouseEvent,
    routeStageLabels,
    routeLegendItems,
    routeBlueprintLabel,
    serviceChecklist,
} = useRouteSummary({
    activeMove,
    destCoords,
    pickupCoords,
    pickupToDestCoords,
    warehouseCoords,
    warehouseToPickupCoords,
})

const {
    showCallModal,
    showChatModal,
    chatMessages,
    pendingMessage,
    chatScrollContainer,
    sendChatMessage,
} = useDriverChat()

let pollTimer = null

onMounted(async () => {
    await store.fetchTrackingOrders()
    warmDisplayOrderMapData(displayOrders.value)
    if (!selectedOrderId.value && allOrders.value.length > 0) {
        selectedOrderId.value = allOrders.value[0].id
    }
    if (activeMove.value && activeMove.value.status !== 'cancelled') {
        loadRouteForOrder(activeMove.value)
    }
    // Poll every 15 seconds for live warehouse updates
    pollTimer = setInterval(() => store.fetchTrackingOrders(), 15000)
})

onActivated(async () => {
    await store.fetchTrackingOrders()
    warmDisplayOrderMapData(displayOrders.value)
    if (!pollTimer) {
        pollTimer = setInterval(() => store.fetchTrackingOrders(), 15000)
    }
})

onUnmounted(() => {
    clearInterval(pollTimer)
    pollTimer = null
    clearTimeout(mapFocusFlashTimer)
})

provide(customerTrackingPageKey, {
    activeMove,
    authStore,
    chatMessages,
    chatScrollContainer,
    destCoords,
    destIcon,
    displayOrders,
    driverIcon,
    geofenceAlert,
    geofenceError,
    geofenceLoading,
    isWarehouseEvent,
    logColor,
    mapCenter,
    mapFocusFlash,
    mapPanelRef,
    mapRef,
    openSlipWithData,
    pendingMessage,
    pickupCoords,
    pickupIcon,
    pickupToDestCoords,
    routeBlueprintLabel,
    routeCoords,
    routeLegendItems,
    routeLoading,
    routeStageLabels,
    selectOrder,
    selectedOrderId,
    sendChatMessage,
    serviceChecklist,
    showCallModal,
    showChatModal,
    toggleGeofence,
    trackingDriver,
    warehouseCoords,
    warehouseIcon,
    warehouseToPickupCoords,
    zoom,
})
</script>
