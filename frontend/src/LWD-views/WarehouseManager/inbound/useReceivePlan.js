// The AI receive plan for an inbound shipment and its primary action.
import { riskClassMap } from './inboundRows'
import { API_BASE_URL } from '@/config/api'

export function useReceivePlan({
    asns,
    authHeaders,
    authStore,
    completeReceiving,
    estimatorForm,
    estimatorLoading,
    estimatorPlan,
    openScheduleFromEstimator,
    selectedEstimatorAsn,
    showEstimatorModal,
    showToast,
    startReceiving,
}) {
    async function fetchInboundReceivePlan() {
        const selectedAsn = asns.value.find((asn) => asn.id === estimatorForm.asnId)
        const warehouseId = authStore.currentUser?.warehouse_id
        if (!selectedAsn?.rawId || !warehouseId) {
            estimatorPlan.value = null
            return
        }

        estimatorLoading.value = true
        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${selectedAsn.rawId}/ai-receive-plan`,
                { headers: authHeaders() }
            )
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.detail || 'Failed to generate AI receive plan')
            }

            const data = await res.json()
            estimatorPlan.value = {
                asn: {
                    id: data?.asn?.id || selectedAsn.id,
                    supplier: data?.asn?.supplier || selectedAsn.supplier,
                    status: data?.asn?.status || selectedAsn.status,
                },
                shipmentType: data?.asn?.shipment_type || 'Inbound transfer',
                materialProfile: data?.asn?.material_profile || 'General cargo',
                expectedUnits: data?.asn?.expected_units || selectedAsn.expected || 0,
                recurring: Boolean(data?.asn?.recurring),
                confidence: data?.confidence || 0,
                suggestedDock: data?.suggested_dock || 'Dock 1',
                workers: data?.workers || 2,
                totalMinutes: data?.total_minutes || 0,
                riskLevel: data?.risk_level || 'Low',
                riskClass: riskClassMap[data?.risk_level] || riskClassMap.Low,
                pallets: data?.pallet_load || 1,
                queueMinutes: data?.queue_minutes || 0,
                activeDockCount: data?.active_dock_count || 0,
                stagingZone: data?.staging_zone || 'Inbound Buffer A',
                nextAction: data?.next_action || 'Review this inbound before scheduling dock work.',
                reason: data?.reason || 'AI reasoning unavailable.',
                watchouts: Array.isArray(data?.watchouts) ? data.watchouts : [],
                summary: data?.summary || '',
                generatedBy: data?.generated_by || 'gemini',
            }
        } catch (error) {
            console.error(error)
            estimatorPlan.value = null
            showToast(error.message || 'Failed to generate AI receive plan')
        } finally {
            estimatorLoading.value = false
        }
    }

    async function openInboundEstimator(asnId = '') {
        if (!asns.value.length) {
            showToast('No inbound ASN available for receive planning yet')
            return
        }
        estimatorForm.asnId = asnId || estimatorForm.asnId || asns.value.find((item) => item.status !== 'Completed')?.id || asns.value[0].id
        showEstimatorModal.value = true
        await fetchInboundReceivePlan()
    }

    async function handleEstimatorPrimaryAction() {
        const selectedAsn = selectedEstimatorAsn.value
        if (!selectedAsn) {
            showEstimatorModal.value = false
            return
        }
        if (selectedAsn.status === 'Receiving') {
            await completeReceiving(selectedAsn)
            return
        }
        if (selectedAsn.status === 'Arrived') {
            startReceiving(selectedAsn)
            return
        }
        openScheduleFromEstimator()
    }

    return { fetchInboundReceivePlan, openInboundEstimator, handleEstimatorPrimaryAction }
}
