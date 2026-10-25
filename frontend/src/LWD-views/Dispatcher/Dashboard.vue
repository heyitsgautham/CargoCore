<template>
  <div>
    <div class="flex h-[calc(94vh-3.5rem)] overflow-hidden">

        <!-- Left Panel: Active Driver Roster -->
        <DriverRosterPanel v-model:show-all="showAllDrivers" v-model:search="driverSearch" :show="showLeftPanel"
            :filtered-drivers="filteredDrivers" :selected-driver="selectedDriver" :drag-over-driver="dragOverDriver"
            @select="selectDriver" @panel-dragover="onDriverPanelDragOver" @panel-drop="onDropOnDriverPanel"
            @driver-dragover="onDriverDragOver" @driver-dragleave="dragOverDriver = null" @driver-drop="onDropOnDriver"
            @view="viewDriverDetail" @chat="chatWithDriver" />

        <!-- Center Panel: Interactive Map -->
        <div class="flex-1 bg-gray-200 dark:bg-gray-900 relative">
            <!-- Live Leaflet Map -->
            <div class="absolute inset-0 z-0">
                <l-map v-if="hasMapCenter" ref="map" :zoom="mapZoom" :center="mapCenter" :use-global-leaflet="false">
                    <!-- Base tile layer — switches between light/dark when Layers is toggled -->
                    <l-tile-layer
                        v-if="!mapLayers.layers"
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        layer-type="base"
                        name="CartoDB Voyager"
                    ></l-tile-layer>
                    <l-tile-layer
                        v-else
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        layer-type="base"
                        name="CartoDB Dark"
                    ></l-tile-layer>

                    <!-- Traffic overlay tile layer -->
                    <l-tile-layer
                        v-if="mapLayers.traffic"
                        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                        layer-type="overlay"
                        name="OpenStreetMap"
                        :options="{ opacity: 0.35 }"
                    ></l-tile-layer>

                    <DispatchMapOverlays :map-layers="mapLayers" :mappable-hubs="mappableHubs" :pickup-locations="pickupLocations"
                        :orders-with-delivery-coords="ordersWithDeliveryCoords" :mappable-crises="mappableCrises"
                        :mappable-zones="mappableZones" :driver-order-routes="driverOrderRoutes" :road-coords="roadCoords"
                        :active-drivers="activeDrivers" :driver-delivery-metrics="driverDeliveryMetrics" :eta-coverage-by-driver="etaCoverageByDriver"
                        :route-history-trails="routeHistoryTrails" />
                </l-map>
                <div v-else class="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-gray-900">
                    <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-white/90 dark:bg-black/40 backdrop-blur px-5 py-4 text-center shadow-lg">
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">Loading map data…</div>
                        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">Waiting for your warehouse or live order coordinates.</div>
                    </div>
                </div>
            </div>

            <!-- Map layer legend overlay when traffic is on -->
            <div v-if="mapLayers.traffic" class="absolute top-14 left-1/2 -translate-x-1/2 z-20 bg-white/90 dark:bg-black/80 backdrop-blur border border-amber-400/30 rounded-lg px-3 py-1.5 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 pointer-events-none">
                <span class="material-symbols-outlined text-[14px]">traffic</span>
                Traffic overlay active — live road data
            </div>

            <!-- Left Panel Toggle -->
            <button
                @click="showLeftPanel = !showLeftPanel"
                class="absolute top-4 left-4 z-20 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-md backdrop-blur-xl p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition-colors group"
                :title="showLeftPanel ? 'Hide Drivers' : 'Show Drivers'"
            >
                <span
                    class="material-symbols-outlined text-[18px]"
                    :class="showLeftPanel ? 'text-primary' : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'"
                >
                    {{ showLeftPanel ? 'left_panel_close' : 'left_panel_open' }}
                </span>
            </button>

            <!-- Right Panel Toggle -->
            <button
                @click="showRightPanel = !showRightPanel"
                class="absolute top-4 right-4 z-20 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-md backdrop-blur-xl p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition-colors group"
                :title="showRightPanel ? 'Hide Loads' : 'Show Loads'"
            >
                <span
                    class="material-symbols-outlined text-[18px]"
                    :class="showRightPanel ? 'text-primary' : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'"
                >
                    {{ showRightPanel ? 'right_panel_close' : 'right_panel_open' }}
                </span>
            </button>

            <MapToolbar :map-layers="mapLayers" :show-map-legend="showMapLegend" @toggle-layer="toggleMapLayer"
                @toggle-legend="showMapLegend = !showMapLegend" />

            <!-- Map Legend Overlay -->
            <MapLegend :show="showMapLegend" :map-layers="mapLayers" :active-layers-count="activeLayersCount"
                @close="showMapLegend = false" />
        </div>

        <!-- Right Panel: Pending Load Queue -->
        <PendingLoadsPanel :show="showRightPanel" :pending-loads="pendingLoads" :dragging-load="draggingLoad"
            :expanded-load="expandedLoad" :sla-projection="slaProjection" @open-assign="showAssignModal = true"
            @drag-start="onDragStart" @drag-end="onDragEnd" @toggle-detail="toggleLoadDetail" @assign-load="assignLoad" />

    </div>

    <!-- Assign Modal -->
    <AssignLoadModal v-model:order-id="assignOrderId" v-model:driver-id="assignDriverId" :show="showAssignModal"
        :pending-loads="pendingLoads" :assignable-drivers="assignableDrivers" :assigning="assigning"
        :success="assignSuccess" :error="assignError" @close="showAssignModal = false" @confirm="confirmAssign" />

    <!-- Driver Detail Modal -->
    <DriverDetailModal :show="showDriverDetailModal" :driver="detailDriver" @close="showDriverDetailModal = false"
        @chat="chatWithDriver" @assign="assignToDriverFromDetail" />


    <!-- Drag Assign Toast -->
    <Teleport to="body">
    <transition name="fade">
    <div v-if="dragAssignToast" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[9999] bg-green-500 text-black font-bold px-6 py-3 rounded-xl shadow-xl flex items-center gap-2 text-sm">
        <span class="material-symbols-outlined text-[18px]">check_circle</span>
        {{ dragAssignToast }}
    </div>
    </transition>
    </Teleport>


    <!-- Chat Modal -->
    <DriverChatModal v-model:draft="chatMsg" :show="showChatModal" :driver="chatDriver" :messages="driverChatMessages"
        @close="showChatModal = false" @send="sendDriverMsg" />
  </div>
