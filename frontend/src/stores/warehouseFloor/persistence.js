// Saving and loading the floor plan layout through the warehouse API.
import { API_BASE_URL } from '@/config/api'

export function useFloorPlanPersistence({
    floors,
    groups,
    initializeFromAPI,
    isLoading,
    isSaving,
    lastSavedAt,
    loadError,
    products,
    racks,
    sections,
    syncInventoryToFloorPlan,
}) {
    /**
     * Save the current floor plan to the backend warehouse.floor_plan_json
     */
    async function saveFloorPlan(authToken, warehouseId) {
        if (!warehouseId) {
            console.warn('FloorPlan: No warehouse ID provided for save')
            return false
        }

        isSaving.value = true
        try {
            const floorPlanData = {
                floors: floors.value,
                groups: groups.value,
                sections: sections.value,
                racks: racks.value,
                products: products.value,
                savedAt: new Date().toISOString()
            }

            const res = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/floor-plan`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ floor_plan_json: floorPlanData })
            })

            if (!res.ok) throw new Error(`HTTP ${res.status}`)

            lastSavedAt.value = new Date()
            console.log('FloorPlan: Saved successfully')
            return true
        } catch (err) {
            console.error('FloorPlan: Failed to save:', err)
            return false
        } finally {
            isSaving.value = false
        }
    }

    /**
     * Load the floor plan from the backend warehouse.floor_plan_json
     * Falls back to initializeFromAPI if no saved floor plan exists
     */
    async function loadFloorPlan(authToken, warehouseId) {
        if (!warehouseId) {
            console.warn('FloorPlan: No warehouse ID provided for load')
            return initializeFromAPI(authToken, null)
        }

        isLoading.value = true
        loadError.value = ''

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            })

            if (!res.ok) throw new Error(`HTTP ${res.status}`)

            const warehouse = await res.json()

            // If warehouse has a saved floor plan, load it
            if (warehouse.floor_plan_json &&
                warehouse.floor_plan_json.floors &&
                warehouse.floor_plan_json.sections) {

                const fp = warehouse.floor_plan_json
                floors.value = fp.floors || [{ id: 1, label: 'Floor 1' }]
                groups.value = fp.groups || []
                sections.value = fp.sections || []
                racks.value = fp.racks || []
                products.value = fp.products || []

                await syncInventoryToFloorPlan(authToken, warehouseId)
                console.log('FloorPlan: Loaded from saved floor plan')
                return true
            }

            // No saved floor plan, initialize from inventory
            console.log('FloorPlan: No saved floor plan, initializing from inventory')
            await initializeFromAPI(authToken, warehouseId)
            return true

        } catch (err) {
            console.error('FloorPlan: Failed to load warehouse:', err)
            loadError.value = 'Could not load warehouse data.'
            // Fall back to inventory initialization
            await initializeFromAPI(authToken, warehouseId)
            return false
        } finally {
            isLoading.value = false
        }
    }

    return { saveFloorPlan, loadFloorPlan }
}
