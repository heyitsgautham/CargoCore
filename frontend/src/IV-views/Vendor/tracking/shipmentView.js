// Pure helpers behind the vendor tracking list and the selected shipment's detail view.
import { formatLogDate, formatLogTime } from './trackingFormat'

const STATUS_ICONS = {
    'Order Placed': 'shopping_cart',
    'Confirmed': 'verified',
    'In Warehouse': 'warehouse',
    'Awaiting Pick': 'inventory_2',
    'Picking': 'forklift',
    'Picked': 'check_circle',
    'Packing': 'inventory',
    'Packed': 'deployed_code',
    'QC Passed': 'fact_check',
    'In Transit': 'local_shipping',
    'Out for Delivery': 'two_wheeler',
    'Delivered': 'done_all',
    'Cancelled': 'cancel',
}

/** The Material icon for a status label, matched on the first known status it contains. */
export function statusIcon(label) {
    for (const [key, icon] of Object.entries(STATUS_ICONS)) {
        if (label && label.toLowerCase().includes(key.toLowerCase())) return icon
    }
    return 'radio_button_checked'
}

/** The transit log, newest step first, or one entry for the current status when there is no history. */
export function buildTrackingLogs(shipment, now = new Date()) {
    if (!shipment) return []
    const history = shipment.statusHistory || []
    if (history.length > 0) {
        return history.slice().reverse().map((step, idx) => ({
            action: step.status,
            location: idx === 0
                ? (shipment.statusKey === 'delivered' ? shipment.destination : shipment.route || '—')
                : shipment.origin,
            date: formatLogDate(step.time),
            time: formatLogTime(step.time),
            icon: statusIcon(step.status),
            isCurrent: idx === 0,
        }))
    }
    return [{
        action: shipment.status,
        location: shipment.route || '—',
        date: 'Today',
        time: now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        icon: statusIcon(shipment.status),
        isCurrent: true,
    }]
}

/** Label, colours and map wording for a shipment that is delivered, cancelled or on the road. */
export function shipmentPhase(shipment) {
    const statusKey = shipment?.statusKey
    if (statusKey === 'delivered') {
        return {
            etaLabel: 'Delivered',
            etaClass: 'text-green-600 dark:text-green-400',
            driver: { label: 'Trip Completed', dotClass: 'bg-green-500', textClass: 'text-green-500' },
            mapLabel: 'Delivered',
        }
    }
    if (statusKey === 'cancelled') {
        return {
            etaLabel: 'Cancelled',
            etaClass: 'text-red-600 dark:text-red-400',
            driver: { label: 'Assignment Closed', dotClass: 'bg-red-500', textClass: 'text-red-500' },
            mapLabel: 'Cancelled',
        }
    }
    return {
        etaLabel: shipment?.eta || 'TBD',
        etaClass: 'text-blue-600 dark:text-blue-400',
        driver: { label: 'Active · On Route', dotClass: 'bg-green-500 animate-pulse', textClass: 'text-green-500' },
        mapLabel: 'In Transit',
    }
}

/** Live coordinates of the shipment's driver, or null when the trip is over or has no fix. */
export function liveDriverPosition(shipment) {
    if (!shipment || ['delivered', 'cancelled'].includes(shipment.statusKey)) return null
    const lat = Number(shipment.driverLat)
    const lng = Number(shipment.driverLng)
    return Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : null
}

export function filterShipments(shipments, statusFilter, query) {
    let list = shipments
    if (statusFilter !== 'all') list = list.filter(s => s.statusKey === statusFilter)
    if (query.trim()) {
        const q = query.toLowerCase()
        list = list.filter(s => s.id.toLowerCase().includes(q) || s.destination.toLowerCase().includes(q) || s.route.toLowerCase().includes(q))
    }
    return list
}

/** The three busiest origin to destination routes with their delivered share. */
export function topRoutes(shipments) {
    const map = {}
    shipments.forEach(s => {
        if (s.origin && s.destination) {
            const key = `${s.origin} → ${s.destination}`
            if (!map[key]) map[key] = { route: key, count: 0, delivered: 0 }
            map[key].count++
            if (s.statusKey === 'delivered') map[key].delivered++
        }
    })
    return Object.values(map)
        .sort((a, b) => b.count - a.count)
        .slice(0, 3)
        .map((r, i) => ({
            ...r,
            rank: String(i + 1).padStart(2, '0'),
            onTime: r.count > 0 ? Math.round((r.delivered / r.count) * 100) : 0,
        }))
}

export const statusClass = k => ({
    pending: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    warehouse: 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
    transit: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    delivery: 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
    delivered: 'bg-green-500/20 text-green-600 dark:text-green-400',
    cancelled: 'bg-red-500/20 text-red-600 dark:text-red-400',
}[k] || 'bg-gray-500/20 text-gray-500')

export const severityClass = sev => ({
    Low: 'border-yellow-500 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
    Medium: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400',
    High: 'border-red-500 bg-red-500/10 text-red-600 dark:text-red-400',
}[sev])

/**
 * Slips the vendor can open for a shipment: the booking confirmation always,
 * and proof of delivery and the final tax invoice once it is delivered.
 */
export function shipmentDocuments(shipment, slips) {
    if (!shipment) return []
    // Tailwind only generates classes it finds written out, so each colour set is spelled in full.
    const doc = (key, description, classes) => ({
        key,
        label: slips.labels[key],
        description,
        icon: slips.icons[key],
        ...classes,
        action: () => slips.open(key),
    })
    const docs = [doc('bookingConfirmation', 'Booking summary and shipment details', {
        iconClass: 'text-indigo-500',
        hoverClass: 'hover:border-indigo-300 dark:hover:border-indigo-500/30',
        downloadClass: 'group-hover:text-indigo-500',
    })]
    if (shipment.statusKey === 'delivered') {
        const photos = shipment.pod?.photoCount
        docs.push(
            doc('proofOfDelivery', photos ? `${photos} proof file${photos === 1 ? '' : 's'} recorded` : 'Delivery confirmation slip', {
                iconClass: 'text-green-500',
                hoverClass: 'hover:border-green-300 dark:hover:border-green-500/30',
                downloadClass: 'group-hover:text-green-500',
            }),
            doc('finalTaxInvoice', 'Final billing document for this shipment', {
                iconClass: 'text-blue-500',
                hoverClass: 'hover:border-blue-300 dark:hover:border-blue-500/30',
                downloadClass: 'group-hover:text-blue-500',
            }),
        )
    }
    return docs
}
