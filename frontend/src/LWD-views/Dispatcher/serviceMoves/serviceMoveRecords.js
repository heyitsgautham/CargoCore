// Rules and mapping for the dispatcher's service moves: who and what can be assigned,
// the metadata packed into delivery notes, and backend orders as move cards.

export function formatVehicleLabel(vehicle) {
    const parts = [vehicle.code, vehicle.type, vehicle.licensePlate].filter(Boolean)
    return parts.length > 0 ? parts.join(' · ') : `Vehicle ${vehicle.id}`
}

export function normalizeAvailabilityStatus(status) {
    return String(status || '')
        .trim()
        .toLowerCase()
        .replace(/[_\s]+/g, '-')
}

export function isDriverAssignableStatus(status) {
    const normalized = normalizeAvailabilityStatus(status)
    return ['active', 'idle', 'available', 'on-duty', 'online', 'on-route', 'standby', 'stand-by'].includes(normalized)
}

export function isVehicleAssignableStatus(status) {
    const normalized = normalizeAvailabilityStatus(status)
    return !['in-use', 'maintenance', 'in-shop', 'out-of-service', 'offline'].includes(normalized)
}

export function hasOpenAssignments(driver) {
    return (driver.activeOrders || []).some((order) => {
        const status = String(order?.status || '').toUpperCase()
        return !['DELIVERED', 'COMPLETED', 'CANCELLED', 'CLOSED'].includes(status)
    })
}

export function parseApiError(payload, fallback) {
    if (Array.isArray(payload?.detail)) return payload.detail[0]?.msg || fallback
    return payload?.detail || fallback
}

export function parseServiceMoveMeta(raw) {
    if (!raw) return { title: '', notes: '' }
    if (!raw.startsWith('SERVICE_MOVE_META::')) return { title: '', notes: raw }

    try {
        const parsed = JSON.parse(raw.slice('SERVICE_MOVE_META::'.length))
        return {
            title: parsed?.title || '',
            notes: parsed?.notes || '',
        }
    } catch (_) {
        return { title: '', notes: raw }
    }
}

export function deriveDurationLabel(serviceTimeBlock) {
    const match = String(serviceTimeBlock || '').match(/(\d+(?:\.\d+)?)h block/i)
    if (match) return `${match[1]} hours`
    return '4 hours'
}

/** A backend service order as a move card, with its crew, vehicle, progress and status badge. */
export function mapServiceMove(order, drivers, vehicles) {
    const iconMap = {
        'House Shift': 'home',
        'Office Shift': 'domain',
        'Warehouse Transfer': 'warehouse',
        'Warehouse Supply Pickup': 'inventory_2',
        'Equipment Transfer': 'construction',
        'Manual Service': 'handyman',
        'service_move': 'local_shipping',
    }
    const colorMap = {
        'House Shift': 'blue',
        'Office Shift': 'purple',
        'Warehouse Transfer': 'green',
        'Warehouse Supply Pickup': 'amber',
        'Equipment Transfer': 'cyan',
        'Manual Service': 'rose',
        'service_move': 'blue',
    }

    const moveType = order.cargo_type || order.order_type || 'service_move'
    const c = colorMap[moveType] || 'blue'
    const moveMeta = parseServiceMoveMeta(order.delivery_notes)

    // Get driver and crew info
    const driver = drivers.find(d => d.id === String(order.assigned_driver_id))
    const crew = driver ? [{ name: driver.name, role: 'Driver', driverId: String(order.assigned_driver_id) }] : []

    // Get vehicle info — prefer order-linked vehicle, then fall back to the driver's own vehicle
    const vehicle = order.assigned_vehicle_id
        ? vehicles.find(v => String(v.id) === String(order.assigned_vehicle_id))
        : null
    // If no vehicle on the order, look up the driver's vehicle from the vehicles list
    const driverVehicleRecord = !vehicle && driver
        ? vehicles.find(v =>
            (v.code && v.code === driver.vehicle) ||
            (v.licensePlate && v.licensePlate === driver.vehicle) ||
            (v.license_plate && v.license_plate === driver.vehicle)
          )
        : null
    const resolvedVehicleRecord = vehicle || driverVehicleRecord
    const vehicleCode =
        order.assigned_vehicle_code ||
        resolvedVehicleRecord?.licensePlate ||
        resolvedVehicleRecord?.license_plate ||
        resolvedVehicleRecord?.code ||
        resolvedVehicleRecord?.model ||
        driver?.vehicle ||
        (order.assigned_vehicle_id ? `Vehicle ${String(order.assigned_vehicle_id).slice(0, 6)}` : '—')

    // Calculate progress based on status
    let progress = 0
    if (order.status === 'ASSIGNED') progress = 10
    else if (order.status === 'IN_TRANSIT') progress = 50
    else if (order.status === 'DELIVERED') progress = 100

    const statusMap = {
        'CONFIRMED': { label: 'Scheduled', class: 'bg-yellow-500/20 text-yellow-400' },
        'ASSIGNED': { label: 'Assigned', class: 'bg-blue-500/20 text-blue-400' },
        'IN_TRANSIT': { label: 'In Progress', class: 'bg-green-500/20 text-green-400' },
        'DELIVERED': { label: 'Completed', class: 'bg-gray-500/20 text-gray-400' }
    }

    const statusInfo = statusMap[order.status] || { label: order.status, class: 'bg-gray-500/20 text-gray-400' }

    return {
        id: order.tracking_code || order.id,
        orderId: order.id,
        title: moveMeta.title || `${moveType} · ${order.tracking_code || String(order.id).slice(0, 8)}`,
        type: moveType,
        icon: iconMap[moveType] || 'local_shipping',
        iconClass: `text-${c}-400`,
        headerBg: `bg-${c}-500/5`,
        status: statusInfo.label,
        statusClass: statusInfo.class,
        pickup: order.pickup_addr || 'Not specified',
        pickupLat: order.pickup_lat ?? null,
        pickupLng: order.pickup_lng ?? null,
        delivery: order.delivery_addr || 'Not specified',
        deliveryLat: order.delivery_lat ?? null,
        deliveryLng: order.delivery_lng ?? null,
        timeBlock: order.service_time_block || (
            order.scheduled_at
                ? new Date(order.scheduled_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
                : 'Not scheduled'
        ),
        duration: deriveDurationLabel(order.service_time_block),
        packingTime: '1h',
        dwellTime: '0.5h',
        transitTime: '2.5h',
        progress,
        vehicle: vehicleCode,
        seatsAvailable: resolvedVehicleRecord?.seatCapacity ?? resolvedVehicleRecord?.seat_capacity ?? 4,
        notes: moveMeta.notes || '',
        tracking: false,
        crew
    }
}
