<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div
                    class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center animate-pulse shadow-lg shadow-red-500/30">
                    <span class="material-symbols-outlined text-gray-900 dark:text-white">warning</span>
                </div>
                <h2 class="text-2xl font-bold text-red-400">Crisis Management Center</h2>
            </div>
            <div class="flex items-center gap-3">
                <span class="text-xs text-gray-400">{{ activeCrises.length }} Active</span>
                <button @click="refreshAlerts" :disabled="isRefreshing"
                    class="bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-700 dark:text-white border border-gray-300 dark:border-white/20 font-bold py-2 px-3 rounded-lg flex items-center gap-2 transition-colors text-sm disabled:opacity-50">
                    <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': isRefreshing }">refresh</span>
                </button>
                <button @click="showBroadcast = true" class="bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white border border-red-700 dark:border-red-500 font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors text-sm shadow-md">
                    <span class="material-symbols-outlined text-[18px]">notification_important</span>
                    Broadcast Alert
                </button>
            </div>
        </div>

        <!-- Disruption Detection Alerts -->
        <div v-if="disruptions.length" class="space-y-2">
            <div v-for="d in disruptions" :key="d.id"
                class="flex items-center justify-between p-3 rounded-lg border"
                :class="d.severity === 'critical' ? 'bg-red-500/10 border-red-500/20' : 'bg-yellow-500/10 border-yellow-500/20'">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined"
                        :class="d.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'">{{ d.icon }}</span>
                    <div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">{{ d.title }}</div>
                        <div class="text-[10px] text-gray-500 dark:text-gray-400">{{ d.detail }} • Affects {{ d.affected }} drivers</div>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button @click="autoReroute(d)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-all border shadow-sm"
                        :class="d.rerouted ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white border-gray-300 dark:border-white/20'">
                        {{ d.rerouted ? '✓ Plan Built' : 'Build Recovery Plan' }}
                    </button>
                    <button @click="updateETAs(d)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-all border shadow-sm"
                        :class="d.etaUpdated ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-blue-600 dark:bg-blue-500/20 hover:bg-blue-700 dark:hover:bg-blue-500/30 text-white dark:text-blue-400 border-blue-700 dark:border-blue-500/30'">
                        {{ d.etaUpdated ? '✓ ETAs Refreshed' : 'Refresh ETAs' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Active Crisis Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div v-for="crisis in activeCrises" :key="crisis.id"
                class="border rounded-xl p-6 relative overflow-hidden"
                :class="crisis.level === 'CRITICAL' ? 'bg-red-500/10 border-red-500/30' : 'bg-yellow-500/10 border-yellow-500/30'">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-1 text-xs font-bold rounded"
                            :class="crisis.level === 'CRITICAL' ? 'bg-red-500 text-white animate-pulse' : 'bg-yellow-500 text-black'">
                            {{ crisis.level }}
                        </span>
                        <span class="text-gray-900 dark:text-white font-bold">{{ crisis.title }}</span>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ crisis.timeAgo }}</div>
                </div>
                <div class="text-gray-600 dark:text-gray-200 text-sm mb-3">{{ crisis.description }}</div>

                <!-- Affected Orders / Reassignment -->
                <div v-if="crisis.affectedOrders?.length" class="mb-3 p-3 bg-gray-100 dark:bg-black/30 rounded-lg">
                    <div class="text-[10px] text-gray-500 dark:text-gray-500 uppercase font-bold mb-2">Affected Orders – Backup Driver Planning</div>
                    <div class="space-y-1">
                        <div v-for="order in crisis.affectedOrders" :key="order.id"
                            class="flex items-center justify-between text-xs">
                            <span class="text-gray-600 dark:text-gray-300">{{ order.id }} – {{ order.dest }}</span>
                            <div class="flex items-center gap-2">
                                <span v-if="order.reassigned" class="text-green-400 font-bold">→ {{ order.newDriver }}</span>
                                <button v-else @click="reassignOrder(crisis.id, order.id)"
                                    class="bg-emerald-600 hover:bg-emerald-700 dark:bg-primary/20 dark:hover:bg-primary/30 text-white dark:text-primary px-2.5 py-1 rounded-lg font-bold transition-colors text-xs shadow-sm">
                                    Suggest Backup
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ETA Update + AI Bot Notification -->
                <div class="mb-3 flex items-center gap-2 text-[10px]">
                    <span class="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded font-bold">ETA Updated</span>
                    <span class="text-gray-500">
                        {{ crisis.type === 'broadcast' ? 'Drivers notified via AI Bot' : (crisis.driverId || crisis.driver_id) ? 'Driver + Customers notified via AI Bot' : 'Customers notified via AI Bot' }}
                    </span>
                </div>

                <div class="flex gap-3">
                    <button v-for="action in crisis.actions" :key="action.label"
                        @click="handleCrisisAction(crisis, action)"
                        :class="[action.baseClass, action.done ? 'opacity-60 cursor-default' : '']" 
                        class="flex-1 font-bold py-2.5 rounded-lg transition-all text-sm border shadow-md">{{ action.done ? '✓ ' + action.label : action.label }}</button>
                </div>
            </div>
        </div>

        <!-- Live Crisis Map + Re-optimization -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 glass-panel rounded-xl h-[400px] relative overflow-hidden">
                <!-- Real Leaflet map -->
                <l-map v-if="hasCrisisMapCenter" :zoom="crisisMapZoom" :center="crisisMapCenter" :use-global-leaflet="false" style="height:100%;width:100%;">
                    <l-tile-layer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        layer-type="base"
                    ></l-tile-layer>

                    <!-- Live driver location markers (blue dots) -->
                    <l-circle-marker
                        v-for="driver in activeDrivers"
                        :key="'driver-' + driver.driver_id"
                        :lat-lng="[driver.latitude, driver.longitude]"
                        :radius="8"
                        :options="getDriverMarkerOptions(driver)"
                    >
                        <l-popup>
                            <div class="text-xs p-1 min-w-[140px]">
                                <div class="font-bold text-blue-500 mb-1 flex items-center gap-1">
                                    <span class="inline-block w-2 h-2 rounded-full" :class="driver.status === 'active' ? 'bg-green-500' : 'bg-gray-400'"></span>
                                    {{ driver.driver_name || driver.name || 'Driver' }}
                                </div>
                                <div class="text-gray-600">{{ driver.vehicle_code || 'No vehicle' }}</div>
                                <div class="text-gray-400 mt-1 text-[10px]">{{ driver.status || 'Unknown status' }}</div>
                            </div>
                        </l-popup>
                    </l-circle-marker>

                    <!-- Crisis incident markers (colored circle markers) -->
                    <l-circle-marker
                        v-for="crisis in activeCrisesWithCoords"
                        :key="crisis.id"
                        :lat-lng="crisis.coords"
                        :radius="crisis.level === 'CRITICAL' ? 16 : 11"
                        :options="crisis.lat && crisis.lng
                            ? { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.95, weight: 3 }
                            : crisis.level === 'CRITICAL'
                                ? { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.75, weight: 2 }
                                : { color: '#eab308', fillColor: '#eab308', fillOpacity: 0.75, weight: 2 }"
                    >
                        <l-popup>
                            <div class="text-xs p-1 min-w-[180px]">
                                <div class="font-bold mb-1" :class="crisis.level === 'CRITICAL' ? 'text-red-500' : 'text-yellow-500'">
                                    {{ crisis.level }}: {{ crisis.title }}
                                </div>
                                <div class="text-gray-600">{{ crisis.description }}</div>
                                <div v-if="crisis.lat && crisis.lng" class="text-green-600 mt-1 text-[10px] font-bold">
                                    📍 GPS: {{ crisis.lat.toFixed(4) }}, {{ crisis.lng.toFixed(4) }}
                                </div>
                                <div v-else class="text-orange-500 mt-1 text-[10px]">📍 Approx. location</div>
                                <div class="text-gray-400 mt-1 text-[10px]">{{ crisis.timeAgo }}</div>
                            </div>
                        </l-popup>
                    </l-circle-marker>

                    <!-- Disruption markers (lower severity, orange) -->
                    <l-circle-marker
                        v-for="d in disruptionCrisesWithCoords"
                        :key="d.id"
                        :lat-lng="d.coords"
                        :radius="8"
                        :options="{ color: '#f97316', fillColor: '#f97316', fillOpacity: 0.7, weight: 1 }"
                    >
                        <l-popup>
                            <div class="text-xs p-1">
                                <div class="font-bold text-orange-500 mb-1">{{ d.title }}</div>
                                <div class="text-gray-600">{{ d.detail }}</div>
                            </div>
                        </l-popup>
                    </l-circle-marker>
                </l-map>
                <div v-else class="h-full flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-6 text-center">
                    <div class="max-w-sm">
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">Waiting for live operational coordinates</div>
                        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">The crisis map will appear once alerts, live driver GPS, active order locations, or warehouse coordinates are available.</div>
                    </div>
                </div>

                <!-- Overlay label -->
                <div v-if="hasCrisisMapCenter" class="absolute top-3 left-1/2 -translate-x-1/2 z-[400] pointer-events-none">
                    <div class="bg-black/70 backdrop-blur border border-red-500/30 px-4 py-2 rounded-lg text-center">
                        <div class="text-red-400 font-bold text-sm">Live Crisis Map</div>
                        <div class="text-gray-400 text-[10px]">{{ activeCrises.length }} incidents • {{ activeDrivers.length }} drivers live • {{ approximateMarkerCount }} approximated</div>
                    </div>
                </div>

                <!-- Weather overlay indicator -->
                <div v-if="weatherDisruptions.length" class="absolute bottom-4 right-4 z-[400] bg-white/90 dark:bg-black/80 backdrop-blur border border-gray-200 dark:border-white/10 rounded-lg p-3">
                    <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Weather Disruptions</div>
                    <div v-for="wd in weatherDisruptions" :key="wd.id" class="flex items-center gap-2 text-xs text-yellow-400 mt-1">
                        <span class="material-symbols-outlined text-[16px]">thunderstorm</span> {{ wd.title }}
                    </div>
                </div>
            </div>

            <!-- Re-Optimization Panel -->
            <div class="glass-panel rounded-xl p-6 flex flex-col">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">autorenew</span>
                    Re-Optimization Engine
                </h3>
                <div class="space-y-3 flex-1">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Impacted Routes</div>
                        <div class="text-gray-900 dark:text-white font-bold text-xl">{{ activeCrises.length }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Orders to Reassign</div>
                        <div class="text-gray-900 dark:text-white font-bold text-xl">{{ activeCrises.reduce((sum, c) => sum + (c.affectedOrders?.length || 0), 0) || 0 }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Confirmed Orders With Destination GPS</div>
                        <div class="text-gray-900 dark:text-white font-bold text-xl">{{ reoptEligibleOrderCount }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Available Backup Drivers</div>
                        <div class="text-primary font-bold text-xl">{{ backupDriverCount }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Disruptions Detected</div>
                        <div class="text-yellow-400 font-bold text-xl">{{ disruptions.length }}</div>
                    </div>

                    <!-- Results after running -->
                    <div v-if="reoptResult" class="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                        <div class="text-xs text-primary font-bold mb-2 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">check_circle</span>
                            {{ reoptResult.routes.length }} routes optimized
                        </div>
                        <div v-for="r in reoptResult.routes" :key="r.driver_id" class="text-[11px] text-gray-700 dark:text-gray-300 flex justify-between py-0.5 border-b border-gray-200 dark:border-white/10 last:border-0">
                            <span class="truncate max-w-[120px]">{{ r.driver_name }}</span>
                            <span class="text-primary font-bold">{{ r.stops.length }} stops · {{ r.total_distance_km }} km</span>
                        </div>
                        <div v-if="reoptResult.error" class="text-xs text-red-400 mt-1">{{ reoptResult.error }}</div>
                    </div>
                </div>
                <button @click="runReoptimization" :disabled="reoptRunning"
                    class="mt-4 w-full bg-primary hover:bg-primary-dark text-black font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined" :class="{ 'animate-spin': reoptRunning }">{{ reoptRunning ? 'progress_activity' : 'bolt' }}</span>
                    {{ reoptRunning ? 'Optimizing...' : 'Run Re-Optimization' }}
                </button>
                <div v-if="reoptRunning" class="mt-2 text-center text-xs text-primary animate-pulse">
                    Fetching confirmed orders and building a recovery route plan...
                </div>
                <div class="mt-2 text-center text-[11px] text-gray-500 dark:text-gray-400">
                    Uses confirmed orders only and builds a dispatcher recovery plan. It does not move in-transit jobs automatically.
                </div>
            </div>
        </div>

        <!-- Crisis History Log -->
        <div class="glass-panel rounded-xl p-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-green-600 dark:text-green-500">task_alt</span>
                Resolved Incidents (Today)
            </h3>
            <div class="space-y-3">
                <div v-for="resolved in resolvedIncidents" :key="resolved.id"
                    class="flex items-start gap-3 p-3 rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-all">
                    <span class="material-symbols-outlined text-green-600 dark:text-green-500 text-[20px]">check_circle</span>
                    <div class="flex-1">
                        <div class="text-gray-800 dark:text-gray-200 text-sm font-semibold mb-1">{{ resolved.title }}</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">{{ resolved.detail }}</div>
                    </div>
                    <span class="text-xs text-gray-700 dark:text-gray-300 font-mono font-semibold bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">{{ resolved.time }}</span>
                </div>
            </div>
        </div>

        <!-- Toast Notification -->
        <Teleport to="body">
        <transition name="slide-up">
        <div v-if="toast.show" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[10000] px-5 py-3 rounded-xl shadow-2xl font-bold text-sm flex items-center gap-2"
            :class="toast.type === 'success' ? 'bg-green-600 text-white' : toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-gray-800 text-white'">
            <span class="material-symbols-outlined text-[18px]">{{ toast.type === 'success' ? 'check_circle' : toast.type === 'error' ? 'error' : 'info' }}</span>
            {{ toast.message }}
        </div>
        </transition>
        </Teleport>

        <!-- Broadcast Alert Modal -->
        <Teleport to="body">
        <div v-if="showBroadcast" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showBroadcast = false">
            <div class="bg-gray-900 shadow-2xl border border-red-500/30 rounded-2xl p-6 w-full max-w-md m-4">
                <h3 class="font-bold text-red-400 mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined">campaign</span> Broadcast Crisis Alert
                </h3>
                <select v-model="broadcastSeverity" class="w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none mb-3">
                    <option class="bg-gray-800" value="critical">CRITICAL — Immediate action required</option>
                    <option class="bg-gray-800" value="high">HIGH — Urgent attention</option>
                    <option class="bg-gray-800" value="warning">WARNING — Advisory</option>
                </select>
                <textarea v-model="broadcastMsg" rows="3" placeholder="Alert message for all drivers..."
                    class="w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-red-500/50 mb-3 resize-none"></textarea>
                <div class="flex gap-2">
                    <button @click="sendBroadcast" :disabled="!broadcastMsg || broadcastSending" class="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold py-2 rounded-lg text-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-1 transition-colors">
                        <span v-if="broadcastSending" class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                        {{ broadcastSending ? 'Sending...' : 'Broadcast Now' }}
                    </button>
                    <button @click="showBroadcast = false" class="flex-1 bg-white/10 text-white py-2 rounded-lg text-sm hover:bg-white/20 transition-colors">Cancel</button>
                </div>
                <div v-if="broadcastSent" class="mt-2 text-center text-xs text-green-400 font-bold">✓ Alert broadcast to all active drivers</div>
            </div>
        </div>
        </Teleport>

        <!-- Contact Driver Modal -->
        <Teleport to="body">
        <div v-if="showDriverContact" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverContact = false">
            <div class="bg-white dark:bg-card-dark shadow-2xl border border-gray-200 dark:border-white/10 rounded-2xl p-6 w-full max-w-md m-4">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">support_agent</span> Contact Driver
                </h3>
                <div class="space-y-4">
                    <div class="flex items-center gap-4">
                        <img :src="contactDriver?.avatar" class="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700">
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white text-lg">{{ contactDriver?.name }}</div>
                            <div class="text-sm text-gray-500 dark:text-gray-400">{{ contactDriver?.vehicle }}</div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Phone Number</div>
                        <div class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">phone</span>
                            {{ contactDriver?.phone }}
                        </div>
                    </div>
                    <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Status</div>
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ contactDriver?.status }}</div>
                    </div>
                    <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Last Known Location</div>
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ contactDriver?.location }}</div>
                    </div>
                </div>
                <div class="flex gap-2 mt-6">
                    <button @click="callDriver" class="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-colors shadow-md">
                        <span class="material-symbols-outlined text-[18px]">call</span> Call Now
                    </button>
                    <button @click="showDriverContact = false" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2.5 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors font-bold">Close</button>
                </div>
            </div>
        </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken } from '@/config/api'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import { LMap, LTileLayer, LCircleMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE = API_BASE.replace(/^http/, 'ws')
function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}