</template>

<script setup>
import DriverRosterPanel from './dashboard/DriverRosterPanel.vue'
import DispatchMapOverlays from './dashboard/DispatchMapOverlays.vue'
import MapToolbar from './dashboard/MapToolbar.vue'
import MapLegend from './dashboard/MapLegend.vue'
import PendingLoadsPanel from './dashboard/PendingLoadsPanel.vue'
import AssignLoadModal from './dashboard/AssignLoadModal.vue'
import DriverDetailModal from './dashboard/DriverDetailModal.vue'
import DriverChatModal from './dashboard/DriverChatModal.vue'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import { useLogisticStore } from '@/stores/logisticStore'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import {
    buildDriverDeliveryMetrics,
    buildDriverOrderContext,
    buildDriverOrderRoutes,
    buildEtaTargets,
    buildPickupLocations,
    chooseMapCenter,
    chooseMapZoom,
    driverBusyReason,
    findBusyDriverIds,
    isDriverAssignable as canAssignDriver,
    mergeLiveMapOrders,
    placeCrises,
    withDeliveryCoords,
} from './dashboard/dispatchMapData'
import { computeEtaCoverage } from './dashboard/etaCoverage'
import {
    buildRouteHistoryTrails,
    extendDriverTrails,
    loadDriverTrailHistory,
    pruneDriverTrailHistory,
    saveDriverTrailHistory,
} from './dashboard/driverTrails'
import { useOrderGeocoding } from './dashboard/useOrderGeocoding'
import { useRoadRoutes } from './dashboard/useRoadRoutes'
import { useMapViewport } from './dashboard/useMapViewport'
import { useDriverChat } from './dashboard/useDriverChat'
import { useLoadDragAssign } from './dashboard/useLoadDragAssign'

