<template>
    <!-- Reschedule Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showRescheduleModal" @close="showRescheduleModal = false">
            <template #title>Reschedule Delivery</template>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current ETA</label>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                        {{
                            selected?.eta }}</div>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Delivery Date *</label>
                    <input v-model="newDate" type="date"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Reason</label>
                    <textarea v-model="rescheduleReason" rows="2" placeholder="Optional reason"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                </div>
            </div>
            <template #footer>
                <button @click="showRescheduleModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                <button @click="reschedule" :disabled="!newDate"
                    class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-bold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Reschedule</button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    newDate,
    reschedule,
    rescheduleReason,
    selected,
    showRescheduleModal,
} = inject(vendorTrackingPageKey)
</script>
