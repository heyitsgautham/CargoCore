<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const { authStore, currentSections, getWarehouseId, store } = inject(floorPlanPageKey)
</script>
