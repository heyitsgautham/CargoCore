<template>
    <div class="space-y-4">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Smart Driver Assignment</h2>
                <p class="text-sm text-gray-400 mt-1">Real-time driver locations · AI-powered nearest driver assignment</p>
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
                <div class="text-2xl font-bold text-primary">{{ aiSuggestions.length }}</div>
                <div class="text-[10px] text-gray-400 uppercase tracking-wider mt-1">AI Suggestions</div>
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

                <!-- AI Driver Suggestions -->
                <div class="glass-panel rounded-xl p-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                        <span class="material-symbols-outlined text-purple-400 text-[18px]">auto_awesome</span>
                        AI Driver Suggestions
                        <span v-if="aiSuggestions.length" class="ml-auto bg-purple-500/20 text-purple-400 text-[10px] font-bold px-2 py-0.5 rounded-full">{{ aiSuggestions.length }}</span>
                    </h3>

                    <!-- Loading -->
                    <div v-if="aiLoading" class="text-center py-6 text-gray-500 text-xs">
                        <span class="material-symbols-outlined text-[28px] text-purple-400 block mb-2 animate-pulse">auto_awesome</span>
                        Gemini is ranking drivers...
                    </div>

                    <div v-else-if="aiSuggestions.length === 0" class="text-center py-6 text-gray-500 text-xs">
                        <span class="material-symbols-outlined text-[32px] text-gray-600 block mb-2">person_search</span>
                        No unassigned orders or no drivers with live GPS right now.
                    </div>

                    <div v-for="s in aiSuggestions" :key="s.order_id"
                        class="mb-2 p-3 rounded-lg border transition-all cursor-pointer"
                        :class="selectedSuggestion?.order_id === s.order_id ? 'border-primary bg-primary/5' : 'border-gray-200 dark:border-white/10 hover:border-purple-500/40'"
                        @click="highlightAiSuggestion(s)">

                        <div class="flex items-start justify-between gap-2 mb-1.5">
                            <div class="min-w-0">
                                <div class="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1.5 truncate">
                                    <span class="w-2 h-2 rounded-full bg-green-400 shrink-0 inline-block"></span>
                                    {{ s.suggested_driver_name }}
                                </div>
                                <div class="text-[10px] text-gray-400 mt-0.5 truncate">
                                    <span class="font-mono text-primary">{{ s.order_tracking_code }}</span>
                                    <span v-if="s.distance_km != null"> · {{ s.distance_km }}km away</span>
                                </div>
                            </div>
                            <div class="flex flex-col items-end gap-1 shrink-0">
                                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
                                    :class="priorityClass(s.priority)">{{ s.priority }}</span>
                                <span class="text-[10px] font-bold text-gray-500">{{ s.confidence }}% match</span>
                            </div>
                        </div>

                        <!-- AI reason -->
                        <div class="mb-2 p-2 rounded-lg text-[10px] leading-relaxed"
                            :class="s.ai_powered ? 'bg-purple-500/5 border border-purple-500/15 text-purple-300' : 'bg-gray-100 dark:bg-white/5 text-gray-500'">
                            <span v-if="s.ai_powered" class="material-symbols-outlined text-[10px] mr-0.5 align-middle text-purple-400">auto_awesome</span>
                            {{ s.reason }}
                        </div>

                        <div class="text-[10px] text-gray-500 truncate mb-2">
                            <span class="material-symbols-outlined text-[10px] align-middle text-orange-400">trip_origin</span>
                            {{ s.pickup_addr }}
                        </div>

                        <button @click.stop="assignAiSuggestion(s)"
                            :disabled="assigningId === s.order_id"
                            class="w-full py-1.5 bg-primary hover:bg-primary/80 disabled:opacity-50 text-black text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">{{ assigningId === s.order_id ? 'progress_activity' : 'person_add' }}</span>
                            {{ assigningId === s.order_id ? 'Assigning...' : 'Assign Driver' }}
                        </button>
                    </div>
                </div>

                <!-- Pending Orders (manual assignment) -->
                <div class="glass-panel rounded-xl p-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                        <span class="material-symbols-outlined text-yellow-400 text-[18px]">pending_actions</span>
                        Manual Assignment
                    </h3>

                    <div v-if="unassignedOrders.length === 0" class="text-center py-4 text-gray-500 text-xs">All orders assigned.</div>

                    <div v-for="order in unassignedOrders" :key="order.id"
                        class="mb-2 p-3 rounded-lg border border-gray-200 dark:border-white/10 hover:border-yellow-500/30 transition-all">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-xs font-mono font-bold text-gray-900 dark:text-white">{{ order.trackingCode || order.id.slice(0,8) }}</span>
                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" :class="priorityClass(order.priority)">{{ order.priority || 'NORMAL' }}</span>
                        </div>
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate mb-1">
                            <span class="material-symbols-outlined text-[11px] align-middle text-orange-400">trip_origin</span>
                            {{ order.pickupAddr || 'Pickup not set' }}
                        </div>
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate mb-2">
                            <span class="material-symbols-outlined text-[11px] align-middle text-blue-400">place</span>
                            {{ order.deliveryAddr || 'Delivery not set' }}
                        </div>
                        <div class="flex gap-2">
                            <select v-model="orderDriverPick[order.id]"
                                class="flex-1 text-[10px] bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-gray-900 dark:text-white outline-none">
                                <option value="">Select Driver</option>
                                <option v-for="d in availableDrivers" :key="d.id" :value="d.id">{{ d.name }}</option>
                            </select>
                            <button @click="manualAssign(order)"
                                :disabled="!orderDriverPick[order.id] || assigningId === order.id"
                                class="px-3 py-1.5 bg-primary disabled:opacity-40 hover:bg-primary/80 text-black text-[10px] font-bold rounded-lg transition-colors">
                                {{ assigningId === order.id ? '...' : 'Assign' }}
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, reactive } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken, API_BASE_URL } from '@/config/api'