const store = useDispatcherStore()
const { activeDrivers } = useRealTimeTracking(null, { mode: 'all' })

// ── Real-time SOS WebSocket ────────────────────────────────────────────────────
// Connects to ws/fleet to receive crisis_alert messages from drivers instantly
let crisisWs = null

function connectCrisisWebSocket() {
    const token = getStoredAccessToken()
    if (!token) return
    crisisWs = new WebSocket(`${WS_BASE}/ws/fleet?token=${encodeURIComponent(token)}`)

    crisisWs.onmessage = async (event) => {
        try {
            const data = JSON.parse(event.data)
            if (data.type === 'crisis_alert') {
                // Driver just sent SOS — refresh immediately so the card + map marker appear
                await store.fetchAlerts()
            }
        } catch (_) {}
    }

    crisisWs.onclose = () => {
        // Reconnect after 5s if closed unexpectedly
        setTimeout(() => { if (crisisWs?.readyState === WebSocket.CLOSED) connectCrisisWebSocket() }, 5000)
    }
}

onMounted(() => {
    store.initialize().catch(() => {})
    connectCrisisWebSocket()
})

onUnmounted(() => {
    crisisWs?.close()
    crisisWs = null
})

// Get driver marker options - highlight drivers in crisis
function getDriverMarkerOptions(driver) {
    const crisisDriverIds = activeCrises.value.map(c => c.driverId).filter(Boolean)
    const isInCrisis = crisisDriverIds.includes(driver.driver_id)
    
    if (isInCrisis) {
        return { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.9, weight: 3, className: 'animate-pulse' }
    }
    return { color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.7, weight: 2 }
}

