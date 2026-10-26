import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useInventoryPlacement } from './warehouseFloor/inventoryPlacement'
import { useFloorPlanPersistence } from './warehouseFloor/persistence'
import { useFloorPlanEditing } from './warehouseFloor/editing'

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

    // One counter for every generated section and rack id, shared by placement and editing.
    const idCounter = { value: 100 }

    const { syncInventoryToFloorPlan, initializeFromAPI } = useInventoryPlacement({
        floors,
        groups,
        idCounter,
        isLoading,
        loadError,
        products,
        rackMap,
        racks,
        sections,
    })

    const { saveFloorPlan, loadFloorPlan } = useFloorPlanPersistence({
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
    })

    const {
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
    } = useFloorPlanEditing({
        comparedZones,
        floors,
        groups,
        idCounter,
        products,
        racks,
        sections,
    })

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
