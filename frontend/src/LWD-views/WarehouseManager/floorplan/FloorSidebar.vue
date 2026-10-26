<template>
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
</template>

<script setup>
import { inject } from 'vue'
import PropertiesPanel from './components/PropertiesPanel.vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const {
    activeFloor,
    activeRack,
    activeRacks,
    activeSection,
    activeSectionProducts,
    canvas,
    currentGroups,
    currentSections,
    editMode,
    editingGroup,
    getProductLocationLabel,
    onSidebarProductClick,
    search,
    selectedElementType,
    showGroupModal,
    store,
    zoom,
} = inject(floorPlanPageKey)
</script>
