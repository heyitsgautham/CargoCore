// Quality check ticks and the pass that marks a packed order ready for dispatch.
import { patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'
import { notifyOrdersUpdated } from './pickingFormat'
import { allChecksTicked } from './pickingBoard'
import * as api from './pickingApi'

export function useQualityDispatch({ token, getWarehouseId, flashAction, dispatchToast, pipelineSteps, refresh }) {
    async function toggleCheck(check, key) {
        if (check.isPassed) return

        const previous = {
            goodsCorrect: check.goodsCorrect,
            countCorrect: check.countCorrect,
            packagingOk: check.packagingOk,
            laborConfirmed: check.laborConfirmed,
            weightOk: check.weightOk,
            labelAttached: check.labelAttached,
            verified: check.verified,
        }

        check[key] = !check[key]
        check.verified = allChecksTicked(check)

        try {
            await api.persistQualityCheck(token(), getWarehouseId(), check)
        } catch (error) {
            Object.assign(check, previous)
            console.error('Error persisting quality check:', error)
            flashAction(error.message || 'Unable to save quality check')
        }
    }

    async function triggerDispatch(check) {
        const warehouseId = getWarehouseId()
        if (!warehouseId || !check.rawId) {
            dispatchToast.value = 'Cannot dispatch - missing warehouse or order'
            setTimeout(() => { dispatchToast.value = '' }, 3000)
            return
        }

        try {
            const checkId = await api.ensureQualityCheckRecord(token(), warehouseId, check)
            await api.persistQualityCheck(token(), warehouseId, check)
            await api.passQualityCheck(token(), warehouseId, checkId)

            patchWarehouseOrderUiState(warehouseId, check.rawId, {
                accepted: true,
                warehouse_substatus: 'QC_PASSED',
            })
            check.isPassed = true
            check.verified = true

            pipelineSteps.value[4].count++
            pipelineSteps.value[4].active = true
            pipelineSteps.value[3].count = Math.max(0, pipelineSteps.value[3].count - 1)
            dispatchToast.value = `${check.orderId} — Ready for Dispatch!`

            notifyOrdersUpdated()
            await refresh()
        } catch (error) {
            console.error('Error triggering dispatch:', error)
            dispatchToast.value = 'Error updating order status'
        }

        setTimeout(() => { dispatchToast.value = '' }, 3000)
    }


    return { toggleCheck, triggerDispatch }
}
