import { ref } from 'vue'
import { apiUrl, API_BASE_URL } from '@/config/api'
import { validPoints } from '@/utils/mapBounds'

/**
 * Live driver positions for a fleet map.
 * A WebSocket on /ws/fleet pushes location updates and reconnects with backoff from
 * 2 to 30 seconds. While it is down, the REST tracking endpoint is polled every 30 seconds.
 * When `mapRef` points at a vue-leaflet map, a REST load fits the map to the drivers.
 */
export function useFleetLiveFeed({ mapRef = null } = {}) {
    const liveDrivers = ref([])
    const fleetLoading = ref(false)
    const wsConnected = ref(false)

    let fleetWs = null
    let wsReconnectTimer = null
    let wsReconnectDelay = 2000
    let pollFallbackTimer = null

    function buildWsUrl() {
        const token = localStorage.getItem('auth_token') || ''
        const wsBase = API_BASE_URL.replace(/^http/, 'ws')
        return `${wsBase}/ws/fleet?token=${encodeURIComponent(token)}`
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
            const leaflet = mapRef?.value?.leafletObject
            if (liveDrivers.value.length > 0 && leaflet) {
                leaflet.fitBounds(validPoints(liveDrivers.value.map(d => [d.latitude, d.longitude])), { padding: [40, 40], maxZoom: 13 })
            }
        } catch {
            // the next poll or socket update fills the map
        } finally {
            fleetLoading.value = false
        }
    }

    function scheduleWsReconnect() {
        clearTimeout(wsReconnectTimer)
        wsReconnectTimer = setTimeout(() => {
            connectFleetWs()
            wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000)
        }, wsReconnectDelay)
    }

    function connectFleetWs() {
        if (fleetWs && fleetWs.readyState <= WebSocket.OPEN) return
        try {
            fleetWs = new WebSocket(buildWsUrl())
        } catch {
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
            } catch {
                // ignore malformed frames
            }
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

    return { liveDrivers, fleetLoading, wsConnected, connectFleetWs, disconnectFleetWs, fetchLiveDrivers }
}
