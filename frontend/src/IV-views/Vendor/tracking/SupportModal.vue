<template>
    <!-- Support Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showSupportModal" @close="showSupportModal = false">
            <template #title>Contact Support</template>
            <div class="space-y-4">
                <p class="text-sm text-gray-600 dark:text-gray-300">Our team is available 24/7 to help you with shipment <span class="font-bold">{{ selected?.id }}</span>.</p>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">How can we help?</label>
                    <textarea v-model="supportMessage" rows="4" placeholder="Describe the issue you're facing..."
                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                </div>
            </div>
            <template #footer>
                <button @click="showSupportModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                <button @click="submitSupport" :disabled="!supportMessage.trim()"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                    Send Message</button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { selected, showSupportModal, submitSupport, supportMessage } = inject(vendorTrackingPageKey)
</script>