const reoptRunning = ref(false)
const reoptResult = ref(null)
const showBroadcast = ref(false)
const showDriverContact = ref(false)
const contactDriver = ref(null)
const broadcastMsg = ref('')
const broadcastSeverity = ref('critical')
const broadcastSent = ref(false)
const broadcastSending = ref(false)
const isRefreshing = ref(false)
const toast = ref({ show: false, message: '', type: 'success' })

function showToast(message, type = 'success', duration = 3000) {
    toast.value = { show: true, message, type }
    setTimeout(() => { toast.value.show = false }, duration)
}

async function refreshAlerts() {
    isRefreshing.value = true
    try {
        await store.fetchAlerts()
    } catch (_) {}
    setTimeout(() => { isRefreshing.value = false }, 500)
}

const actionDoneMap = ref({})   // key: `${crisisId}-${actionLabel}`
const disruptionStateMap = ref({}) // key: `${disruptionId}-rerouted` or `-etaUpdated`
const reassignmentPlans = ref({})

function hasCoordinates(lat, lng) {
    return Number.isFinite(lat) && Number.isFinite(lng)
}

function buildApproximateCoords(baseCoords, index) {
    if (!Array.isArray(baseCoords) || baseCoords.length !== 2) return null
    const angle = (index * 137.508) * (Math.PI / 180)
    const distance = 0.02 + (index * 0.01)
    return [
        baseCoords[0] + Math.sin(angle) * distance,
        baseCoords[1] + Math.cos(angle) * distance,
    ]
}

