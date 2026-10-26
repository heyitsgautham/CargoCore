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
        <DisruptionAlerts />

        <!-- Active Crisis Cards -->
        <CrisisCards />

        <!-- Live Crisis Map + Re-optimization -->
        <CrisisMapPanel />

        <!-- Crisis History Log -->
        <CrisisHistory />

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
        <BroadcastAlertModal />

        <!-- Contact Driver Modal -->
        <DriverContactModal />
    </div>
</template>

<script setup>
import DisruptionAlerts from './crisis/DisruptionAlerts.vue'
import CrisisCards from './crisis/CrisisCards.vue'
import CrisisMapPanel from './crisis/CrisisMapPanel.vue'
import CrisisHistory from './crisis/CrisisHistory.vue'
import BroadcastAlertModal from './crisis/BroadcastAlertModal.vue'
import DriverContactModal from './crisis/DriverContactModal.vue'
import { crisisPageKey } from './crisis/crisisPageContext'
import { useCrisisAlertsSocket } from './crisis/useCrisisAlertsSocket'
import { buildApproximateCoords, hasCoordinates } from './crisis/crisisGeometry'
import { ref, computed, onMounted, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken } from '@/config/api'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import 'leaflet/dist/leaflet.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}

const store = useDispatcherStore()
const { activeDrivers } = useRealTimeTracking(null, { mode: 'all' })

onMounted(() => {
    store.initialize().catch(() => {})
})
useCrisisAlertsSocket(() => store.fetchAlerts())


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

provide(crisisPageKey, {
    activeCrises,
    activeCrisesWithCoords,
    activeDrivers,
    approximateMarkerCount,
    autoReroute,
    backupDriverCount,
    broadcastMsg,
    broadcastSending,
    broadcastSent,
    broadcastSeverity,
    callDriver,
    contactDriver,
    crisisMapCenter,
    crisisMapZoom,
    disruptionCrisesWithCoords,
    disruptions,
    getDriverMarkerOptions,
    handleCrisisAction,
    hasCrisisMapCenter,
    reassignOrder,
    reoptEligibleOrderCount,
    reoptResult,
    reoptRunning,
    resolvedIncidents,
    runReoptimization,
    sendBroadcast,
    showBroadcast,
    showDriverContact,
    updateETAs,
    weatherDisruptions,
})
</script>

<style scoped>
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translate(-50%, 20px); }
</style>
