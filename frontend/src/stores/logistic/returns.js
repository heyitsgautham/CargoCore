/**
 * Reverse logistics actions on return cases: status changes, refunds and pickups.
 */

import { apiRequest, authHeaders } from './api'
import {
    mapReturnRecord,
    normalizeReturnStatus,
} from './mappers'

export function useLogisticReturns({ returns, refresh }) {
    async function updateReturnStatus(rmaId, newStatus, details = {}) {
        const updatedReturn = await apiRequest(`/logistics/returns/${rmaId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                status: newStatus,
                refund_amount: details.refundAmount ?? null,
                condition: details.condition ?? null,
                notes: details.notes ?? null,
                apply_transport_charge: details.applyTransportCharge ?? false,
            }),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            const previous = returns.value[existingIndex]
            returns.value.splice(existingIndex, 1, {
                ...previous,
                ...mapReturnRecord(updatedReturn),
                wmDisposition: updatedReturn.wm_disposition ?? previous.wmDisposition ?? null,
                wmGenuineness: typeof updatedReturn.wm_is_genuine === 'boolean' ? updatedReturn.wm_is_genuine : previous.wmGenuineness,
                wmRecommendedSettlement: updatedReturn.wm_recommended_outcome ?? previous.wmRecommendedSettlement ?? null,
                wmRemarks: updatedReturn.wm_inspection_remarks ?? previous.wmRemarks ?? null,
                wmActualCondition: updatedReturn.condition ?? previous.wmActualCondition ?? null,
                wmDamageSeverity: updatedReturn.condition ?? previous.wmDamageSeverity ?? null,
                wmGradedAt: updatedReturn.wm_graded_at ?? previous.wmGradedAt ?? null,
                wmGraderName: updatedReturn.wm_grader_name ?? previous.wmGraderName ?? null,
                transportChargeAmount: Number(updatedReturn.transport_charge_amount ?? previous.transportChargeAmount ?? 0),
                transportChargeWalletCollected: Number(updatedReturn.transport_charge_wallet_collected ?? previous.transportChargeWalletCollected ?? 0),
                transportChargePendingAmount: Number(updatedReturn.transport_charge_pending_amount ?? previous.transportChargePendingAmount ?? 0),
                transportChargeStatus: updatedReturn.transport_charge_status ?? previous.transportChargeStatus ?? null,
                transportChargeAppliedAt: updatedReturn.transport_charge_applied_at ?? previous.transportChargeAppliedAt ?? null,
                notes: details.notes ?? previous.notes ?? '',
            })
        } else {
            await refresh()
        }
        return updatedReturn
    }

    async function issueReturnRefund(rmaId) {
        const result = await apiRequest(`/logistics/returns/${rmaId}/issue-refund`, {
            method: 'POST',
            headers: authHeaders(),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            returns.value.splice(existingIndex, 1, {
                ...returns.value[existingIndex],
                status: 'Refunded',
                walletCredited: true,
            })
        }
        return result
    }

    async function scheduleReturnPickup(rmaId) {
        const updatedCase = await apiRequest(`/logistics/returns/${rmaId}/schedule-pickup`, {
            method: 'POST',
            headers: authHeaders(),
        })
        const existingIndex = returns.value.findIndex((item) => item.id === String(rmaId))
        if (existingIndex !== -1) {
            returns.value.splice(existingIndex, 1, {
                ...returns.value[existingIndex],
                ...mapReturnRecord(updatedCase),
                status: normalizeReturnStatus(updatedCase.status || 'Pickup Scheduled'),
            })
        }
        return updatedCase
    }

    return { updateReturnStatus, issueReturnRefund, scheduleReturnPickup }
}
