// Pending dispatch queue rules: whether an order can be dispatched now, its labels,
// and how long until its deadline.

export function formatMetric(value, hasValue, unit) {
    return hasValue ? `${value} ${unit}` : '—'
}

export function formatOrderWeight(order) {
    return formatMetric(order?.weight, order?.hasWeight, 'kg')
}

export function formatOrderVolume(order) {
    return formatMetric(order?.volume, order?.hasVolume, 'm³')
}

export function formatCapacityValue(value, hasValue, capacity, unit) {
    return hasValue ? `${value} / ${capacity} ${unit}` : `— / ${capacity} ${unit}`
}

export function orderAllowsDirectVehicleSelection(order) {
    const type = String(order?.type || '').toUpperCase()
    // VENDOR (hub-based recurring inbound), SERVICE_MOVE, and PARCEL_PICKUP skip the
    // warehouse loading-dock vehicle assignment step — dispatcher assigns vehicle directly.
    return type === 'PARCEL_PICKUP' || type === 'SERVICE_MOVE' || type === 'VENDOR'
}

export function getPriorityClass(priority) {
    const map = {
        URGENT: 'bg-red-500/20 text-red-400 border-red-500/30',
        HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        NORMAL: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        LOW: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
    return map[priority] || map.NORMAL
}

export function isDeadlineCritical(deadline, now = new Date()) {
    if (!deadline) return false
    const diff = new Date(deadline) - now
    return diff < 3 * 60 * 60 * 1000
}

export function getTimeRemaining(deadline, now = new Date()) {
    if (!deadline) return '--'
    const diff = new Date(deadline) - now
    if (diff < 0) return 'OVERDUE'
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours}h ${mins}m remaining`
}

export function evaluateDispatchFeasibility(order, availableDrivers) {
    if (!order) return { feasibility: 'unchecked', failReason: '' }

    if (order.warehouseSubstatus === 'ON_HOLD' || order.status === 'ON_HOLD') {
        return { feasibility: 'infeasible', failReason: 'Warehouse hold' }
    }

    if (order.loadingInProgress || !order.readyForDispatch) {
        return { feasibility: 'unchecked', failReason: '' }
    }

    // Vendor/service-move orders: dispatcher assigns vehicle directly — no pre-assignment required
    if (!order.vehicleId && !orderAllowsDirectVehicleSelection(order)) {
        return { feasibility: 'infeasible', failReason: 'No vehicle' }
    }

    if (Number(order.weight || 0) > 2000) {
        return { feasibility: 'infeasible', failReason: 'Overweight' }
    }

    if (Number(order.volume || 0) > 12) {
        return { feasibility: 'infeasible', failReason: 'Over volume' }
    }

    if (availableDrivers === 0) {
        return { feasibility: 'infeasible', failReason: 'No driver' }
    }

    return { feasibility: 'feasible', failReason: '' }
}

export function deriveFeasibility(order, overrides = {}) {
    if (!order) return { feasibility: 'unchecked', failReason: '' }

    const manual = overrides[String(order.id)]
    if (manual?.feasibility) {
        return {
            feasibility: manual.feasibility,
            failReason: manual.failReason || '',
        }
    }

    if (order.warehouseSubstatus === 'ON_HOLD' || order.status === 'ON_HOLD') {
        return { feasibility: 'infeasible', failReason: 'Warehouse hold' }
    }

    if (order.feasibility && order.feasibility !== 'unchecked') {
        return { feasibility: order.feasibility, failReason: order.failReason || '' }
    }

    if (order.loadingInProgress || !order.readyForDispatch) {
        return { feasibility: 'unchecked', failReason: '' }
    }

    return { feasibility: 'unchecked', failReason: '' }
}
