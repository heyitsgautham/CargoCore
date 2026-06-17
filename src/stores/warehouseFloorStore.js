import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * @typedef {Object} Floor
 * @property {number} id
 * @property {string} label
 */

/**
 * @typedef {Object} Group
 * @property {string} id
 * @property {number} floorId
 * @property {string} name
 * @property {string} color
 * @property {number} internalGap
 * @property {number} externalGap
 */

/**
 * @typedef {Object} Section
 * @property {string} id
 * @property {number} floorId
 * @property {string|null} groupId
 * @property {string} label
 * @property {number} x
 * @property {number} y
 * @property {number} w
 * @property {number} h
 * @property {boolean} [manualPosition]
 */

/**
 * @typedef {Object} Rack
 * @property {string} id
 * @property {string} sectionId
 * @property {string} label
 * @property {number} x
 * @property {number} y
 * @property {number} w
 * @property {number} h
 * @property {number} rows
 * @property {number} cols
 */

/**
 * @typedef {Object} CellProduct
 * @property {string} sku
 * @property {string} name
 * @property {string} orderId
 * @property {string|null} rma
 * @property {string} rackId
 * @property {number} cell
 * @property {number} qty
 * @property {string} unit
 */

export const useWarehouseFloorStore = defineStore('warehouseFloor', () => {
    // ── Core Data ──────────────────────────────────────────────
    const floors = ref([
        { id: 1, label: 'Floor 1' },
    ])

    const groups = ref([])

    const sections = ref([])

    const racks = ref([])

    const products = ref([])

    const presetColors = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1']

    const comparedZones = ref([])

    // ── Lookup Maps (computed, rebuilt on data change) ──────────
    const sectionMap = computed(() => {
        const m = new Map()
        sections.value.forEach(s => m.set(s.id, s))
        return m
    })

    const rackMap = computed(() => {
        const m = new Map()
        racks.value.forEach(r => m.set(r.id, r))
        return m
    })

    const groupMap = computed(() => {
        const m = new Map()
        groups.value.forEach(g => m.set(g.id, g))
        return m
    })

    // ── Filtered Getters ──────────────────────────────────────────
    function sectionsByFloor(floorId) {
        return sections.value.filter(s => s.floorId === floorId)
    }

    function groupsByFloor(floorId) {
        return groups.value.filter(g => g.floorId === floorId)
    }

    function racksBySection(sectionId) {
        return racks.value.filter(r => r.sectionId === sectionId)
    }

    function productsByRack(rackId) {
        return products.value.filter(p => p.rackId === rackId)
    }

    function productsBySection(sectionId) {
        const rids = racksBySection(sectionId).map(r => r.id)
        return products.value.filter(p => rids.includes(p.rackId))
    }

    function productsByFloor(floorId) {
        const sids = sectionsByFloor(floorId).map(s => s.id)
        const rids = racks.value.filter(r => sids.includes(r.sectionId)).map(r => r.id)
        return products.value.filter(p => rids.includes(p.rackId))
    }

    function racksOnFloor(floorId) {
        const sids = sectionsByFloor(floorId).map(s => s.id)
        return racks.value.filter(r => sids.includes(r.sectionId))
    }

    function sectionsByGroup(groupId) {
        return sections.value.filter(s => s.groupId === groupId)
    }

    function getGroupColor(section) {
        if (!section) return '#6b7280'
        const g = groupMap.value.get(section.groupId)
        return g?.color || '#6b7280'
    }

    function getGroupName(groupId) {
        return groupMap.value.get(groupId)?.name || ''
    }

    function getCellProduct(rackId, cellIndex) {
        return products.value.find(p => p.rackId === rackId && p.cell === cellIndex) || null
    }

    /** Get the full breadcrumb path for a product */
    function resolveProductPath(product) {
        const rack = rackMap.value.get(product.rackId)
        if (!rack) return null
        const section = sectionMap.value.get(rack.sectionId)
        if (!section) return null
        const floor = floors.value.find(f => f.id === section.floorId)
        const group = groupMap.value.get(section.groupId)
        const row = Math.ceil(product.cell / rack.cols)
        const col = ((product.cell - 1) % rack.cols) + 1
        return {
            floor: floor?.label || 'Unknown',
            group: group?.name || 'Uncategorized',
            section: section.label,
            rack: rack.label,
            cell: `R${row}C${col}`,
            cellIndex: product.cell
        }
    }

    /** Generate a cell grid array for a rack */
    function generateCellGrid(rack) {
        const cells = []
        for (let row = 1; row <= rack.rows; row++) {
            for (let col = 1; col <= rack.cols; col++) {
                const index = (row - 1) * rack.cols + col
                cells.push({
                    id: `${rack.id}:R${row}C${col}`,
                    index,
                    row,
                    col,
                    product: getCellProduct(rack.id, index)
                })
            }
        }
        return cells
    }

    /** Get the group boundary rectangle for visual grouping */
    function getGroupBoundary(group) {
        const secs = sectionsByGroup(group.id).filter(s => s.floorId === group.floorId)
        if (!secs.length) return { opacity: 0 }
        const pad = 12
        const mnX = Math.min(...secs.map(s => s.x)) - pad
        const mnY = Math.min(...secs.map(s => s.y)) - pad
        const mxX = Math.max(...secs.map(s => s.x + s.w)) + pad
        const mxY = Math.max(...secs.map(s => s.y + s.h)) + pad
        return {
            left: mnX + 'px',
            top: mnY + 'px',
            width: (mxX - mnX) + 'px',
            height: (mxY - mnY) + 'px',
            borderColor: group.color + '50'
        }
    }

    const isLoading = ref(false)
    const loadError = ref('')
    const isSaving = ref(false)
    const lastSavedAt = ref(null)

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

            const res = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/floor-plan`, {
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
            const res = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}`, {
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

    async function fetchInventoryItems(authToken, warehouseId) {
        const pageSize = 100
        let page = 1
        let allRows = []

        while (true) {
            let url = `http://localhost:8000/api/v1/inventory?page=${page}&page_size=${pageSize}`
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

        const sectionId = `s${_idCounter++}`
        const rackId = `r${_idCounter++}`
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

        const sectionId = `s${_idCounter++}`
        const rackId = `r${_idCounter++}`
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

    // ── Mutations ──────────────────────────────────────────────
    let _idCounter = 100

    function addFloor() {
        const nid = Math.max(...floors.value.map(f => f.id), 0) + 1
        floors.value.push({ id: nid, label: `Floor ${nid}` })
        return nid
    }

    function deleteFloor(floorId) {
        if (floors.value.length <= 1) return false
        const rackIds = racks.value
            .filter(r => sections.value.find(s => s.id === r.sectionId)?.floorId === floorId)
            .map(r => r.id)
        products.value = products.value.filter(p => !rackIds.includes(p.rackId))
        racks.value = racks.value.filter(r => !rackIds.includes(r.id))
        sections.value = sections.value.filter(s => s.floorId !== floorId)
        groups.value = groups.value.filter(g => g.floorId !== floorId)
        floors.value = floors.value.filter(f => f.id !== floorId)
        return true
    }

    function renameFloor(floorId, newLabel) {
        const f = floors.value.find(fl => fl.id === floorId)
        if (f && newLabel.trim()) f.label = newLabel.trim()
    }

    function addSection(floorId) {
        const id = 'c' + (_idCounter++)
        sections.value.push({
            id,
            floorId,
            groupId: null,
            label: `SEC-${_idCounter}`,
            x: 80 + Math.random() * 200,
            y: 80 + Math.random() * 200,
            w: 120,
            h: 140
        })
        return id
    }

    function deleteSection(sectionId) {
        const rackIds = racks.value.filter(r => r.sectionId === sectionId).map(r => r.id)
        products.value = products.value.filter(p => !rackIds.includes(p.rackId))
        racks.value = racks.value.filter(r => r.sectionId !== sectionId)
        sections.value = sections.value.filter(s => s.id !== sectionId)
    }

    function addRack(sectionId) {
        const id = 'r' + (_idCounter++)
        racks.value.push({
            id,
            sectionId,
            label: `Rack-${_idCounter}`,
            x: 30 + Math.random() * 100,
            y: 30 + Math.random() * 100,
            w: 180,
            h: 110,
            cols: 4,
            rows: 3
        })
        return id
    }

    function deleteRack(rackId) {
        products.value = products.value.filter(p => p.rackId !== rackId)
        racks.value = racks.value.filter(r => r.id !== rackId)
    }

    function addGroup(floorId, data) {
        const id = 'g' + Date.now()
        groups.value.push({ id, floorId, ...data })
        return id
    }

    function updateGroup(groupId, data) {
        const g = groups.value.find(g => g.id === groupId)
        if (g) Object.assign(g, data)
    }

    function deleteGroup(groupId) {
        sections.value.forEach(s => { if (s.groupId === groupId) s.groupId = null })
        groups.value = groups.value.filter(g => g.id !== groupId)
    }

    function addComparedZone(zoneId) {
        if (!comparedZones.value.find(z => z.id === zoneId)) {
            const zone = groups.value.find(g => g.id === zoneId)
            if (zone) {
                comparedZones.value.push(zone)
            }
        }
    }

    function removeComparedZone(zoneId) {
        comparedZones.value = comparedZones.value.filter(z => z.id !== zoneId)
    }

    return {
        // State
        floors,
        groups,
        sections,
        racks,
        products,
        presetColors,
        comparedZones,
        isLoading,
        loadError,
        isSaving,
        lastSavedAt,
        // Maps
        sectionMap,
        rackMap,
        groupMap,
        // Getters
        sectionsByFloor,
        groupsByFloor,
        racksBySection,
        productsByRack,
        productsBySection,
        productsByFloor,
        racksOnFloor,
        sectionsByGroup,
        getGroupColor,
        getGroupName,
        getCellProduct,
        resolveProductPath,
        generateCellGrid,
        getGroupBoundary,
        // Mutations
        addFloor,
        deleteFloor,
        renameFloor,
        addSection,
        deleteSection,
        addRack,
        deleteRack,
        addGroup,
        updateGroup,
        deleteGroup,
        addComparedZone,
        removeComparedZone,
        initializeFromAPI,
        syncInventoryToFloorPlan,
        saveFloorPlan,
        loadFloorPlan
    }
})
