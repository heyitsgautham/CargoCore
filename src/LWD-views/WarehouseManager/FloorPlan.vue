<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <!-- ═══ Header ═══ -->
        <div class="flex justify-between items-center flex-wrap gap-2">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Warehouse Floor Plan</h2>
                <p class="text-sm text-gray-500 mt-0.5">Click a section to view its racks & cells</p>
            </div>

            <SearchBar v-model="search.searchQuery.value" :results="search.searchResults.value"
                @search="search.onSearch" @focus-result="onFocusSearchResult"
                @clear="search.clearSearchNav()" />

            <div class="flex items-center gap-2">
                <div
                    class="bg-gray-100 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-1 flex">
                    <template v-for="f in store.floors" :key="f.id">
                        <input v-if="editingFloorId === f.id" ref="floorNameInput"
                            :value="f.label"
                            @blur="finishFloorRename($event, f.id)"
                            @keydown.enter="$event.target.blur()"
                            @keydown.escape="editingFloorId = null"
                            class="px-3 py-1 text-sm font-bold rounded bg-primary text-background-dark shadow-lg outline-none border-b-2 border-white/50 w-24" />
                        <button v-else
                            class="px-3 py-1 text-sm font-bold rounded transition-colors"
                            :class="activeFloor === f.id ? 'bg-primary text-background-dark shadow-lg' : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'"
                            @click="switchFloor(f.id)"
                            @dblclick.stop="startFloorRename(f.id)">{{ f.label }}</button>
                    </template>
                </div>
                <button @click="onAddFloor"
                    class="w-7 h-7 flex items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20">
                    <span class="material-symbols-outlined text-[16px]">add</span>
                </button>
                <button v-if="store.floors.length > 1" @click="onDeleteFloor"
                    class="w-7 h-7 flex items-center justify-center rounded-lg bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20">
                    <span class="material-symbols-outlined text-[16px]">delete</span>
                </button>
                <button @click="toggleEditMode"
                    class="py-1 px-3 rounded-lg text-sm font-bold flex items-center gap-1 border transition-colors"
                    :class="editMode ? 'bg-primary/20 text-primary border-primary/30' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-white/10'">
                    <span class="material-symbols-outlined text-[16px]">{{ editMode ? 'lock_open' : 'edit' }}</span>
                    {{ editMode ? 'Editing' : 'Edit' }}
                </button>
                <button v-if="editMode" @click="onSaveFloorPlan"
                    class="py-1 px-3 rounded-lg text-sm font-bold flex items-center gap-1 border transition-colors"
                    :class="store.isSaving ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 border-gray-300 dark:border-gray-600 cursor-wait' : 'bg-green-500/20 text-green-600 border-green-500/30 hover:bg-green-500/30'"
                    :disabled="store.isSaving">
                    <span class="material-symbols-outlined text-[16px]">{{ store.isSaving ? 'hourglass_empty' : 'save' }}</span>
                    {{ store.isSaving ? 'Saving...' : 'Save' }}
                </button>
                <button v-if="editMode" @click="showGroupModal = true"
                    class="bg-primary hover:bg-primary/90 text-white font-bold py-1 px-3 rounded-lg text-sm flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">add</span>Category
                </button>
            </div>
        </div>

        <!-- ═══ Main Area ═══ -->
        <div class="flex-1 flex gap-4 min-h-0">
            <div class="flex-1 glass-panel rounded-xl relative overflow-hidden flex flex-col">

                <!-- Edit toolbar -->
                <div v-if="editMode"
                    class="flex items-center gap-2 px-4 py-2 border-b border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/20 z-10">
                    <button v-if="zoom.state.level === 'FLOOR'" @click="onAddSection"
                        class="bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 px-3 py-1 rounded text-xs font-bold border border-blue-500/20">
                        <span class="material-symbols-outlined text-[14px] align-middle">view_column</span> + Section
                    </button>
                    <button v-if="zoom.state.level === 'SECTION'" @click="onAddRack"
                        class="bg-purple-500/10 hover:bg-purple-500/20 text-purple-500 px-3 py-1 rounded text-xs font-bold border border-purple-500/20">
                        <span class="material-symbols-outlined text-[14px] align-middle">grid_view</span> + Rack
                    </button>
                    <div class="flex-1"></div>
                    <label class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer">
                        <input type="checkbox" v-model="canvas.snapToGrid.value" class="accent-primary" />Snap
                    </label>
                    <button v-if="canvas.selectedElement.value" @click="onDeleteSelected"
                        class="bg-red-500/10 text-red-500 px-3 py-1 rounded text-xs font-bold border border-red-500/20">
                        <span class="material-symbols-outlined text-[14px] align-middle">delete</span>
                    </button>
                </div>

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

                    <!-- ═══ Floating Tooltip (pinned to canvas container) ═══ -->
                    <div v-if="tooltipData" class="absolute z-[100] pointer-events-auto" :style="tooltipFloatStyle">
                        <div
                            class="bg-gray-900/95 dark:bg-black/95 text-white p-4 rounded-xl shadow-2xl border border-primary/30 min-w-[240px] max-w-[320px] backdrop-blur-sm">
                            <div class="text-[9px] text-gray-500 mb-1.5 flex items-center gap-1 flex-wrap">
                                <span>{{ currentFloorLabel }}</span><span>›</span>
                                <span>{{ activeSection?.label || tooltipData.sectionLabel }}</span><span>›</span>
                                <span>{{ tooltipData.rackLabel }}</span><span>›</span>
                                <span class="text-primary font-bold">R{{ tooltipData.cell.row }}C{{
                                    tooltipData.cell.col
                                    }}</span>
                            </div>
                            <div class="font-bold text-primary text-sm mb-1">{{ tooltipData.product.name }}</div>
                            <div class="space-y-0.5 text-[11px]">
                                <div class="flex justify-between"><span class="text-gray-400">SKU</span><span
                                        class="font-bold text-gray-200">{{ tooltipData.product.sku }}</span></div>
                                <div class="flex justify-between"><span class="text-gray-400">Qty</span><span
                                        class="font-bold text-white">{{ tooltipData.product.qty }} {{
                                            tooltipData.product.unit }}</span>
                                </div>
                                <div class="flex justify-between"><span class="text-gray-400">Order</span><span
                                        class="font-bold text-gray-200">{{ tooltipData.product.orderId }}</span>
                                </div>
                                <div v-if="tooltipData.product.rma" class="flex justify-between"><span
                                        class="text-yellow-400">⚠
                                        RMA</span><span class="font-bold text-yellow-400">{{ tooltipData.product.rma
                                        }}</span></div>
                            </div>
                            <button @click="tooltipData = null"
                                class="absolute top-2 right-2 text-gray-500 hover:text-white w-5 h-5 flex items-center justify-center rounded-full hover:bg-white/10">
                                <span class="material-symbols-outlined text-[14px]">close</span>
                            </button>
                        </div>
                    </div>

                    <!-- ═══ Floor Name (pinned bottom-left) ═══ -->
                    <div
                        class="absolute bottom-3 left-3 z-50 flex items-center gap-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur rounded-lg shadow-lg border border-gray-200 dark:border-white/10 px-3 py-1.5">
                        <span class="material-symbols-outlined text-primary text-[16px]">layers</span>
                        <span class="text-xs font-bold text-gray-900 dark:text-white">{{ currentFloorLabel }}</span>
                        <span v-if="zoom.state.level !== 'FLOOR'" class="text-[10px] text-gray-500">› {{
                            zoom.state.level === 'SECTION' ?
                                activeSection?.label : activeRack?.label }}</span>
                    </div>

                    <!-- ═══ Zoom Controls (pinned bottom-right) ═══ -->
                    <div
                        class="absolute bottom-3 right-3 flex items-center gap-1 bg-white/90 dark:bg-gray-800/90 backdrop-blur rounded-lg shadow-lg border border-gray-200 dark:border-white/10 p-1 z-50">
                        <button @click="zoomCanvas(-1)"
                            class="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-white/10 text-gray-600 dark:text-gray-300"
                            title="Zoom out">
                            <span class="material-symbols-outlined text-[16px]">remove</span>
                        </button>
                        <span
                            class="px-1.5 text-[11px] font-bold text-gray-600 dark:text-gray-300 min-w-[36px] text-center">{{
                                canvasZoomPercent }}%</span>
                        <button @click="zoomCanvas(1)"
                            class="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-white/10 text-gray-600 dark:text-gray-300"
                            title="Zoom in">
                            <span class="material-symbols-outlined text-[16px]">add</span>
                        </button>
                        <div class="w-px h-5 bg-gray-300 dark:bg-white/10 mx-0.5"></div>
                        <button @click="recenterCanvas"
                            class="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-white/10 text-gray-600 dark:text-gray-300"
                            title="Recenter">
                            <span class="material-symbols-outlined text-[16px]">filter_center_focus</span>
                        </button>
                    </div>

                </div><!-- end canvas container -->

                <!-- Loading overlay -->
                <div v-if="store.isLoading"
                    class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50/80 dark:bg-gray-900/80 backdrop-blur-sm z-20 rounded-xl">
                    <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-3"></div>
                    <div class="text-gray-600 dark:text-gray-400 text-sm">Loading floor plan from inventory...</div>
                </div>

                <!-- Empty state (no sections) -->
                <div v-else-if="!store.isLoading && currentSections.length === 0"
                    class="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10 pointer-events-none">
                    <span class="material-symbols-outlined text-5xl text-gray-400 opacity-40">warehouse</span>
                    <div class="text-center">
                        <div class="text-gray-500 font-bold">No sections on this floor</div>
                        <div class="text-gray-400 text-sm mt-1">
                            {{ store.loadError || 'Add inventory items via the Inventory page, then reload. Or use Edit mode to add sections manually.' }}
                        </div>
                    </div>
                    <button v-if="!store.isLoading" @click="store.initializeFromAPI(authStore.authToken, getWarehouseId())"
                        class="pointer-events-auto mt-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px]">refresh</span> Reload from Inventory
                    </button>
                </div>

            </div>

            <!-- ═══ Sidebar ═══ -->
            <div class="w-64 flex flex-col gap-3">
                <PropertiesPanel v-if="editMode" :element="canvas.selectedElement.value"
                    :element-type="selectedElementType" :categories="currentGroups" />

                <div class="glass-panel rounded-xl p-4 flex-1 overflow-hidden flex flex-col gap-2">
                    <div class="flex items-center justify-between">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1">
                            <span class="material-symbols-outlined text-[16px] text-yellow-600 dark:text-yellow-400">folder</span>Categories
                        </h3>
                        <button @click="showGroupModal = true"
                            class="w-6 h-6 flex items-center justify-center rounded bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
                            title="Add new category">
                            <span class="material-symbols-outlined text-[14px]">add</span>
                        </button>
                    </div>
                    <div class="flex-1 overflow-y-auto space-y-2">
                        <div v-for="g in currentGroups" :key="g.id" @click="editingGroup = g"
                            class="p-2 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 cursor-pointer hover:border-primary/30">
                            <div class="flex items-center gap-2">
                                <div class="w-3 h-3 rounded-full" :style="{ background: g.color }"></div>
                                <span class="text-xs font-bold text-gray-900 dark:text-white flex-1">{{ g.name
                                    }}</span>
                                <span class="text-[9px] text-gray-500">{{ store.sectionsByGroup(g.id).length }}
                                    sections</span>
                            </div>
                        </div>
                        <div v-if="!currentGroups.length" class="text-center text-gray-500 text-xs py-6">No categories yet. Click + to add.
                        </div>
                    </div>
                </div>

                <!-- ═══ Searched Product Details ═══ -->
                <div v-if="search.highlightedProducts.value.length" class="glass-panel rounded-xl p-4 flex flex-col gap-2 max-h-56 overflow-y-auto">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px] text-primary">search</span>
                        Search Results
                        <span class="text-[10px] text-gray-500 font-normal ml-auto">{{ search.highlightedProducts.value.length }} found</span>
                    </h3>
                    <div v-for="p in search.highlightedProducts.value" :key="p.sku + p.rackId"
                        class="p-2.5 rounded-lg bg-primary/5 border border-primary/20 space-y-1 cursor-pointer hover:bg-primary/10 transition-colors"
                        @click="onSidebarProductClick(p)">
                        <div class="text-xs font-bold text-primary truncate">📦 {{ p.name }}</div>
                        <div class="flex justify-between text-[10px]"><span class="text-gray-500">SKU</span><span class="font-bold text-gray-700 dark:text-gray-300">{{ p.sku }}</span></div>
                        <div class="flex justify-between text-[10px]"><span class="text-gray-500">Qty</span><span class="font-bold text-gray-700 dark:text-gray-300">{{ p.qty }} {{ p.unit }}</span></div>
                        <div class="flex justify-between text-[10px]"><span class="text-gray-500">Order</span><span class="font-bold text-gray-700 dark:text-gray-300">{{ p.orderId }}</span></div>
                        <div v-if="p.rma" class="flex justify-between text-[10px]"><span class="text-yellow-500">⚠ RMA</span><span class="font-bold text-yellow-500">{{ p.rma }}</span></div>
                        <div class="text-[9px] text-gray-500 dark:text-gray-400 mt-0.5">
                            {{ getProductLocationLabel(p) }}
                        </div>
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-4 space-y-2">
                    <template v-if="zoom.state.level === 'FLOOR'">
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Sections</span><span
                                class="font-bold text-gray-900 dark:text-white">{{ currentSections.length }}</span>
                        </div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Total
                                Racks</span><span class="font-bold text-gray-900 dark:text-white">{{
                                    store.racksOnFloor(activeFloor).length }}</span></div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Total
                                Products</span><span class="font-bold text-primary">{{
                                    store.productsByFloor(activeFloor).length }}</span>
                        </div>
                    </template>
                    <template v-else-if="zoom.state.level === 'SECTION'">
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Section</span><span
                                class="font-bold text-gray-900 dark:text-white">{{ activeSection?.label }}</span>
                        </div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Racks</span><span
                                class="font-bold text-gray-900 dark:text-white">{{ activeRacks.length }}</span>
                        </div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Products</span><span
                                class="font-bold text-primary">{{ activeSectionProducts.length }}</span></div>
                    </template>
                    <template v-else-if="zoom.state.level === 'RACK' && activeRack">
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Rack</span><span
                                class="font-bold text-gray-900 dark:text-white">{{ activeRack.label }}</span></div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Grid</span><span
                                class="font-bold text-gray-900 dark:text-white">{{ activeRack.rows }}×{{
                                    activeRack.cols
                                }}</span></div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Occupied</span><span
                                class="font-bold text-primary">{{ store.productsByRack(activeRack.id).length }}/{{
                                    activeRack.rows * activeRack.cols }}</span></div>
                    </template>
                </div>
            </div>
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useWarehouseFloorStore } from '@/stores/warehouseFloorStore'
import { useZoomStateMachine } from './floorplan/composables/useZoomStateMachine'
import { useCanvasInteraction } from './floorplan/composables/useCanvasInteraction'
import { useFloorSearch } from './floorplan/composables/useFloorSearch'
import { useAuthStore } from '@/stores/authStore'

