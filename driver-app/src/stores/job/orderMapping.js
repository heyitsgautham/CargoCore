// Turn an assigned order from the API and the driver dashboard into the job the driver app runs.

export function mapOrderTypeToJobType(orderType) {
    const signal = String(orderType || '').toLowerCase()
    if (['house', 'shift', 'move', 'moving', 'relocation', 'furniture',
         'luggage', 'household', 'mixed'].some(token => signal.includes(token))) {
        return 'HOUSE_SHIFT'
    }
    if (['pickup', 'return', 'reverse', 'collection'].some(token => signal.includes(token))) {
        return 'PARCEL_PICKUP'
    }
    return 'PARCEL_DELIVERY'
}

export function mapOrderStatusToJobState(status, jobType = 'PARCEL_DELIVERY') {
    const upper = String(status || '').toUpperCase()
    const pickupStateMap = {
        'ASSIGNED': 'ASSIGNED',
        'CONFIRMED': 'ASSIGNED',
        'IN_TRANSIT': 'RETURN_TRANSIT',
        'DELIVERED': 'COMPLETED',
        'COMPLETED': 'COMPLETED',
        'CLOSED': 'COMPLETED',
    }
    const deliveryStateMap = {
        'ASSIGNED': 'ASSIGNED',
        'CONFIRMED': 'ASSIGNED',
        'IN_TRANSIT': 'IN_TRANSIT',
        'DELIVERED': 'COMPLETED',
        'COMPLETED': 'COMPLETED',
        'CLOSED': 'COMPLETED',
    }
    if (jobType === 'HOUSE_SHIFT') return deliveryStateMap[upper] || 'ASSIGNED'
    return (jobType === 'PARCEL_PICKUP' ? pickupStateMap : deliveryStateMap)[upper] || 'ASSIGNED'
}

export function estimateDuration(order, jobType) {
    if (jobType === 'HOUSE_SHIFT') return 6 * 60
    const itemCount = (order.items || []).reduce((sum, item) => sum + (item.quantity || 0), 0)
    return Math.max(45, 35 + itemCount * 8)
}

export function estimateDistance(order, dashboard, jobType) {
    if (dashboard?.manifest?.total_distance_km && jobType === dashboard?.current_job?.jobType) {
        return dashboard.manifest.total_distance_km
    }
    if (jobType === 'HOUSE_SHIFT') return 24
    return 8.5
}

export function normalizeCrewMembers(rawCrew = []) {
    return rawCrew.map(member => ({
        id: member.labourer_id || member.id,
        labourerId: member.labourer_id || member.id,
        name: member.name,
        role: member.role || 'Crew',
        photo: member.photo || null,
        checkedIn: Boolean(member.checked_in || member.checkedIn),
        checkInTime: member.check_in_time || member.checkInTime || null,
    }))
}

export function buildHouseShiftChecklist(crew = []) {
    return [
        { id: 'packing-1', phase: 'packing', task: 'Crew attendance confirmed', required: true, completed: crew.length > 0 && crew.every(member => member.checkedIn) },
        { id: 'packing-2', phase: 'packing', task: 'Customer inventory verified', required: true, completed: false },
        { id: 'loading-1', phase: 'loading', task: 'Heavy items secured', required: true, completed: false },
        { id: 'unloading-1', phase: 'unloading', task: 'Destination placement confirmed', required: true, completed: false },
        { id: 'final-1', phase: 'final', task: 'Customer walkthrough completed', required: true, completed: false },
    ]
}

