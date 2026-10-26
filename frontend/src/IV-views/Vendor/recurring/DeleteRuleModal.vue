<template>
    <BaseModal :isOpen="showDeleteModal" @close="showDeleteModal = false">
        <template #title>Delete Schedule</template>
        <div class="text-center py-4">
            <span class="material-symbols-outlined text-5xl text-red-500 mb-3">warning</span>
            <p class="text-gray-600 dark:text-gray-300 text-sm">Are you sure you want to delete <strong class="text-gray-900 dark:text-white">{{ deletingRule?.name }}</strong>?</p>
            <p class="text-xs text-gray-400 mt-2">This action cannot be undone.</p>
            <p v-if="deleteError" class="text-xs text-red-500 mt-3">{{ deleteError }}</p>
        </div>
        <template #footer>
            <button @click="showDeleteModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
            <button @click="executeDelete" :disabled="isDeleting"
                class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                <span v-if="isDeleting" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                Delete
            </button>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { recurringPageKey } from './recurringPageContext'

const {
    deleteError,
    deletingRule,
    executeDelete,
    isDeleting,
    showDeleteModal,
} = inject(recurringPageKey)
</script>
