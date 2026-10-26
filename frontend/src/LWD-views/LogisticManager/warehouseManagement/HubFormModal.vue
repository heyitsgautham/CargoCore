<template>
    <div v-if="isModalOpen"
        class="fixed inset-0 w-screen h-screen z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
        <div class="bg-slate-950/98 rounded-2xl shadow-xl w-full max-w-lg overflow-hidden border border-white/10 backdrop-blur-xl"
            @click.stop>
            <div
                class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">{{ isEditing ? 'edit' : 'add_business'
                        }}</span>
                    {{ isEditing ? 'Edit Hub' : 'Add New Hub' }}
                </h3>
                <button @click="closeModal"
                    class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 space-y-4 bg-slate-950/95">
                <div class="space-y-1">
                    <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Hub
                        Code</label>
                    <input type="text" v-model="draftHub.hubCode" placeholder="e.g. HUB-NY-01"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                </div>

                <div class="space-y-1">
                    <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Hub
                        Name</label>
                    <input type="text" v-model="draftHub.name" placeholder="North-East Distribution Center"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                </div>

                <div class="space-y-1">
                    <label
                        class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Location</label>
                    <input type="text" v-model="draftHub.location" placeholder="New York, NY"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                </div>

                <div class="space-y-1">
                    <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Operating
                        Hours</label>
                    <input type="text" v-model="draftHub.operatingHours" placeholder="09:00 AM - 09:00 PM"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm font-mono text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label
                            class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Manager
                            Name</label>
                        <input type="text" v-model="draftHub.manager" placeholder="Alex Chen"
                            class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                    </div>
                    <div class="space-y-1">
                        <label
                            class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Capacity
                            (%)</label>
                        <input type="number" v-model="draftHub.capacity" min="0" max="100" placeholder="92"
                            class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                    </div>
                </div>

                <div class="space-y-1">
                    <label
                        class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Status</label>
                    <select v-model="draftHub.status"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors">
                        <option value="Optimal" class="bg-slate-900 text-white">Optimal</option>
                        <option value="Active" class="bg-slate-900 text-white">Active</option>
                        <option value="Congested" class="bg-slate-900 text-white">Congested</option>
                        <option value="Archived" class="bg-slate-900 text-white">Archived</option>
                    </select>
                </div>
            </div>

            <div
                class="p-6 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                <button @click="closeModal" :disabled="isSavingHub"
                    class="px-5 py-2 rounded-lg text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 border border-white/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                    Cancel
                </button>
                <button @click="saveHub" :disabled="isSavingHub"
                    class="px-5 py-2 rounded-lg text-sm font-medium bg-primary hover:bg-primary/90 text-white transition-colors shadow-sm border border-primary/30 disabled:opacity-60 disabled:cursor-not-allowed">
                    {{ isSavingHub ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create Hub') }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { warehouseManagementPageKey } from './warehouseManagementPageContext'

const {
    closeModal,
    draftHub,
    isEditing,
    isModalOpen,
    isSavingHub,
    saveHub,
} = inject(warehouseManagementPageKey)
</script>