export function parseOrderStops(order, jobType) {
    const items = Array.isArray(order.items) ? order.items : []
    const completed = ['DELIVERED', 'COMPLETED', 'CLOSED'].includes(String(order.status || '').toUpperCase())

    return [{
        id: order.id || order.tracking_code || 'stop-1',
        orderId: order.id || order.tracking_code || 'stop-1',
        trackingCode: order.tracking_code,
        sequence: 1,
        stopNumber: 1,
        type: jobType === 'PARCEL_PICKUP' ? 'pickup' : 'parcel',
        stopType: jobType === 'PARCEL_PICKUP' ? 'pickup' : 'delivery',
        address: jobType === 'PARCEL_PICKUP' ? (order.pickup_addr || '') : (order.delivery_addr || order.destination_addr || ''),
        lat: order.delivery_lat || order.destination_lat || order.dest_lat,
        lng: order.delivery_lng || order.destination_lng || order.dest_lng,
        location: {
            lat: order.delivery_lat || order.destination_lat || order.dest_lat || null,
            lng: order.delivery_lng || order.destination_lng || order.dest_lng || null,
        },
        backendStatus: order.status,
        status: completed ? 'completed' : 'pending',
        customerName: order.customer_name || `Order ${order.tracking_code || ''}`.trim(),
        customerPhone: order.customer_phone || '',
        phone: order.customer_phone || '',
        packages: items.map(item => ({
            id: item.id,
            barcode: item.sku,
            weight: `${item.quantity} unit`,
            description: item.sku,
        })),
        expectedItems: items.reduce((sum, item) => sum + (item.quantity || 0), 0),
        itemsScanned: [],
        serviceOtp: order.service_otp || null,
        timeWindow: order.scheduled_at
            ? {
                start: new Date(order.scheduled_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
                end: new Date(new Date(order.scheduled_at).getTime() + 45 * 60 * 1000).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
            }
            : { start: '--:--', end: '--:--' },
        cod: String(order.payment_mode || '').toUpperCase() === 'COD',
        codAmount: Math.max((order.total_amount || 0) - (order.paid_amount || 0), 0),
        paymentMode: order.payment_mode || null,
        paymentStatus: order.payment_status || null,
        specialInstructions: order.service_time_block || 'Follow dispatch instructions.',
    }]
}

// Cargo types that belong to the "Small Package / Parcel" booking mode.
// Everything else under INDIVIDUAL order_type is a house shift / goods move.
const SMALL_PACKAGE_CARGO_TYPES = new Set([
    'document', 'fragile item', 'soft item', 'hard item',
])

export function mapOrderToJob(order, dashboard) {
    const rawOrderType = String(order.order_type || '').toUpperCase()
    const rawCargoType = String(order.cargo_type || '').toLowerCase().trim()

    let jobType
    if (rawOrderType === 'SERVICE_MOVE') {
        // SERVICE_MOVE is always a goods move
        jobType = 'HOUSE_SHIFT'
    } else if (rawOrderType === 'INDIVIDUAL') {
        // For INDIVIDUAL orders the cargo_type tells us which booking mode was used:
        // Small Package mode uses: Document / Fragile Item / Soft Item / Hard Item
        // House Shift mode uses everything else (Household Goods, Furniture, Luggage/Boxes, etc.)
        jobType = SMALL_PACKAGE_CARGO_TYPES.has(rawCargoType) ? 'PARCEL_DELIVERY' : 'HOUSE_SHIFT'
    } else {
        jobType = mapOrderTypeToJobType([
            order.order_type,
            order.cargo_type,
            order.vehicle_type,
            order.service_time_block,
        ].filter(Boolean).join(' '))
    }
    const vehicleId = order.assigned_vehicle_code?.split(' · ')[0]
        || dashboard?.current_vehicle?.vehicleId
        || null
    const assignedAt = order.scheduled_at || order.created_at || new Date().toISOString()
    const currentState = mapOrderStatusToJobState(order.status, jobType)
    const routeDistance = estimateDistance(order, dashboard, jobType)
    const estimatedDuration = estimateDuration(order, jobType)
    const normalizedCrew = normalizeCrewMembers(dashboard?.crew || [])
    const items = Array.isArray(order.items) ? order.items : []

    if (jobType === 'HOUSE_SHIFT') {
        if (dashboard?.current_job?.jobType === 'HOUSE_SHIFT' && String(dashboard.current_job.jobId) === String(order.tracking_code)) {
            return dashboard.current_job
        }
        return {
            id: order.id || order.tracking_code,
            jobId: order.tracking_code,
            jobType,
            currentState,
            manifestId: dashboard?.manifest?.route_id || order.tracking_code,
            vehicleId,
            driverId: dashboard?.profile?.driverId || null,
            assignedAt,
            estimatedDuration,
            routeDistance,
            currentStopIndex: 0,
            crewRequired: order.labor_count || normalizedCrew.length || 0,
            crewAssigned: normalizedCrew,
            sourceLocation: {
                name: 'Source Address',
                customerName: order.customer_name || 'Pickup Location',
                customerPhone: order.customer_phone || '',
                address: order.pickup_addr || '',
                location: { lat: null, lng: null },
            },
            destinationLocation: {
                name: 'Destination Address',
                customerName: order.customer_name || 'Drop Location',
                customerPhone: order.customer_phone || '',
                address: order.delivery_addr || '',
                location: { lat: order.delivery_lat || null, lng: order.delivery_lng || null },
            },
            inventory: items.map(item => ({
                id: item.id,
                category: 'Inventory',
                item: item.sku,
                qty: item.quantity,
                loaded: false,
                unloaded: false,
                packed: false,
            })),
            equipment: [],
            checklist: buildHouseShiftChecklist(normalizedCrew),
            beforePhotos: [],
            afterPhotos: [],
            totalCost: order.total_amount || 0,
            advancePaid: order.paid_amount || 0,
            balanceDue: Math.max((order.total_amount || 0) - (order.paid_amount || 0), 0),
            stops: parseOrderStops(order, jobType),
        }
    }

    return {
        id: order.id || order.tracking_code,
        jobId: order.tracking_code,
        jobType,
        currentState,
        manifestId: dashboard?.manifest?.route_id || order.tracking_code,
        trackingCode: order.tracking_code,
        vehicleId,
        driverId: dashboard?.profile?.driverId || null,
        assignedAt,
        estimatedDuration,
        routeDistance,
        currentStopIndex: 0,
        customerName: order.customer_name || 'Customer',
        pickupAddr: order.pickup_addr || '',
        deliveryAddr: order.delivery_addr || order.destination_addr || '',
        weight: order.cargo_weight_kg || order.weight || order.total_weight || 0,
        volume: order.cargo_volume_m3 || order.volume || order.total_volume || 0,
        deadline: order.delivery_deadline || order.scheduled_at,
        stops: parseOrderStops(order, jobType),
        warehouseId: order.warehouse_id || null,
        warehouseLocation: {
            name: dashboard?.shift?.warehouse_name || 'Warehouse',
            address: dashboard?.shift?.warehouse_name || 'Warehouse',
        },
    }
}
