// Issuing packing materials to an order and recording the issuance log.
import { mergeIssuanceLogs, normalizeIssuanceLog, writeCachedIssuanceLogs } from './materialRecords'
import { apiUrl } from '@/config/api'

export function useIssueSubmit({
    activeOrders,
    allInventory,
    authStore,
    canSubmitIssue,
    closeIssueModal,
    getWarehouseId,
    issuableItemsForSelectedOrder,
    issuanceLogs,
    issueForm,
    issueValidationErrors,
    issuingMaterials,
    labourers,
    selectedIssuingLabourer,
    showError,
    showSuccess,
}) {
    async function submitIssue() {
        if (!canSubmitIssue.value) {
            if (issueValidationErrors.value.length > 0) {
                showError(issueValidationErrors.value[0])
            }
            return
        }

        issuingMaterials.value = true
        const issuedAt = new Date().toISOString()
        const warehouseId = getWarehouseId()
        const issuingLabourer = selectedIssuingLabourer.value
        const issuedToName = issuingLabourer?.name || issuingLabourer?.full_name || 'Selected Labourer'

        // Find the selected order to get its ID
        const selectedOrder = activeOrders.value.find(o => o.tracking_code === issueForm.orderId)
        const referenceOrderId = selectedOrder?.id || null

        try {
            const headers = {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }

            let successCount = 0
            let errorCount = 0
            const newLogs = []

            const allIssuableItems = issuableItemsForSelectedOrder()

            for (const item of allIssuableItems) {
                const qty = issueForm.items[item.id]
                if (qty && qty > 0) {
                    // Call inventory movement API
                    const response = await fetch(apiUrl('api/v1/inventory/movements'), {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({
                            item_id: item.id,
                            movement_type: 'ISSUE',
                            quantity: qty,
                            reference_order_id: referenceOrderId
                        })
                    })

                    if (response.ok) {
                        successCount++
                        const movement = await response.json().catch(() => null)
                        newLogs.push(normalizeIssuanceLog(movement ? {
                            ...movement,
                            issuedTo: issuedToName,
                        } : {
                            id: `local-${item.id}-${Date.now()}`,
                            movement_type: 'ISSUE',
                            quantity: qty,
                            reference_order_tracking: issueForm.orderId,
                            item_name: item.name,
                            issuedTo: issuedToName,
                            created_at: issuedAt,
                        }))

                        // Update local stock count
                        const inv = allInventory.value.find(i => i.id === item.id)
                        if (inv) {
                            if (inv.quantity_on_hand !== undefined) inv.quantity_on_hand = Math.max(0, inv.quantity_on_hand - qty)
                            else if (inv.quantity !== undefined) inv.quantity = Math.max(0, inv.quantity - qty)
                            else if (inv.stock_quantity !== undefined) inv.stock_quantity = Math.max(0, inv.stock_quantity - qty)
                            else if (inv.quantity_available !== undefined) inv.quantity_available = Math.max(0, inv.quantity_available - qty)
                        }
                    } else {
                        errorCount++
                        console.error('Failed to issue material:', item.name, await response.text())
                    }
                }
            }

            if (
                successCount > 0 &&
                issuingLabourer &&
                referenceOrderId &&
                String(issuingLabourer.assigned_order_id || '') === String(referenceOrderId)
            ) {
                const releaseResponse = await fetch(apiUrl(`api/v1/labourers/${issuingLabourer.id}`), {
                    method: 'PUT',
                    headers,
                    body: JSON.stringify({ assigned_order_id: null })
                })

                if (releaseResponse.ok) {
                    labourers.value = labourers.value.map(labourer =>
                        String(labourer.id) === String(issuingLabourer.id)
                            ? {
                                ...labourer,
                                assigned_order_id: null,
                                assigned_order_tracking: null,
                                assigned_order_substatus: null,
                                status: 'AVAILABLE',
                            }
                            : labourer
                    )
                } else {
                    console.error('Failed to release labourer after materials issue:', await releaseResponse.text())
                }
            }

            if (newLogs.length > 0) {
                issuanceLogs.value = mergeIssuanceLogs(issuanceLogs.value, newLogs)
                writeCachedIssuanceLogs(warehouseId, issuanceLogs.value)
            }

            closeIssueModal()

            if (successCount > 0 && errorCount === 0) {
                showSuccess(`Materials issued successfully (${successCount} items)`)
            } else if (successCount > 0) {
                showSuccess(`Partially issued: ${successCount} items (${errorCount} failed)`)
            } else {
                showError('Failed to issue materials')
            }

        } catch (error) {
            console.error('Error issuing materials:', error)
            showError('Error issuing materials')
        } finally {
            issuingMaterials.value = false
        }
    }

    return { submitIssue }
}
