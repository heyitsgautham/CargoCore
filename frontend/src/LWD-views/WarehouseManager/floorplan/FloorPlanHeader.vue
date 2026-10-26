<template>
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
</template>

<script setup>
import { inject } from 'vue'
import SearchBar from './components/SearchBar.vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const {
    activeFloor,
    editMode,
    editingFloorId,
    finishFloorRename,
    floorNameInput,
    onAddFloor,
    onDeleteFloor,
    onFocusSearchResult,
    onSaveFloorPlan,
    search,
    showGroupModal,
    startFloorRename,
    store,
    switchFloor,
    toggleEditMode,
} = inject(floorPlanPageKey)
</script>
