<template>
    <!-- Role & Hub -->
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
            <input value="Customer Support" type="text" disabled
                class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white opacity-60 cursor-not-allowed">
        </div>
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hub
                Assignment</label>
            <div class="relative">
                <select v-model="formData.hubId"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none">
                    <option v-for="h in assignableHubs" :key="h.id" :value="h.id"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        {{
                            h.name }}
                    </option>
                </select>
                <span
                    class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">arrow_drop_down</span>
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
                <input v-model="formData.username" type="text" placeholder="e.g. support_bangalore_01"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Password</label>
                <input v-model="formData.password" type="text" placeholder="Minimum 8 characters"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono">
            </div>
            <p class="col-span-2 text-xs text-gray-400">
                The Customer Support agent will use this username and password to sign in to the AI dashboard.
            </p>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const { assignableHubs, formData } = inject(userManagementPageKey)
</script>
