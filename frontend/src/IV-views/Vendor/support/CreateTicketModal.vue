<template>
    <!-- Create Ticket Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showCreateModal" @close="showCreateModal = false">
            <template #title>Create Support Ticket</template>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Subject *</label>
                    <input v-model="newTicket.subject" type="text" placeholder="Brief description of issue"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Priority</label>
                    <div class="flex gap-2">
                        <label v-for="p in ['Low', 'Medium', 'High']" :key="p"
                            class="flex-1 text-center px-3 py-2 rounded-lg border cursor-pointer text-xs font-bold transition-colors"
                            :class="newTicket.priority === p ? priorityBorderClass(p) : 'border-gray-200 dark:border-white/10 text-gray-500'">
                            <input type="radio" :value="p" v-model="newTicket.priority" class="sr-only">{{ p }}
                        </label>
                    </div>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Related Shipment (optional)</label>
                    <select v-model="newTicket.shipmentId"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                        <option value="" class="bg-white dark:bg-gray-800">None</option>
                        <option v-for="s in store.shipments" :key="s.id" :value="s.backendId" class="bg-white dark:bg-gray-800">
                            {{ s.id }} — {{ s.origin }} → {{ s.destination }}
                        </option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description *</label>
                    <textarea v-model="newTicket.message" rows="4" placeholder="Provide details about your issue..."
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                </div>
            </div>
            <template #footer>
                <button @click="showCreateModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                <button @click="submitTicket" :disabled="!newTicket.subject || !newTicket.message"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">
                    Submit Ticket
                </button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    newTicket,
    priorityBorderClass,
    showCreateModal,
    store,
    submitTicket,
} = inject(vendorSupportPageKey)
</script>
