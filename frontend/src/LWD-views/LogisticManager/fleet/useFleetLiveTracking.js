// Live driver positions for the fleet map: a WebSocket feed with exponential
// reconnect, and a 30-second REST poll while the socket is down.
import { computed, ref } from 'vue'
import { apiUrl, API_BASE_URL } from '@/config/api'
import { validPoints } from '@/utils/mapBounds'

export function useFleetLiveTracking(store) {
    const liveDrivers = ref([])
    const fleetLoading = ref(false)
    const wsConnected = ref(false)
    const liveLocationsMap = ref(null)

    let fleetWs = null
    let wsReconnectTimer = null
    let wsReconnectDelay = 2000
    let pollFallbackTimer = null

    function buildWsUrl() {
        const token = localStorage.getItem('auth_token') || ''
        const wsBase = API_BASE_URL.replace(/^http/, 'ws')
        return `${wsBase}/ws/fleet?token=${encodeURIComponent(token)}`
    }

    function liveDriverLocation(d) {
        // Try to get a human-readable location from the store driver record
        const storeDriver = store.drivers.find(sd =>
            String(sd.id) === String(d.driver_id) ||
            String(sd.name || '').trim().toLowerCase() === String(d.driver_name || '').trim().toLowerCase()
        )
        if (storeDriver?.location) return storeDriver.location
        const hub = store.hubs.find(h => h.id === storeDriver?.hubId)
        if (hub?.name) return hub.name
        if (d.last_updated) {
            return 'Updated ' + new Date(d.last_updated).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
        }
        return 'Location updating…'
    }

    function applyLocationUpdate(msg) {
        if (msg.latitude == null || msg.longitude == null) return
        const existing = liveDrivers.value.findIndex(d => d.driver_id === msg.driver_id)
        const entry = {
            driver_id: msg.driver_id,
            driver_name: msg.driver_name,
            latitude: msg.latitude,
            longitude: msg.longitude,
            status: msg.status,
            vehicle_code: msg.vehicle_code,
            vehicle_id: msg.vehicle_id,
            last_updated: msg.last_updated,
        }
        if (existing >= 0) {
            liveDrivers.value[existing] = entry
        } else {
            liveDrivers.value.push(entry)
        }
    }

    function connectFleetWs() {
        if (fleetWs && fleetWs.readyState <= WebSocket.OPEN) return
        try {
            fleetWs = new WebSocket(buildWsUrl())
        } catch (e) {
            scheduleWsReconnect()
            return
        }
        fleetWs.onopen = () => {
            wsConnected.value = true
            wsReconnectDelay = 2000
            clearInterval(pollFallbackTimer)
            pollFallbackTimer = null
        }
        fleetWs.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data)
                if (msg.type === 'location_update') applyLocationUpdate(msg)
                if (msg.type === 'ping') fleetWs.send(JSON.stringify({ type: 'pong' }))
            } catch (e) { /* ignore malformed frames */ }
        }
        fleetWs.onerror = () => { /* handled in onclose */ }
        fleetWs.onclose = () => {
            wsConnected.value = false
            fleetWs = null
            if (!pollFallbackTimer) {
                pollFallbackTimer = setInterval(fetchLiveDrivers, 30000)
            }
            scheduleWsReconnect()
        }
    }

    function scheduleWsReconnect() {
        clearTimeout(wsReconnectTimer)
        wsReconnectTimer = setTimeout(() => {
            connectFleetWs()
            wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000)
        }, wsReconnectDelay)
    }

    function disconnectFleetWs() {
        clearTimeout(wsReconnectTimer)
        clearInterval(pollFallbackTimer)
        if (fleetWs) {
            fleetWs.onclose = null
            fleetWs.close()
            fleetWs = null
        }
        wsConnected.value = false
    }

    async function fetchLiveDrivers() {
        fleetLoading.value = true
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/tracking/drivers'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) return
            const data = await res.json()
            liveDrivers.value = data.filter(d => d.latitude != null && d.longitude != null)
            if (liveDrivers.value.length > 0 && liveLocationsMap.value?.leafletObject) {
                liveLocationsMap.value.leafletObject.fitBounds(validPoints(liveDrivers.value.map(d => [d.latitude, d.longitude])), { padding: [40, 40], maxZoom: 13 })
            }
        } catch (e) { /* silent */ } finally {
            fleetLoading.value = false
        }
    }

    // Center map on first active driver, fallback to India center
    const fleetMapCenter = computed(() => {
        if (liveDrivers.value.length > 0) {
            const first = liveDrivers.value[0]
            return [first.latitude, first.longitude]
        }
        return [20.5937, 78.9629]
    })

    return {
        liveDrivers,
        fleetLoading,
        wsConnected,
        liveLocationsMap,
        liveDriverLocation,
        connectFleetWs,
        disconnectFleetWs,
        fetchLiveDrivers,
        fleetMapCenter,
    }
}
