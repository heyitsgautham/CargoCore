// Dispatcher order status board: the allowed transitions, status labels and the
// mapping from store orders to table rows.

export const STATUS_TRANSITIONS = {
    dispatched: { backendStatus: 'ASSIGNED', label: 'Dispatched' },
    'in-transit': { backendStatus: 'IN_TRANSIT', label: 'In Transit' },
    delivered: { backendStatus: 'DELIVERED', label: 'Delivered' },
}

export function mapStatusToUI(backendStatus) {
    const statusMap = {
        'CONFIRMED': 'ready',
        'ASSIGNED': 'dispatched',
        'IN_TRANSIT': 'in-transit',
        'DELIVERED': 'delivered',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase().replace('_', '-') || 'ready'
}

export function mapStatusLabel(backendStatus) {
    const labelMap = {
        'CONFIRMED': 'Ready',
        'ASSIGNED': 'Dispatched',
        'IN_TRANSIT': 'In Transit',
        'DELIVERED': 'Delivered',
    }
    return labelMap[backendStatus] || backendStatus || 'Ready'
}

export function formatTimeOnly(value) {
    if (!value || value === '—') return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return String(value)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function toUiOrder(o) {
    const podTime = o.pod?.time || o.pod?.timestamp || (o.deliveredAt ? new Date(o.deliveredAt).toLocaleString() : null)
    return {
        id: o.trackingCode || o.id,
        backendId: o.backendId || o.id,
        status: mapStatusToUI(o.status),
        statusLabel: mapStatusLabel(o.status),
        driver: o.driver || null,
        driverId: o.driverId || null,
        vehicle: o.vehicle || null,
        vehicleId: o.vehicleId || null,
        eta: o.eta || null,
        etaOverdue: o.etaOverdue || false,
        slaStatus: o.slaStatus || 'Pending',
        slaClass: o.slaClass || 'bg-gray-500/20 text-gray-400',
        lastUpdatedRaw: o.lastUpdated || o.deliveredAt || o.createdAt || null,
        lastUpdated: formatTimeOnly(o.lastUpdated || o.deliveredAt || o.createdAt),
        customerName: o.customerName || null,
        customerPhone: o.customerPhone || null,
        createdAt: o.createdAt || null,
        deliveredAt: o.deliveredAt || null,
        deliveryAddr: o.deliveryAddr || '',
        pickupAddr: o.pickupAddr || '',
        deliveryNotes: o.deliveryNotes || null,
        escalated: o.escalated || false,
        escalationId: o.escalationId || null,
        escalationStatus: o.escalationStatus || null,
        pod: o.pod ? {
            ...o.pod,
            time: podTime || o.pod.time || 'Delivered',
            timestamp: o.pod.timestamp || podTime || 'Delivered',
        } : null,
    }
}
