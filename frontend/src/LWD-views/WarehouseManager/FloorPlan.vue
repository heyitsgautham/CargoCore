<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <!-- ═══ Header ═══ -->
        <FloorPlanHeader />

        <!-- ═══ Main Area ═══ -->
        <div class="flex-1 flex gap-4 min-h-0">
            <div class="flex-1 glass-panel rounded-xl relative overflow-hidden flex flex-col">

                <EditToolbar />

                <!-- Breadcrumb -->
                <FloorBreadcrumb :level="zoom.state.level" :floor-label="currentFloorLabel"
                    :section-label="activeSection?.label" :section-color="activeSectionColor"
                    :category-name="activeSectionCategoryName" :rack-label="activeRack?.label"
                    @navigate="onBreadcrumbNavigate" />

                <!-- ═══ Canvas (fixed container with scrollable inner grid) ═══ -->
                <div class="flex-1 relative canvas-grid min-h-0">

                    <!-- Scrollable inner area (sections/racks scroll inside here) -->
                    <div ref="canvasRef" class="absolute inset-0 overflow-auto" @mousedown="onCanvasMouseDown"
                        @mousemove="onCanvasMouseMove" @mouseup="onCanvasMouseUp" @mouseleave="onCanvasMouseUp">

                        <!-- Size wrapper (sets scrollable area) -->
                        <div :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }">
                            <!-- Scale wrapper (visually scales all content) -->
                            <div
                                :style="{ transform: 'scale(' + canvasZoom + ')', transformOrigin: '0 0', opacity: zoom.transitionOpacity.value, width: (100 / canvasZoom) + '%', height: (100 / canvasZoom) + '%' }">

                              <!-- Inner offset wrapper — creates positioned context with breathing room -->
                              <div class="relative" style="margin-top: 100px; margin-left: 20px; width: calc(100% - 20px); height: calc(100% - 100px);">

                                <!-- ══════ FLOOR LEVEL ══════ -->
                                <template v-if="zoom.state.level === 'FLOOR'">

                                    <!-- Group boundaries -->
                                    <div v-for="g in currentGroups" :key="'gb' + g.id"
                                        class="absolute rounded-xl border-2 border-dashed pointer-events-none"
                                        :style="store.getGroupBoundary(g)"
                                        :class="{ 'opacity-0': store.sectionsByGroup(g.id).length === 0 }">
                                        <div class="absolute -top-5 left-2 text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                                            :style="{ background: g.color + '30', color: g.color }">{{ g.name }}</div>
                                    </div>

                                    <!-- Section cards -->
                                    <SectionCard v-for="sec in currentSections" :key="sec.id" :section="sec"
                                        :group-color="store.getGroupColor(sec)"
                                        :category-name="store.getGroupName(sec.groupId)"
                                        :rack-count="store.racksBySection(sec.id).length"
                                        :product-count="store.productsBySection(sec.id).length"
                                        :is-selected="canvas.selectedElement.value?.id === sec.id"
                                        :is-highlighted="search.highlightedSectionIds.value.includes(sec.id)"
                                        :is-edit-mode="editMode"
                                        :highlight-products="search.getHighlightProductsForSection(sec.id)"
                                        @click="onSectionClick(sec)" @dragstart="onElementDragStart($event, sec)"
                                        @resizestart="onElementResizeStart($event, sec)" />
                                </template>

                                <!-- ══════ SECTION LEVEL ══════ -->
                                <template v-if="zoom.state.level === 'SECTION'">
                                    <RackGridView v-for="rack in activeRacks" :key="rack.id" :rack="rack"
                                        :cell-grid="store.generateCellGrid(rack)"
                                        :total-products="store.productsByRack(rack.id).length"
                                        :is-selected="canvas.selectedElement.value?.id === rack.id"
                                        :is-highlighted="search.highlightedRackIds.value.includes(rack.id)"
                                        :is-edit-mode="editMode"
                                        :highlight-products="search.getHighlightProductsForRack(rack.id)"
                                        :highlighted-cell-keys="search.highlightedCellKeys.value"
                                        :use-absolute-position="true" @rackclick="onRackClick(rack)"
                                        @cellclick="onCellClick" @dragstart="onElementDragStart($event, rack)"
                                        @resizestart="onElementResizeStart($event, rack)" />
                                </template>

                                <!-- ══════ RACK LEVEL ══════ -->
                                <template v-if="zoom.state.level === 'RACK' && activeRack">
                                    <div class="absolute grid gap-2 p-4 bg-purple-500/5 rounded-xl border border-purple-500/20"
                                        :style="rackCellGridStyle">
                                        <div v-for="cell in activeRackCellGrid" :key="cell.id"
                                            class="rounded-lg border-2 flex flex-col items-center justify-center text-xs relative transition-all duration-200 cursor-pointer"
                                            :class="getRackCellClasses(cell)"
                                            style="min-width: 120px; min-height: 80px;"
                                            @click.stop="onRackLevelCellClick(cell, $event)">
                                            <span class="text-[9px] font-mono opacity-50 absolute top-1 left-1.5">R{{
                                                cell.row }}C{{ cell.col }}</span>
                                            <template v-if="cell.product">
                                                <span class="font-bold text-sm">📦</span>
                                                <span
                                                    class="font-bold text-[10px] mt-0.5 text-center leading-tight px-1">{{
                                                        cell.product.name }}</span>
                                                <span class="text-[8px] opacity-60">{{ cell.product.qty }} {{
                                                    cell.product.unit }}</span>
                                            </template>
                                            <template v-else>
                                                <span class="text-lg opacity-20">○</span>
                                                <span class="text-[8px] opacity-30">Empty</span>
                                            </template>
                                        </div>
                                    </div>
                                </template>

                              </div><!-- end inner offset wrapper -->
                            </div><!-- end scale wrapper -->
                        </div><!-- end size wrapper -->
                    </div><!-- end scrollable area -->

                    <CellTooltip />

                    <CanvasOverlayControls />

                </div><!-- end canvas container -->

                <CanvasStatusOverlay />

            </div>

            <FloorSidebar />
        </div>

        <!-- ═══ Group Modal ═══ -->
        <GroupModal :visible="showGroupModal || !!editingGroup" :editing="editingGroup"
            :preset-colors="store.presetColors" @close="showGroupModal = false; editingGroup = null" @save="onSaveGroup"
            @delete="onDeleteGroup" />

        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-2 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold text-sm">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import EditToolbar from './floorplan/EditToolbar.vue'
