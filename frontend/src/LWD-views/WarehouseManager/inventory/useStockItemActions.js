// Editing, relocating and labelling a stock item, and showing the item a scan found.
import { getStoredAccessToken } from '@/config/api'

export function useStockItemActions({
    API_BASE,
    editItem,
    fetchInventory,
    getWarehouseId,
    inventory,
    moveItem,
    newLocation,
    scanError,
    scanResult,
    showEditModal,
    showMoveModal,
    showToast,
}) {
    function openEditModal(item) {
        editItem.value = item
        showEditModal.value = true
    }

    function saveEdit() {
        showEditModal.value = false
        showToast(`${editItem.value.sku} updated`)
    }

    function openMoveModal(item) {
        moveItem.value = item
        newLocation.zone = item.zone
        newLocation.aisle = item.aisle
        newLocation.rack = item.rack
        newLocation.shelf = item.shelf
        newLocation.bin = item.bin
        showMoveModal.value = true
    }

    async function confirmMove() {
        const item = moveItem.value
        const warehouseId = getWarehouseId()
        const newAisle = `${newLocation.zone}-${newLocation.aisle}`

        // Optimistically update UI immediately
        item.zone = newLocation.zone
        item.aisle = newLocation.aisle
        item.rack = newLocation.rack
        item.shelf = newLocation.shelf
        item.bin = newLocation.bin
        showMoveModal.value = false

        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/inventory/${item.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    aisle: newAisle,
                    shelf: newLocation.shelf,
                    bin: newLocation.bin
                })
            })

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`)
            }

            // Re-fetch inventory to stay in sync with backend
            await fetchInventory()

            // Notify Floor Plan to re-sync
            window.dispatchEvent(new CustomEvent('warehouse-inventory-updated', {
                detail: { warehouseId, sku: item.sku }
            }))

            showToast(`${item.sku} moved to ${newLocation.zone}-${newLocation.aisle}-${newLocation.rack}-${newLocation.shelf}-${newLocation.bin}`)
        } catch (e) {
            console.error('Failed to save move:', e)
            // Revert optimistic update on failure
            await fetchInventory()
            showToast(`Failed to move ${item.sku} — please try again`)
        }
    }

    function printLabel(item) {
        showToast(`Label printed for ${item.sku} — ${item.name}`)
    }

    function lookupScan(scannedSku) {
        scanResult.value = null
        scanError.value = ''

        // Safety check just in case
        if (!scannedSku) return

        const found = inventory.value.find(i => i.sku.toLowerCase() === scannedSku.toLowerCase())
        if (found) {
            scanResult.value = found
        } else {
            scanError.value = `SKU "${scannedSku}" not found in inventory`
        }
    }

    function clearScan() {
        scanResult.value = null
        scanError.value = ''
    }

    return {
        openEditModal,
        saveEdit,
        openMoveModal,
        confirmMove,
        printLabel,
        lookupScan,
        clearScan,
    }
}
