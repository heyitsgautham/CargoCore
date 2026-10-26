<template>
    <BaseModal :isOpen="showUploadModal" title="Upload Bulk Shipments" @close="showUploadModal = false">
        <div class="py-6 space-y-4">
            <div
                class="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer">
                <input type="file" accept=".csv,.xlsx,.json" class="hidden" id="bulkFileInput">
                <label for="bulkFileInput" class="cursor-pointer">
                    <span
                        class="material-symbols-outlined text-gray-400 text-5xl mb-3 block">cloud_upload</span>
                    <div class="text-sm text-gray-600 dark:text-gray-400 mb-1">Click to upload or drag & drop
                    </div>
                    <div class="text-xs text-gray-500">CSV, XLSX, or JSON files</div>
                </label>
            </div>
            <div class="flex gap-3">
                <button @click="showUploadModal = false"
                    class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm">Upload</button>
                <button @click="showUploadModal = false"
                    class="px-6 py-2.5 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg text-sm">Cancel</button>
            </div>
        </div>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { showUploadModal } = inject(createShipmentPageKey)
</script>