import SectionCard from './floorplan/components/SectionCard.vue'
import RackGridView from './floorplan/components/RackGridView.vue'
import FloorBreadcrumb from './floorplan/components/FloorBreadcrumb.vue'
import SearchBar from './floorplan/components/SearchBar.vue'
import GroupModal from './floorplan/components/GroupModal.vue'
import PropertiesPanel from './floorplan/components/PropertiesPanel.vue'

const store = useWarehouseFloorStore()
const authStore = useAuthStore()
const zoom = useZoomStateMachine()
const canvas = useCanvasInteraction()
const search = useFloorSearch(store, zoom)

const activeFloor = ref(1)
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

// Canvas zoom (changes content area size, scrollbars handle navigation)
const canvasZoom = ref(1)
const BASE_W = 2000
const BASE_H = 1400
const CONTENT_OFFSET_TOP = 100
const CONTENT_OFFSET_LEFT = 20
const CONTENT_PADDING = 150

/** Dynamically compute scrollable area based on actual content extent */
const contentExtent = computed(() => {
    let maxRight = 0
    let maxBottom = 0

    if (zoom.state.level === 'FLOOR') {
        for (const sec of currentSections.value) {
            maxRight = Math.max(maxRight, sec.x + sec.w)
            maxBottom = Math.max(maxBottom, sec.y + sec.h)
        }
    } else if (zoom.state.level === 'SECTION') {
        for (const rack of activeRacks.value) {
            maxRight = Math.max(maxRight, rack.x + rack.w)
            maxBottom = Math.max(maxBottom, rack.y + rack.h)
        }
    } else if (zoom.state.level === 'RACK' && activeRack.value) {
        const r = activeRack.value
        maxRight = 40 + r.cols * 124 + 16
        maxBottom = 40 + r.rows * 84 + 16
    }

    return {
        right: maxRight + CONTENT_OFFSET_LEFT + CONTENT_PADDING,
        bottom: maxBottom + CONTENT_OFFSET_TOP + CONTENT_PADDING
    }
})

