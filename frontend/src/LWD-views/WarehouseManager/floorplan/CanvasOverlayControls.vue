<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const {
    activeRack,
    activeSection,
    canvasZoomPercent,
    currentFloorLabel,
    recenterCanvas,
    zoom,
    zoomCanvas,
} = inject(floorPlanPageKey)
</script>
