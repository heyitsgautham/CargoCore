// Pure rules behind the Picking view: which orders sit at which warehouse stage,
// how an order becomes a pick wave card, and how the board groups and filters them.
import { getEffectiveWarehouseSubstatus } from '@/utils/warehouseOrderState'
import {
    isDirectTransportOrder,
    formatDate,
    getStatusClass,
    dedupeOrders,
    getItemRemainingQuantity,
} from './pickingFormat'

export const PICK_CONFIRMED_STATUSES = ['PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED']

export const BOARD_STATUSES = ['ON_HOLD', 'AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING']

export const QC_FIELDS = ['goodsCorrect', 'countCorrect', 'packagingOk', 'laborConfirmed', 'weightOk', 'labelAttached']

export function hasCompletedPicking(status) {
    return PICK_CONFIRMED_STATUSES.includes(status)
}

function inStage(order, warehouseId, substatus) {
    return order.status !== 'CANCELLED' &&
        !isDirectTransportOrder(order) &&
        getEffectiveWarehouseSubstatus(order, warehouseId) === substatus
}

/**
 * Split the hub's orders into the picking stages.
 * Direct transport orders never enter the pick and pack flow; the ones a dispatcher
 * already gave a driver come back as dispatcherAssigned so the view can mention them.
 */
export function classifyPickingOrders(orders, warehouseId) {
    const warehouseOrders = (orders || []).filter(order =>
        warehouseId ? order.warehouse_id === warehouseId : true
    )

    const awaitingPick = warehouseOrders.filter(order => {
        const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
        return order.status === 'CONFIRMED' &&
            !isDirectTransportOrder(order) &&
            substatus === 'AWAITING_PICK'
    }).map(order => ({ ...order, warehouse_substatus: 'AWAITING_PICK' }))

    const dispatcherAssigned = warehouseOrders.filter(order =>
        order.status === 'ASSIGNED' &&
        isDirectTransportOrder(order) &&
        order.assigned_driver_id != null &&
        order.assigned_vehicle_id == null
    )

    const picking = warehouseOrders.filter(order => inStage(order, warehouseId, 'PICKING'))
        .map(order => ({ ...order, warehouse_substatus: 'PICKING' }))
    const picked = warehouseOrders.filter(order => inStage(order, warehouseId, 'PICKED'))
        .map(order => ({ ...order, warehouse_substatus: 'PICKED' }))
    const packing = warehouseOrders.filter(order => inStage(order, warehouseId, 'PACKING'))
        .map(order => ({ ...order, warehouse_substatus: 'PACKING' }))
    const packed = warehouseOrders.filter(order => {
        if (order.status === 'CANCELLED') return false
        if (isDirectTransportOrder(order)) return false
        const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
        return ['PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH'].includes(substatus)
    }).map(order => ({
        ...order,
        warehouse_substatus: getEffectiveWarehouseSubstatus(order, warehouseId),
    }))

    return { awaitingPick, dispatcherAssigned, picking, picked, packing, packed }
}

export function toDispatcherNotice(order) {
    return {
        id: order.tracking_code || String(order.id).slice(0, 8).toUpperCase(),
        rawId: order.id,
        driverName: order.assigned_driver_name || 'a driver',
        pickupAddr: order.pickup_addr || '',
        value: order.total_amount || 0,
    }
}

/** Map each order id to the labourers working on it. */
export function groupLabourersByOrder(labourers) {
    const byOrder = {}
    for (const labourer of labourers || []) {
        if (!labourer.assigned_order_id) continue
        if (!byOrder[labourer.assigned_order_id]) byOrder[labourer.assigned_order_id] = []
        byOrder[labourer.assigned_order_id].push({
            id: labourer.id,
            name: labourer.name || labourer.full_name || labourer.email || 'Labourer',
            skill_tags: labourer.skill_tags,
        })
    }
    return byOrder
}

/** The first labourer on each order, which the start-picking call sends along. */
export function buildOrderAssignments(labourers) {
    return (labourers || []).reduce((map, labourer) => {
        if (labourer.assigned_order_id) {
            map[labourer.assigned_order_id] = {
                labourerId: labourer.id,
                labourerName: labourer.name || labourer.email || 'Assigned labourer',
            }
        }
        return map
    }, {})
}

export function toPickWave(order, { assignment, laborAssigned = [], canUndo = false }) {
    return {
        id: order.tracking_code || order.id?.slice(0, 8).toUpperCase(),
        type: order.order_type || 'Standard',
        priority: order.priority || order.shipping_priority || 'STANDARD',
        items: (order.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0) || order.item_count || 0,
        value: order.total_amount || 0,
        deadline: formatDate(order.scheduled_at),
        status: order.warehouse_substatus || order.status,
        statusClass: getStatusClass(order.warehouse_substatus || order.status),
        rawId: order.id,
        assignedPicker: assignment?.labourerName || null,
        canUndo,
        laborRequired: order.labor_count ?? order.laborCount ?? 0,
        laborAssigned,
        materialsAmount: Number(order.materials_amount ?? 0),
        packingAmount: Number(order.packing_amount ?? 0),
        assignedDriverId: order.assigned_driver_id || null,
        assignedDriverName: order.assigned_driver_name || null,
        assignedVehicleId: order.assigned_vehicle_id || null,
        // Dispatcher-direct flow: driver assigned by dispatcher, no WM vehicle yet
        isDispatcherAssigned: !!order.assigned_driver_id && !order.assigned_vehicle_id && Number(order.packing_amount ?? 0) === 0,
    }
}

