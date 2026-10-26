// Scoring and risk rules behind the Smart Assignment board. Pure functions of the order,
// the candidate driver or vehicle, and the current time.
import {
    isDirectDispatchAiCandidate,
    orderAllowsDirectVehicleSelection,
    priorityWeight,
    vehicleFitScore,
} from '../dispatchRules'

export function formatDeadline(value) {
    if (!value || value === '—') return 'Not scheduled'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return String(value)
    return parsed.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function hoursUntil(value, now = Date.now()) {
    if (!value || value === '—') return null
    const parsed = new Date(value).getTime()
    if (Number.isNaN(parsed)) return null
    return (parsed - now) / 3_600_000
}

/** Driver fit for an order: same hub, light load, fresh shift, efficiency, and priority. */
export function scoreDriver(driver, order) {
    let score = 40
    const orderWarehouseId = order.warehouseId ? String(order.warehouseId) : ''
    const driverHubId = driver.hubId ? String(driver.hubId) : ''
    const locationText = `${driver.location || ''} ${driver.currentJob || ''}`.toLowerCase()
    const warehouseText = `${order.warehouse || ''} ${order.hub || ''}`.toLowerCase().trim()

    if (orderWarehouseId && driverHubId && orderWarehouseId === driverHubId) score += 30
    if (warehouseText && locationText && locationText.includes(warehouseText.split(/\s+/)[0])) score += 12
    if ((driver.load || 0) === 0) score += 14
    else score += Math.max(0, 12 - Math.round((driver.load || 0) / 8))

    if ((driver.hours || 0) < 3) score += 10
    else if ((driver.hours || 0) < 6) score += 6
    else score -= 4

    if (driver.breakDue) score -= 18
    score += Math.min(12, Math.round((driver.efficiency || 0) / 8))

    if (priorityWeight(order.priority) >= 3) score += 4
    return score
}

export function scoreVehicle(vehicle, order) {
    return vehicleFitScore(vehicle, order) + (priorityWeight(order.priority) >= 3 ? 6 : 0)
}

export function buildDriverReasons(driver, order) {
    const reasons = []
    if (order.warehouseId && driver.hubId && String(order.warehouseId) === String(driver.hubId)) {
        reasons.push('same warehouse coverage')
    }
    if ((driver.activeOrders?.length || 0) === 0) reasons.push('no active order assigned')
    if ((driver.hours || 0) < 4) reasons.push('healthy shift time remaining')
    if ((driver.efficiency || 0) >= 70) reasons.push('strong recent dispatch efficiency')
    if (reasons.length === 0) reasons.push('best available dispatcher match')
    return reasons.slice(0, 3)
}

export function buildVehicleReasons(vehicle, order) {
    const reasons = []
    const vehicleType = String(vehicle?.type || '').trim().toLowerCase()
    const orderVehicleType = String(order?.vehicleType || '').trim().toLowerCase()
    if (vehicleType && orderVehicleType && vehicleType === orderVehicleType) reasons.push('matching vehicle type')
    if (vehicle?.cargoCapacityTons) reasons.push(`capacity ${vehicle.cargoCapacityTons}t available`)
    if (reasons.length === 0) reasons.push('best available vehicle fit')
    return reasons.slice(0, 2)
}

/** The highest-scoring driver for an order with the reasons to show, or null when none is free. */
export function topDriverMatch(order, driverPool) {
    if (!driverPool.length) return null
    const ranked = driverPool
        .map((driver) => ({ driver, score: scoreDriver(driver, order), reasons: buildDriverReasons(driver, order) }))
        .sort((a, b) => b.score - a.score)
    return ranked[0] || null
}

/** The best vehicle for a direct-dispatch order that has none, or null. */
export function topVehicleMatch(order, vehiclePool) {
    if (!orderAllowsDirectVehicleSelection(order) || order.vehicleId || !vehiclePool.length) return null
    const ranked = vehiclePool
        .map((vehicle) => ({ vehicle, score: scoreVehicle(vehicle, order), reasons: buildVehicleReasons(vehicle, order) }))
        .sort((a, b) => b.score - a.score)
    return ranked[0] || null
}

export function buildRisk(order, recommendation, vehicleRecommendation, now = Date.now()) {
    const deadlineHours = hoursUntil(order.deadline || order.eta, now)
    if (isDirectDispatchAiCandidate(order) && !order.readyForDispatch) {
        if (!vehicleRecommendation) {
            return { level: 'High', text: 'Accepted direct-dispatch order is waiting in dispatcher review, but no free vehicle is available yet.' }
        }
        if (!recommendation) {
            return { level: 'High', text: 'Accepted direct-dispatch order has a vehicle path, but no free driver is available yet.' }
        }
        return { level: 'Low', text: 'Accepted direct-dispatch order is ready for AI planning before warehouse release.' }
    }
    if (orderAllowsDirectVehicleSelection(order) && !order.vehicleId && !vehicleRecommendation) {
        return { level: 'High', text: 'Direct-dispatch order is ready, but no dispatcher-selectable vehicle is free right now.' }
    }
    if (!recommendation) {
        return {
            level: 'High',
            text: orderAllowsDirectVehicleSelection(order) && !order.vehicleId
                ? 'AI found a vehicle path, but no free driver is currently available for this direct-dispatch order.'
                : 'Vehicle assigned but no free driver is currently available for this released order.',
        }
    }
    if (deadlineHours !== null && deadlineHours <= 2) {
        return { level: 'High', text: 'Dispatch window is close. Confirm the driver quickly to avoid delay.' }
    }
    if (recommendation.driver.breakDue || (recommendation.driver.hours || 0) >= 8) {
        return { level: 'Medium', text: 'Recommended driver is nearing shift limit. Review before confirming.' }
    }
    if (priorityWeight(order.priority) >= 3) {
        return { level: 'Medium', text: 'Priority order. Confirm driver and release paperwork without delay.' }
    }
    return { level: 'Low', text: 'Ready for assignment with low operational risk.' }
}

export function orderHasAssignableResources(item) {
    if (!item?.recommendedDriver) return false
    if (item.vehicleId) return true
    return !!item.recommendedVehicle
}
