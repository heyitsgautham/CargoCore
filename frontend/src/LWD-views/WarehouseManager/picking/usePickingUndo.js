// Undo for pick wave moves: the last five moves per session, with a toast that offers
// to revert the latest one for ten seconds.
import { ref } from 'vue'
import { patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'
import { notifyOrdersUpdated } from './pickingFormat'
import * as api from './pickingApi'

export function usePickingUndo({ token, getWarehouseId, flashAction, refresh }) {
    const undoAction = ref(null)
    const undoHistory = ref([]) // Stack of previous states
    let undoTimeout = null

    function saveUndoState(wave, previousStatus, newStatus) {
        undoHistory.value.push({
            orderId: wave.rawId,
            waveId: wave.id,
            previousStatus,
            newStatus,
            timestamp: Date.now()
        })

        // Keep only last 5 undo actions
        if (undoHistory.value.length > 5) {
            undoHistory.value.shift()
        }

        undoAction.value = {
            message: `${wave.id} moved to ${newStatus.replace(/_/g, ' ')}`,
            orderId: wave.rawId,
            previousStatus,
            newStatus
        }

        // Auto-dismiss after 10 seconds
        if (undoTimeout) clearTimeout(undoTimeout)
        undoTimeout = setTimeout(() => {
            undoAction.value = null
        }, 10000)
    }

    async function performUndo() {
        if (!undoAction.value) return

        const { orderId, previousStatus, newStatus } = undoAction.value
        const warehouseId = getWarehouseId()

        if (!warehouseId) return

        // Only a started pick has a revert endpoint on the backend state machine.
        if (newStatus === 'PICKING') {
            try {
                const res = await fetch(api.revertPickingUrl(warehouseId, orderId), { method: 'POST', headers: api.jsonHeaders(token()) })
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}))
                    flashAction(err.detail || `Failed to undo: ${res.status}`, 3000)
                    undoAction.value = null
                    if (undoTimeout) clearTimeout(undoTimeout)
                    return
                }
            } catch {
                flashAction('Network error during undo', 3000)
                return
            }
        }

        patchWarehouseOrderUiState(warehouseId, orderId, {
            accepted: true,
            warehouse_substatus: previousStatus,
        })

        notifyOrdersUpdated()
        await refresh()

        flashAction(`Reverted to ${previousStatus.replace(/_/g, ' ')}`)

        undoAction.value = null
        if (undoTimeout) clearTimeout(undoTimeout)
    }

    function dismissUndo() {
        undoAction.value = null
        if (undoTimeout) clearTimeout(undoTimeout)
    }

    async function undoWaveStatus(wave) {
        const lastState = undoHistory.value.filter(h => h.orderId === wave.rawId).pop()
        if (!lastState) return

        const warehouseId = getWarehouseId()
        if (!warehouseId) return

        patchWarehouseOrderUiState(warehouseId, wave.rawId, {
            accepted: true,
            warehouse_substatus: lastState.previousStatus,
        })

        notifyOrdersUpdated()
        await refresh()

        flashAction(`${wave.id} reverted to ${lastState.previousStatus.replace(/_/g, ' ')}`)

        const idx = undoHistory.value.indexOf(lastState)
        if (idx >= 0) undoHistory.value.splice(idx, 1)
    }

    function clearUndoTimer() {
        if (undoTimeout) clearTimeout(undoTimeout)
    }

    return { undoAction, undoHistory, saveUndoState, performUndo, dismissUndo, undoWaveStatus, clearUndoTimer }
}
