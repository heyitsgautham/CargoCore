// Requests for new packing materials: list them by status, submit one, and pre-fill the
// add stock form from an approved request.
import { ref, computed, reactive } from 'vue'
import { getStoredAccessToken } from '@/config/api'

export function useMaterialRequests({
    API_BASE,
    addForm,
    customCategories,
    persistCustomCategories,
    showAddModal,
    toastMsg,
}) {
    // Material Request state
    const showRequestMaterialModal = ref(false)
    const submittingRequest = ref(false)
    const myMaterialRequests = ref([])
    const materialRequestForm = reactive({
        name: '',
        unit: 'pcs',
        suggestedRate: null,
        reason: ''
    })

    // Computed filters for material requests
    const approvedMaterials = computed(() => myMaterialRequests.value.filter(r => r.status === 'APPROVED'))
    const pendingMaterials = computed(() => myMaterialRequests.value.filter(r => r.status === 'PENDING'))
    const rejectedMaterials = computed(() => myMaterialRequests.value.filter(r => r.status === 'REJECTED'))

    async function fetchMyMaterialRequests() {
        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/inventory/material-requests`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const data = await res.json()
                myMaterialRequests.value = data.items || []
            }
        } catch (e) {
            console.error('Failed to fetch material requests:', e)
        }
    }

    async function submitMaterialRequest() {
        if (!materialRequestForm.name) return

        submittingRequest.value = true
        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/inventory/material-requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    material_name: materialRequestForm.name,
                    unit: materialRequestForm.unit,
                    suggested_rate: materialRequestForm.suggestedRate || null,
                    reason: materialRequestForm.reason || null
                })
            })

            if (res.ok) {
                showRequestMaterialModal.value = false
                materialRequestForm.name = ''
                materialRequestForm.unit = 'pcs'
                materialRequestForm.suggestedRate = null
                materialRequestForm.reason = ''
                toastMsg.value = 'Material request submitted!'
                setTimeout(() => { toastMsg.value = '' }, 3000)
                fetchMyMaterialRequests()
            } else {
                const err = await res.json()
                alert(err.detail || 'Failed to submit request')
            }
        } catch (e) {
            console.error('Failed to submit material request:', e)
            alert('Failed to submit request')
        } finally {
            submittingRequest.value = false
        }
    }

    // Quick add approved material to inventory - pre-fills the Add Stock form
    function addApprovedMaterial(req) {
        // Close the Request Material modal first
        showRequestMaterialModal.value = false

        // Generate SKU from material name
        const sku = req.material_name.toUpperCase().replace(/\s+/g, '-').substring(0, 10)

        // Pre-fill the add form
        addForm.sku = sku
        addForm.name = req.material_name
        addForm.category = 'Packing Materials'
        addForm.stock = 0
        addForm.weight = 0
        addForm.zone = 'A'

        // Ensure Packing Materials category exists
        if (!customCategories.value.includes('Packing Materials')) {
            customCategories.value.push('Packing Materials')
            persistCustomCategories()
        }

        // Open the add modal
        showAddModal.value = true
    }

    return {
        showRequestMaterialModal,
        submittingRequest,
        myMaterialRequests,
        materialRequestForm,
        approvedMaterials,
        pendingMaterials,
        rejectedMaterials,
        fetchMyMaterialRequests,
        submitMaterialRequest,
        addApprovedMaterial,
    }
}