import CanvasStatusOverlay from './floorplan/CanvasStatusOverlay.vue'
import FloorPlanHeader from './floorplan/FloorPlanHeader.vue'
import CellTooltip from './floorplan/CellTooltip.vue'
import CanvasOverlayControls from './floorplan/CanvasOverlayControls.vue'
import FloorSidebar from './floorplan/FloorSidebar.vue'
import { floorPlanPageKey } from './floorplan/floorPlanPageContext'
import { ref, computed, watch, nextTick, onMounted, onUnmounted, provide } from 'vue'
import { useWarehouseFloorStore } from '@/stores/warehouseFloorStore'
import { useZoomStateMachine } from './floorplan/composables/useZoomStateMachine'
import { useCanvasInteraction } from './floorplan/composables/useCanvasInteraction'
import { useFloorSearch } from './floorplan/composables/useFloorSearch'
import { useCanvasZoom } from './floorplan/composables/useCanvasZoom'
import { useInventorySync } from './floorplan/composables/useInventorySync'
import { useAuthStore } from '@/stores/authStore'

import SectionCard from './floorplan/components/SectionCard.vue'
import RackGridView from './floorplan/components/RackGridView.vue'
import FloorBreadcrumb from './floorplan/components/FloorBreadcrumb.vue'
import GroupModal from './floorplan/components/GroupModal.vue'

const store = useWarehouseFloorStore()
const authStore = useAuthStore()
const zoom = useZoomStateMachine()
const canvas = useCanvasInteraction()
const search = useFloorSearch(store, zoom)

const activeFloor = ref(1)
const { getWarehouseId, syncInventoryCategoriesToFloor, syncFloorInventory } =
    useInventorySync({ store, authStore, activeFloor })
