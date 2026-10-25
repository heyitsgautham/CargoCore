/**
 * Turn customer order and quote payloads from the API into the shapes the customer screens render, including the transport timeline.
 */

import { buildPodData } from '@/utils/pod'

export function normalizeBackendStatus(status) {
    const value = String(status || '').toUpperCase()
    if (value === 'DRAFT' || value === 'CONFIRMED') return 'pending'
    if (value === 'ASSIGNED') return 'dispatched'
    if (value === 'IN_TRANSIT') return 'in-transit'
    if (value === 'DELIVERED' || value === 'CLOSED') return 'delivered'
    if (value === 'CANCELLED') return 'cancelled'
    return value.toLowerCase()
}

// Build transport log with warehouse operations
export function buildTransportLog(order, status, warehouseSubstatus) {
    const log = []
    const createdTime = order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'

    // Direct transport orders skip all warehouse steps — the driver goes straight
    // to the customer's location. Only treat as direct if there is truly no
    // warehouse assigned to the order.
    const hasWarehouse = !!(order.warehouse_id || order.warehouse_name || order.warehouse_address)
    const isDirectTransport = Number(order.packing_amount ?? 0) === 0 && !hasWarehouse

    // Order created
    log.push({ event: 'Order created', time: createdTime, icon: 'receipt_long', color: 'blue' })

    // Order confirmed
    if (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status)) {
        log.push({ event: 'Order confirmed', time: createdTime, icon: 'check_circle', color: 'green' })
    }

    if (isDirectTransport) {
        // ── Direct transport path: no warehouse steps ──────────────────────
        if (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status)) {
            log.push({
                event: 'Driver assigned',
                description: 'A driver has been assigned and will head directly to your pickup location.',
                time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Assigned',
                icon: 'person_pin_circle',
                color: 'blue'
            })
        }

        if (status === 'in-transit') {
            log.push({
                event: 'Driver en route to pickup',
                description: 'Your driver is on the way to collect your items.',
                time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'On the way',
                icon: 'local_shipping',
                color: 'green'
            })
        }
    } else {
        // ── Full warehouse path ────────────────────────────────────────────

        // Backfill: confirmed orders with no substatus still show as queued
        let ws = warehouseSubstatus
        if (!ws && (order.status === 'CONFIRMED' || ['dispatched', 'in-transit', 'delivered'].includes(status))) {
            ws = 'AWAITING_PICK'
        }

        // Queued / Awaiting Pick
        if (['AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Queued for Picking',
                description: "Orders that are queued up and ready, but no one has started picking them yet.",
                time: order.created_at ? new Date(order.created_at).toLocaleString() : 'Ready',
                icon: 'hourglass_empty',
                color: 'amber'
            })
        }

        // On Hold
        if (ws === 'ON_HOLD') {
            log.push({
                event: 'Order On Hold',
                description: "Orders that are blocked. Usually, this means they don't have enough labourers assigned to them yet.",
                time: new Date().toLocaleString(),
                icon: 'pause_circle',
                color: 'red'
            })
        }

        // Picking started
        if (['PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Picking started',
                description: "Orders currently being gathered by your staff from the warehouse shelves.",
                time: order.picking_started_at ? new Date(order.picking_started_at).toLocaleString() : 'In progress',
                icon: 'shopping_basket',
                color: 'blue'
            })
        }

        // Picking completed (Picked)
        if (['PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Picking completed',
                description: "Orders where all items are gathered and are waiting to be boxed.",
                time: order.picking_completed_at ? new Date(order.picking_completed_at).toLocaleString() : 'Completed',
                icon: 'inventory_2',
                color: 'cyan'
            })
        }

        // Packing started
        if (['PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Packing started',
                description: "Orders currently at a packing station, being boxed and prepped for dispatch.",
                time: order.packing_started_at ? new Date(order.packing_started_at).toLocaleString() : 'In progress',
                icon: 'package_2',
                color: 'amber'
            })
        }

        // Packing completed
        if (['PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Packing completed',
                time: order.packing_completed_at ? new Date(order.packing_completed_at).toLocaleString() : 'Completed',
                icon: 'deployed_code',
                color: 'green'
            })
        }

        // Quality check passed
        if (['QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Quality check passed',
                time: order.qc_passed_at ? new Date(order.qc_passed_at).toLocaleString() : 'Verified',
                icon: 'verified',
                color: 'green'
            })
        }

        // Ready for dispatch
        if (['READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED'].includes(ws) || status === 'dispatched' || status === 'in-transit') {
            log.push({
                event: 'Ready for dispatch',
                time: order.dispatch_ready_at ? new Date(order.dispatch_ready_at).toLocaleString() : 'Ready',
                icon: 'local_shipping',
                color: 'blue'
            })
        }

        // Dispatched from warehouse (truck left the dock, driver not yet assigned)
        if (['ON_DOCK', 'DISPATCHED'].includes(ws)) {
            log.push({
                event: 'Dispatched from warehouse',
                description: 'Your shipment has left the warehouse and is awaiting driver assignment.',
                time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Dispatched',
                icon: 'output',
                color: 'blue'
            })
        }

        // Driver assigned (dispatcher assigned a driver + vehicle)
        if (status === 'dispatched' || status === 'in-transit') {
            log.push({
                event: 'Driver assigned',
                description: 'A driver and vehicle have been assigned to your shipment.',
                time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'Assigned',
                icon: 'person_pin_circle',
                color: 'blue'
            })
        }

        // Shipment in transit (vehicle is on the road)
        if (status === 'in-transit') {
            log.push({
                event: 'Shipment in transit',
                description: 'Your shipment is on its way to the destination.',
                time: order.dispatched_at ? new Date(order.dispatched_at).toLocaleString() : 'On the way',
                icon: 'local_shipping',
                color: 'green'
            })
        }
    }

    // Delivered (same for both paths)
    if (status === 'delivered') {
        log.push({
            event: 'Delivery completed',
            time: order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Delivered',
            icon: 'where_to_vote',
            color: 'green'
        })
    }

    // Cancelled (same for both paths)
    if (status === 'cancelled') {
        const cancelReason = order.cancel_reason || 'Order was cancelled'
        log.push({
            event: 'Order Cancelled',
            description: cancelReason,
            time: order.updated_at ? new Date(order.updated_at).toLocaleString() : new Date().toLocaleString(),
            icon: 'cancel',
            color: 'red'
        })
    }

    return log
}

