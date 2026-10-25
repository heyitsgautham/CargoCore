// The ETA coverage layer: how far each live driver reaches in 15 minutes and
// which pickup or unloading stop is nearest, from straight-line distance plus 25%.
import { getDriverSpeedKmph, haversineKm, toCoordinatePair } from './mapHelpers'

export const ETA_THRESHOLD_MINUTES = 15
const NO_STOPS_LABEL = 'No live pickup or unloading points'

function defaultRadiusMeters(speedKmph) {
    return Math.max(1500, Math.round((speedKmph * (ETA_THRESHOLD_MINUTES / 60)) * 1000))
}

export function emptyEtaCoverage(driver) {
    const speedKmph = getDriverSpeedKmph(driver)
    return {
        radiusMeters: defaultRadiusMeters(speedKmph),
        reachableCount: 0,
        nearestEtaMinutes: null,
        nearestLabel: NO_STOPS_LABEL,
        nearestKindLabel: 'stop',
        speedKmph,
        thresholdMinutes: ETA_THRESHOLD_MINUTES,
        loading: false,
    }
}

/** Coverage keyed by driver id for every driver with a live position. */
export function computeEtaCoverage(activeDrivers, targets) {
    const driversWithCoords = activeDrivers.filter((driver) => toCoordinatePair(driver.latitude, driver.longitude))
    const entries = driversWithCoords.map((driver) => {
        const driverKey = String(driver.driver_id)
        if (!targets.length) return [driverKey, emptyEtaCoverage(driver)]

        const speedKmph = getDriverSpeedKmph(driver)
        const baseRadius = defaultRadiusMeters(speedKmph)
        const analyses = targets
            .map((target) => {
                const linearKm = haversineKm(Number(driver.latitude), Number(driver.longitude), target.coords[0], target.coords[1])
                const estimatedRoadKm = linearKm * 1.25
                const etaMinutes = Math.max(1, Math.round((estimatedRoadKm / speedKmph) * 60))
                return { ...target, linearKm, estimatedRoadKm, etaMinutes }
            })
            .sort((a, b) => a.linearKm - b.linearKm)
            .slice(0, 12)

        const reachable = analyses.filter((target) => target.etaMinutes <= ETA_THRESHOLD_MINUTES)
        const nearest = analyses.slice().sort((a, b) => a.etaMinutes - b.etaMinutes)[0] || null
        const farthestReachableLinearMeters = reachable.length > 0
            ? Math.max(...reachable.map((target) => Math.round(target.linearKm * 1000)))
            : baseRadius

        return [driverKey, {
            radiusMeters: Math.max(baseRadius, farthestReachableLinearMeters),
            reachableCount: reachable.length,
            nearestEtaMinutes: nearest?.etaMinutes ?? null,
            nearestLabel: nearest?.label || NO_STOPS_LABEL,
            nearestKindLabel: nearest?.kind === 'pickup' ? 'pickup' : nearest?.kind === 'delivery' ? 'unloading' : 'stop',
            speedKmph,
            thresholdMinutes: ETA_THRESHOLD_MINUTES,
            loading: false,
        }]
    })
    return Object.fromEntries(entries)
}
