function storageKey(warehouseId) {
    return `warehouse-order-state:${warehouseId || 'unassigned'}`
}

export function readWarehouseOrderState(warehouseId) {
    if (typeof window === 'undefined') return {}
    try {
        const raw = window.localStorage.getItem(storageKey(warehouseId))
        return raw ? JSON.parse(raw) : {}
    } catch {
        return {}
    }
}

export function writeWarehouseOrderState(warehouseId, state) {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(storageKey(warehouseId), JSON.stringify(state))
}

export function getWarehouseOrderUiState(warehouseId, orderId) {
    const state = readWarehouseOrderState(warehouseId)
    return state[orderId] || {}
}

export function patchWarehouseOrderUiState(warehouseId, orderId, patch) {
    const state = readWarehouseOrderState(warehouseId)
    state[orderId] = {
        ...(state[orderId] || {}),
        ...patch,
    }
    writeWarehouseOrderState(warehouseId, state)
    return state[orderId]
}

export function getEffectiveWarehouseSubstatus(order, warehouseId) {
    const state = getWarehouseOrderUiState(warehouseId, order?.id)
    return state.warehouse_substatus || order?.warehouse_substatus || null
}

export function isWarehouseOrderAccepted(order, warehouseId) {
    const state = getWarehouseOrderUiState(warehouseId, order?.id)
    return Boolean(state.accepted)
}