const disruptions = computed(() =>
    store.disruptions.map(d => ({
        ...d,
        rerouted: disruptionStateMap.value[`${d.id}-rerouted`] || false,
        etaUpdated: disruptionStateMap.value[`${d.id}-etaUpdated`] || false,
    }))
)

const weatherDisruptions = computed(() =>
    store.disruptions.filter(d => d.type === 'weather' || d.icon === 'thunderstorm' || d.icon === 'foggy')
)

const backupDriverCount = computed(() =>
    store.dispatcherDrivers.filter(d => !d.breakDue && d.statusColor === 'bg-green-500' && (d.load || 0) < 30).length
)

const firstLiveDriverCoords = computed(() => {
    const driver = activeDrivers.value.find((item) => hasCoordinates(item.latitude, item.longitude))
    return driver ? [driver.latitude, driver.longitude] : null
})

const firstOrderCoords = computed(() => {
    for (const order of store.activeOrders) {
        if (hasCoordinates(order.deliveryLat, order.deliveryLng)) return [order.deliveryLat, order.deliveryLng]
        if (hasCoordinates(order.pickupLat, order.pickupLng)) return [order.pickupLat, order.pickupLng]
    }
    return null
})

const firstHubCoords = computed(() => {
    const hub = store.hubs.find((item) => hasCoordinates(item.lat, item.lng))
    return hub ? [hub.lat, hub.lng] : null
})

