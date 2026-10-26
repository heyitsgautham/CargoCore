// The arrival alert toggle: asks the backend to simulate the driver reaching the geofence,
// and remembers per order in localStorage that the alert is on.
import { ref, watch } from 'vue'
import { apiUrl } from '@/config/api'

export function useGeofenceAlert({ activeMove, authStore }) {
    const geofenceAlert = ref(false)
    const geofenceLoading = ref(false)
    const geofenceError = ref('')

    const GEOFENCE_KEY = 'geofence_alerts'

    function loadGeofenceState(orderId) {
        if (!orderId) return false
        try {
            const saved = JSON.parse(localStorage.getItem(GEOFENCE_KEY) || '{}')
            return !!saved[orderId]
        } catch { return false }
    }

    function saveGeofenceState(orderId, active) {
        if (!orderId) return
        try {
            const saved = JSON.parse(localStorage.getItem(GEOFENCE_KEY) || '{}')
            if (active) {
                saved[orderId] = true
            } else {
                delete saved[orderId]
            }
            localStorage.setItem(GEOFENCE_KEY, JSON.stringify(saved))
        } catch {}
    }

    // Restore persisted state whenever the active order changes
    watch(
        () => activeMove.value?.backendId || activeMove.value?.id,
        (orderId) => {
            geofenceAlert.value = loadGeofenceState(orderId)
            geofenceError.value = ''
        },
        { immediate: true }
    )

    async function toggleGeofence() {
        if (geofenceAlert.value) {
            geofenceAlert.value = false
            const orderId = activeMove.value?.backendId || activeMove.value?.id
            saveGeofenceState(orderId, false)
            return
        }

        const orderId = activeMove.value?.backendId || activeMove.value?.id
        if (!orderId) {
            geofenceAlert.value = true
            return
        }

        geofenceLoading.value = true
        geofenceError.value = ''
        try {
            const res = await fetch(apiUrl(`api/v1/orders/${orderId}/simulate-arrival`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            })
            if (res.ok) {
                geofenceAlert.value = true
                saveGeofenceState(orderId, true)
            } else {
                const data = await res.json().catch(() => ({}))
                geofenceError.value = data.detail || 'Could not simulate arrival'
                geofenceAlert.value = true
                saveGeofenceState(orderId, true)
            }
        } catch {
            geofenceAlert.value = true
            saveGeofenceState(orderId, true)
        } finally {
            geofenceLoading.value = false
        }
    }

    return { geofenceAlert, geofenceLoading, geofenceError, toggleGeofence }
}
