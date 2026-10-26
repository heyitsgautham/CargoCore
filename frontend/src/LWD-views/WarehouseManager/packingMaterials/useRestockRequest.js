// Requesting a restock of packing materials, and escalating it to the logistics manager.
import { apiUrl } from '@/config/api'

export function useRestockRequest({
    allInventory,
    authStore,
    escalateMsg,
    lowStockItems,
    restockForm,
    restocking,
    showError,
    showRestockModal,
    showSuccess,
}) {
    async function submitRestock() {
        restocking.value = true

        try {
            const headers = {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }

            let successCount = 0
            let errorCount = 0

            for (const item of lowStockItems.value) {
                const qty = restockForm[item.id]
                if (qty && qty > 0) {
                    // Call inventory movement API with RESTOCK type
                    const response = await fetch(apiUrl('api/v1/inventory/movements'), {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({
                            item_id: item.id,
                            movement_type: 'RESTOCK',
                            quantity: qty,
                            reference_order_id: null
                        })
                    })

                    if (response.ok) {
                        successCount++
                        // Update local stock count
                        const inv = allInventory.value.find(i => i.id === item.id)
                        if (inv) {
                            if (inv.quantity_on_hand !== undefined) inv.quantity_on_hand += qty
                            else if (inv.quantity !== undefined) inv.quantity += qty
                            else if (inv.stock_quantity !== undefined) inv.stock_quantity += qty
                            else if (inv.quantity_available !== undefined) inv.quantity_available += qty
                        }
                    } else {
                        errorCount++
                        console.error('Failed to restock:', item.name)
                    }
                }
            }

            showRestockModal.value = false

            if (successCount > 0 && errorCount === 0) {
                showSuccess(`Restock completed (${successCount} items)`)
            } else if (successCount > 0) {
                showSuccess(`Partial restock: ${successCount} items (${errorCount} failed)`)
            } else if (errorCount === 0) {
                showSuccess('Restock request submitted')
            } else {
                showError('Failed to restock materials')
            }

        } catch (error) {
            console.error('Error restocking materials:', error)
            showError('Error restocking materials')
        } finally {
            restocking.value = false
        }
    }

    function escalateRestock() {
        showRestockModal.value = false
        escalateMsg.value = 'Low stock items escalated for urgent procurement'
        setTimeout(() => { escalateMsg.value = '' }, 3000)
    }

    return { submitRestock, escalateRestock }
}
