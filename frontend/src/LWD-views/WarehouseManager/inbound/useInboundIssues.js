// Reporting a quantity mismatch or damage on an inbound shipment, with an optional camera photo.
import { API_BASE_URL } from '@/config/api'

export function useInboundIssues({
    asns,
    authHeaders,
    authStore,
    damageForm,
    damagePhoto,
    fetchInboundShipments,
    isCameraOpen,
    mismatchForm,
    showDamageModal,
    showMismatchModal,
    showToast,
}) {
    async function submitMismatch() {
        const asn = asns.value.find(a => a.id === mismatchForm.asnId)
        if (!asn?.rawId) {
            showToast('Select a valid ASN first')
            return
        }
        try {
            const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
            const res = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/report-mismatch`,
                {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        mismatch_type: mismatchForm.type,
                        details: mismatchForm.details || null,
                    }),
                }
            )
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.detail || 'Failed to report mismatch')
            }
            showMismatchModal.value = false
            mismatchForm.details = ''
            showToast(`Mismatch flagged for ${mismatchForm.asnId}`)
            await fetchInboundShipments()
        } catch (error) {
            console.error(error)
            showToast(error.message || 'Failed to report mismatch')
        }
    }

    async function submitDamage() {
        const asn = asns.value.find(a => a.id === damageForm.asnId)
        if (!asn?.rawId) {
            showToast('Select a valid ASN first')
            return
        }
        if (!damageForm.count || damageForm.count < 1) {
            showToast('Enter damaged item count')
            return
        }
        if (!damageForm.description.trim()) {
            showToast('Enter damage description')
            return
        }
        try {
            const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
            const res = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/report-damage`,
                {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        damaged_count: damageForm.count,
                        description: damageForm.description.trim(),
                        photo_url: damagePhoto.value || null,
                    }),
                }
            )
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.detail || 'Failed to report damage')
            }
            showDamageModal.value = false
            damageForm.description = ''
            damageForm.count = 0
            damageForm.hasPhoto = false
            damagePhoto.value = null
            showToast(`Damage report submitted for ${damageForm.asnId}`)
            await fetchInboundShipments()
        } catch (error) {
            console.error(error)
            showToast(error.message || 'Failed to report damage')
        }
    }

    function openDamageCamera() {
        isCameraOpen.value = true
    }

    function handlePhotoCapture(photoData) {
        damagePhoto.value = typeof photoData === 'string' ? photoData : (photoData?.preview || null)
        damageForm.hasPhoto = true
    }

    function retakeDamagePhoto() {
        damagePhoto.value = null
        damageForm.hasPhoto = false
        isCameraOpen.value = true
    }

    return {
        submitMismatch,
        submitDamage,
        openDamageCamera,
        handlePhotoCapture,
        retakeDamagePhoto,
    }
}
