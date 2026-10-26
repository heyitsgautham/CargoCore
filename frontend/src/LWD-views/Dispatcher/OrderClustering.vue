<template>
    <div class="space-y-4">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Smart Driver Assignment</h2>
                <p class="text-sm text-gray-400 mt-1">Real-time driver locations · AI-powered non-packing return-trip matching</p>
            </div>
            <div class="flex items-center gap-3">
                <!-- AI badge -->
                <div class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
                    AI Dispatch Engine
                </div>
                <!-- WS status -->
                <div class="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full"
                    :class="wsConnected ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'">
                    <span class="w-1.5 h-1.5 rounded-full" :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'"></span>
                    {{ wsConnected ? 'Live Tracking' : 'Reconnecting...' }}
                </div>
                <button @click="refreshAll"
                    class="bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-bold">
                    <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': refreshing }">refresh</span>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Stats Row -->
        <div class="grid grid-cols-3 gap-3">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-green-400">{{ availableDrivers.length }}</div>
                <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Available Drivers</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-yellow-400">{{ unassignedOrders.length }}</div>
                <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Pending Pickups</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-primary">{{ availableVehicles.length }}</div>
                <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">Free Vehicles</div>
            </div>
        </div>

        <!-- Main Layout: Map + Side Panel -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

            <!-- Map -->
            <div class="lg:col-span-2 glass-panel rounded-xl overflow-hidden relative" style="height: 560px">
                <div id="smart-assign-map" class="w-full h-full"></div>

                <!-- Map Legend -->
                <div class="absolute bottom-3 left-3 bg-gray-900/90 backdrop-blur rounded-lg p-3 text-xs space-y-1.5 z-[999]">
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-green-400 inline-block"></span> Available Driver</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-yellow-400 inline-block"></span> On Trip</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-orange-500 inline-block"></span> Pending Pickup</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-blue-400 inline-block"></span> Delivery Point</div>
                </div>

                <!-- Selected suggestion highlight -->
                <div v-if="selectedSuggestion" class="absolute top-3 left-1/2 -translate-x-1/2 bg-primary text-black text-xs font-bold px-4 py-2 rounded-full z-[999] shadow-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-[14px]">route</span>
                    {{ selectedSuggestion.suggested_driver_name || selectedSuggestion.driver_name }} → {{ selectedSuggestion.order_tracking_code || selectedSuggestion.pending_tracking_code }}
                    <button @click="clearSelection" class="ml-1 opacity-60 hover:opacity-100">✕</button>
                </div>
            </div>

            <!-- Right Panel -->
            <div class="flex flex-col gap-3 overflow-y-auto" style="max-height: 560px">

                <AiSuggestionsPanel />
                <!-- Pending Orders (manual assignment) -->
                <PendingOrdersPanel />
            </div>
        </div>
    </div>
</template>

<script setup>
import AiSuggestionsPanel from './clustering/AiSuggestionsPanel.vue'
import PendingOrdersPanel from './clustering/PendingOrdersPanel.vue'
import { clusteringPageKey } from './clustering/clusteringPageContext'
import { needsDispatcherVehicle, priorityClass, vehicleLabel } from './clustering/clusterRules'
import { makeDeliveryIcon, makeDriverIcon, makeOrderIcon, parseLatLng } from './clustering/clusterMap'
import { ref, computed, onMounted, onUnmounted, nextTick, reactive, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import {
    isVehicleDispatchableStatus,
    orderAllowsDirectVehicleSelection,
    recurringRuleId,
    vehicleFitScore,
    vehicleHasOpenAssignments,
} from './dispatchRules'
import { getStoredAccessToken, API_BASE_URL } from '@/config/api'

const store = useDispatcherStore()

// ── State ────────────────────────────────────────────────────────────────────
const wsConnected = ref(false)
const refreshing = ref(false)
const assigningId = ref(null)       // order_id or pending_order_id being assigned
const selectedSuggestion = ref(null)
const orderDriverPick = reactive({})
const orderVehiclePick = reactive({})

// AI suggestion state
const aiSuggestions = ref([])
const aiLoading = ref(false)

// Live driver locations from WebSocket — keyed by driver_id
const liveLocations = ref({})

let map = null
let ws = null
let wsRetryTimeout = null
const driverMarkers = {}
const orderMarkers = {}

// ── Helpers ───────────────────────────────────────────────────────────────────

function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}

