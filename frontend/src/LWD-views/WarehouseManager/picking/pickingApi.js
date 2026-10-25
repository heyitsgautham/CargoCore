// Backend calls the Picking view makes. Each one takes the bearer token explicitly,
// so the view decides which session and hub it acts for.
import { apiUrl } from '@/config/api'
import { readResponseError } from './pickingFormat'
import { allChecksTicked } from './pickingBoard'

function jsonHeaders(token) {
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
}

function opsUrl(warehouseId, path) {
    return apiUrl(`api/v1/warehouses/${warehouseId}/operations/${path}`)
}

export async function fetchOrders(token, search = '') {
    const searchParam = search.trim() ? `&search=${encodeURIComponent(search.trim())}` : ''
    const response = await fetch(apiUrl(`api/v1/orders?page=1&page_size=100${searchParam}`), {
        headers: jsonHeaders(token),
    })
    if (!response.ok) return null
    const data = await response.json()
    return data.items || []
}

/** The generated pick list, or the order's own items when no list can be generated. */
export async function fetchPickListItems(token, orderId) {
    const response = await fetch(apiUrl(`api/v1/inventory/pick-list/${orderId}`), {
        method: 'POST',
        headers: jsonHeaders(token),
    })

    if (response.ok) {
        const data = await response.json()
        return data.items || []
    }

    const orderRes = await fetch(apiUrl(`api/v1/orders/${orderId}`), { headers: jsonHeaders(token) })

    if (!orderRes.ok) {
        const pickListError = await readResponseError(response, `Unable to load pick list (${response.status})`)
        throw new Error(pickListError)
    }

    const orderData = await orderRes.json()
    return (orderData.items || []).map((item, idx) => ({
        sku: item.sku || `ITEM-${idx + 1}`,
        item_name: item.name || item.description || 'Item',
        required_quantity: item.quantity || 1,
        available_quantity: item.quantity || 1,
        shortage_quantity: 0,
        unit: item.unit || 'pcs',
        scan_code: item.sku || `SCAN-${idx + 1}`,
        zone: null,
        aisle: null,
        shelf: null,
        bin: null,
        location_path: 'Location TBD',
    }))
}

export async function fetchPickProgress(token, warehouseId, orderId) {
    if (!warehouseId) return null
    const response = await fetch(opsUrl(warehouseId, `orders/${orderId}/pick-progress`), {
        headers: jsonHeaders(token),
    })
    if (!response.ok) return null
    return await response.json()
}

export async function confirmPickItem(token, warehouseId, orderId, body) {
    const response = await fetch(opsUrl(warehouseId, `orders/${orderId}/pick-item`), {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(body),
    })
    if (!response.ok) {
        throw new Error(await readResponseError(response, `Failed to confirm pick (${response.status})`))
    }
    return await response.json()
}

/** The hub's labourers, or an empty list when the request fails. */
export async function fetchLabourerList(token, warehouseId) {
    try {
        const response = await fetch(apiUrl(`api/v1/labourers?warehouse_id=${warehouseId}&page_size=100`), {
            headers: jsonHeaders(token),
        })
        if (!response.ok) return []
        const data = await response.json()
        return data.items || []
    } catch (error) {
        console.error('Failed to fetch labourers:', error)
        return []
    }
}

export async function assignLabourer(token, labourerId, orderId) {
    const response = await fetch(apiUrl(`api/v1/labourers/${labourerId}/assign/${orderId}`), {
        method: 'POST',
        headers: jsonHeaders(token),
    })
    return response.ok
}

/**
 * Inventory count and floor plan state for the hub.
 * Errors other than a missing floor plan count as configured, so they never block picking.
 */