const operationalAnchor = computed(() => {
    const crisisWithGps = store.activeCrises.find((item) => hasCoordinates(item.lat, item.lng))
    if (crisisWithGps) return [crisisWithGps.lat, crisisWithGps.lng]
    if (firstOrderCoords.value) return firstOrderCoords.value
    if (firstLiveDriverCoords.value) return firstLiveDriverCoords.value
    if (firstHubCoords.value) return firstHubCoords.value
    return null
})

const reoptEligibleOrderCount = computed(() =>
    store.pendingOrders.filter((order) => hasCoordinates(order.deliveryLat, order.deliveryLng)).length
)

function matchCrisisOrders(crisis) {
    const targetDriverId = crisis.driverId ? String(crisis.driverId) : null
    const targetDriverName = String(crisis.driver || '').trim().toLowerCase()
    return store.activeOrders
        .filter((order) => order.status !== 'DELIVERED')
        .filter((order) => {
            if (targetDriverId && String(order.driverId || '') === targetDriverId) return true
            return targetDriverName && String(order.driver || '').trim().toLowerCase() === targetDriverName
        })
}

function resolveCrisisDriver(crisis) {
    const targetDriverId = crisis.driverId ? String(crisis.driverId) : null
    const targetDriverName = String(crisis.driver || '').trim().toLowerCase()
    return store.dispatcherDrivers.find((driver) => {
        if (targetDriverId && String(driver.id) === targetDriverId) return true
        return targetDriverName && String(driver.name || '').trim().toLowerCase() === targetDriverName
    }) || null
}