// Fix Leaflet icons issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

const { activeDrivers } = useRealTimeTracking()

const store = useDispatcherStore()
const authStore = useAuthStore()
const logisticStore = useLogisticStore()

const showLeftPanel = ref(false)
const showRightPanel = ref(false)
const driverSearch = ref('')
const showAllDrivers = ref(false)
const selectedDriver = ref(null)
const expandedLoad = ref(null)
const showAssignModal = ref(false)
const assignOrderId = ref('')
const assignDriverId = ref('')
const assignSuccess = ref(false)
const assigning = ref(false)
const assignError = ref('')
const mapLayers = ref({ 
    layers: false, 
    traffic: false, 
    heatmap: false, 
    history: false,
    // New optional toggles
    hubs: true,           // Essential - always on by default
    pickups: true,        // Essential - pending order pickup points
    destinations: true,   // Optional - delivery destinations (NOW ENABLED BY DEFAULT)
    alerts: false,        // Optional - crisis/alert zones
    zones: false,         // Optional - geofence zones
    routes: false,        // Optional - driver-to-order routes
    eta: false,           // Nice-to-have - ETA circles
    clusters: false,      // Nice-to-have - order clustering
})
const showDriverDetailModal = ref(false)
const detailDriver = ref(null)
const showMapLegend = ref(false)

const drivers = computed(() => store.dispatcherDrivers)
const pendingLoads = computed(() => store.pendingOrders)
const slaProjection = computed(() => store.slaProjection)

// Map data sources
const hubs = computed(() => store.hubs || [])
const activeOrders = computed(() => store.activeOrders || [])
const activeCrises = computed(() => store.activeCrises || [])
const zones = computed(() => store.filteredZones || [])
const { resolveDestination, resolvePickup, geocodeMissing } = useOrderGeocoding()

const mappableHubs = computed(() => 
    hubs.value.filter(h => h.lat && h.lng && !isNaN(h.lat) && !isNaN(h.lng))
)

const scopedWarehouseHub = computed(() => {
    const explicitWarehouseId = String(logisticStore.activeWarehouse || 'all')
    const assignedWarehouseId = authStore.currentUser?.warehouse_id
        ? String(authStore.currentUser.warehouse_id)
        : null
    const targetWarehouseId = explicitWarehouseId !== 'all' ? explicitWarehouseId : assignedWarehouseId

    if (!targetWarehouseId) return null

    return mappableHubs.value.find((hub) => String(hub.id) === targetWarehouseId) || null
})

const liveMapOrders = computed(() => mergeLiveMapOrders(pendingLoads.value, activeOrders.value))
const ordersWithDeliveryCoords = computed(() => withDeliveryCoords(liveMapOrders.value, resolveDestination))
const mappableCrises = computed(() => placeCrises(activeCrises.value, mappableHubs.value, mapCenter.value))
const mappableZones = computed(() =>
    zones.value.filter(z => z.lat && z.lng && !isNaN(z.lat) && !isNaN(z.lng) && z.radius)
)
const pickupLocations = computed(() => buildPickupLocations(liveMapOrders.value, resolvePickup))

const mapAnchors = computed(() => ({
    scopedHub: scopedWarehouseHub.value,
    firstPickup: pickupLocations.value[0] || null,
    firstDestination: ordersWithDeliveryCoords.value[0] || null,
    activeDrivers: activeDrivers.value,
    hubs: mappableHubs.value,
    zones: mappableZones.value,
}))
const mapCenter = computed(() => chooseMapCenter(mapAnchors.value))
const hasMapCenter = computed(() => Array.isArray(mapCenter.value) && mapCenter.value.length === 2)
const mapZoom = computed(() => chooseMapZoom(mapAnchors.value))

