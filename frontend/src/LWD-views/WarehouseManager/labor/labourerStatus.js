// How a labourer shows on the labour board: status badge, current assignment, and the
// order and stage labels behind it.

export function mapStatusClass(displayStatus) {
    const classMap = {
        'In Warehouse': 'bg-green-500/10 text-green-500',
        'Warehouse Order': 'bg-blue-500/10 text-blue-500',
        'Service Move': 'bg-purple-500/10 text-purple-400',
        'With Driver': 'bg-purple-500/10 text-purple-400',
        'Off Duty': 'bg-gray-500/10 text-gray-500',
    }
    return classMap[displayStatus] || 'bg-gray-500/10 text-gray-500'
}

export function getInitials(name) {
    if (!name) return '?'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

export function formatTime(dateString) {
    if (!dateString) return '--'
    try {
        return new Date(dateString).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    } catch {
        return '--'
    }
}

export function formatOrderDisplayId(orderId, trackingCode = null) {
    const preferredId = String(trackingCode || '').trim()
    if (preferredId) return preferredId

    const rawId = String(orderId || '').trim()
    if (!rawId) return null

    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    return uuidPattern.test(rawId) ? rawId.slice(0, 8).toUpperCase() : rawId
}

export function formatWarehouseSubstatus(substatus) {
    const labelMap = {
        AWAITING_INBOUND: 'Awaiting Inbound',
        AWAITING_PICK: 'Awaiting Pick',
        PICKING: 'Picking',
        PICKED: 'Picked',
        PACKING: 'Packing',
        PACKED: 'Packed',
        QC_PASSED: 'QC Passed',
        READY_FOR_DISPATCH: 'Ready for Dispatch',
        ON_DOCK: 'On Dock',
        DISPATCHED: 'Dispatched',
        ON_HOLD: 'On Hold',
    }
    return labelMap[substatus] || substatus || ''
}

export function buildAssignmentMeta(labourer) {
    if (!labourer.assigned_order_id) {
        return {
            task: labourer.current_task || 'Available',
            assignmentHint: '',
            orderScope: '',
        }
    }

    if (labourer.assigned_order_substatus) {
        return {
            task: formatWarehouseSubstatus(labourer.assigned_order_substatus),
            assignmentHint: 'Warehouse pick/pack assignment',
            orderScope: 'WM order',
        }
    }

    if (labourer.status === 'ON_FIELD') {
        return {
            task: 'With Driver',
            assignmentHint: 'Customer move in progress',
            orderScope: 'Service move order',
        }
    }

    return {
        task: 'Driver Move Assigned',
        assignmentHint: 'Waiting to start customer move',
        orderScope: 'Service move order',
    }
}

export function buildDisplayStatus(labourer) {
    if (!labourer.is_active || ['OFF_DUTY', 'INACTIVE'].includes(labourer.status)) {
        return 'Off Duty'
    }

    if (!labourer.assigned_order_id) {
        return 'In Warehouse'
    }

    if (labourer.assigned_order_substatus) {
        return 'Warehouse Order'
    }

    if (labourer.status === 'ON_FIELD') {
        return 'With Driver'
    }

    return 'Service Move'
}

export function buildLocalAssignmentState(type, orderId) {
    const displayOrderId = formatOrderDisplayId(orderId)
    if (type === 'Field Duty (With Driver)') {
        return {
            orderId: displayOrderId,
            status: 'With Driver',
            statusClass: mapStatusClass('With Driver'),
            task: 'With Driver',
            assignmentHint: 'Customer move in progress',
            orderScope: 'Service move order',
        }
    }

    return {
        orderId: displayOrderId,
        status: 'Warehouse Order',
        statusClass: mapStatusClass('Warehouse Order'),
        task: type || 'Warehouse Task',
        assignmentHint: 'Warehouse pick/pack assignment',
        orderScope: 'WM order',
    }
}