const availableVehicles = computed(() =>
    (store.filteredVehicles || []).filter((vehicle) =>
        isVehicleDispatchableStatus(vehicle.status)
        && !vehicleHasOpenAssignments(vehicle.id, store.activeOrders)
    )
)

const ordersById = computed(() => {
    const mapped = new Map()
    for (const order of store.pendingOrders || []) {
        mapped.set(String(order.id), order)
    }
    return mapped
})

function getRecommendedVehicle(order) {
    if (!needsDispatcherVehicle(order) || !availableVehicles.value.length) return null
    return [...availableVehicles.value]
        .map((vehicle) => ({ vehicle, score: vehicleFitScore(vehicle, order) }))
        .sort((a, b) => b.score - a.score)[0]?.vehicle || null
}

function resolveVehicleIdForOrder(order) {
    if (!order) return null
    return order.vehicleId || orderVehiclePick[order.id] || getRecommendedVehicle(order)?.id || null
}

function recommendedVehicleLabel(order) {
    return vehicleLabel(getRecommendedVehicle(order))
}

function canAssignOrder(order) {
    if (!order) return false
    if (!orderDriverPick[order.id]) return false
    if (!needsDispatcherVehicle(order)) return true
    return !!resolveVehicleIdForOrder(order)
}

function orderForSuggestion(suggestion) {
    return ordersById.value.get(String(suggestion?.order_id || '')) || null
}

function vehicleLabelForSuggestion(suggestion) {
    const order = orderForSuggestion(suggestion)
    if (!order) return ''
    if (order.vehicleId) return order.vehicle
    const recommended = getRecommendedVehicle(order)
    return recommended ? vehicleLabel(recommended) : ''
}

function canAssignSuggestion(suggestion) {
    const order = orderForSuggestion(suggestion)
    if (!order) return false
    if (!needsDispatcherVehicle(order)) return true
    return !!resolveVehicleIdForOrder(order)
}

function aiSuggestionActionLabel(suggestion) {
    const order = orderForSuggestion(suggestion)
    return needsDispatcherVehicle(order) ? 'Assign Driver + Vehicle' : 'Assign Driver'
}

// ── Computed data ─────────────────────────────────────────────────────────────
const driversWithLocation = computed(() => {
    return store.dispatcherDrivers
        .filter(d => (d.status || '').toLowerCase() !== 'off-duty')
        .map(d => {
            const live = liveLocations.value[d.id]
            const coords = live
                ? { lat: live.latitude, lng: live.longitude }
                : parseLatLng(d.location)
            return { ...d, coords, liveStatus: live?.status || d.status }
        }).filter(d => d.coords)
})

const availableDrivers = computed(() =>
    driversWithLocation.value.filter(d => !['On Trip', 'IN_TRANSIT', 'Busy', 'off-duty', 'Off-Duty'].includes(d.liveStatus))
)

const unassignedOrders = computed(() =>
    {
        const candidates = store.pendingOrders.filter((order) =>
            !order.driverId
            && !order.packingAmount
            && (order.vehicleId || orderAllowsDirectVehicleSelection(order))
        )
        const byRule = new Map()
        const deduped = []

        for (const order of candidates) {
            if (!needsDispatcherVehicle(order)) {
                deduped.push(order)
                continue
            }

            const ruleId = recurringRuleId(order)
            if (!ruleId) {
                deduped.push(order)
                continue
            }

            const existing = byRule.get(ruleId)
            const orderTs = new Date(order.deadline || order.createdAt || 0).getTime() || Number.MAX_SAFE_INTEGER
            const existingTs = existing ? (new Date(existing.deadline || existing.createdAt || 0).getTime() || Number.MAX_SAFE_INTEGER) : Number.MAX_SAFE_INTEGER
            if (!existing || orderTs < existingTs) {
                byRule.set(ruleId, order)
            }
        }

        return [...deduped, ...byRule.values()]
    }
)

