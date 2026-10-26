<template>
    <!-- Login Credentials — Driver only -->
    <div v-if="modalMode === 'create-driver'"
        class="bg-slate-900/70 p-4 rounded-xl border border-white/10 space-y-4 shadow-sm">
        <h4 class="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <div class="w-6 h-6 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[14px]">key</span>
            </div>
            Login Credentials
        </h4>
        <div class="grid grid-cols-2 gap-4 mt-3">
            <div class="col-span-2 md:col-span-1">
                <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Driver ID</label>
                <input v-model="formData.username" type="text" placeholder="e.g. driver1"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono"
                     />
            </div>
            <div class="col-span-2 md:col-span-1">
                <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">PIN / Password</label>
                <input v-model="formData.password" type="text" placeholder="e.g. 1234 (4-digit PIN)"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono"
                    inputmode="numeric" maxlength="4" />
            </div>
            <p class="col-span-2 text-xs text-gray-400">
                The driver will enter this short Driver ID and 4-digit PIN on the mobile app to log in. Share it with them directly.
            </p>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const { formData, modalMode } = inject(userManagementPageKey)
</script>
