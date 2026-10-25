// Pickup and unloading coordinates for orders saved with only an address.
// Lookups go to the backend geocoder first and Nominatim second, once per order.
import { ref } from 'vue'
import { apiUrl } from '@/config/api'
import { getOrderDestinationLabel, getOrderPickupLabel, toCoordinatePair } from './mapHelpers'

export async function geocodeAddress(address) {
    const raw = String(address || '').trim()
    if (!raw) return null

    try {
        const response = await fetch(apiUrl(`api/v1/geocoding/search?q=${encodeURIComponent(raw)}&limit=1`))
        if (response.ok) {
            const data = await response.json()
            if (Array.isArray(data) && data[0]) {
                const coords = toCoordinatePair(data[0].lat, data[0].lon)
                if (coords) return coords
            }
        }
    } catch {
        // fall through to Nominatim
    }

    const queries = raw.toLowerCase().includes('india') ? [raw] : [raw, `${raw}, India`]
    for (const query of queries) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`, {
                headers: { 'Accept-Language': 'en' },
            })
            const data = await response.json()
            if (Array.isArray(data) && data[0]) {
                const coords = toCoordinatePair(data[0].lat, data[0].lon)
                if (coords) return coords
            }
        } catch {
            // try the next query
        }
    }

    return null
}

export function useOrderGeocoding() {
    const geocodedDestinations = ref({})
    const geocodedPickups = ref({})
    const pendingDestinations = new Set()
    const pendingPickups = new Set()

    function resolveDestination(order) {
        const directCoords = toCoordinatePair(order.deliveryLat, order.deliveryLng)
        if (directCoords) return directCoords
        const cachedCoords = geocodedDestinations.value[order.id]
        return Array.isArray(cachedCoords) ? cachedCoords : null
    }

    function resolvePickup(order) {
        const directCoords = toCoordinatePair(order.pickupLat, order.pickupLng)
        if (directCoords) return directCoords
        const cachedCoords = geocodedPickups.value[order.id]
        return Array.isArray(cachedCoords) ? cachedCoords : null
    }

    async function lookup(order, resolve, label, pending, cache) {
        if (!order?.id || resolve(order)) return
        if (!label || pending.has(order.id)) return
        pending.add(order.id)
        try {
            const coords = await geocodeAddress(label)
            if (coords) cache.value = { ...cache.value, [order.id]: coords }
        } finally {
            pending.delete(order.id)
        }
    }

    /** Start lookups for pickups without coordinates, and for assigned orders' unloading points. */
    function geocodeMissing(orders) {
        orders.forEach((order) => {
            if (!resolvePickup(order) && order.pickupAddr) {
                void lookup(order, resolvePickup, getOrderPickupLabel(order), pendingPickups, geocodedPickups)
            }
            if (order.driverId && !resolveDestination(order) && order.deliveryAddr) {
                void lookup(order, resolveDestination, getOrderDestinationLabel(order), pendingDestinations, geocodedDestinations)
            }
        })
    }

    return { resolveDestination, resolvePickup, geocodeMissing }
}