const editMode = ref(false)
const showGroupModal = ref(false)
const editingGroup = ref(null)
const toastMsg = ref('')
const canvasRef = ref(null)
const floorNameInput = ref(null)
const editingFloorId = ref(null)
const tooltipData = ref(null)
const tooltipAnchor = ref({ x: 0, y: 0 })

// Track whether current mouse action is an element drag (to avoid starting pan)
const isDraggingElement = ref(false)

// ── Computed ──
const currentFloorLabel = computed(() => store.floors.find(f => f.id === activeFloor.value)?.label || 'Floor')
const currentSections = computed(() => store.sectionsByFloor(activeFloor.value))
const currentGroups = computed(() => store.groupsByFloor(activeFloor.value))
const activeSection = computed(() => store.sectionMap.get(zoom.state.activeSectionId))
const activeSectionColor = computed(() => store.getGroupColor(activeSection.value))
const activeSectionCategoryName = computed(() => store.getGroupName(activeSection.value?.groupId))
const activeRack = computed(() => store.rackMap.get(zoom.state.activeRackId))
const activeRacks = computed(() => zoom.state.activeSectionId ? store.racksBySection(zoom.state.activeSectionId) : [])
const activeSectionProducts = computed(() => zoom.state.activeSectionId ? store.productsBySection(zoom.state.activeSectionId) : [])
const activeRackCellGrid = computed(() => activeRack.value ? store.generateCellGrid(activeRack.value) : [])
const selectedElementType = computed(() => {
    const el = canvas.selectedElement.value
    return el?.rows !== undefined ? 'rack' : 'section'
})

/** Position rack cells as a grid that starts at (40, 40) on the canvas */
const rackCellGridStyle = computed(() => {
    if (!activeRack.value) return {}
    return {
        left: '40px',
        top: '40px',
        gridTemplateColumns: `repeat(${activeRack.value.cols}, minmax(120px, 1fr))`
    }
})

/** Floating tooltip clamped within the canvas viewport */
const { canvasZoom, canvasWidth, canvasHeight, canvasZoomPercent, zoomCanvas, recenterCanvas } =
    useCanvasZoom({ zoom, currentSections, activeRacks, activeRack, canvasRef })
const tooltipFloatStyle = computed(() => {
    if (!tooltipData.value || !canvasRef.value) return { display: 'none' }
    const cRect = canvasRef.value.getBoundingClientRect()
    const tw = 280, th = 160
    let x = tooltipAnchor.value.x
    let y = tooltipAnchor.value.y + 14
    if (x + tw > cRect.width - 10) x = cRect.width - tw - 10
    if (x < 10) x = 10
    if (y + th > cRect.height - 10) y = tooltipAnchor.value.y - th - 14
    if (y < 10) y = 10
    return { left: x + 'px', top: y + 'px' }
})

// ── Canvas Mouse Handlers (simple drag for edit mode) ──
function onCanvasMouseDown(e) {
    const isOnBackground = e.target === canvasRef.value ||
        e.target.closest('.canvas-grid') === canvasRef.value && !e.target.closest('.absolute.select-none')
    if (isOnBackground) {
        canvas.deselect()
        tooltipData.value = null
    }
}

function onCanvasMouseMove(e) {
    if (editMode.value && canvas.isDragging.value) {
        canvas.onMove(e, 1, canvasRef.value)
    }
}

function onCanvasMouseUp() {
    canvas.onUp()
    isDraggingElement.value = false
}

// ── Element Interactions ──
function onSectionClick(sec) {
    if (editMode.value) { canvas.selectElement(sec); return }
    tooltipData.value = null
    zoom.zoomToSection(sec.id)
}

function onRackClick(rack) {
    if (editMode.value) { canvas.selectElement(rack); return }
    tooltipData.value = null
    zoom.zoomToRack(rack.id)
}

function onCellClick({ cell, rackId, event }) {
    if (cell.product) showTooltipAt(cell, rackId, event)
}

function onRackLevelCellClick(cell, event) {
    if (cell.product) showTooltipAt(cell, activeRack.value?.id, event)
}

