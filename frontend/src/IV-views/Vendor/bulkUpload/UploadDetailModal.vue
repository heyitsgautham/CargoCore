<template>
    <BaseModal :isOpen="!!viewingUpload" @close="viewingUpload = null">
        <template #title>Upload Details — {{ viewingUpload?.filename }}</template>
        <div v-if="viewingUpload" class="space-y-4">
            <div class="grid grid-cols-3 gap-3">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Orders</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ viewingUpload.orders }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Status</div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                        :class="uploadStatusClass(viewingUpload.status)">{{ viewingUpload.status }}</span>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Errors</div>
                    <div class="text-lg font-bold"
                        :class="viewingUpload.errors ? 'text-red-500' : 'text-green-500'">{{
                        viewingUpload.errors || 0 }}</div>
                </div>
            </div>
            <div v-if="viewingUpload.errors" class="space-y-2">
                <div class="text-xs font-bold text-red-500">Error Details:</div>
                <div class="p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-xs text-red-400 flex items-start gap-2">
                    <span class="material-symbols-outlined text-[14px] mt-0.5 flex-shrink-0">error</span>
                    <span>{{ viewingUpload.errors }} row(s) failed validation. Review your file for missing required fields, invalid data formats, or duplicate reference IDs, then retry the upload.</span>
                </div>
            </div>
            <div v-if="viewingUpload.status === 'Processed'" class="p-3 bg-green-500/5 border border-green-500/20 rounded-lg text-xs text-green-600 dark:text-green-400 flex items-center gap-2">
                <span class="material-symbols-outlined text-[14px]">check_circle</span>
                All {{ viewingUpload.orders }} shipments were created and queued for dispatch.
            </div>
            <div class="text-xs text-gray-500">Uploaded on {{ viewingUpload.date }}</div>
            <div v-if="viewingUpload.scheduled_for" class="text-xs text-purple-400">Scheduled for {{ viewingUpload.scheduled_for }}</div>
        </div>
        <template #footer>
            <button @click="viewingUpload = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
            <button v-if="viewingUpload?.status === 'Failed'" @click="retryUpload(viewingUpload)"
                :disabled="saving"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2">
                <span v-if="saving" class="material-symbols-outlined text-[14px] animate-spin">progress_activity</span>
                {{ saving ? 'Retrying...' : 'Retry Upload' }}
            </button>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { bulkUploadPageKey } from './bulkUploadPageContext'

const { retryUpload, saving, uploadStatusClass, viewingUpload } = inject(bulkUploadPageKey)
</script>
