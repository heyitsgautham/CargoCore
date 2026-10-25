// Pending restock requests the manager approves or rejects from the assets tab.
import { computed, ref } from 'vue'
import { apiUrl } from '@/config/api'

export function useRestockReview({ store, authStore, showNotification }) {
    const restockModalOpen = ref(false)
    const restockItems = ref([])
    const escalatedRestockCount = computed(() => restockItems.value.filter(i => i._escalated).length)

    const openRestockModal = async () => {
        restockItems.value = []
        restockModalOpen.value = true
        try {
            const res = await fetch(apiUrl('api/v1/inventory/restock-requests?status_filter=PENDING&page=1&page_size=100'), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}` }
            })
            if (res.ok) {
                const data = await res.json()
                const items = (data.items || []).map(item => ({
                    ...item,
                    _escalated: (item.manager_notes || '').includes('[ESCALATED]')
                }))
                // Sort: escalated first, then by created_at desc
                items.sort((a, b) => {
                    if (a._escalated && !b._escalated) return -1
                    if (!a._escalated && b._escalated) return 1
                    return new Date(b.created_at) - new Date(a.created_at)
                })
                restockItems.value = items
            }
        } catch(e) {
            console.error("Failed to fetch pending restock requests", e)
        }
    }

    const resolveRestock = async (id, status, fundingSource) => {
        try {
            const res = await fetch(apiUrl(`api/v1/inventory/restock-requests/${id}/status`), {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status, funding_source: fundingSource || 'APP_REVENUE' })
            })
            if (res.ok) {
                showNotification(`Restock request ${status.toLowerCase()}`, status === 'APPROVED' ? 'success' : 'info')
                restockItems.value = restockItems.value.filter(i => i.id !== id)
                if (status === 'APPROVED') {
                    store.refresh() // refresh inventory metrics
                }
            } else {
                showNotification('Failed to update request', 'error')
            }
        } catch(e) {
            console.error(e)
            showNotification('Error updating request', 'error')
        }
    }

    return { restockModalOpen, restockItems, escalatedRestockCount, openRestockModal, resolveRestock }
}