// ── Fetch AI suggestions ──────────────────────────────────────────────────────
async function fetchAiSuggestions() {
    aiLoading.value = true
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/orders/return-suggestions`, {
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
        })
        if (res.ok) {
            const data = await res.json()
            aiSuggestions.value = (data.suggestions || []).map((item) => ({
                order_id: item.pending_order_id,
                order_tracking_code: item.pending_tracking_code,
                pickup_addr: item.pickup_addr,
                delivery_addr: item.delivery_addr,
                priority: item.priority,
                suggested_driver_id: item.driver_id,
                suggested_driver_name: item.driver_name,
                distance_km: item.distance_km,
                confidence: Math.max(70, 95 - Math.round(Number(item.distance_km || 0) * 4)),
                reason: item.reason,
                ai_powered: item.ai_powered,
                delivered_minutes_ago: item.delivered_minutes_ago,
                last_delivery_addr: item.last_delivery_addr,
            }))
        }
    } catch (err) {
        console.warn('AI driver suggestions fetch failed:', err)
    } finally {
        aiLoading.value = false
    }
}

// ── Map setup ──────────────────────────────────────────────────────────────────
async function initMap() {
    const L = (await import('leaflet')).default
    await import('leaflet/dist/leaflet.css')

    if (map) { map.remove(); map = null }

    map = L.map('smart-assign-map', { zoomControl: true }).setView([12.9716, 77.5946], 10)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map)

    renderMarkers(L)
}

async function renderMarkers(L) {
    if (!map) return

    Object.values(driverMarkers).forEach(m => m.remove())
    Object.values(orderMarkers).forEach(m => m.remove())

    for (const driver of driversWithLocation.value) {
        const marker = L.marker([driver.coords.lat, driver.coords.lng], { icon: makeDriverIcon(L, driver.liveStatus) })
            .addTo(map)
            .bindPopup(`
                <div style="min-width:160px">
                    <div style="font-weight:bold;font-size:13px">${driver.name}</div>
                    <div style="font-size:11px;color:#888;margin-top:2px">${driver.liveStatus}</div>
                    <div style="font-size:11px;margin-top:4px">${driver.vehicle || 'No vehicle'}</div>
                </div>
            `)
        driverMarkers[driver.id] = marker
    }

    for (const order of unassignedOrders.value) {
        if (!order.pickupLat || !order.pickupLng) continue
        const marker = L.marker([order.pickupLat, order.pickupLng], { icon: makeOrderIcon(L) })
            .addTo(map)
            .bindPopup(`
                <div style="min-width:180px">
                    <div style="font-weight:bold;font-size:12px;color:#f97316">📦 Pending Pickup</div>
                    <div style="font-size:11px;font-weight:bold;margin-top:4px">${order.trackingCode || order.id.slice(0, 8)}</div>
                    <div style="font-size:10px;color:#888;margin-top:2px">${order.pickupAddr || ''}</div>
                    <div style="font-size:10px;margin-top:4px">→ ${order.deliveryAddr || ''}</div>
                </div>
            `)
        orderMarkers[order.id] = marker

        if (order.deliveryLat && order.deliveryLng) {
            L.marker([order.deliveryLat, order.deliveryLng], { icon: makeDeliveryIcon(L) })
                .addTo(map)
                .bindPopup(`<div style="font-size:11px"><b>Delivery Point</b><br>${order.deliveryAddr || ''}</div>`)
            L.polyline([[order.pickupLat, order.pickupLng], [order.deliveryLat, order.deliveryLng]], {
                color: '#f97316', dashArray: '6 6', weight: 1.5, opacity: 0.5,
            }).addTo(map)
        }
    }

    const allCoords = [
        ...driversWithLocation.value.map(d => [d.coords.lat, d.coords.lng]),
        ...unassignedOrders.value.filter(o => o.pickupLat && o.pickupLng).map(o => [o.pickupLat, o.pickupLng]),
    ]
    if (allCoords.length > 0) {
        map.fitBounds(allCoords, { padding: [40, 40], maxZoom: 13 })
    }
}

// Update a single driver marker in real-time from WebSocket
async function updateDriverMarker(driverId, lat, lng, status) {
    if (!map) return
    const L = (await import('leaflet')).default
    const existing = driverMarkers[driverId]
    if (existing) {
        existing.setLatLng([lat, lng])
        existing.setIcon(makeDriverIcon(L, status))
    } else {
        const driver = store.dispatcherDrivers.find(d => d.id === driverId)
        const marker = L.marker([lat, lng], { icon: makeDriverIcon(L, status) })
            .addTo(map)
            .bindPopup(`<b>${driver?.name || 'Driver'}</b><br>${status}`)
        driverMarkers[driverId] = marker
    }
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connectWS() {
    if (ws) ws.close()
    const token = getStoredAccessToken()
    if (!token) return
    const wsBase = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://127.0.0.1:8000'
    ws = new WebSocket(`${wsBase}/ws/fleet?token=${token}`)

    ws.onopen = () => { wsConnected.value = true }
    ws.onclose = () => {
        wsConnected.value = false
        wsRetryTimeout = setTimeout(connectWS, 5000)
    }
    ws.onerror = () => { wsConnected.value = false }

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'location_update') {
                const dId = String(msg.driver_id)
                liveLocations.value = {
                    ...liveLocations.value,
                    [dId]: { latitude: msg.latitude, longitude: msg.longitude, status: msg.status, lastUpdated: msg.last_updated },
                }
                updateDriverMarker(dId, msg.latitude, msg.longitude, msg.status)
            }
        } catch { /* ignore parse errors */ }
    }
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function assignAiSuggestion(suggestion) {
    assigningId.value = suggestion.order_id
    try {
        const order = orderForSuggestion(suggestion)
        const vehicleId = resolveVehicleIdForOrder(order)
        await store.assignOrder(suggestion.order_id, suggestion.suggested_driver_id, vehicleId)
        // Remove from list immediately — don't wait for refetch
        aiSuggestions.value = aiSuggestions.value.filter(s => s.order_id !== suggestion.order_id)
        await store.fetchOrders()
        await refreshMarkers()
    } finally {
        assigningId.value = null
        selectedSuggestion.value = null
    }
}

async function manualAssign(order) {
    const driverId = orderDriverPick[order.id]
    if (!driverId) return
    assigningId.value = order.id
    try {
        await store.assignOrder(order.id, driverId, resolveVehicleIdForOrder(order))
        delete orderDriverPick[order.id]
        delete orderVehiclePick[order.id]
        await refreshMarkers()
    } finally {
        assigningId.value = null
    }
}

async function refreshAll() {
    refreshing.value = true
    try {
        await store.initialize()
        await fetchAiSuggestions()
        await refreshMarkers()
    } finally {
        refreshing.value = false
    }
}

async function refreshMarkers() {
    const L = (await import('leaflet')).default
    await nextTick()
    renderMarkers(L)
}

function highlightAiSuggestion(s) {
    selectedSuggestion.value = s
    if (!map) return
    // Find the order's pickup marker and pan to it
    const marker = orderMarkers[s.order_id]
    if (marker) {
        map.panTo(marker.getLatLng(), { animate: true })
        marker.openPopup()
    }
}

function clearSelection() {
    selectedSuggestion.value = null
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
let driverPollInterval = null

onMounted(async () => {
    await store.initialize().catch(() => {})
    await nextTick()
    await initMap()
    connectWS()
    // Fetch AI suggestions — may take a few seconds with Gemini
    fetchAiSuggestions()
    // Poll driver locations every 30 s so Off-Duty drivers disappear
    // and new Active drivers appear without a manual refresh
    driverPollInterval = setInterval(async () => {
        await store.fetchDrivers().catch(() => {})
        await refreshMarkers()
    }, 30_000)
})

onUnmounted(() => {
    if (ws) ws.close()
    if (wsRetryTimeout) clearTimeout(wsRetryTimeout)
    if (map) { map.remove(); map = null }
    if (driverPollInterval) clearInterval(driverPollInterval)
})

provide(clusteringPageKey, {
    aiLoading,
    aiSuggestionActionLabel,
    aiSuggestions,
    assignAiSuggestion,
    assigningId,
    availableDrivers,
    availableVehicles,
    canAssignOrder,
    canAssignSuggestion,
    highlightAiSuggestion,
    manualAssign,
    needsDispatcherVehicle,
    orderDriverPick,
    orderVehiclePick,
    priorityClass,
    recommendedVehicleLabel,
    selectedSuggestion,
    unassignedOrders,
    vehicleLabel,
    vehicleLabelForSuggestion,
})
</script>