const store = useDispatcherStore()

// ── State ────────────────────────────────────────────────────────────────────
const wsConnected = ref(false)
const refreshing = ref(false)
const assigningId = ref(null)       // order_id or pending_order_id being assigned
const selectedSuggestion = ref(null)
const orderDriverPick = reactive({})

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
function haversine(lat1, lng1, lat2, lng2) {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLng = (lng2 - lng1) * Math.PI / 180
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function parseLatLng(locationStr) {
    if (!locationStr || typeof locationStr !== 'string') return null
    const parts = locationStr.split(',').map(s => parseFloat(s.trim()))
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) return { lat: parts[0], lng: parts[1] }
    return null
}

function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}

function priorityClass(priority) {
    const p = (priority || 'NORMAL').toUpperCase()
    if (p === 'URGENT') return 'bg-red-500/20 text-red-400'
    if (p === 'HIGH') return 'bg-orange-500/20 text-orange-400'
    if (p === 'LOW') return 'bg-gray-500/20 text-gray-400'
    return 'bg-blue-500/20 text-blue-400'
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

const activeDrivers = computed(() =>
    driversWithLocation.value.filter(d => ['On Trip', 'IN_TRANSIT', 'Busy'].includes(d.liveStatus))
)

const unassignedOrders = computed(() =>
    store.pendingOrders.filter(o => !o.driverId)
)

// ── Fetch AI suggestions ──────────────────────────────────────────────────────
async function fetchAiSuggestions() {
    aiLoading.value = true
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/orders/ai-driver-suggestions`, {
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
        })
        if (res.ok) {
            const data = await res.json()
            aiSuggestions.value = data.suggestions || []
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

function makeDriverIcon(L, status) {
    const color = ['On Trip', 'IN_TRANSIT', 'Busy'].includes(status) ? '#facc15' : '#4ade80'
    return L.divIcon({
        className: '',
        html: `<div style="width:32px;height:32px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:14px;">🚚</span>
               </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    })
}

function makeOrderIcon(L) {
    return L.divIcon({
        className: '',
        html: `<div style="width:28px;height:28px;border-radius:50%;background:#f97316;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:12px;">📦</span>
               </div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 28],
    })
}

function makeDeliveryIcon(L) {
    return L.divIcon({
        className: '',
        html: `<div style="width:24px;height:24px;border-radius:50%;background:#60a5fa;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:10px;">🏁</span>
               </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 24],
    })
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
        await store.assignOrder(suggestion.order_id, suggestion.suggested_driver_id)
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
        await store.assignOrder(order.id, driverId)
        delete orderDriverPick[order.id]
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
</script>
