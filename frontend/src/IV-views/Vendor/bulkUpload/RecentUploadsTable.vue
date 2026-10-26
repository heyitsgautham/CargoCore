<template>
    <div class="glass-panel rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Recent Uploads</h3>
            <div class="flex items-center gap-3">
                <span class="text-xs text-gray-500">{{ store.bulkUploads.length }} upload(s)</span>
                <button @click="store.fetchBulkUploads()"
                    class="text-xs text-blue-500 hover:text-blue-600 font-semibold flex items-center gap-1 transition-colors">
                    <span class="material-symbols-outlined text-[14px]">refresh</span> Refresh
                </button>
            </div>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm min-w-[600px]">
                <thead class="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 uppercase text-[10px]">
                    <tr>
                        <th class="px-4 py-3">File</th>
                        <th class="px-4 py-3">Date</th>
                        <th class="px-4 py-3">Orders</th>
                        <th class="px-4 py-3">Status</th>
                        <th class="px-4 py-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-if="store.bulkUploads.length === 0">
                        <td colspan="5" class="px-4 py-8 text-center text-gray-400 text-sm">No uploads yet</td>
                    </tr>
                    <tr v-for="u in store.bulkUploads" :key="u.id"
                        class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                        <td class="px-4 py-3">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-[16px]"
                                    :class="u.status === 'Processed' ? 'text-green-500' : u.status === 'Failed' ? 'text-red-500' : u.status === 'Scheduled' ? 'text-purple-500' : 'text-yellow-500 animate-pulse'">{{
                                        u.status === 'Processed' ? 'check_circle' : u.status === 'Failed' ? 'error' :
                                    u.status === 'Scheduled' ? 'schedule' : 'pending' }}</span>
                                <span class="text-gray-900 dark:text-white text-xs font-medium">{{ u.filename }}</span>
                            </div>
                        </td>
                        <td class="px-4 py-3 text-gray-500 text-xs">{{ u.date }}</td>
                        <td class="px-4 py-3 text-gray-900 dark:text-white text-xs font-bold">{{ u.orders }}</td>
                        <td class="px-4 py-3">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                                :class="uploadStatusClass(u.status)">{{ u.status }}</span>
                            <span v-if="u.errors" class="ml-1 text-[10px] text-red-400">({{ u.errors }}
                                errors)</span>
                            <div v-if="u.status === 'Scheduled' && u.scheduled_for" class="text-[10px] text-purple-400 mt-0.5">{{ u.scheduled_for }}</div>
                        </td>
                        <td class="px-4 py-3 text-right">
                            <button @click="viewUploadDetail(u)"
                                class="text-blue-500 hover:text-blue-600 text-xs font-bold transition-colors">{{
                                    u.status === 'Failed' ? 'View Errors' : 'View Details' }}</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bulkUploadPageKey } from './bulkUploadPageContext'

const { store, uploadStatusClass, viewUploadDetail } = inject(bulkUploadPageKey)
</script>