function showTooltipAt(cell, rackId, event) {
    const rack = store.rackMap.get(rackId)
    const section = rack ? store.sectionMap.get(rack.sectionId) : null
    if (tooltipData.value?.cell?.id === cell.id && tooltipData.value?.rackId === rackId) {
        tooltipData.value = null
        return
    }
    const cRect = canvasRef.value?.getBoundingClientRect()
    if (cRect && event) {
        tooltipAnchor.value = { x: event.clientX - cRect.left, y: event.clientY - cRect.top }
    }
    tooltipData.value = { cell, rackId, product: cell.product, rackLabel: rack?.label || '?', sectionLabel: section?.label || '?' }
}

function getRackCellClasses(cell) {
    const isSelected = tooltipData.value?.cell?.id === cell.id
    const isHighlighted = search.highlightedCellKeys.value.includes(`${activeRack.value?.id}:${cell.index}`)
    if (isSelected) return 'border-primary bg-primary/20 text-primary ring-2 ring-primary/40 shadow-lg shadow-primary/10'
    if (isHighlighted) return 'border-primary bg-primary/15 text-primary animate-pulse'
    if (cell.product) return 'border-purple-400/50 bg-purple-500/15 text-purple-600 dark:text-purple-300 hover:bg-purple-500/25 hover:border-purple-400 hover:shadow-md'
    return 'border-gray-200 dark:border-white/10 bg-white/50 dark:bg-white/3 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'
}

function onElementDragStart(event, element) {
    if (!editMode.value) return
    isDraggingElement.value = true
    canvas.startDrag(event, element)
}

function onElementResizeStart(event, element) {
    if (!editMode.value) return
    isDraggingElement.value = true
    canvas.startResize(event, element)
}

// ── Navigation ──
function onBreadcrumbNavigate(targetLevel) {
    tooltipData.value = null
    if (targetLevel === 'FLOOR') zoom.zoomToFloor()
    else if (targetLevel === 'SECTION' && zoom.state.level === 'RACK') zoom.levelBack()
}

async function handleLevelBack() {
    tooltipData.value = null
    await zoom.levelBack()
}

// ── Search ──
function onFocusSearchResult(result) {
    tooltipData.value = null
    search.focusSearchResult(result, activeFloor.value, switchFloor, null)
}

// ── Floor CRUD ──
function switchFloor(floorId) {
    activeFloor.value = floorId
    zoom.zoomToFloor()
    canvas.deselect()
    tooltipData.value = null
    search.clearSearchNav()
}

function onAddFloor() { const nid = store.addFloor(); activeFloor.value = nid; zoom.zoomToFloor(); showToast(`Floor ${nid} added`) }
function onDeleteFloor() { if (store.deleteFloor(activeFloor.value)) { activeFloor.value = store.floors[0].id; zoom.zoomToFloor(); showToast('Floor deleted') } }
function onAddSection() { store.addSection(activeFloor.value); showToast('Section added') }
function onAddRack() { if (!zoom.state.activeSectionId) return; store.addRack(zoom.state.activeSectionId); showToast('Rack added') }
function onDeleteSelected() {
    const el = canvas.selectedElement.value
    if (!el) return
    if (el.rows !== undefined) store.deleteRack(el.id)
    else store.deleteSection(el.id)
    canvas.deselect()
    showToast('Deleted')
}

// ── Group Ops ──
function onSaveGroup(data) {
    if (editingGroup.value) { store.updateGroup(editingGroup.value.id, data); showToast('Category updated'); editingGroup.value = null }
    else { store.addGroup(activeFloor.value, data); showToast('Category created'); showGroupModal.value = false }
}
function onDeleteGroup() { if (editingGroup.value) { store.deleteGroup(editingGroup.value.id); editingGroup.value = null; showToast('Category deleted') } }

// ── Save/Load Floor Plan ──
async function onSaveFloorPlan() {
    const warehouseId = authStore.currentWarehouse?.id
    if (!warehouseId) {
        showToast('No warehouse selected')
        return
    }
    const success = await store.saveFloorPlan(authStore.authToken, warehouseId)
    if (success) {
        showToast('Floor plan saved!')
    } else {
        showToast('Failed to save floor plan')
    }
}

