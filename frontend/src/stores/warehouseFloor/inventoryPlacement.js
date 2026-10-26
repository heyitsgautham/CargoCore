// Fetching inventory and placing each item in a rack cell, adding overflow racks when the floor is full.
import { API_BASE_URL } from '@/config/api'

export function useInventoryPlacement({
    floors,
    groups,
    idCounter,
    isLoading,
    loadError,
    products,
    rackMap,
    racks,
    sections,
}) {
    async function fetchInventoryItems(authToken, warehouseId) {
        const pageSize = 100
        let page = 1
        let allRows = []

        while (true) {
            let url = `${API_BASE_URL}/api/v1/inventory?page=${page}&page_size=${pageSize}`
            if (warehouseId) {
                url += `&warehouse_id=${warehouseId}`
            }

            const res = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            })

            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            const data = await res.json()
            const rows = Array.isArray(data) ? data : (data.items || [])
            allRows = allRows.concat(rows)

            if (Array.isArray(data)) break

            const total = Number(data.total ?? 0)
            const reachedEndByCount = rows.length < pageSize
            const reachedEndByTotal = total > 0 && allRows.length >= total

            if (reachedEndByCount || reachedEndByTotal) break
            page += 1
        }

        return allRows.map(item => ({
            sku: item.sku || item.id?.slice(0, 8).toUpperCase(),
            name: item.name || item.product_name || 'Item',
            qty: Number(item.quantity_on_hand ?? item.quantity ?? item.stock_quantity ?? item.quantity_available ?? 0),
            unit: item.unit || item.unit_of_measure || 'pcs',
            category: item.category || item.product_category || 'General',
            raw: item
        }))
    }

    function ensureBaseFloorPlanStructure() {
        if (!floors.value.length) {
            floors.value = [{ id: 1, label: 'Floor 1' }]
        }

        if (sections.value.length && racks.value.length) {
            return
        }

        const floorId = floors.value[0]?.id || 1
        const autoGroupId = 'g-auto-general'
        const existingGeneral = groups.value.find(g => g.id === autoGroupId)
        if (!existingGeneral) {
            groups.value.push({
                id: autoGroupId,
                floorId,
                name: 'General',
                color: '#3b82f6',
                internalGap: 2,
                externalGap: 10
            })
        }

        const sectionId = `s${idCounter.value++}`
        const rackId = `r${idCounter.value++}`
        sections.value.push({
            id: sectionId,
            floorId,
            groupId: autoGroupId,
            label: 'GENERAL-01',
            x: 40,
            y: 60,
            w: 130,
            h: 150
        })
        racks.value.push({
            id: rackId,
            sectionId,
            label: 'Rack-01',
            x: 20,
            y: 25,
            w: 230,
            h: 130,
            cols: 4,
            rows: 3
        })
    }

    function createOverflowRack() {
        const floorId = floors.value[0]?.id || 1
        const autoGroupId = 'g-auto-general'
        let autoGroup = groups.value.find(g => g.id === autoGroupId)
        if (!autoGroup) {
            autoGroup = {
                id: autoGroupId,
                floorId,
                name: 'General',
                color: '#3b82f6',
                internalGap: 2,
                externalGap: 10
            }
            groups.value.push(autoGroup)
        }

        const maxX = sections.value.length
            ? Math.max(...sections.value.map(s => s.x + s.w))
            : 40

        const sectionId = `s${idCounter.value++}`
        const rackId = `r${idCounter.value++}`
        const nextRackNumber = racks.value.length + 1

        sections.value.push({
            id: sectionId,
            floorId,
            groupId: autoGroupId,
            label: `GENERAL-${String(nextRackNumber).padStart(2, '0')}`,
            x: maxX + 40,
            y: 60,
            w: 130,
            h: 150
        })
        racks.value.push({
            id: rackId,
            sectionId,
            label: `Rack-${String(nextRackNumber).padStart(2, '0')}`,
            x: 20,
            y: 25,
            w: 230,
            h: 130,
            cols: 4,
            rows: 3
        })

        return rackId
    }

    function findFreeSlot(occupiedCells) {
        for (const rack of racks.value) {
            const rows = rack.rows || 3
            const cols = rack.cols || 4
            const capacity = rows * cols
            for (let cell = 1; cell <= capacity; cell++) {
                const key = `${rack.id}:${cell}`
                if (!occupiedCells.has(key)) {
                    return { rackId: rack.id, cell }
                }
            }
        }

        const rackId = createOverflowRack()
        return { rackId, cell: 1 }
    }

    function toFloorProduct(item, placement, previousProduct = null) {
        return {
            sku: item.sku,
            name: item.name,
            orderId: previousProduct?.orderId || '--',
            rma: previousProduct?.rma || null,
            rackId: placement.rackId,
            cell: placement.cell,
            qty: item.qty,
            unit: item.unit
        }
    }

    async function syncInventoryToFloorPlan(authToken, warehouseId) {
        try {
            const items = await fetchInventoryItems(authToken, warehouseId)
            if (!items.length) {
                products.value = []
                return true
            }

            ensureBaseFloorPlanStructure()

            const existingBySku = new Map()
            for (const product of products.value) {
                if (!existingBySku.has(product.sku)) {
                    existingBySku.set(product.sku, product)
                }
            }

            const occupiedCells = new Set()
            const nextProducts = []

            for (const item of items) {
                const previous = existingBySku.get(item.sku)
                let placement = null

                if (previous) {
                    const rack = rackMap.value.get(previous.rackId)
                    const capacity = (rack?.rows || 0) * (rack?.cols || 0)
                    const isValidCell = rack && previous.cell >= 1 && previous.cell <= capacity
                    const key = `${previous.rackId}:${previous.cell}`
                    if (isValidCell && !occupiedCells.has(key)) {
                        placement = { rackId: previous.rackId, cell: previous.cell }
                    }
                }

                if (!placement) {
                    placement = findFreeSlot(occupiedCells)
                }

                occupiedCells.add(`${placement.rackId}:${placement.cell}`)
                nextProducts.push(toFloorProduct(item, placement, previous))
            }

            products.value = nextProducts
            return true
        } catch (err) {
            console.error('FloorPlan: Failed to sync inventory into floor plan:', err)
            return false
        }
    }

    /**
     * Fetch real inventory from backend and build the floor plan layout.
     * Groups are created per category. Sections per group. Each section gets
     * one rack, and inventory items fill the rack cells in order.
     */
    async function initializeFromAPI(authToken, warehouseId = null) {
        isLoading.value = true
        loadError.value = ''
        try {
            const items = await fetchInventoryItems(authToken, warehouseId)
            if (!items.length) return

            // Reset everything
            groups.value = []
            sections.value = []
            racks.value = []
            products.value = []
            // Keep only Floor 1 by default, reset extras
            floors.value = [{ id: 1, label: 'Floor 1' }]

            const colorPalette = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1']

            // Group inventory items by category
            const categoryMap = new Map()
            items.forEach(item => {
                const cat = item.category || 'General'
                if (!categoryMap.has(cat)) categoryMap.set(cat, [])
                categoryMap.get(cat).push(item)
            })

            let sectionX = 40
            let colorIdx = 0
            let sCounter = 1
            let rCounter = 1

            categoryMap.forEach((catItems, categoryName) => {
                // Create a group per category
                const groupId = `g-${categoryName.replace(/\s+/g, '_').toLowerCase()}`
                const color = colorPalette[colorIdx % colorPalette.length]
                colorIdx++

                groups.value.push({
                    id: groupId,
                    floorId: 1,
                    name: categoryName,
                    color,
                    internalGap: 2,
                    externalGap: 10
                })

                // Split items into sections of max 12 items each (4 cols × 3 rows)
                const ITEMS_PER_SECTION = 12
                const COLS = 4
                const ROWS = 3
                const chunks = []
                for (let i = 0; i < catItems.length; i += ITEMS_PER_SECTION) {
                    chunks.push(catItems.slice(i, i + ITEMS_PER_SECTION))
                }

                chunks.forEach((chunk, chunkIdx) => {
                    const sectionId = `s${sCounter++}`
                    const rackId = `r${rCounter++}`

                    sections.value.push({
                        id: sectionId,
                        floorId: 1,
                        groupId,
                        label: `${categoryName.substring(0, 8).toUpperCase()}-${String(chunkIdx + 1).padStart(2, '0')}`,
                        x: sectionX,
                        y: 60,
                        w: 130,
                        h: 150
                    })
                    sectionX += 145

                    racks.value.push({
                        id: rackId,
                        sectionId,
                        label: `Rack-${String(rCounter - 1).padStart(2, '0')}`,
                        x: 20,
                        y: 25,
                        w: 230,
                        h: 130,
                        cols: COLS,
                        rows: ROWS
                    })

                    // Fill cells with real inventory items
                    chunk.forEach((item, itemIdx) => {
                        products.value.push({
                            sku: item.sku,
                            name: item.name,
                            orderId: '--',
                            rma: null,
                            rackId,
                            cell: itemIdx + 1,
                            qty: item.qty,
                            unit: item.unit
                        })
                    })
                })

                // Add spacer between groups
                sectionX += 30
            })

        } catch (err) {
            console.error('FloorPlan: Failed to load inventory:', err)
            loadError.value = 'Could not load inventory. Use Edit mode to add sections manually.'
        } finally {
            isLoading.value = false
        }
    }

    return {
        fetchInventoryItems,
        ensureBaseFloorPlanStructure,
        createOverflowRack,
        findFreeSlot,
        toFloorProduct,
        syncInventoryToFloorPlan,
        initializeFromAPI,
     }
}
