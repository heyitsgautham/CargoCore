<template>
    <div class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-white/5 flex justify-between items-center">
        <h3 class="font-bold text-gray-900 dark:text-white">All Active Zones</h3>
        <div class="flex gap-2 text-sm text-gray-500">
            <button class="hover:text-primary flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">filter_list</span> Filter</button>
            <button class="hover:text-primary flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">download</span> Export</button>
        </div>
    </div>
    <div class="flex-1 overflow-auto custom-scrollbar">
        <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-card-dark sticky top-0 z-10">
                <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                    <th class="py-3 px-4 font-medium">Zone Name</th>
                    <th class="py-3 px-4 font-medium">Type</th>
                    <th class="py-3 px-4 font-medium">Hub Assignment</th>
                    <th class="py-3 px-4 font-medium text-right">Radius (km)</th>
                    <th class="py-3 px-4 font-medium text-right">Status</th>
                    <th class="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                <tr v-if="isLoading">
                    <td colspan="6" class="py-12 text-center text-sm text-gray-400">
                        <span class="material-symbols-outlined align-middle animate-spin text-xl mr-2">progress_activity</span>Loading zones...
                    </td>
                </tr>
                <tr v-else-if="searchedZones.length === 0">
                    <td colspan="6" class="py-12 text-center text-sm text-gray-400">No zones found</td>
                </tr>
                <tr v-for="zone in searchedZones" :key="zone.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group">
                    <td class="py-3 px-4 font-medium text-gray-900 dark:text-white">{{ zone.name }}</td>
                    <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">{{ getZoneIcon(zone.type) }}</span>
                            {{ zone.type }}
                        </div>
                    </td>
                    <td class="py-3 px-4 text-gray-600 dark:text-gray-300">{{ store.hubs.find(h => h.id === zone.hubId)?.name || '—' }}</td>
                    <td class="py-3 px-4 text-right font-mono">{{ zone.radius }}</td>
                    <td class="py-3 px-4 text-right">
                        <span class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
                            :class="zone.status === 'Active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500'">
                            {{ zone.status || 'Active' }}
                        </span>
                    </td>
                    <td class="py-3 px-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                        <button @click="openZoneModal('edit', zone)" class="text-primary hover:text-primary-dark font-medium text-xs mr-3">Edit</button>
                        <button @click="handleDeleteZone(zone.id)" class="text-red-500 hover:text-red-700 font-medium text-xs">Delete</button>
                    </td>
                </tr>
            </tbody>
        </table>
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
    searchedZones,
    store,
} = inject(geofencingPageKey)
</script>