export function buildPickWaves(stages, { labourers, orderAssignments, undoHistory }) {
    const laborByOrder = groupLabourersByOrder(labourers)
    const active = dedupeOrders([...stages.awaitingPick, ...stages.picking, ...stages.picked, ...stages.packing])
    return active.map(order => toPickWave(order, {
        assignment: orderAssignments[order.id],
        laborAssigned: laborByOrder[order.id] || [],
        canUndo: undoHistory.some(entry => entry.orderId === order.id),
    }))
}

/** Counts and highlight flags for the five pipeline steps, in order. */
export function pipelineCounts(stages) {
    const accepted = stages.awaitingPick.filter(order => Number(order.packing_amount ?? 0) > 0).length
    const ready = stages.packed.filter(order =>
        ['QC_PASSED', 'READY_FOR_DISPATCH'].includes(order.warehouse_substatus)
    ).length
    return [
        accepted,
        stages.picking.length + stages.picked.length,
        stages.packing.length,
        stages.packed.length,
        ready,
    ]
}

export function buildQualityChecks(packedOrders, qcItems, orderAssignments) {
    const qcByOrderId = new Map((qcItems || []).map(item => [item.order_id, item]))
    return packedOrders.map(order => {
        const existing = qcByOrderId.get(order.id)
        const fields = {
            goodsCorrect: Boolean(existing?.goods_correct),
            countCorrect: Boolean(existing?.count_correct),
            packagingOk: Boolean(existing?.packaging_verified),
            laborConfirmed: Boolean(existing?.labor_assigned || orderAssignments[order.id]),
            weightOk: Boolean(existing?.weight_verified),
            labelAttached: Boolean(existing?.label_attached),
        }
        return {
            orderId: order.tracking_code || order.id?.slice(0, 8),
            rawId: order.id,
            checkId: existing?.id || null,
            ...fields,
            verified: Boolean(existing?.is_passed) || allChecksTicked(fields),
            isPassed: Boolean(existing?.is_passed),
        }
    })
}

export function allChecksTicked(check) {
    return QC_FIELDS.every(key => Boolean(check[key]))
}

/** Waves grouped for the board tabs. Orders short of labourers go on hold. */
export function groupWavesByStatus(waves) {
    const grouped = { ON_HOLD: [], AWAITING_PICK: [], PICKING: [], PICKED: [], PACKING: [] }
    for (const wave of waves) {
        const laborRequired = wave.laborRequired ?? 0
        const laborAssigned = wave.laborAssigned?.length || 0
        if (laborAssigned < laborRequired && ['AWAITING_PICK', 'CONFIRMED'].includes(wave.status)) {
            grouped.ON_HOLD.push({ ...wave, status: 'ON_HOLD' })
        } else if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') {
            grouped.AWAITING_PICK.push(wave)
        } else if (['PICKING', 'PICKED', 'PACKING'].includes(wave.status)) {
            grouped[wave.status].push(wave)
        }
    }
    return grouped
}

export function wavesForTab(grouped, tab) {
    if (tab === 'ALL') return BOARD_STATUSES.flatMap(status => grouped[status] || [])
    return grouped[tab] || []
}

export function filterWaves(waves, { search = '', statuses = [], priority = '' }) {
    let result = waves
    const query = search.toLowerCase().trim()
    if (query) {
        result = result.filter(w =>
            w.id.toLowerCase().includes(query) ||
            (w.type || '').toLowerCase().includes(query) ||
            (w.priority || '').toLowerCase().includes(query) ||
            (w.assignedPicker || '').toLowerCase().includes(query)
        )
    }
    if (statuses.length > 0) {
        result = result.filter(w => statuses.includes(w.status))
    }
    if (priority) {
        result = result.filter(w => (w.priority || 'STANDARD').toUpperCase() === priority)
    }
    return result
}

/** Fold saved pick progress into the pick list, trusting later stages as fully picked. */
export function mergePickListWithProgress(items = [], progressItems = [], status) {
    const progressBySku = new Map((progressItems || []).map(progressItem => [progressItem.sku, progressItem]))
    const inferCompletedPick = hasCompletedPicking(status)

    return items.map(item => {
        const progressItem = progressBySku.get(item.sku)
        const requiredQuantity = Number(
            progressItem?.quantity_required ?? item.quantity_required ?? item.required_quantity ?? item.quantity ?? 0
        ) || 0
        const quantityPicked = Math.min(
            requiredQuantity,
            Number(progressItem?.quantity_picked ?? (inferCompletedPick ? requiredQuantity : 0)) || 0
        )
        const isComplete = Boolean(progressItem?.is_complete) || (inferCompletedPick && requiredQuantity > 0)

        return {
            ...item,
            quantity_required: requiredQuantity,
            required_quantity: requiredQuantity,
            quantity_picked: quantityPicked,
            picked_by: progressItem?.picked_by || null,
            picker_name: progressItem?.picker_name || null,
            picked_record_id: progressItem?.id || null,
            is_complete: isComplete,
            picked: isComplete,
            syncing: false,
        }
    })
}

/** Why a wave may not start picking yet, as the warning lines the view lists. */
export function prerequisiteWarnings({ hasHouseShiftOrders, inventoryCount, floorPlanConfigured, labourerCount }) {
    const warnings = []
    if (hasHouseShiftOrders && inventoryCount === 0) {
        warnings.push('No inventory items configured — go to Inventory to add stock before picking.')
    }
    if (hasHouseShiftOrders && floorPlanConfigured === false) {
        warnings.push('Floor plan not configured — set up warehouse layout in Floor Plan before picking.')
    }
    if (labourerCount === 0) {
        warnings.push('No labourers registered — add labourers in Labour Management before assigning to orders.')
    }
    return warnings
}

/** A pick list row can be confirmed only while its wave is picking and items remain. */
export function canConfirmPick(wave, item) {
    return wave?.status === 'PICKING' && !item.syncing && getItemRemainingQuantity(item) > 0
}
