// Flow 1 of returns: the warehouse reviews a customer's damage photos and sends the
// manager a severity, a genuineness call and a recommended settlement.
import { API_BASE_URL } from '@/config/api'
import { ref } from 'vue'

export function useDamageReview({ authStore, submittingReview, toastMsg }) {
    // Flow 1 (damage review) state
    const damageReviewQueue = ref([])  // claims with status = 'Under Review' and flow_type = 'photo_review'
    const selectedDamageReport = ref(null)
    const reviewPhotoPreview = ref(null)
    const damageReviewForm = ref({ severity: '', genuineness: '', recommendedSettlement: '', remarks: '' })

    function selectDamageReport(claim) {
        selectedDamageReport.value = claim
        damageReviewForm.value = { severity: '', genuineness: '', recommendedSettlement: '', remarks: '' }
    }

    async function submitDamageReview() {
        if (!selectedDamageReport.value || submittingReview.value) return
        submittingReview.value = true
        try {
            const headers = {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
            // PATCH the damage report with WM assessment and set status to Claims Reviewed
            const reviewRes = await fetch(
                `${API_BASE_URL}/api/v1/damage-reports/${selectedDamageReport.value.id}/review`,
                {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        damage_severity: damageReviewForm.value.severity,
                        is_genuine: damageReviewForm.value.genuineness,
                        recommended_settlement: damageReviewForm.value.recommendedSettlement,
                        remarks: damageReviewForm.value.remarks,
                        new_status: 'Claims Reviewed',
                    })
                }
            )
            if (!reviewRes.ok) throw new Error(`HTTP ${reviewRes.status}`)
            // Remove from local queue
            damageReviewQueue.value = damageReviewQueue.value.filter(c => c.id !== selectedDamageReport.value.id)
            selectedDamageReport.value = null
            damageReviewForm.value = { severity: '', genuineness: '', recommendedSettlement: '', remarks: '' }
            toastMsg.value = 'Damage review submitted to Logistics Manager.'
        } catch (e) {
            console.error('submitDamageReview error:', e)
            toastMsg.value = 'Failed to submit damage review.'
        } finally {
            submittingReview.value = false
            setTimeout(() => { toastMsg.value = '' }, 2500)
        }
    }

    async function fetchDamageReviewQueue() {
        if (!authStore.authToken) return
        try {
            const headers = { 'Authorization': `Bearer ${authStore.authToken}` }
            const res = await fetch(
                `${API_BASE_URL}/api/v1/damage-reports?status=Under%20Review&flow_type=photo_review&page_size=50`,
                { headers }
            )
            if (res.ok) {
                const data = await res.json()
                damageReviewQueue.value = data.items || data || []
            } else {
                console.warn(`Damage review queue fetch failed: HTTP ${res.status}`)
            }
        } catch (e) {
            console.error('fetchDamageReviewQueue error:', e)
        }
    }

    return {
        damageReviewQueue,
        selectedDamageReport,
        reviewPhotoPreview,
        damageReviewForm,
        selectDamageReport,
        submitDamageReview,
        fetchDamageReviewQueue,
    }
}
