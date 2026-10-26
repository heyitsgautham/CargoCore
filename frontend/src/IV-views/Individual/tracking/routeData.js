// Route data for the customer tracking map: pins, geocoding, OSRM road routes and the
// cached warehouse, pickup and destination route bundle per order.
import L from 'leaflet'
import { apiUrl } from '@/config/api'

export const MAP_FIT_PADDING_TOP_LEFT = [72, 104]
export const MAP_FIT_PADDING_BOTTOM_RIGHT = [72, 132]
export const geocodeCache = new Map()
export const orderRouteCache = new Map()
export const routeResolvePromises = new Map()

// Custom map pin icons
export function makePinIcon(color, label) {
    return L.divIcon({
        html: `<div style="width:30px;height:30px;background:${color};border:3px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 2px 8px rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;"><span style="transform:rotate(45deg);color:white;font-size:12px;font-weight:900;line-height:1;">${label}</span></div>`,
        className: '',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -34]
    })
}
export const warehouseIcon = makePinIcon('#d97706', 'W')
export const pickupIcon = makePinIcon('#16a34a', 'A')
export const destIcon   = makePinIcon('#dc2626', 'B')
export const driverIcon = L.divIcon({
    html: `<div style="width:38px;height:38px;background:#2563eb;border:3px solid white;border-radius:50%;box-shadow:0 2px 12px rgba(37,99,235,0.55);display:flex;align-items:center;justify-content:center;"><svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='white'><path d='M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z'/></svg></div>`,
    className: '',
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -22]
})

// Geocode an address string → [lat, lng] using Nominatim
export async function geocodeAddress(address) {
    if (!address) return null

    const raw = String(address).trim()
    if (!raw) return null
    const cacheKey = raw.toLowerCase()

    if (geocodeCache.has(cacheKey)) {
        return geocodeCache.get(cacheKey)
    }

    try {
        const res = await fetch(apiUrl(`api/v1/geocoding/search?q=${encodeURIComponent(raw)}&limit=1`))
        if (res.ok) {
            const data = await res.json()
            if (Array.isArray(data) && data[0]) {
                const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
                geocodeCache.set(cacheKey, coords)
                return coords
            }
        }
    } catch {}

    const queries = raw.toLowerCase().includes('india') ? [raw] : [raw, `${raw}, India`]
    for (const query of queries) {
        try {
            const q = encodeURIComponent(query)
            const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=1`, {
                headers: { 'Accept-Language': 'en' }
            })
            const data = await res.json()
            if (data[0]) {
                const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
                geocodeCache.set(cacheKey, coords)
                return coords
            }
        } catch {}
    }

    return null
}

// Fetch full OSRM route geometry → [[lat,lng],...] for Leaflet polyline
export async function fetchRouteGeometry(lat1, lon1, lat2, lon2) {
    try {
        const url = `https://router.project-osrm.org/route/v1/driving/${lon1},${lat1};${lon2},${lat2}?overview=full&geometries=geojson`
        const controller = new AbortController()
        const timer = setTimeout(() => controller.abort(), 8000)
        const res = await fetch(url, { signal: controller.signal })
        clearTimeout(timer)
        if (!res.ok) return null
        const data = await res.json()
        if (data.code !== 'Ok' || !data.routes?.[0]) return null
        // OSRM returns [lon, lat] — swap to [lat, lon] for Leaflet
        return data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon])
    } catch {
        return null
    }
}

export function fallbackRouteGeometry(pickup, dest) {
    if (pickup && dest) {
        if (Math.abs(pickup[0] - dest[0]) < 0.000001 && Math.abs(pickup[1] - dest[1]) < 0.000001) {
            return [clonePoint(pickup)]
        }
        return [clonePoint(pickup), clonePoint(dest)]
    }
    if (pickup) return [clonePoint(pickup)]
    if (dest) return [clonePoint(dest)]
    return []
}

export function clonePoint(point) {
    return Array.isArray(point) ? [point[0], point[1]] : null
}

export function cloneCoords(coords) {
    return Array.isArray(coords) ? coords.map(clonePoint).filter(Boolean) : []
}

export function hasDetailedRoute(coords) {
    return Array.isArray(coords) && coords.length > 2
}

export function pointsMatch(start, end) {
    return Array.isArray(start)
        && Array.isArray(end)
        && Math.abs(start[0] - end[0]) < 0.000001
        && Math.abs(start[1] - end[1]) < 0.000001
}

export function pointFromValues(lat, lng) {
    if (lat === null || lat === undefined || lat === '' || lng === null || lng === undefined || lng === '') {
        return null
    }
    const safeLat = Number(lat)
    const safeLng = Number(lng)
    if (!Number.isFinite(safeLat) || !Number.isFinite(safeLng)) return null
    return [safeLat, safeLng]
}

export function mergeRouteSegments(...segments) {
    const merged = []

    for (const segment of segments) {
        for (const point of cloneCoords(segment)) {
            const previous = merged[merged.length - 1]
            if (!previous || !pointsMatch(previous, point)) {
                merged.push(point)
            }
        }
    }

    return merged
}

