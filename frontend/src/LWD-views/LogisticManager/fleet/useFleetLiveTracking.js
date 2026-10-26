// The fleet page's live map: the shared live feed plus a readable location for each driver.
import { computed, ref } from 'vue'
import { useFleetLiveFeed } from '@/composables/useFleetLiveFeed'

export function useFleetLiveTracking(store) {
    const liveLocationsMap = ref(null)
    const feed = useFleetLiveFeed({ mapRef: liveLocationsMap })

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

    // Center map on first active driver, fallback to India center
    const fleetMapCenter = computed(() => {
        if (feed.liveDrivers.value.length > 0) {
            const first = feed.liveDrivers.value[0]
            return [first.latitude, first.longitude]
        }
        return [20.5937, 78.9629]
    })

    return { ...feed, liveLocationsMap, liveDriverLocation, fleetMapCenter }
}
