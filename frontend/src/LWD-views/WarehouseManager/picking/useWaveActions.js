// Moving a pick wave to its next stage, with the checks each stage needs first.
import { ref } from 'vue'
import { patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'
import { isHouseShift, notifyOrdersUpdated, readResponseError } from './pickingFormat'
import * as api from './pickingApi'

export function useWaveActions({
    token,
    getWarehouseId,
    flashAction,
    refresh,
    actionToast,
    inventoryCount,
    floorPlanConfigured,
    labourers,
    orderAssignments,
    saveUndoState,
}) {
    const waveActionPending = ref({})

    function isWaveActionPending(wave) {
        return Boolean(wave?.rawId && waveActionPending.value[wave.rawId])
    }

    async function updateWaveStatus(wave, targetStatus, request, options = {}) {
        const warehouseId = getWarehouseId()
        if (!warehouseId) {
            flashAction('Warehouse not linked')
            return false
        }
        if (!wave?.rawId) {
            flashAction('Order action is missing an order id')
            return false
        }
        if (waveActionPending.value[wave.rawId]) {
            return false
        }

        waveActionPending.value = {
            ...waveActionPending.value,
            [wave.rawId]: true,
        }

        try {
            const response = await fetch(request.url, request.options)
            if (!response.ok) {
                throw new Error(await readResponseError(response, `Failed warehouse action: ${response.status}`))
            }

            if (typeof options.onSuccess === 'function') {
                options.onSuccess()
            }

            // Only update UI state if backend call succeeds
            patchWarehouseOrderUiState(warehouseId, wave.rawId, {
                accepted: true,
                warehouse_substatus: targetStatus,
            })
            notifyOrdersUpdated()
            actionToast.value = `${wave.id} moved to ${targetStatus.replaceAll('_', ' ')}`
            await refresh()
            setTimeout(() => { actionToast.value = '' }, 2500)
            return true
        } catch (error) {
            console.error('Warehouse action error:', error)
            flashAction(error.message || 'Unable to update order status', 3500)
            // Refresh to get accurate state from backend
            await refresh()
            return false
        } finally {
            const nextPending = { ...waveActionPending.value }
            delete nextPending[wave.rawId]
            waveActionPending.value = nextPending
        }
    }

    async function handleWaveAction(wave) {
        const warehouseId = getWarehouseId()
        const previousStatus = wave.status

        if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') {
            if (isHouseShift(wave) && inventoryCount.value === 0) {
                flashAction('Cannot start picking — no inventory configured. Add inventory items first.', 5000)
                return false
            }
            if (isHouseShift(wave) && floorPlanConfigured.value === false) {
                flashAction('Cannot start picking — floor plan not configured. Set up the warehouse layout first.', 5000)
                return false
            }
            if (labourers.value.length === 0) {
                flashAction('Cannot start picking — no labourers registered. Add labourers in Labour Management first.', 5000)
                return false
            }
        }

        if (wave.status === 'PACKING') {
            // Customer-selected packing materials must be issued before packing completes.
            const materials = await api.packingMaterialsStatus(token(), wave.rawId)
            if (materials === 'unverified') {
                flashAction('⚠ Could not verify packing material issuance. Please try again.', 6000)
                return false
            }
            if (materials === 'not-issued') {
                flashAction('⚠ Packing materials not issued! Go to Packing Materials → Issue to Order before completing packing.', 6000)
                return false
            }
            if (materials === 'check-failed') {
                flashAction('⚠ Could not verify packing materials. Please try again.', 6000)
                return false
            }
        }

        const transition = api.waveTransition(warehouseId, wave, orderAssignments.value[wave.rawId]?.labourerId)
        if (!transition) return false

        const options = { method: 'POST', headers: api.jsonHeaders(token()) }
        if (transition.body !== undefined) options.body = transition.body
        return updateWaveStatus(wave, transition.target, { url: transition.url, options }, {
            onSuccess: () => saveUndoState(wave, previousStatus, transition.target)
        })
    }

    return { isWaveActionPending, handleWaveAction }
}
