<template>
    <div v-if="isZoneModalOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col animate-scale-in" style="max-height:92vh">
            <div class="p-5 border-b border-gray-100 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5 flex-shrink-0">
                <div>
                    <h3 class="text-base font-bold text-gray-900 dark:text-white">{{ zoneModalMode === 'create' ? 'Create New Zone' : 'Edit Zone' }}</h3>
                    <p class="text-xs text-gray-500">Define geofence parameters and restrictions</p>
                </div>
                <button @click="closeZoneModal" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-5 space-y-3 overflow-y-auto flex-1 min-h-0">
                <div>
                    <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Name</label>
                    <input v-model="zoneForm.name" type="text" placeholder="e.g. Downtown Exclusion Zone" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Type</label>
                        <select v-model="zoneForm.type" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                            <option value="Polygon" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Polygon</option>
                            <option value="Circle" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Circle</option>
                            <option value="Exclusion" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Exclusion Zone</option>
                            <option value="Corridor" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Corridor</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Radius (km)</label>
                        <input v-model="zoneForm.radius" type="number" step="0.1" min="0.1" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Assigned Warehouse</label>
                    <select v-model="zoneForm.hubId" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                        <option v-for="hub in store.hubs" :key="hub.id" :value="hub.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ hub.name }}</option>
                    </select>
                </div>

                <!-- Zone Location -->
                <div>
                    <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Center</label>
                    <div v-if="zoneForm.lat && zoneForm.lng"
                        class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                        <div class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center"
                            :style="{ backgroundColor: getZoneColor(zoneForm.color) + '25', color: getZoneColor(zoneForm.color) }">
                            <span class="material-symbols-outlined text-[18px]">location_on</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p v-if="draftAddress === 'Locating...'" class="text-xs text-gray-400 flex items-center gap-1">
                                <span class="material-symbols-outlined text-[12px] animate-spin">progress_activity</span> Locating...
                            </p>
                            <p v-else class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ draftAddress || 'Location selected' }}</p>
                            <p class="text-[10px] text-gray-400 font-mono">{{ zoneForm.lat?.toFixed(5) }}, {{ zoneForm.lng?.toFixed(5) }}</p>
                        </div>
                        <button @click="pickFromMap" type="button"
                            class="text-xs text-primary hover:text-primary/80 font-semibold flex-shrink-0 flex items-center gap-1 px-2 py-1 rounded hover:bg-primary/10 transition-colors">
                            <span class="material-symbols-outlined text-[14px]">edit_location</span>
                            Change
                        </button>
                    </div>
                    <div v-else
                        class="flex items-center gap-3 p-3 bg-orange-50 dark:bg-orange-500/10 rounded-lg border border-orange-200 dark:border-orange-500/20 cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-500/20 transition-colors"
                        @click="pickFromMap">
                        <span class="material-symbols-outlined text-orange-500 text-xl">location_searching</span>
                        <div>
                            <p class="text-sm font-semibold text-orange-700 dark:text-orange-300">No location set</p>
                            <p class="text-xs text-orange-500">Click here or "Change" to pick a spot on the map</p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Status</label>
                        <select v-model="zoneForm.status" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                            <option value="Active" class="bg-white dark:bg-gray-800">Active</option>
                            <option value="Inactive" class="bg-white dark:bg-gray-800">Inactive</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Color</label>
                        <div class="flex gap-1.5 flex-wrap">
                            <button v-for="(hex, name) in { blue: '#3b82f6', green: '#22c55e', red: '#ef4444', orange: '#f97316', purple: '#a855f7', teal: '#14b8a6', indigo: '#6366f1', yellow: '#eab308' }"
                                :key="name"
                                type="button"
                                @click="zoneForm.color = name"
                                :title="name"
                                class="w-6 h-6 rounded-full border-2 transition-all"
                                :style="{ backgroundColor: hex }"
                                :class="zoneForm.color === name ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'">
                            </button>
                        </div>
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Alert Settings</label>
                    <div class="flex items-center gap-2 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                        <input type="checkbox" id="entryAlert" v-model="zoneForm.entryAlert" class="rounded text-primary focus:ring-offset-0 bg-transparent border-gray-300">
                        <label for="entryAlert" class="text-sm text-gray-700 dark:text-white select-none cursor-pointer">Trigger alert on vehicle entry</label>
                    </div>
                </div>

                <p v-if="saveError" class="text-xs text-red-500">{{ saveError }}</p>
            </div>

            <div class="p-5 pt-0 flex justify-end gap-3 flex-shrink-0 border-t border-gray-100 dark:border-white/10">
                <button @click="closeZoneModal" class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">Cancel</button>
                <button @click="saveZone" :disabled="isSaving"
                    class="px-6 py-2 bg-primary hover:bg-primary/90 disabled:opacity-60 text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/20 transition-all flex items-center gap-2">
                    <span v-if="isSaving" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                    <span v-else class="material-symbols-outlined text-sm">save</span>
                    {{ zoneModalMode === 'create' ? 'Create Zone' : 'Update Zone' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { geofencingPageKey } from './geofencingPageContext'

const {
    closeZoneModal,
    draftAddress,
    getZoneColor,
    isSaving,
    isZoneModalOpen,
    pickFromMap,
    saveError,
    saveZone,
    store,
    zoneForm,
    zoneModalMode,
} = inject(geofencingPageKey)
</script>