const activeCrises = computed(() =>
    store.activeCrises.map(c => {
        const driverProfile = resolveCrisisDriver(c)
        const affectedOrders = matchCrisisOrders(c).map((order) => {
            const plan = reassignmentPlans.value[`${c.id}:${order.id}`]
            return {
                id: order.id,
                trackingCode: order.trackingCode || order.id,
                dest: order.deliveryAddr || order.pickupAddr || 'Destination pending',
                reassigned: Boolean(plan),
                newDriver: plan?.driverName || null,
            }
        })
        return {
            ...c,
            type: c.alertType || 'alert',
            affectedOrders,
            driver: {
                name: driverProfile?.name || c.driver || 'Unknown',
                phone: driverProfile?.phone || 'No phone available',
                vehicle: driverProfile?.vehicle || 'Vehicle not linked',
                status: c.title,
                location: driverProfile?.location || c.description || '',
                avatar: driverProfile?.avatar || '',
            },
            actions: [
                {
                    label: 'Dispatch Recovery',
                    baseClass: 'bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 text-white border-red-700 dark:border-red-400',
                    done: actionDoneMap.value[`${c.id}-Dispatch Recovery`] || false,
                },
                {
                    label: 'Ignore',
                    baseClass: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-900 dark:text-white border-gray-400 dark:border-white/20',
                    done: actionDoneMap.value[`${c.id}-Ignore`] || false,
                },
            ],
        }
    })
)