const canvasWidth = computed(() => {
    const base = zoom.state.level === 'FLOOR' ? BASE_W : 600
    return Math.round(Math.max(base, contentExtent.value.right) * canvasZoom.value)
})
const canvasHeight = computed(() => {
    const base = zoom.state.level === 'FLOOR' ? BASE_H : 500
    return Math.round(Math.max(base, contentExtent.value.bottom) * canvasZoom.value)
})
const canvasZoomPercent = computed(() => Math.round(canvasZoom.value * 100))

function zoomCanvas(dir) {
    const step = 0.25
    if (dir > 0) canvasZoom.value = Math.min(3, canvasZoom.value + step)
    else canvasZoom.value = Math.max(0.5, canvasZoom.value - step)
}

function recenterCanvas() {
    canvasZoom.value = 1
    if (canvasRef.value) {
        canvasRef.value.scrollTo({ left: 0, top: 0, behavior: 'smooth' })
    }
}

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

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null
}

/** Read inventory custom categories from localStorage and add as floor groups (if not already present) */
function syncInventoryCategoriesToFloor() {
    const warehouseId = getWarehouseId()
    const storageKey = `warehouse-manager-inventory-categories:${warehouseId || 'default'}`
    let customCategories = []
    try {
        const raw = JSON.parse(window.localStorage.getItem(storageKey) || '[]')
        customCategories = Array.isArray(raw) ? raw : []
    } catch (e) {
        customCategories = []
    }

    const floorId = activeFloor.value || store.floors[0]?.id || 1
    const colorPalette = store.presetColors
    const existingNames = new Set(store.groupsByFloor(floorId).map(g => g.name.toLowerCase()))

    customCategories.forEach((catName, idx) => {
        if (typeof catName !== 'string' || !catName.trim()) return
        const name = catName.trim()
        if (existingNames.has(name.toLowerCase())) return
        const color = colorPalette[idx % colorPalette.length] || '#6366f1'
        store.addGroup(floorId, { name, color, internalGap: 2, externalGap: 10 })
        existingNames.add(name.toLowerCase())
    })
}

