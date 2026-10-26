// Choosing an order in the issue dialog: loads its packing items, matches them to stock
// and suggests quantities.
import { getEmoji, inventoryIdTokenFromSku, keywordsForSku, normalizeSku } from './materialRecords'
import { apiUrl } from '@/config/api'

export function useIssueOrderSelection({
    activeOrders,
    allInventory,
    authStore,
    issueForm,
    packingItems,
    recommendedMaterials,
    selectedOrderDetails,
    showIssueModal,
    showSuccess,
}) {
    async function onOrderSelected() {
        const selected = activeOrders.value.find(o => o.tracking_code === issueForm.orderId)
        selectedOrderDetails.value = selected
        recommendedMaterials.value = []

        if (!selected) return

        // Fetch the customer's actual material selections saved at booking time
        try {
            const res = await fetch(apiUrl(`api/v1/orders/${selected.id}/items`), {
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            })
            if (res.ok) {
                const orderItems = await res.json()
                console.log(`[PackingMaterials] Order ${selected.tracking_code} items from DB:`, orderItems)
                const withQty = (orderItems || []).filter(item => item.quantity > 0)

                // Always stop here — either show customer-selected items or nothing.
                // Never fall through to the formula so we never show items the customer didn't pick.
                if (withQty.length === 0) {
                    console.log(`[PackingMaterials] No items with qty>0 stored for ${selected.tracking_code} — customer selected no packing materials`)
                    recommendedMaterials.value = []
                    return
                }
                console.log(`[PackingMaterials] Items to resolve:`, withQty)

                const headers2 = { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }

                // Resolve each order item to a real WM inventory item
                const resolved = await Promise.all(withQty.map(async (item) => {
                    const itemInventoryIdToken = inventoryIdTokenFromSku(item.sku)

                    // 1. Exact SKU or legacy PKG-<inventory-id> match in local packing inventory
                    let invItem = packingItems.value.find(p => normalizeSku(p.sku) === normalizeSku(item.sku))
                        || packingItems.value.find(p => normalizeSku(p.id) === itemInventoryIdToken)
                    if (invItem) {
                        return { id: invItem.id, sku: item.sku, name: invItem.name, emoji: getEmoji(invItem.name, ''), unit: invItem.unit || 'pcs', suggestedQty: item.quantity, stock: invItem.stock ?? null }
                    }

                    // 2. Exact SKU or legacy PKG-<inventory-id> match in full local inventory
                    const raw = allInventory.value.find(p => normalizeSku(p.sku) === normalizeSku(item.sku))
                        || allInventory.value.find(p => normalizeSku(p.id) === itemInventoryIdToken)
                    if (raw) {
                        return { id: raw.id, sku: item.sku, name: raw.name, emoji: getEmoji(raw.name, ''), unit: raw.unit || 'pcs', suggestedQty: item.quantity, stock: raw.quantity_on_hand ?? null }
                    }

                    // 3. Keyword name match in packing inventory (PKG-* legacy SKUs)
                    const keywords = keywordsForSku(item.sku)
                    const kwMatch = packingItems.value.find(p => {
                        const text = `${p.name || ''} ${p.sku || ''} ${p.category || ''}`.toLowerCase()
                        return keywords.some(kw => text.includes(kw))
                    })
                    if (kwMatch) {
                        return { id: kwMatch.id, sku: item.sku, name: kwMatch.name, emoji: getEmoji(kwMatch.name, ''), unit: kwMatch.unit || 'pcs', suggestedQty: item.quantity, stock: kwMatch.stock ?? null }
                    }

                    // 4. Backend SKU lookup — handles cross-warehouse SKUs not in local allInventory
                    try {
                        const skuRes = await fetch(apiUrl(`api/v1/inventory?sku=${encodeURIComponent(item.sku)}&page_size=1`), { headers: headers2 })
                        if (skuRes.ok) {
                            const skuData = await skuRes.json()
                            const found = (skuData.items || [])[0]
                            if (found) {
                                console.log(`[PackingMaterials] Resolved ${item.sku} via backend SKU lookup:`, found.name)
                                return { id: found.id, sku: item.sku, name: found.name, emoji: getEmoji(found.name, ''), unit: found.unit || 'pcs', suggestedQty: item.quantity, stock: found.quantity_on_hand ?? null }
                            }
                        }
                    } catch { /* ignore */ }

                    console.warn(`[PackingMaterials] Could not resolve inventory item for SKU: ${item.sku}`)
                    return null
                }))

                recommendedMaterials.value = resolved.filter(Boolean)
                console.log(`[PackingMaterials] Resolved ${recommendedMaterials.value.length}/${withQty.length} items`)
                return
            }
        } catch { /* network error — show nothing */ }

        // API failed entirely — show nothing rather than guessing
        recommendedMaterials.value = []
    }

    function applyRecommendedQuantities() {
        recommendedMaterials.value.forEach(rec => {
            issueForm.items[rec.id] = rec.suggestedQty
        })
        showSuccess('Recommended quantities applied')
    }

    function closeIssueModal() {
        showIssueModal.value = false
        issueForm.orderId = ''
        issueForm.issuedToLabourerId = ''
        issueForm.items = {}
        selectedOrderDetails.value = null
        recommendedMaterials.value = []
    }

    return { onOrderSelected, applyRecommendedQuantities, closeIssueModal }
}
