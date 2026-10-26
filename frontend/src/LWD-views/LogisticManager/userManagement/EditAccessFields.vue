<template>
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full
                Name</label>
            <input :value="formData.name" type="text" disabled
                class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white opacity-60 cursor-not-allowed">
        </div>
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email
                Address</label>
            <input :value="formData.email" type="email" disabled
                class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white opacity-60 cursor-not-allowed">
        </div>
    </div>

    <div class="h-px bg-gray-200 dark:bg-white/10 my-4"></div>

    <!-- Editable Role & Hub -->
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role
                Update</label>
            <div class="relative">
                <select v-model="formData.role"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none">
                    <option v-for="r in roles" :key="r" :value="r"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        {{ r
                        }}</option>
                </select>
                <span
                    class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">arrow_drop_down</span>
            </div>
        </div>
        <div>
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hub
                Relocation</label>
            <div class="relative">
                <select v-model="formData.hubId"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none">
                    <option value="all"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        Global (All Warehouses)</option>
                    <option v-for="h in hubOptionsForEdit" :key="h.id" :value="h.id"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        {{
                            h.name }}
                    </option>
                </select>
                <span
                    class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">arrow_drop_down</span>
            </div>
        </div>
        <div class="col-span-2">
            <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <div class="relative">
                <select v-model="formData.status"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none">
                    <option v-for="s in statuses" :key="s" :value="s"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        {{ s
                        }}</option>
                </select>
                <span
                    class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">arrow_drop_down</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const { formData, hubOptionsForEdit, roles, statuses } = inject(userManagementPageKey)
</script>