const activeCrisesWithCoords = computed(() =>
    activeCrises.value
        .map((c, index) => {
            const exactCoords = hasCoordinates(c.lat, c.lng) ? [c.lat, c.lng] : null
            const approxCoords = exactCoords ? null : buildApproximateCoords(operationalAnchor.value, index)
            const coords = exactCoords || approxCoords
            if (!coords) return null
            return {
                ...c,
                coords,
                isApproximate: !exactCoords,
            }
        })
        .filter(Boolean)
)

const approximateMarkerCount = computed(() =>
    activeCrisesWithCoords.value.filter((item) => item.isApproximate).length
)

const disruptionCrisesWithCoords = computed(() =>
    disruptions.value
        .map((d, index) => {
            const coords = buildApproximateCoords(operationalAnchor.value, index + activeCrisesWithCoords.value.length)
            if (!coords) return null
            return {
                ...d,
                coords,
            }
        })
        .filter(Boolean)
)

const crisisMapCenter = computed(() => {
    if (activeCrisesWithCoords.value.length > 0) return activeCrisesWithCoords.value[0].coords
    if (operationalAnchor.value) return operationalAnchor.value
    return null
})

const hasCrisisMapCenter = computed(() => Array.isArray(crisisMapCenter.value) && crisisMapCenter.value.length === 2)

const crisisMapZoom = computed(() => {
    if (activeCrisesWithCoords.value.length > 0) return 12
    if (firstOrderCoords.value) return 12
    if (firstHubCoords.value) return 13
    if (firstLiveDriverCoords.value) return 11
    return 11
})

const resolvedIncidents = ref([])