export async function checkPrerequisites(token, warehouseId) {
    let inventoryCount = 0
    let floorPlanConfigured = true
    try {
        const invRes = await fetch(apiUrl(`api/v1/inventory?warehouse_id=${warehouseId}&page_size=1`), {
            headers: jsonHeaders(token),
        })
        if (invRes.ok) {
            const invData = await invRes.json()
            inventoryCount = invData.total ?? invData.count ?? (invData.items?.length ?? 0)
        }
    } catch {
        inventoryCount = 0
    }

    try {
        const fpRes = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/floor-plan`), {
            headers: jsonHeaders(token),
        })
        if (fpRes.ok) {
            const fpData = await fpRes.json()
            floorPlanConfigured = (
                (fpData.sections?.length ?? 0) > 0 ||
                (fpData.racks?.length ?? 0) > 0 ||
                (fpData.groups?.length ?? 0) > 0
            )
        } else if (fpRes.status === 404) {
            floorPlanConfigured = false
        }
    } catch {
        floorPlanConfigured = true
    }
    return { inventoryCount, floorPlanConfigured }
}

export async function fetchQualityChecks(token, warehouseId) {
    if (!warehouseId) return []
    try {
        const response = await fetch(opsUrl(warehouseId, 'quality-checks'), { headers: jsonHeaders(token) })
        if (!response.ok) return []
        const data = await response.json()
        return data.items || []
    } catch (error) {
        console.error('Failed to fetch quality checks:', error)
        return []
    }
}

/** Create the order's quality check record once, or find the one that already exists. */
export async function ensureQualityCheckRecord(token, warehouseId, check) {
    if (check.checkId) return check.checkId

    if (!warehouseId || !check.rawId) {
        throw new Error('Missing warehouse or order for quality check')
    }

    const createResponse = await fetch(opsUrl(warehouseId, `orders/${check.rawId}/quality-check`), {
        method: 'POST',
        headers: jsonHeaders(token),
    })

    if (createResponse.ok) {
        const data = await createResponse.json()
        check.checkId = data.id
        return check.checkId
    }

    if (createResponse.status === 409) {
        const existingResponse = await fetch(opsUrl(warehouseId, `quality-checks?order_id=${check.rawId}`), {
            headers: jsonHeaders(token),
        })
        if (existingResponse.ok) {
            const data = await existingResponse.json()
            const existingCheck = data.items?.[0]
            if (existingCheck) {
                check.checkId = existingCheck.id
                return check.checkId
            }
        }
    }

    throw new Error(`Unable to create quality check (${createResponse.status})`)
}

export async function persistQualityCheck(token, warehouseId, check) {
    const checkId = await ensureQualityCheckRecord(token, warehouseId, check)
    const response = await fetch(opsUrl(warehouseId, `quality-checks/${checkId}`), {
        method: 'PUT',
        headers: jsonHeaders(token),
        body: JSON.stringify({
            goods_correct: check.goodsCorrect,
            count_correct: check.countCorrect,
            packaging_verified: check.packagingOk,
            labor_assigned: check.laborConfirmed,
            weight_verified: check.weightOk,
            label_attached: check.labelAttached,
        }),
    })

    if (!response.ok) {
        throw new Error(`Unable to persist quality check (${response.status})`)
    }

    const data = await response.json()
    check.checkId = data.id
    check.verified = Boolean(data.is_passed) || allChecksTicked(check)
    check.isPassed = Boolean(data.is_passed)
}

export async function passQualityCheck(token, warehouseId, checkId) {
    const response = await fetch(opsUrl(warehouseId, `quality-checks/${checkId}/pass`), {
        method: 'POST',
        headers: jsonHeaders(token),
    })
    if (!response.ok) {
        throw new Error(`Unable to pass quality check (${response.status})`)
    }
}

/** Packing stations shaped for the stations panel, or an empty list on any failure. */
export async function fetchPackingStations(token, warehouseId) {
    try {
        const response = await fetch(opsUrl(warehouseId, 'packing-stations'), { headers: jsonHeaders(token) })
        if (!response.ok) return []
        const data = await response.json()
        return (data.items || []).map(station => ({
            id: station.id,
            name: station.station_number,
            packer: station.assigned_labourer_name || (station.status === 'ACTIVE' ? 'Active' : '-- Idle --'),
            rate: station.items_packed_today || 0,
            active: station.status === 'ACTIVE',
            currentOrderId: station.current_order_id,
            currentOrderTracking: station.current_order_tracking,
        }))
    } catch (error) {
        console.error('Error fetching packing stations:', error)
        return []
    }
}

/**
 * Whether an order that asked for packing materials has had them issued.
 * Returns 'ok', 'not-issued', 'unverified' when the movements lookup fails, or 'check-failed' on a network error.
 */
export async function packingMaterialsStatus(token, orderId) {
    const headers = jsonHeaders(token)
    try {
        const orderItemsRes = await fetch(apiUrl(`api/v1/orders/${orderId}/items`), { headers })
        if (!orderItemsRes.ok) return 'ok'
        const orderItems = await orderItemsRes.json()
        const hasPackingItems = (orderItems || []).some(i => i.quantity > 0)
        if (!hasPackingItems) return 'ok'

        const movRes = await fetch(
            apiUrl(`api/v1/inventory/movements?reference_order_id=${orderId}&page_size=50`),
            { headers }
        )
        if (!movRes.ok) return 'unverified'
        const movements = await movRes.json()
        const issued = (Array.isArray(movements) ? movements : (movements.items || [])).filter(m =>
            (m.movement_type || '').toUpperCase() === 'ISSUE'
        )
        return issued.length === 0 ? 'not-issued' : 'ok'
    } catch {
        return 'check-failed'
    }
}

/** Transition endpoints for each wave status, keyed by the status the wave is in now. */
export function waveTransition(warehouseId, wave, labourerId) {
    const order = (path) => opsUrl(warehouseId, `orders/${wave.rawId}/${path}`)
    switch (wave.status) {
        case 'AWAITING_PICK':
        case 'CONFIRMED':
            return { target: 'PICKING', url: order('start-picking'), body: JSON.stringify({ labourer_id: labourerId || null }) }
        case 'PICKING':
            return { target: 'PICKED', url: order('complete-picking') }
        case 'PICKED':
            return { target: 'PACKING', url: order('start-packing'), body: JSON.stringify({}) }
        case 'PACKING':
            return { target: 'PACKED', url: order('complete-packing') }
        default:
            return null
    }
}

export function revertPickingUrl(warehouseId, orderId) {
    return opsUrl(warehouseId, `orders/${orderId}/revert-picking`)
}

export { jsonHeaders }
