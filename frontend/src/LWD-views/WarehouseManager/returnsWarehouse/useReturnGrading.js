// Flow 2 of returns: grading a physically inspected item, with its condition, disposition,
// genuineness call and a photo, then moving it from the queue to the completed list.
import { API_BASE_URL } from '@/config/api'

export function useReturnGrading({
    authStore,
    capturedPhoto,
    completedItems,
    conditionNotes,
    disposition,
    inboundReturns,
    inspectionGenuineness,
    inspectionRecommendedOutcome,
    inspectionRemarks,
    itemCondition,
    mapGradingToCompleted,
    pendingGradings,
    rmaId,
    selectedGradingId,
    selectedOrderForReturn,
    submitting,
    toastMsg,
    warehouseId,
}) {
    async function submitReturn() {
        if (!warehouseId.value) {
            toastMsg.value = 'No warehouse selected'
            setTimeout(() => { toastMsg.value = '' }, 2500)
            return
        }

        submitting.value = true
        const labels = { restock: 'Restocked', claims: 'Sent to Claims', discard: 'Discarded', recycle: 'Recycled' }

        try {
            const headers = {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }

            let gradingId = selectedGradingId.value

            if (gradingId) {
                // Existing pending grading — update it first, then complete
                await fetch(
                    `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}`,
                    {
                        method: 'PUT',
                        headers,
                        body: JSON.stringify({
                            item_condition: itemCondition.value,
                            condition_notes: conditionNotes.value || null,
                            disposition: disposition.value,
                            is_genuine: inspectionGenuineness.value !== '' ? inspectionGenuineness.value : null,
                            recommended_outcome: inspectionRecommendedOutcome.value || null,
                            inspection_remarks: inspectionRemarks.value || null,
                        })
                    }
                )
            } else {
                // New grading — create it
                const response = await fetch(
                    `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns`,
                    {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({
                            rma_code: rmaId.value,
                            order_id: selectedOrderForReturn.value?.id || null,
                            item_condition: itemCondition.value,
                            condition_notes: conditionNotes.value || null,
                            disposition: disposition.value,
                            is_genuine: inspectionGenuineness.value !== '' ? inspectionGenuineness.value : null,
                            recommended_outcome: inspectionRecommendedOutcome.value || null,
                            inspection_remarks: inspectionRemarks.value || null,
                        })
                    }
                )
                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const grading = await response.json()
                gradingId = grading.id
            }

            // Upload photo if captured
            if (capturedPhoto.value && gradingId) {
                await uploadDamagePhoto(gradingId, capturedPhoto.value)
            }

            // Mark as completed — this is what moves it to the "Completed" tab
            const completeRes = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}/complete`,
                { method: 'POST', headers }
            )
            if (!completeRes.ok) throw new Error(`Complete failed: HTTP ${completeRes.status}`)
            const completed = await completeRes.json()

            // Add to completed list immediately
            completedItems.value.unshift(mapGradingToCompleted(completed))

            // Remove from processing queue
            const gradingIdx = pendingGradings.value.findIndex(g => g.id === selectedGradingId.value)
            if (gradingIdx !== -1) pendingGradings.value.splice(gradingIdx, 1)
            const orderIdx = inboundReturns.value.findIndex(o =>
                rmaId.value.includes(o.tracking_code) || rmaId.value.includes(o.id?.slice(0, 6))
            )
            if (orderIdx !== -1) inboundReturns.value.splice(orderIdx, 1)

            toastMsg.value = `Return ${rmaId.value} — ${labels[disposition.value]}`

            // Reset form
            capturedPhoto.value = null
            rmaId.value = ''
            itemCondition.value = ''
            conditionNotes.value = ''
            disposition.value = ''
            inspectionGenuineness.value = ''
            inspectionRecommendedOutcome.value = ''
            inspectionRemarks.value = ''
            selectedOrderForReturn.value = null
            selectedGradingId.value = null

        } catch (error) {
            console.error('Error submitting return:', error)
            toastMsg.value = 'Failed to submit return grading'
        } finally {
            submitting.value = false
            setTimeout(() => { toastMsg.value = '' }, 2500)
        }
    }

    async function uploadDamagePhoto(gradingId, photoData) {
        try {
            // Convert base64/data URL to blob if needed
            let blob
            if (typeof photoData === 'string' && photoData.startsWith('data:')) {
                const res = await fetch(photoData)
                blob = await res.blob()
            } else if (photoData instanceof Blob) {
                blob = photoData
            } else {
                // Mock photo - skip upload
                return
            }

            const formData = new FormData()
            formData.append('file', blob, 'damage_photo.jpg')

            const response = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}/photo`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authStore.authToken}`,
                    },
                    body: formData
                }
            )

            if (!response.ok) {
                console.warn('Failed to upload photo:', response.status)
            }
        } catch (error) {
            console.error('Error uploading damage photo:', error)
        }
    }

    return { submitReturn }
}