const etaTargets = computed(() => buildEtaTargets(liveMapOrders.value, resolvePickup, resolveDestination))
const etaCoverageByDriver = ref({})
let etaCoverageTimer = null
const driverTrailHistory = ref(loadDriverTrailHistory())
const driverOrderContextMap = computed(() => buildDriverOrderContext(liveMapOrders.value))
const driverDeliveryMetrics = computed(() => buildDriverDeliveryMetrics(activeOrders.value))
const routeHistoryTrails = computed(() => buildRouteHistoryTrails(driverTrailHistory.value, activeDrivers.value))

function refreshEtaCoverage() {
    etaCoverageByDriver.value = mapLayers.value.eta
        ? computeEtaCoverage(activeDrivers.value, etaTargets.value)
        : {}
}

function scheduleEtaCoverageRefresh() {
    if (etaCoverageTimer) clearTimeout(etaCoverageTimer)
    etaCoverageTimer = setTimeout(() => {
        refreshEtaCoverage()
    }, 100)
}

function updateDriverTrailHistory() {
    driverTrailHistory.value = extendDriverTrails(driverTrailHistory.value, activeDrivers.value, driverOrderContextMap.value)
    saveDriverTrailHistory(driverTrailHistory.value)
}

const driverOrderRoutes = computed(() => buildDriverOrderRoutes(activeDrivers.value, liveMapOrders.value, resolveDestination))
const roadCoords = useRoadRoutes(driverOrderRoutes)

// Count active layers for legend
const activeLayersCount = computed(() => {
    return Object.values(mapLayers.value).filter(Boolean).length
})

const busyDriverIds = computed(() => findBusyDriverIds(activeOrders.value))

function isDriverAssignable(driver) {
    return canAssignDriver(driver, busyDriverIds.value)
}

const { showChatModal, chatDriver, chatMsg, driverChatMessages, chatWithDriver, sendDriverMsg } = useDriverChat(store)
const {
    draggingLoad,
    dragOverDriver,
    dragAssignToast,
    onDragStart,
    onDragEnd,
    onDriverPanelDragOver,
    onDriverDragOver,
    onDropOnDriverPanel,
    onDropOnDriver,
} = useLoadDragAssign({ store, isDriverAssignable })

const assignableDrivers = computed(() => (
    drivers.value.filter((driver) => isDriverAssignable(driver))
))

const filteredDrivers = computed(() => {
    let list = showAllDrivers.value ? drivers.value : assignableDrivers.value
    list = list.map((driver) => ({
        ...driver,
        isAssignable: isDriverAssignable(driver),
        busyReason: driverBusyReason(driver, busyDriverIds.value),
    }))
    if (driverSearch.value) {
        const q = driverSearch.value.toLowerCase()
        list = list.filter(d => d.name.toLowerCase().includes(q) || d.id.toLowerCase().includes(q) || d.vehicle.toLowerCase().includes(q))
    }
    return list
})

const { map, fitMapBounds, invalidateMapSize } = useMapViewport(() => {
    const points = []
    // Anchor the dashboard to the dispatcher's current warehouse when available.
    if (scopedWarehouseHub.value) {
        points.push([scopedWarehouseHub.value.lat, scopedWarehouseHub.value.lng])
    } else {
        mappableHubs.value.forEach(h => points.push([h.lat, h.lng]))
    }
    activeDrivers.value.forEach(d => {
        if (d.latitude && d.longitude) points.push([d.latitude, d.longitude])
    })
    if (mapLayers.value.pickups) {
        pickupLocations.value.forEach((pickup) => points.push([pickup.lat, pickup.lng]))
    }
    if (mapLayers.value.destinations) {
        ordersWithDeliveryCoords.value.forEach(o => points.push([o.resolvedDeliveryLat, o.resolvedDeliveryLng]))
    }
    return points
})

