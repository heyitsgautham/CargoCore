// Pure builders for what the dispatcher map draws, from the store's orders,
// hubs, drivers and live GPS positions. Coordinate lookups come in as functions
// so geocoded addresses can stand in for missing coordinates.
import { getDriverLocationLabel, getOrderDestinationLabel, isMapVisibleOrder, toCoordinatePair } from './mapHelpers'

const TERMINAL_ORDER_STATUSES = new Set(['DELIVERED', 'CLOSED', 'CANCELLED'])

/** Pending and active orders still on the road, active data winning for the same id. */
export function mergeLiveMapOrders(pendingLoads, activeOrders) {
    const merged = new Map()
    for (const order of pendingLoads) {
        if (isMapVisibleOrder(order)) merged.set(String(order.id), order)
    }
    for (const order of activeOrders) {
        if (isMapVisibleOrder(order)) merged.set(String(order.id), order)
        else merged.delete(String(order.id))
    }
    return [...merged.values()]
}

export function withDeliveryCoords(orders, resolveDestination) {
    return orders
        .map((order) => {
            const coords = resolveDestination(order)
            if (!coords) return null
            return { ...order, resolvedDeliveryLat: coords[0], resolvedDeliveryLng: coords[1] }
        })
        .filter(Boolean)
}

export function buildPickupLocations(orders, resolvePickup) {
    const locations = []
    for (const order of orders) {
        const pickupCoords = resolvePickup(order)
        if (!pickupCoords) continue
        locations.push({
            id: order.id,
            lat: pickupCoords[0],
            lng: pickupCoords[1],
            orderId: order.id,
            priority: order.priority,
            type: order.type,
            weight: order.weight,
            locationLabel: order.pickupAddr || order.hub || 'Customer Pickup',
        })
    }
    return locations
}

export function buildEtaTargets(orders, resolvePickup, resolveDestination) {
    const targets = []
    for (const order of orders) {
        const pickupCoords = resolvePickup(order)
        if (pickupCoords) {
            targets.push({ id: `pickup-${order.id}`, orderId: order.id, kind: 'pickup', label: `Pickup • Order #${order.id}`, coords: pickupCoords })
        }
        const destinationCoords = resolveDestination(order)
        if (destinationCoords) {
            targets.push({ id: `delivery-${order.id}`, orderId: order.id, kind: 'delivery', label: `Unloading • Order #${order.id}`, coords: destinationCoords })
        }
    }
    return targets
}

/** The most advanced order per driver: in transit beats assigned beats confirmed. */
export function buildDriverOrderContext(orders) {
    const rank = { IN_TRANSIT: 0, ASSIGNED: 1, CONFIRMED: 2 }
    const mapped = new Map()
    for (const order of orders) {
        if (!order.driverId) continue
        const driverId = String(order.driverId)
        const current = mapped.get(driverId)
        const nextRank = rank[String(order.status || '').toUpperCase()] ?? 99
        if (!current || nextRank < current.rank) {
            mapped.set(driverId, {
                rank: nextRank,
                orderId: order.id,
                status: order.status,
                label: order.deliveryAddr || order.pickupAddr || `Order #${order.id}`,
            })
        }
    }
    return mapped
}

export function buildDriverDeliveryMetrics(orders) {
    const metrics = new Map()
    for (const order of orders) {
        if (!order.driverId) continue
        const id = String(order.driverId)
        if (!metrics.has(id)) metrics.set(id, { delivered: 0, pending: 0 })
        const m = metrics.get(id)
        if (String(order.status || '').toUpperCase() === 'DELIVERED') m.delivered++
        else m.pending++
    }
    return metrics
}

export function buildDriverOrderRoutes(activeDrivers, orders, resolveDestination) {
    const routes = []
    for (const driver of activeDrivers) {
        const driverCoords = toCoordinatePair(driver.latitude, driver.longitude)
        if (!driverCoords) continue
        const driverOrders = orders.filter(o =>
            o.driverId && String(o.driverId) === String(driver.driver_id) &&
            !TERMINAL_ORDER_STATUSES.has(String(o.status || '').toUpperCase())
        )
        for (const order of driverOrders) {
            const destinationCoords = resolveDestination(order)
            if (!destinationCoords) continue
            routes.push({
                id: `route-${driver.driver_id}-${order.id}`,
                driverId: driver.driver_id,
                orderId: order.id,
                driverName: driver.driver_name || `Driver ${driver.driver_id}`,
                driverLocationLabel: getDriverLocationLabel(driver),
                destinationLabel: getOrderDestinationLabel(order),
                from: driverCoords,
                to: destinationCoords,
                status: order.status,
            })
        }
    }
    return routes
}

/** Drivers with an order that is not yet delivered, closed or cancelled. */
export function findBusyDriverIds(orders) {
    const ids = new Set()
    for (const order of orders) {
        const status = String(order?.status || '').toUpperCase()
        if (!order?.driverId || TERMINAL_ORDER_STATUSES.has(status)) continue
        ids.add(String(order.driverId))
    }
    return ids
}

export function driverBusyReason(driver, busyIds) {
    if (!driver) return ''
    if (driver.suspended) return 'Suspended'
    if (driver.maintenance) return 'Maintenance'
    if (busyIds.has(String(driver.id))) return 'Assigned'
    if (driver.statusColor === 'bg-gray-500') return 'Offline'
    return ''
}

export function isDriverAssignable(driver, busyIds) {
    if (!driver || !driver.id) return false
    if (driver.suspended || driver.maintenance) return false
    if (driver.statusColor === 'bg-gray-500') return false
    return !busyIds.has(String(driver.id))
}

/** Crises without coordinates are spread around the first hub on a golden-angle spiral. */
export function placeCrises(crises, hubs, center) {
    const fallback = center || [0, 0]
    return crises.map((c, i) => {
        if (c.lat && c.lng && !isNaN(c.lat) && !isNaN(c.lng)) return c
        const baseHub = hubs[0]
        const baseLat = baseHub ? baseHub.lat : fallback[0]
        const baseLng = baseHub ? baseHub.lng : fallback[1]
        const angle = (i * 137.508) * (Math.PI / 180)
        const dist = 0.03 + i * 0.02
        return { ...c, lat: baseLat + Math.sin(angle) * dist, lng: baseLng + Math.cos(angle) * dist }
    })
}

/**
 * Where the map opens: the dispatcher's hub, then the first pickup, the first
 * unloading point, a live driver, any hub, any zone. Never a hardcoded city.
 */
export function chooseMapCenter({ scopedHub, firstPickup, firstDestination, activeDrivers, hubs, zones }) {
    if (scopedHub) return [scopedHub.lat, scopedHub.lng]
    if (firstPickup) return [firstPickup.lat, firstPickup.lng]
    if (firstDestination) return [firstDestination.resolvedDeliveryLat, firstDestination.resolvedDeliveryLng]
    const driver = activeDrivers.find(d => d.latitude && d.longitude)
    if (driver) return [driver.latitude, driver.longitude]
    if (hubs.length > 0) return [hubs[0].lat, hubs[0].lng]
    if (zones.length > 0) return [zones[0].lat, zones[0].lng]
    return null
}

export function chooseMapZoom({ scopedHub, firstPickup, firstDestination, activeDrivers, hubs }) {
    if (scopedHub) return 13
    if (firstPickup || firstDestination) return 13
    if (hubs.length > 0) return 13
    if (activeDrivers.length > 0) return 12
    return 11
}
