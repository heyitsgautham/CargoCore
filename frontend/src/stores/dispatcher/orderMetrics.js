/**
 * Pure helpers for dispatcher views: driver badges, coordinates, cargo metrics and recurring order visibility.
 */

export function driverStatusColor(status) {
    if (!status) return 'bg-gray-500'
    const s = status.toLowerCase()
    if (s === 'active' || s === 'on route' || s === 'on_route') return 'bg-green-500'
    if (s === 'idle' || s === 'on break' || s === 'on_break') return 'bg-yellow-500'
    return 'bg-gray-500'
}

export function generateAvatar(name, id) {
    const seed = encodeURIComponent(name || id || 'driver')
    return `https://api.dicebear.com/7.x/initials/svg?seed=${seed}&backgroundColor=374151&textColor=ffffff`
}

export function parseCoordinate(value) {
    if (value === null || value === undefined || value === '') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
}

export function parseMetric(value) {
    if (value === null || value === undefined || value === '') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
}

export function roundMetric(value) {
    return value === null ? null : Math.round(value * 100) / 100
}

export function normalizeCargoMetric(value) {
    const rounded = roundMetric(value)
    return rounded !== null && rounded <= 0 ? null : rounded
}

export function resolveCargoWeight(order) {
    return normalizeCargoMetric(
        parseMetric(order.cargo_weight_kg ?? order.weight ?? order.total_weight)
    )
}

export function resolveCargoVolume(order) {
    const direct = parseMetric(order.cargo_volume_m3 ?? order.volume ?? order.total_volume)
    if (direct !== null) return normalizeCargoMetric(direct)

    const items = Array.isArray(order.items) ? order.items : []
    const estimatedVolume = items.reduce((sum, item) => sum + Number(item?.estimated_volume || 0), 0)
    return estimatedVolume > 0 ? normalizeCargoMetric(estimatedVolume) : null
}

export function isRecurringOrder(order) {
    const notes = String(order?.delivery_notes || order?.deliveryNotes || '')
    return notes.includes('RECURRING_RULE:') && notes.includes('|RUN:')
}

export function isDispatcherVisiblePendingOrder(order) {
    if (!isRecurringOrder(order)) return true
    if (!order?.scheduled_at) return true

    const scheduledAt = new Date(order.scheduled_at)
    if (Number.isNaN(scheduledAt.getTime())) return true

    // Match the vendor/customer recurring visibility rule so dispatcher does
    // not see future recurring runs earlier than the other operational views.
    const cutoff = new Date()
    cutoff.setUTCHours(0, 0, 0, 0)
    cutoff.setUTCDate(cutoff.getUTCDate() + 1)
    const scheduledDate = new Date(scheduledAt)
    scheduledDate.setUTCHours(0, 0, 0, 0)

    return scheduledDate <= cutoff
}
