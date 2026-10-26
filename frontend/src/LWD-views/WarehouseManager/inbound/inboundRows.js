// Inbound shipment labels and the mapping from the inbound API to rows on the receiving board.

export const inboundStatusClassMap = {
    Arrived: 'bg-green-500/10 text-green-500 border-green-500/20',
    Scheduled: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    Receiving: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Completed: 'bg-green-500/10 text-green-500 border-green-500/20',
    InTransit: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    OnHold: 'bg-red-500/10 text-red-500 border-red-500/20',
}
export const dockStatusClassMap = {
    Completed: 'bg-green-500/20 text-green-600 dark:text-green-400',
    Active: 'bg-blue-500/20 text-blue-500',
    Scheduled: 'bg-gray-500/20 text-gray-500',
}
export const issueStatusClassMap = {
    new: 'bg-blue-500/10 text-blue-600 border-blue-500/20 dark:text-blue-300',
    in_progress: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-300',
    resolved: 'bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-300',
}
export const riskClassMap = {
    Low: 'text-green-600 dark:text-green-400',
    Medium: 'text-yellow-600 dark:text-yellow-400',
    High: 'text-red-600 dark:text-red-400',
}
export const inboundDisplayStatusClassMap = {
    'Ready for Picking': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    Picking: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Picked: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    Packing: 'bg-green-500/10 text-green-500 border-green-500/20',
    Packed: 'bg-green-500/10 text-green-500 border-green-500/20',
    'QC Passed': 'bg-green-500/10 text-green-500 border-green-500/20',
    'Ready for Dispatch': 'bg-green-500/10 text-green-500 border-green-500/20',
    'On Dock': 'bg-green-500/10 text-green-500 border-green-500/20',
    Dispatched: 'bg-green-500/10 text-green-500 border-green-500/20',
    'Vendor Take-Back': 'bg-red-500/10 text-red-500 border-red-500/20',
}
export const PICKING_FLOW_SUBSTATUSES = new Set([
    'AWAITING_PICK',
    'PICKING',
    'PICKED',
    'PACKING',
    'PACKED',
    'QC_PASSED',
    'READY_FOR_DISPATCH',
    'ON_DOCK',
    'DISPATCHED',
])

export function getInboundDisplayStatus(status, warehouseSubstatus) {
    const substatus = (warehouseSubstatus || '').toUpperCase()
    const labelMap = {
        AWAITING_PICK: 'Ready for Picking',
        PICKING: 'Picking',
        PICKED: 'Picked',
        PACKING: 'Packing',
        PACKED: 'Packed',
        QC_PASSED: 'QC Passed',
        READY_FOR_DISPATCH: 'Ready for Dispatch',
        ON_DOCK: 'On Dock',
        DISPATCHED: 'Dispatched',
        ON_HOLD: 'Vendor Take-Back',
    }
    return labelMap[substatus] || status
}

export function getInboundStatusClass(status, warehouseSubstatus) {
    const displayStatus = getInboundDisplayStatus(status, warehouseSubstatus)
    return inboundDisplayStatusClassMap[displayStatus]
        || inboundStatusClassMap[status]
        || inboundStatusClassMap.Scheduled
}

export function isAsnInPickingFlow(asn) {
    return PICKING_FLOW_SUBSTATUSES.has((asn?.warehouseSubstatus || '').toUpperCase())
}

export function formatIssueStatus(status) {
    return {
        new: 'Support New',
        in_progress: 'Support Working',
        resolved: 'Support Resolved',
    }[(status || '').toLowerCase()] || 'Support Open'
}

export function issueStatusClass(status) {
    return issueStatusClassMap[(status || '').toLowerCase()] || issueStatusClassMap.new
}

export function formatDateTime(value) {
    if (!value) return 'TBD'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return 'TBD'
    return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

/** One inbound API shipment as a board row; rows already in the pick and pack flow are dropped later. */
export function toInboundRow(shipment, warehouseId) {
    return {
        id: shipment.tracking_code || `ASN-${String(shipment.order_id).slice(0, 6).toUpperCase()}`,
        rawId: shipment.order_id,
        warehouseId,
        supplier: shipment.supplier_name,
        expected: shipment.expected_qty || 0,
        received: shipment.received_qty || 0,
        eta: formatDateTime(shipment.eta || shipment.scheduled_at || shipment.created_at),
        status: shipment.status || 'Scheduled',
        displayStatus: getInboundDisplayStatus(shipment.status, shipment.warehouse_substatus),
        statusClass: getInboundStatusClass(shipment.status, shipment.warehouse_substatus),
        warehouseSubstatus: shipment.warehouse_substatus || null,
        mismatch: Boolean(shipment.has_mismatch),
        mismatchDetails: shipment.mismatch_details || '',
        mismatchType: shipment.mismatch_type || '',
        damaged: Boolean(shipment.has_damage),
        damageCount: shipment.damage_count || 0,
        damageDescription: shipment.damage_description || '',
        issueType: shipment.issue_type || null,
        issueResolutionAction: shipment.issue_resolution_action || null,
        issueResolutionLabel: shipment.issue_resolution_label || null,
        issueStatus: shipment.issue_status || null,
        issueTicketId: shipment.issue_ticket_id || null,
        issueTicketReference: shipment.issue_ticket_reference || null,
        issueBlockingReason: shipment.issue_blocking_reason || '',
        canMoveToPicking: shipment.can_move_to_picking !== false,
        canGenerateTakeBack: Boolean(shipment.can_generate_take_back),
        // Payment info for auto-debit confirmation
        totalAmount: Number(shipment.total_amount || 0),
        autoDebitEnabled: Boolean(shipment.auto_debit_enabled),
        isRecurring: Boolean(shipment.is_recurring),
    }
}

export function toDockSlot(slot) {
    return { ...slot, statusClass: dockStatusClassMap[slot.status] || dockStatusClassMap.Scheduled }
}

/** The four stat cards from the inbound API's stats block. */
export function inboundStatsFrom(stats) {
    return {
        arrivedToday: stats?.arrived_today || 0,
        inTransit: stats?.in_transit || 0,
        mismatchesFound: stats?.mismatches_found || 0,
        damageReports: stats?.damage_reports || 0,
    }
}
