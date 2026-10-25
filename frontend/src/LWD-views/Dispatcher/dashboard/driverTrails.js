// Recent GPS trails per driver, kept in localStorage for six hours so the
// route history layer survives a page reload.
import { hasValidCoordinate, haversineKm, toCoordinatePair } from './mapHelpers'

export const DRIVER_TRAIL_STORAGE_KEY = 'dispatcher-driver-route-history-v1'
export const DRIVER_TRAIL_RETENTION_MS = 6 * 60 * 60 * 1000
const DRIVER_TRAIL_MIN_SAMPLE_GAP_MS = 45 * 1000
const DRIVER_TRAIL_MIN_MOVE_KM = 0.08
export const DRIVER_TRAIL_MAX_POINTS = 120

/** Drop samples that are invalid or older than the retention window, and keep the newest points. */
export function pruneDriverTrailHistory(history, now = Date.now()) {
    const nextHistory = {}

    for (const [driverId, samples] of Object.entries(history || {})) {
        const cleaned = Array.isArray(samples)
            ? samples
                .filter((sample) =>
                    hasValidCoordinate(sample?.lat) &&
                    hasValidCoordinate(sample?.lng) &&
                    sample?.ts &&
                    now - Number(sample.ts) <= DRIVER_TRAIL_RETENTION_MS
                )
                .slice(-DRIVER_TRAIL_MAX_POINTS)
            : []

        if (cleaned.length > 0) {
            nextHistory[driverId] = cleaned
        }
    }

    return nextHistory
}

export function loadDriverTrailHistory() {
    if (typeof window === 'undefined') return {}
    try {
        const raw = window.localStorage.getItem(DRIVER_TRAIL_STORAGE_KEY)
        if (!raw) return {}
        return pruneDriverTrailHistory(JSON.parse(raw))
    } catch {
        return {}
    }
}

export function saveDriverTrailHistory(history) {
    if (typeof window === 'undefined') return
    try {
        window.localStorage.setItem(DRIVER_TRAIL_STORAGE_KEY, JSON.stringify(pruneDriverTrailHistory(history)))
    } catch {
        // storage full or blocked: the trail simply stays in memory
    }
}

/**
 * Add each driver's current position to their trail.
 * A new point starts when the order or status changes, the driver moved 80 m,
 * or 45 seconds passed; otherwise the last point is updated in place.
 */
export function extendDriverTrails(history, activeDrivers, orderContextByDriver, now = Date.now()) {
    const nextHistory = pruneDriverTrailHistory(history, now)

    for (const driver of activeDrivers) {
        const coords = toCoordinatePair(driver.latitude, driver.longitude)
        if (!coords) continue

        const driverId = String(driver.driver_id)
        const existing = nextHistory[driverId] ? [...nextHistory[driverId]] : []
        const lastSample = existing[existing.length - 1] || null
        const orderContext = orderContextByDriver.get(driverId) || null
        const nextSample = {
            lat: coords[0],
            lng: coords[1],
            ts: now,
            orderId: orderContext?.orderId || null,
            orderStatus: orderContext?.status || null,
            orderLabel: orderContext?.label || 'Recent route trail',
        }

        if (!lastSample) {
            existing.push(nextSample)
        } else {
            const movedKm = haversineKm(lastSample.lat, lastSample.lng, nextSample.lat, nextSample.lng)
            const elapsedMs = nextSample.ts - Number(lastSample.ts || 0)
            const sameOrder = String(lastSample.orderId || '') === String(nextSample.orderId || '')
            const sameStatus = String(lastSample.orderStatus || '') === String(nextSample.orderStatus || '')

            if (!sameOrder || !sameStatus || movedKm >= DRIVER_TRAIL_MIN_MOVE_KM || elapsedMs >= DRIVER_TRAIL_MIN_SAMPLE_GAP_MS) {
                existing.push(nextSample)
            } else {
                existing[existing.length - 1] = { ...lastSample, ...nextSample }
            }
        }

        nextHistory[driverId] = existing.slice(-DRIVER_TRAIL_MAX_POINTS)
    }

    return nextHistory
}

/** Polylines for the route history layer, one per active driver with two or more points. */
export function buildRouteHistoryTrails(history, activeDrivers) {
    const activeDriverMap = new Map(activeDrivers.map((driver) => [String(driver.driver_id), driver]))

    return Object.entries(history)
        .map(([driverId, samples]) => {
            const activeDriver = activeDriverMap.get(driverId)
            if (!activeDriver || !Array.isArray(samples) || samples.length < 2) return null

            const points = samples
                .map((sample) => toCoordinatePair(sample.lat, sample.lng))
                .filter(Boolean)

            if (points.length < 2) return null

            const lastSample = samples[samples.length - 1]
            const lastUpdated = lastSample?.ts ? new Date(lastSample.ts) : null

            return {
                driverId,
                driverName: activeDriver.driver_name || `Driver ${driverId}`,
                points,
                pointCount: points.length,
                orderId: lastSample?.orderId || null,
                orderStatus: lastSample?.orderStatus || null,
                orderLabel: lastSample?.orderLabel || 'Recent route trail',
                lastUpdatedLabel: lastUpdated && !Number.isNaN(lastUpdated.getTime())
                    ? lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
                    : 'Unknown',
            }
        })
        .filter(Boolean)
}
