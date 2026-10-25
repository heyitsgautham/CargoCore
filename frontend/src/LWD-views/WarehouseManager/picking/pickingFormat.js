/**
 * Formatting, status and pick-quantity helpers for the warehouse Picking & Packing screen.
 */

// INDIVIDUAL (house-shift) orders require customers to select packing materials,
// so they need warehouse inventory stocked and a floor plan configured before picking.
// Small package / parcel orders (VENDOR etc.) are pre-packaged — no packing materials,
// no inventory tracking, no floor plan needed. Only a labourer is required for all types.
export function isHouseShift(wave) {
    return wave.laborRequired > 0
}

// Direct transport orders have packing_amount == 0, meaning the customer did NOT request
// packing services. The driver goes straight to the pickup location — no warehouse
// picking, packing, or loading dock processing is needed.
export function isDirectTransport(wave) {
    return wave.packingAmount === 0
}

export function isDirectTransportOrder(order) {
    return Number(order?.packing_amount ?? order?.packingAmount ?? 0) === 0
}

export function getPriorityIcon(priority) {
    const p = (priority || 'STANDARD').toUpperCase()
    if (p === 'EXPRESS' || p === 'URGENT') return '🔥'
    if (p === 'ECONOMY' || p === 'LOW') return '🐢'
    return '📦'
}

export function getPriorityBadgeClass(priority) {
    const p = (priority || 'STANDARD').toUpperCase()
    if (p === 'EXPRESS' || p === 'URGENT') return 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
    if (p === 'ECONOMY' || p === 'LOW') return 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30'
    return 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border border-gray-500/30'
}

export function isOverdue(deadline) {
    if (!deadline || deadline === 'N/A') return false
    try {
        const deadlineDate = new Date(deadline)
        return deadlineDate < new Date()
    } catch {
        return false
    }
}

export function formatCurrency(value) {
    if (!value) return '₹0'
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value)
}

export function formatDate(dateString) {
    if (!dateString) return 'N/A'
    try {
        return new Date(dateString).toLocaleDateString('en-IN', {
            month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
        })
    } catch {
        return 'N/A'
    }
}

export function formatLocation(item) {
    const parts = []
    if (item.zone) parts.push(item.zone)
    if (item.aisle) parts.push(`A${item.aisle}`)
    if (item.rack) parts.push(`R${item.rack}`)
    if (item.shelf) parts.push(`S${item.shelf}`)
    if (item.bin) parts.push(`B${item.bin}`)
    return parts.length > 0 ? parts.join('-') : 'Location TBD'
}

export function getStatusClass(status) {
    const map = {
        'ON_HOLD': 'bg-red-500/10 text-red-500 border-red-500/20',
        'AWAITING_PICK': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        'PICKING': 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        'PICKED': 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
        'PACKING': 'bg-green-500/10 text-green-500 border-green-500/20',
        'PACKED': 'bg-teal-500/10 text-teal-500 border-teal-500/20',
        'QC_PASSED': 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
        'READY_FOR_DISPATCH': 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        'ON_DOCK': 'bg-orange-500/10 text-orange-500 border-orange-500/20',
        'CONFIRMED': 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    }
    return map[status] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'
}

export function dedupeOrders(orders) {
    const seen = new Set()
    return orders.filter(order => {
        const key = order.id || order.tracking_code
        if (!key || seen.has(key)) return false
        seen.add(key)
        return true
    })
}

export function getActionLabel(wave) {
    if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') return 'Start Picking'
    if (wave.status === 'PICKING') return 'Complete Picking'
    if (wave.status === 'PICKED') return 'Start Packing'
    if (wave.status === 'PACKING') return 'Complete Packing'
    return ''
}

export function hasAction(wave) {
    return Boolean(getActionLabel(wave))
}

export function getPickItemKey(item) {
    return [item.sku, item.location_path || formatLocation(item), item.required_quantity || item.quantity_required || item.quantity || 0].join('::')
}

export function getItemRequiredQuantity(item) {
    return Number(item.quantity_required ?? item.required_quantity ?? item.quantity ?? 0) || 0
}

export function getItemPickedQuantity(item) {
    return Math.max(0, Number(item.quantity_picked ?? 0) || 0)
}

export function getItemRemainingQuantity(item) {
    return Math.max(0, getItemRequiredQuantity(item) - getItemPickedQuantity(item))
}

export function getPickActionLabel(item) {
    if (item.syncing) return 'Saving...'
    if (item.is_complete) return 'Picked'
    if (getItemPickedQuantity(item) > 0) return 'Mark Remaining Picked'
    return 'Mark Picked'
}

export function notifyOrdersUpdated() {
    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('warehouse-orders-updated'))
    }
}

export async function readResponseError(response, fallbackMessage) {
    try {
        const errorData = await response.json()
        return errorData.detail || errorData.message || fallbackMessage
    } catch {
        return fallbackMessage
    }
}