// Watch for panel changes
watch([showLeftPanel, showRightPanel], () => {
    invalidateMapSize()
})

// Watch for hub data changes to re-fit bounds
watch(mappableHubs, (newHubs, oldHubs) => {
    if (newHubs.length !== oldHubs?.length) {
        fitMapBounds()
    }
}, { deep: true })

watch(scopedWarehouseHub, (newHub, oldHub) => {
    if (newHub?.id !== oldHub?.id) {
        fitMapBounds()
    }
}, { deep: true })

watch(mapCenter, (newCenter, oldCenter) => {
    const changed = JSON.stringify(newCenter) !== JSON.stringify(oldCenter)
    if (changed && newCenter) {
        invalidateMapSize()
        fitMapBounds()
    }
}, { deep: true })

watch(ordersWithDeliveryCoords, (newOrders, oldOrders) => {
    if (newOrders.length !== (oldOrders?.length || 0)) {
        fitMapBounds()
    }
}, { deep: true })

watch(pickupLocations, (newPickups, oldPickups) => {
    if (newPickups.length !== (oldPickups?.length || 0)) {
        fitMapBounds()
    }
}, { deep: true })

watch([() => mapLayers.value.eta, activeDrivers, etaTargets], () => {
    scheduleEtaCoverageRefresh()
}, { immediate: true, deep: true })

watch([activeDrivers, driverOrderContextMap], () => {
    updateDriverTrailHistory()
}, { immediate: true, deep: true })

watch(liveMapOrders, (orders) => geocodeMissing(orders), { immediate: true, deep: true })

onMounted(() => {
    driverTrailHistory.value = pruneDriverTrailHistory(driverTrailHistory.value)
    saveDriverTrailHistory(driverTrailHistory.value)
    store.initialize().catch(() => {})
    scheduleEtaCoverageRefresh()
    // Invalidate map and fit bounds after initial render
    setTimeout(() => {
        invalidateMapSize()
        fitMapBounds()
    }, 500)
})

onUnmounted(() => {
    if (etaCoverageTimer) {
        clearTimeout(etaCoverageTimer)
        etaCoverageTimer = null
    }
})


function selectDriver(driver) {
    if (!driver?.isAssignable && !showAllDrivers.value) return
    selectedDriver.value = selectedDriver.value?.id === driver.id ? null : driver
}
function toggleLoadDetail(load) { expandedLoad.value = expandedLoad.value?.id === load.id ? null : load }
function toggleMapLayer(layer) { mapLayers.value[layer] = !mapLayers.value[layer] }

function assignLoad(load) {
    assignOrderId.value = load.id
    showAssignModal.value = true
}

async function confirmAssign() {
    if (!assignOrderId.value || !assignDriverId.value) return
    const driver = drivers.value.find((candidate) => String(candidate.id) === String(assignDriverId.value))
    if (!isDriverAssignable(driver)) {
        assignError.value = 'Selected driver is already assigned or unavailable.'
        return
    }
    assigning.value = true
    assignError.value = ''
    const ok = await store.assignOrder(assignOrderId.value, assignDriverId.value)
    assigning.value = false
    if (ok) {
        assignSuccess.value = true
        setTimeout(() => { showAssignModal.value = false; assignSuccess.value = false; assignOrderId.value = ''; assignDriverId.value = '' }, 1200)
    } else {
        assignError.value = 'Failed to assign. Please try again.'
    }
}

// Driver Detail Modal
function viewDriverDetail(driver) {
    detailDriver.value = driver
    showDriverDetailModal.value = true
}

function assignToDriverFromDetail() {
    showDriverDetailModal.value = false
    assignDriverId.value = detailDriver.value?.id || ''
    showAssignModal.value = true
}

</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
}
</style>
