<template>
    <!-- Address Update Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showAddressModal" @close="showAddressModal = false">
            <template #title>Update Delivery Address</template>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current Address</label>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                        {{
                            selected?.destination }}</div>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Address *</label>
                    <input v-model="newAddress" type="text" placeholder="Enter new delivery address"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
            </div>
            <template #footer>
                <button @click="showAddressModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                <button @click="updateAddress" :disabled="!newAddress.trim()"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Update
                    Address</button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { newAddress, selected, showAddressModal, updateAddress } = inject(vendorTrackingPageKey)
</script>