async function toggleEditMode() {
    if (editMode.value) {
        // Exiting edit mode - auto-save
        const warehouseId = authStore.currentWarehouse?.id
        if (warehouseId) {
            await store.saveFloorPlan(authStore.authToken, warehouseId)
            showToast('Changes saved')
        }
    }
    editMode.value = !editMode.value
}

function showToast(m) { toastMsg.value = m; setTimeout(() => { toastMsg.value = '' }, 2500) }

// ── Floor Name Editor ──
function startFloorRename(floorId) {
    editingFloorId.value = floorId
    nextTick(() => {
        const input = Array.isArray(floorNameInput.value) ? floorNameInput.value[0] : floorNameInput.value
        input?.focus()
        input?.select()
    })
}

function finishFloorRename(e, floorId) {
    const val = e.target.value.trim()
    if (val) store.renameFloor(floorId, val)
    editingFloorId.value = null
}

// ── Sidebar product click → drill-down to that product ──
function onSidebarProductClick(product) {
    const rack = store.rackMap.get(product.rackId)
    const section = rack ? store.sectionMap.get(rack.sectionId) : null
    if (!section) return
    const result = {
        product,
        rackId: product.rackId,
        sectionId: rack.sectionId,
        sectionLabel: section.label,
        rackLabel: rack.label,
        floorId: section.floorId
    }
    search.focusSearchResult(result, activeFloor.value, switchFloor, null)
}

/** Get a human-readable location label for a product */
function getProductLocationLabel(product) {
    const rack = store.rackMap.get(product.rackId)
    const section = rack ? store.sectionMap.get(rack.sectionId) : null
    const floor = section ? store.floors.find(f => f.id === section.floorId) : null
    return [floor?.label, section?.label, rack?.label].filter(Boolean).join(' › ')
}

// ── Keyboard ──
function onKeyDown(e) {
    if (e.key === 'Escape') {
        if (tooltipData.value) tooltipData.value = null
        else if (zoom.state.level !== 'FLOOR') handleLevelBack()
        else canvas.deselect()
    }
}

// Reset scroll position when zoom level changes
watch(() => zoom.state.level, () => {
    nextTick(() => {
        if (canvasRef.value) {
            canvasRef.value.scrollTo({ left: 0, top: 0, behavior: 'smooth' })
        }
    })
})

onMounted(async () => {
    window.addEventListener('keydown', onKeyDown)
    // Load from saved floor plan or initialize from inventory
    const warehouseId = getWarehouseId()
    if (store.sections.length === 0) {
        if (warehouseId) {
            await store.loadFloorPlan(authStore.authToken, warehouseId)
        } else {
            await store.initializeFromAPI(authStore.authToken, null)
        }
    } else {
        await syncFloorInventory()
    }
    syncInventoryCategoriesToFloor()
})
onUnmounted(() => {
    window.removeEventListener('keydown', onKeyDown)
})

provide(floorPlanPageKey, {
    activeFloor,
    activeRack,
    activeRacks,
    activeSection,
    activeSectionProducts,
    authStore,
    canvas,
    canvasZoomPercent,
    currentFloorLabel,
    currentGroups,
    currentSections,
    editMode,
    editingFloorId,
    editingGroup,
    finishFloorRename,
    floorNameInput,
    getProductLocationLabel,
    getWarehouseId,
    onAddFloor,
    onAddRack,
    onAddSection,
    onDeleteFloor,
    onDeleteSelected,
    onFocusSearchResult,
    onSaveFloorPlan,
    onSidebarProductClick,
    recenterCanvas,
    search,
    selectedElementType,
    showGroupModal,
    startFloorRename,
    store,
    switchFloor,
    toggleEditMode,
    tooltipData,
    tooltipFloatStyle,
    zoom,
    zoomCanvas,
})
</script>

<style scoped src="./floorplan/FloorPlan.css"></style>

<!-- Unscoped styles so search-highlight animation reaches child components -->
<style>
.search-highlight {
    animation: pulse-hl 1s ease-in-out infinite !important;
}
</style>