export function normalizeTrackingOrder(order) {
    const status = order.ui_status || normalizeBackendStatus(order.status)
    const warehouseSubstatus = order.warehouse_substatus || ''

    // Enrich order with warehouse timestamps for buildTransportLog
    const enriched = {
        ...order,
        picking_started_at: order.picking_started_at || null,
        picking_completed_at: order.picking_completed_at || null,
        packing_started_at: order.packing_started_at || null,
        packing_completed_at: order.packing_completed_at || null,
        qc_passed_at: order.qc_passed_at || null,
        dispatched_at: order.dispatched_at || null,
    }

    // Always rebuild transport log locally so warehouse steps always appear correctly.
    const transportLog = buildTransportLog(enriched, status, warehouseSubstatus)

    return {
        id: order.tracking_code || String(order.id),
        backendId: order.id,
        trackingCode: order.tracking_code,
        status,
        rawStatus: order.status,
        warehouseId: order.warehouse_id ? String(order.warehouse_id) : null,
        warehouseName: order.warehouse_name || null,
        warehouseAddress: order.warehouse_address || null,
        warehouseLat: order.warehouse_lat ?? null,
        warehouseLng: order.warehouse_lng ?? null,
        warehouseSubstatus,
        moveType: 'house-shift',
        cargoType: order.cargo_type || 'Household Goods',
        pickup: order.pickup_addr,
        destination: order.delivery_addr,
        date: order.scheduled_at ? new Date(order.scheduled_at).toLocaleDateString('en-CA') : new Date(order.created_at).toLocaleDateString('en-CA'),
        timeWindow: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
        laborCount: order.labor_count || 0,
        packingRequired: false,
        vehicleType: order.vehicle_type || 'assigned',
        materials: {},
        cost: {
            base: Number(order.base_amount || 0),
            labor: Number(order.labor_amount || 0),
            materials: Number(order.materials_amount || 0),
            packing: Number(order.packing_amount || 0),
            vehicle: Number(order.vehicle_amount || 0),
            platformFee: Number(order.platform_fee || 0),
            taxes: Number(order.tax_amount || 0),
            total: Number(order.total_amount || 0),
        },
        driver: order.assigned_driver_name || order.driver || null,
        customerName: order.customer_name || null,
        customerPhone: order.customer_phone || null,
        eta: order.eta_label || 'TBD',
        progress: order.progress ?? 0,
        paymentMode: order.payment_mode || 'Pending',
        paymentStatus: order.payment_status || (status === 'delivered' ? 'paid' : 'pending'),
        paidAmount: Number(order.paid_amount || 0),
        isDummyPayment: false,
        rating: null,
        feedback: '',
        customerRating: order.customer_rating ?? null,
        customerFeedback: order.customer_feedback ?? null,
        createdAt: order.created_at,
        deliveredAt: order.delivered_at || null,
        declaredValue: Number(order.declared_value || 0),
        serviceTimeBlock: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
        dwellTime: { loading: 0, unloading: 0, total: 0 },
        beforeAfterPhotos: {},
        crewCheckin: order.crew_checkin || null,
        transportLog,
        picking_started_at: enriched.picking_started_at,
        picking_completed_at: enriched.picking_completed_at,
        packing_started_at: enriched.packing_started_at,
        packing_completed_at: enriched.packing_completed_at,
        qc_passed_at: enriched.qc_passed_at,
        dispatched_at: enriched.dispatched_at,
        pod: status === 'delivered' ? buildPodData(order, {
            timestamp: order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Delivered',
            location: order.delivery_addr || '—',
            signedByFallback: 'Receiver',
        }) : null,
        cancellation: order.cancel_reason
            ? { reason: order.cancel_reason, fee: order.cancellation_fee || 0, date: order.updated_at || new Date().toISOString() }
            : null,
    }
}

export function mapQuote(quote) {
    return {
        id: quote.id,
        cargoType: quote.cargo_type,
        from: quote.from_location,
        to: quote.to_location,
        laborCount: quote.labor_count,
        packing: quote.packing,
        total: quote.total,
        date: quote.date,
        status: quote.status,
    }
}

export function fallbackPackingSku(name = '') {
    return String(name || '')
        .trim()
        .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
        .toUpperCase()
        .replace(/[^A-Z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 10)
}
