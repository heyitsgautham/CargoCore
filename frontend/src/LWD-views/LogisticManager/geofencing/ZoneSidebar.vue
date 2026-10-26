<template>
    <div class="w-80 glass-panel rounded-xl flex flex-col border border-gray-200 dark:border-white/5 flex-shrink-0">
        <div class="p-4 border-b border-gray-200 dark:border-white/5 space-y-3">
            <div class="relative">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search zones..."
                    class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow text-gray-900 dark:text-white">
            </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
            <div v-if="isLoading" class="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <span class="material-symbols-outlined text-gray-400 text-4xl animate-spin">progress_activity</span>
                <p class="text-sm text-gray-400">Loading zones...</p>
            </div>
            <div v-else-if="searchedZones.length === 0" class="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <span class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-4xl">add_location_alt</span>
                <p class="text-sm text-gray-400">No zones found</p>
            </div>
            <div v-for="zone in searchedZones" :key="zone.id"
                @click="selectZone(zone)"
                class="p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer border transition-all group shadow-sm flex flex-col gap-2 relative"
                :class="selectedZone?.id === zone.id ? 'bg-primary/5 border-primary/30' : 'border-transparent bg-white dark:bg-transparent'">

                <div class="flex justify-between items-start">
                    <div class="font-bold text-gray-900 dark:text-white text-sm">{{ zone.name }}</div>
                    <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button @click.stop="openZoneModal('edit', zone)" class="p-1 hover:bg-gray-200 dark:hover:bg-white/10 rounded text-gray-500"><span class="material-symbols-outlined text-[16px]">edit</span></button>
                        <button @click.stop="handleDeleteZone(zone.id)" class="p-1 hover:bg-red-100 dark:hover:bg-red-500/20 rounded text-red-500"><span class="material-symbols-outlined text-[16px]">delete</span></button>
                    </div>
                </div>

                <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <span class="material-symbols-outlined text-[14px]">{{ getZoneIcon(zone.type) }}</span>
                    <span>{{ zone.type }}</span>
                    <span>•</span>
                    <span>{{ zone.radius }}km Radius</span>
                </div>

                <div class="flex justify-between items-center mt-1">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                        :class="zone.status === 'Active' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500 border-gray-200'">
                        {{ zone.status || 'Active' }}
                    </span>
                    <span class="text-[10px] text-gray-400 font-mono">{{ store.hubs.find(h => h.id === zone.hubId)?.name }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { geofencingPageKey } from './geofencingPageContext'

const {
    getZoneIcon,
    handleDeleteZone,
    isLoading,
    openZoneModal,
    searchQuery,
    searchedZones,
    selectZone,
    selectedZone,
    store,
} = inject(geofencingPageKey)
</script>