async function syncFloorInventory() {
    const warehouseId = getWarehouseId()
    if (warehouseId) {
        await store.syncInventoryToFloorPlan(authStore.authToken, warehouseId)
    } else {
        await store.syncInventoryToFloorPlan(authStore.authToken, null)
    }
    syncInventoryCategoriesToFloor()
}

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

async function onInventoryUpdated(event) {
    const eventWarehouseId = event?.detail?.warehouseId
    const currentWarehouseId = getWarehouseId()

    if (!currentWarehouseId || !eventWarehouseId || eventWarehouseId === currentWarehouseId) {
        await syncFloorInventory()
    }
}

function onCategoryCreated() {
    syncInventoryCategoriesToFloor()
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
    window.addEventListener('warehouse-inventory-updated', onInventoryUpdated)
    window.addEventListener('warehouse-category-created', onCategoryCreated)
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
    window.removeEventListener('warehouse-inventory-updated', onInventoryUpdated)
    window.removeEventListener('warehouse-category-created', onCategoryCreated)
})
</script>

<style scoped>
.canvas-grid {
    background-color: #f9fafb;
    background-image:
        linear-gradient(rgba(156, 163, 175, 0.15) 1px, transparent 1px),
        linear-gradient(90deg, rgba(156, 163, 175, 0.15) 1px, transparent 1px),
        linear-gradient(rgba(156, 163, 175, 0.3) 1px, transparent 1px),
        linear-gradient(90deg, rgba(156, 163, 175, 0.3) 1px, transparent 1px);
    background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
}

:is(.dark) .canvas-grid {
    background-color: #111827;
    background-image:
        linear-gradient(rgba(75, 85, 99, 0.15) 1px, transparent 1px),
        linear-gradient(90deg, rgba(75, 85, 99, 0.15) 1px, transparent 1px),
        linear-gradient(rgba(75, 85, 99, 0.3) 1px, transparent 1px),
        linear-gradient(90deg, rgba(75, 85, 99, 0.3) 1px, transparent 1px);
    background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
}

.search-highlight {
    animation: pulse-hl 1s ease-in-out infinite;
}

@keyframes pulse-hl {

    0%,
    100% {
        box-shadow: 0 0 0 0 rgba(68, 233, 150, .4);
    }

    50% {
        box-shadow: 0 0 0 8px rgba(68, 233, 150, 0);
    }
}
</style>

<!-- Unscoped styles so search-highlight animation reaches child components -->
<style>
.search-highlight {
    animation: pulse-hl 1s ease-in-out infinite !important;
}
</style>