export function buildRouteBundle(data = {}) {
    const warehouse = clonePoint(data.warehouse)
    const pickup = clonePoint(data.pickup)
    const dest = clonePoint(data.dest)
    const warehouseToPickup = cloneCoords(data.warehouseToPickup)
    const pickupToDest = cloneCoords(data.pickupToDest)

    const normalizedWarehouseToPickup = warehouse && pickup
        ? (warehouseToPickup.length ? warehouseToPickup : fallbackRouteGeometry(warehouse, pickup))
        : []
    const normalizedPickupToDest = pickup && dest
        ? (pickupToDest.length ? pickupToDest : fallbackRouteGeometry(pickup, dest))
        : []

    return {
        warehouse,
        pickup,
        dest,
        warehouseToPickup: normalizedWarehouseToPickup,
        pickupToDest: normalizedPickupToDest,
        coords: mergeRouteSegments(normalizedWarehouseToPickup, normalizedPickupToDest),
    }
}

export function hasUsableSegment(start, end, coords, { requireGeometry = false } = {}) {
    if (!start || !end) return true
    if (!Array.isArray(coords) || coords.length === 0) return false
    return requireGeometry ? hasDetailedRoute(coords) || coords.length >= 2 : coords.length >= 2
}

export function hasUsableRouteData(data, { allowGeometry = false } = {}) {
    if (!data) return false

    const normalized = buildRouteBundle(data)
    if (!normalized.coords.length && !normalized.pickup && !normalized.dest && !normalized.warehouse) {
        return false
    }

    return hasUsableSegment(normalized.warehouse, normalized.pickup, normalized.warehouseToPickup, { requireGeometry: allowGeometry })
        && hasUsableSegment(normalized.pickup, normalized.dest, normalized.pickupToDest, { requireGeometry: allowGeometry })
}

export function getCachedRouteData(orderId) {
    const cached = orderRouteCache.get(String(orderId))
    if (!cached) return null

    return buildRouteBundle(cached)
}

export function setCachedRouteData(orderId, data) {
    orderRouteCache.set(String(orderId), buildRouteBundle(data))
}

export function haversineKm(start, end) {
    if (!start || !end) return 0
    const [lat1, lon1] = start
    const [lat2, lon2] = end
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function getRouteFocusSettings(coords) {
    if (!Array.isArray(coords) || coords.length < 2) {
        return { maxZoom: 12, duration: 0.8, padFactor: 0.35 }
    }

    const distanceKm = haversineKm(coords[0], coords[coords.length - 1])

    if (distanceKm <= 1.5) return { maxZoom: 10, duration: 0.78, padFactor: 1.15 }
    if (distanceKm <= 4) return { maxZoom: 11, duration: 0.82, padFactor: 0.9 }
    if (distanceKm <= 10) return { maxZoom: 11, duration: 0.88, padFactor: 0.65 }
    if (distanceKm <= 30) return { maxZoom: 10, duration: 0.96, padFactor: 0.45 }
    if (distanceKm <= 80) return { maxZoom: 9, duration: 1.05, padFactor: 0.28 }
    return { maxZoom: 8, duration: 1.12, padFactor: 0.18 }
}

export async function ensureRouteData(order, { allowGeometry = true } = {}) {
    const orderKey = order?.id ? String(order.id) : '__draft__'
    const pendingKey = `${orderKey}:${allowGeometry ? 'route' : 'pins'}`
    const cached = getCachedRouteData(orderKey)

    if (hasUsableRouteData(cached, { allowGeometry })) {
        return cached
    }

    if (routeResolvePromises.has(pendingKey)) {
        return routeResolvePromises.get(pendingKey)
    }

    const promise = (async () => {
        const warehouseCandidates = [
            pointFromValues(order?.warehouseLat, order?.warehouseLng),
            cached?.warehouse,
        ].filter(Boolean)
        let warehouse = warehouseCandidates[0] || null

        if (!warehouse) {
            const warehouseQueries = [
                order?.warehouseAddress,
                order?.warehouseName && order?.warehouseAddress ? `${order.warehouseName}, ${order.warehouseAddress}` : null,
                order?.warehouseName,
            ].filter(Boolean)

            for (const query of warehouseQueries) {
                warehouse = await geocodeAddress(query)
                if (warehouse) break
            }
        }

        const pickup = cached?.pickup || await geocodeAddress(order?.pickup)
        const dest = cached?.dest || await geocodeAddress(order?.destination)

        let warehouseToPickup = cached?.warehouseToPickup?.length
            ? cloneCoords(cached.warehouseToPickup)
            : fallbackRouteGeometry(warehouse, pickup)
        let pickupToDest = cached?.pickupToDest?.length
            ? cloneCoords(cached.pickupToDest)
            : fallbackRouteGeometry(pickup, dest)

        if (allowGeometry && warehouse && pickup && !hasDetailedRoute(warehouseToPickup)) {
            warehouseToPickup = await fetchRouteGeometry(warehouse[0], warehouse[1], pickup[0], pickup[1]) || warehouseToPickup
        }

        if (allowGeometry && pickup && dest && !hasDetailedRoute(pickupToDest)) {
            pickupToDest = await fetchRouteGeometry(pickup[0], pickup[1], dest[0], dest[1]) || pickupToDest
        }

        const resolved = buildRouteBundle({
            warehouse,
            pickup,
            dest,
            warehouseToPickup,
            pickupToDest,
        })

        setCachedRouteData(orderKey, resolved)
        return getCachedRouteData(orderKey)
    })()

    routeResolvePromises.set(pendingKey, promise)

    try {
        return await promise
    } finally {
        routeResolvePromises.delete(pendingKey)
    }
}

export function warmDisplayOrderMapData(orders = []) {
    const priorityOrders = orders.slice(0, 6)
    for (const order of priorityOrders) {
        ensureRouteData(order, { allowGeometry: true }).catch(() => {})
    }
}
