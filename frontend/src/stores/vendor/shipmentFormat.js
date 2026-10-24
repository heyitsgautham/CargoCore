/**
 * Pure helpers that turn vendor shipment payloads into status keys, labels and dates.
 */

export function parseStatusKey(status) {
    const value = String(status || '').toLowerCase()
    if (['warehouse', 'awaiting_pick', 'picking', 'picked', 'packing', 'packed', 'qc_passed'].includes(value)) return 'warehouse'
    if (value.includes('transit') || value === 'assigned') return 'transit'
    if (value === 'delivered' || value === 'closed') return 'delivered'
    if (value === 'cancelled') return 'cancelled'
    if (value === 'out_for_delivery') return 'delivery'
    return 'pending'
}

export function formatStatusLabel(statusKey) {
    return {
        pending: 'Pending',
        warehouse: 'In Warehouse',
        transit: 'In Transit',
        delivery: 'Out for Delivery',
        delivered: 'Delivered',
        cancelled: 'Cancelled',
    }[statusKey] || 'Pending'
}

export function statusProgress(statusKey) {
    return { pending: 15, warehouse: 35, transit: 65, delivery: 85, delivered: 100, cancelled: 0 }[statusKey] || 0
}

export function safeDateLabel(value, fallback = 'TBD') {
    if (!value) return fallback
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime())
        ? String(value)
        : parsed.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

export function safeDateTimeLabel(value, fallback = 'TBD') {
    if (!value) return fallback
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime())
        ? String(value)
        : parsed.toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
}

export function routeSummary(pickup, delivery) {
    return `${pickup || 'Origin'} → ${delivery || 'Destination'}`
}

export function isRecurringShipment(raw) {
    const notes = String(raw.delivery_notes || '')
    return Boolean(
        raw.recurring_rule_id ||
        raw.is_recurring ||
        (notes.includes('RECURRING_RULE:') && notes.includes('|RUN:'))
    )
}
