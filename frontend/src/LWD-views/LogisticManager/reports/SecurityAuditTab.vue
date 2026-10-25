<template>
    <!-- 8. SECURITY & AUDIT LOGS (New) -->
    <div v-if="activeTab === 'security_audit'" class="space-y-6 animate-fade-in">
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
            <div
                class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-900 text-white flex justify-between items-center">
                <h3 class="font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-400">gpp_good</span> Immutable System
                    Audit Ledger
                </h3>
                <span class="text-xs text-gray-400 font-mono">Last Sync: Live</span>
            </div>
            <table class="w-full text-left text-xs">
                <thead
                    class="bg-gray-100 dark:bg-black/40 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-4">Timestamp</th>
                        <th class="p-4">Admin User</th>
                        <th class="p-4">Action Type</th>
                        <th class="p-4">Target Entity</th>
                        <th class="p-4">Details</th>
                        <th class="p-4 text-right">IP Address</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5 font-mono">
                    <tr v-for="log in store.filteredSecurityLogs" :key="`${log.time}-${log.target}`" class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-4 text-gray-400">{{ log.time }}</td>
                        <td class="p-4 font-bold text-blue-600">{{ log.actor }}</td>
                        <td class="p-4"><span class="text-blue-600 bg-blue-100 px-2 py-0.5 rounded font-bold">{{ log.action }}</span></td>
                        <td class="p-4">{{ log.target }}</td>
                        <td class="p-4 text-gray-600 font-sans text-sm">{{ log.details }}</td>
                        <td class="p-4 text-right text-gray-400">{{ log.ip }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const { activeTab, store } = inject(reportsPageKey)
</script>
