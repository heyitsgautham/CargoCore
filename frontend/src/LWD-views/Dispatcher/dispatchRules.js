// Dispatch rules shared by the dispatcher views: who and what is free, which orders the
// dispatcher may give a vehicle directly, and how recurring orders are recognised.

const ASSIGNABLE_DRIVER_STATUSES = ['active', 'idle', 'available', 'on-duty', 'online', 'on-route', 'standby', 'stand-by', 'on-break']
const DISPATCHABLE_VEHICLE_STATUSES = ['active', 'idle', 'available', 'standby', 'ready']
const CLOSED_ORDER_STATUSES = ['DELIVERED', 'COMPLETED', 'CANCELLED', 'CLOSED']
const DIRECT_DISPATCH_SUBSTATUSES = ['AWAITING_INBOUND', 'AWAITING_PICK', 'QC_PASSED', 'READY_FOR_DISPATCH', 'DISPATCHED']

/** "On Duty", "on_duty" and "ON-DUTY" all become "on-duty". */
export function normalizeAvailabilityStatus(status) {
    return String(status || '')
        .trim()
        .toLowerCase()
        .replace(/[_\s]+/g, '-')
}

export function isDriverAssignableStatus(status) {
    return ASSIGNABLE_DRIVER_STATUSES.includes(normalizeAvailabilityStatus(status))
}

export function isVehicleDispatchableStatus(status) {
    return DISPATCHABLE_VEHICLE_STATUSES.includes(normalizeAvailabilityStatus(status))
}

export function driverHasOpenAssignments(driver) {
    return (driver.activeOrders || []).some(
        (order) => !CLOSED_ORDER_STATUSES.includes(String(order?.status || '').toUpperCase()),
    )
}

export function vehicleHasOpenAssignments(vehicleId, activeOrders) {
    if (!vehicleId) return false
    return (activeOrders || []).some((order) => {
        const status = String(order?.status || '').toUpperCase()
        return String(order?.vehicleId || '') === String(vehicleId) && ['ASSIGNED', 'IN_TRANSIT'].includes(status)
    })
}

/**
 * VENDOR (hub-based recurring inbound), SERVICE_MOVE and PARCEL_PICKUP skip the warehouse
 * loading-dock vehicle step, so the dispatcher assigns their vehicle directly.
 */
export function orderAllowsDirectVehicleSelection(order) {
    const type = String(order?.type || '').toUpperCase()
    return type === 'PARCEL_PICKUP' || type === 'SERVICE_MOVE' || type === 'VENDOR'
}

/** The recurring rule an order came from, read from its RECURRING_RULE: delivery note. */
export function recurringRuleId(order) {
    const notes = String(order?.deliveryNotes || '')
    const match = notes.match(/RECURRING_RULE:([^|\n]+)/i)
    return match?.[1] || null
}

/** A direct-dispatch order with no driver or packing that the AI may plan before warehouse release. */
export function isDirectDispatchAiCandidate(order) {
    const substatus = String(order?.warehouseSubstatus || '').toUpperCase()
    return (
        orderAllowsDirectVehicleSelection(order) &&
        !order?.driverId &&
        Number(order?.packingAmount || 0) === 0 &&
        DIRECT_DISPATCH_SUBSTATUSES.includes(substatus)
    )
}

export function priorityWeight(priority) {
    const normalized = String(priority || '').toUpperCase()
    if (normalized === 'CRITICAL' || normalized === 'URGENT') return 4
    if (normalized === 'VIP') return 3
    if (normalized === 'HIGH') return 2
    if (normalized === 'MEDIUM') return 1
    return 0
}

/** Milliseconds for sorting, with missing or unreadable dates last. */
export function safeTimestamp(value) {
    if (!value || value === '—') return Number.MAX_SAFE_INTEGER
    const ts = new Date(value).getTime()
    return Number.isNaN(ts) ? Number.MAX_SAFE_INTEGER : ts
}

/** Keep only the earliest open occurrence of each recurring direct-dispatch rule. */
export function dedupeRecurringDirectCandidates(orders) {
    const byRule = new Map()
    const passthrough = []

    for (const order of orders) {
        const ruleId = isDirectDispatchAiCandidate(order) ? recurringRuleId(order) : null
        if (!ruleId) {
            passthrough.push(order)
            continue
        }
        const existing = byRule.get(ruleId)
        const orderTs = safeTimestamp(order.deadline || order.createdAt)
        const existingTs = existing ? safeTimestamp(existing.deadline || existing.createdAt) : Number.MAX_SAFE_INTEGER
        if (!existing || orderTs < existingTs) byRule.set(ruleId, order)
    }

    return [...passthrough, ...byRule.values()]
}

/** How well a vehicle suits an order by type and cargo capacity. Higher is better. */
export function vehicleFitScore(vehicle, order) {
    let score = 30
    const vehicleType = String(vehicle?.type || '').trim().toLowerCase()
    const orderVehicleType = String(order?.vehicleType || '').trim().toLowerCase()

    if (vehicleType && orderVehicleType && vehicleType === orderVehicleType) score += 35
    else if (!orderVehicleType) score += 10

    const orderWeightTons = Number(order?.weight || 0) / 1000
    const capacityTons = Number(vehicle?.cargoCapacityTons || 0)
    if (capacityTons > 0 && orderWeightTons > 0) {
        if (capacityTons >= orderWeightTons) score += 18
        else score -= 25
    }
    return score
}
