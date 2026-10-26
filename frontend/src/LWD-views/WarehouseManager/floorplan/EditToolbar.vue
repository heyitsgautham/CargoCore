<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const {
    canvas,
    editMode,
    onAddRack,
    onAddSection,
    onDeleteSelected,
    zoom,
} = inject(floorPlanPageKey)
</script>