// Track locally resolved crises for the history log
function addToResolved(crisis, resolution) {
    resolvedIncidents.value.unshift({
        id: crisis.id,
        title: crisis.title,
        detail: resolution,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
}

function pickBackupDriver(excludedDriverId = null) {
    return [...store.dispatcherDrivers]
        .filter((driver) => String(driver.id) !== String(excludedDriverId || ''))
        .filter((driver) => driver.statusColor === 'bg-green-500')
        .filter((driver) => !driver.breakDue && !driver.suspended)
        .sort((left, right) => (left.load || 0) - (right.load || 0))[0] || null
}

function reassignOrder(crisisId, orderId) {
    const crisis = activeCrises.value.find(c => c.id === crisisId)
    if (!crisis) return
    const order = crisis.affectedOrders.find(o => o.id === orderId)
    if (!order) return

    const backupDriver = pickBackupDriver(crisis.driverId)
    if (!backupDriver) {
        showToast('No backup driver is currently available for this recovery plan.', 'error')
        return
    }

    reassignmentPlans.value = {
        ...reassignmentPlans.value,
        [`${crisisId}:${orderId}`]: {
            driverId: backupDriver.id,
            driverName: backupDriver.name,
        },
    }

    showToast(`Backup plan ready: ${backupDriver.name} can recover ${order.trackingCode || order.id}.`, 'success')
}

async function runReoptimization() {
    if (reoptRunning.value) return
    reoptRunning.value = true
    reoptResult.value = null
    try {
        await Promise.allSettled([store.fetchOrders(), store.fetchActiveOrders(), store.fetchDrivers()])
        const res = await fetch(`${API_BASE}/api/v1/orders/optimize-routes?optimize_for=distance&prioritize_urgent=true`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
        })
        if (res.ok) {
            const routes = await res.json()
            if (routes.length === 0) {
                reoptResult.value = { routes: [], error: 'No confirmed orders with destination coordinates are ready for recovery planning.' }
            } else {
                reoptResult.value = { routes }
                showToast(`Recovery plan built for ${routes.length} driver routes across ${routes.reduce((s, r) => s + r.stops.length, 0)} stops.`, 'success')
            }
        } else {
            const err = await res.json().catch(() => ({}))
            reoptResult.value = { routes: [], error: err.detail || 'Optimization failed' }
            showToast(reoptResult.value.error, 'error')
        }
    } catch (_) {
        reoptResult.value = { routes: [], error: 'Could not reach server' }
        showToast('Re-optimization failed — check connection', 'error')
    } finally {
        reoptRunning.value = false
    }
}

async function autoReroute(disruption) {
    if (disruptionStateMap.value[`${disruption.id}-rerouted`]) return
    await runReoptimization()
    if (!reoptResult.value?.error) {
        disruptionStateMap.value[`${disruption.id}-rerouted`] = true
    }
}

async function updateETAs(disruption) {
    try {
        await Promise.allSettled([store.fetchOrders(), store.fetchActiveOrders(), store.fetchAlerts()])
        disruptionStateMap.value[`${disruption.id}-etaUpdated`] = true
        showToast('Dispatcher ETAs refreshed from the latest live order data.', 'success')
    } catch (_) {
        showToast('Could not refresh ETAs right now.', 'error')
    }
}

async function handleCrisisAction(crisis, action) {
    if (action.done) return
    if (action.label === 'Contact Driver') {
        contactDriver.value = crisis.driver
        showDriverContact.value = true
        return
    }
    actionDoneMap.value[`${crisis.id}-${action.label}`] = true
    if (action.label === 'Ignore') {
        await store.resolveAlert(crisis.id).catch(() => {})
        addToResolved(crisis, 'Marked as ignored by dispatcher')
        showToast('Crisis marked as ignored', 'success')
        return
    }
    if (action.label === 'Dispatch Recovery' || action.label === 'Reroute All') {
        // Notify the driver via broadcast
        try {
            await fetch(`${API_BASE}/api/v1/logistics/notifications/broadcast`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify({
                    audience: 'drivers',
                    type: 'emergency',
                    message: `Recovery team dispatched for: ${crisis.title}. Please stay at your location.`,
                })
            })
        } catch (_) {}
        // Resolve the crisis — removes it from active list
        await store.resolveAlert(crisis.id).catch(() => {})
        addToResolved(crisis, 'Recovery team dispatched, driver notified')
        showToast('Recovery dispatched — driver notified', 'success')
    }
}

function callDriver() {
    window.open(`tel:${contactDriver.value?.phone}`)
    showDriverContact.value = false
}

async function sendBroadcast() {
    if (!broadcastMsg.value) return
    broadcastSending.value = true
    try {
        // Map severity to broadcast type
        const severityToType = {
            critical: 'emergency',
            high: 'warning',
            warning: 'info'
        }
        // Call the broadcast endpoint directly for real-time driver notification
        const res = await fetch(`${API_BASE}/api/v1/logistics/notifications/broadcast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({
                audience: 'drivers',
                type: severityToType[broadcastSeverity.value] || 'warning',
                message: broadcastMsg.value
            })
        })
        if (res.ok) {
            // Also create an alert record for dispatcher's own crisis management view
            await store.createAlert({
                type: 'broadcast',
                title: `Broadcast: ${broadcastSeverity.value.toUpperCase()}`,
                description: broadcastMsg.value,
                severity: broadcastSeverity.value,
                icon: broadcastSeverity.value === 'critical' ? 'campaign' : 'notification_important',
            })
        }
        broadcastSent.value = true
        setTimeout(() => { showBroadcast.value = false; broadcastSent.value = false; broadcastMsg.value = '' }, 1500)
    } catch (_) {
        broadcastSent.value = true
        setTimeout(() => { showBroadcast.value = false; broadcastSent.value = false; broadcastMsg.value = '' }, 1500)
    } finally {
        broadcastSending.value = false
    }
}
</script>

<style scoped>
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translate(-50%, 20px); }
</style>
