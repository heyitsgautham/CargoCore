import { onMounted, onUnmounted } from 'vue'

export function categoriesStorageKey(warehouseId) {
    return `warehouse-manager-inventory-categories:${warehouseId || 'default'}`
}

function readCustomCategories(warehouseId) {
    try {
        const raw = JSON.parse(window.localStorage.getItem(categoriesStorageKey(warehouseId)) || '[]')
        return Array.isArray(raw) ? raw : []
    } catch {
        return []
    }
}

/**
 * Keeps the floor plan in step with the Inventory page.
 * Custom categories created there become floor groups, and inventory changes re-sync the racks.
 */
export function useInventorySync({ store, authStore, activeFloor }) {
    function getWarehouseId() {
        return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null
    }

    /** Add each custom inventory category as a floor group unless one with that name exists. */
    function syncInventoryCategoriesToFloor() {
        const floorId = activeFloor.value || store.floors[0]?.id || 1
        const colorPalette = store.presetColors
        const existingNames = new Set(store.groupsByFloor(floorId).map(g => g.name.toLowerCase()))

        readCustomCategories(getWarehouseId()).forEach((catName, idx) => {
            if (typeof catName !== 'string' || !catName.trim()) return
            const name = catName.trim()
            if (existingNames.has(name.toLowerCase())) return
            const color = colorPalette[idx % colorPalette.length] || '#6366f1'
            store.addGroup(floorId, { name, color, internalGap: 2, externalGap: 10 })
            existingNames.add(name.toLowerCase())
        })
    }

    async function syncFloorInventory() {
        await store.syncInventoryToFloorPlan(authStore.authToken, getWarehouseId())
        syncInventoryCategoriesToFloor()
    }

    async function onInventoryUpdated(event) {
        const eventWarehouseId = event?.detail?.warehouseId
        const currentWarehouseId = getWarehouseId()
        if (!currentWarehouseId || !eventWarehouseId || eventWarehouseId === currentWarehouseId) {
            await syncFloorInventory()
        }
    }

    onMounted(() => {
        window.addEventListener('warehouse-inventory-updated', onInventoryUpdated)
        window.addEventListener('warehouse-category-created', syncInventoryCategoriesToFloor)
    })
    onUnmounted(() => {
        window.removeEventListener('warehouse-inventory-updated', onInventoryUpdated)
        window.removeEventListener('warehouse-category-created', syncInventoryCategoriesToFloor)
    })

    return { getWarehouseId, syncInventoryCategoriesToFloor, syncFloorInventory, onInventoryUpdated }
}
