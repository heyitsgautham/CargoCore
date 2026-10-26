<template>
    <!-- Role & Hub -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 md:items-start">
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
            <div class="relative">
                <select v-model="formData.role"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none">
                    <option value="Warehouse Manager"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        Warehouse Manager</option>
                    <option value="Dispatcher"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        Dispatcher</option>
                </select>
                <span
                    class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">arrow_drop_down</span>
            </div>
        </div>
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hub
                Assignment</label>
            <div class="relative z-30">
                <button type="button" @click.stop="toggleHubMenu"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-left text-white focus:outline-none focus:border-primary/50 transition-colors flex items-center justify-between gap-3"
                    :class="isHubMenuOpen ? 'ring-2 ring-primary/40 border-primary/40' : ''">
                    <span class="truncate">{{ selectedHubLabel }}</span>
                    <span
                        class="material-symbols-outlined text-gray-400 transition-transform"
                        :class="isHubMenuOpen ? 'rotate-180' : ''">arrow_drop_down</span>
                </button>

                <div v-if="isHubMenuOpen"
                    class="absolute left-0 right-0 top-full mt-2 rounded-xl border border-white/10 bg-slate-900 shadow-2xl overflow-hidden z-40">
                    <div class="max-h-56 overflow-y-auto py-2">
                        <button v-for="h in assignableHubs" :key="h.id" type="button"
                            @click.stop="selectHub(h.id)"
                            class="w-full px-4 py-3 text-left text-sm transition-colors flex items-center justify-between gap-3 hover:bg-white/5"
                            :class="formData.hubId === h.id ? 'bg-primary/10 text-white' : 'text-gray-300'">
                            <span class="truncate">{{ h.name }}</span>
                            <span v-if="formData.hubId === h.id"
                                class="material-symbols-outlined text-primary text-[18px]">check</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="bg-slate-900/70 p-4 rounded-xl border border-white/10 space-y-4 shadow-sm">
        <h4
            class="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <div
                class="w-6 h-6 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[14px]">key</span>
            </div>
            Login Credentials
        </h4>
        <div class="grid grid-cols-2 gap-4 mt-3">
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Username</label>
                <input v-model="formData.username" type="text" placeholder="e.g. hub_north_manager"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Password</label>
                <input v-model="formData.password" type="text" placeholder="Minimum 8 characters"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono">
            </div>
            <p class="col-span-2 text-xs text-gray-400">
                The Warehouse Manager or Dispatcher will use this username and password to log in to their dashboard.
            </p>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const {
    assignableHubs,
    formData,
    isHubMenuOpen,
    selectHub,
    selectedHubLabel,
    toggleHubMenu,
} = inject(userManagementPageKey)
</script>
