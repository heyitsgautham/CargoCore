<template>
    <BaseModal :isOpen="showConfirmModal" title="Shipment Created"
        @close="showConfirmModal = false; resetForm()">
        <div class="text-center py-6">
            <div
                class="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-4">
                <span
                    class="material-symbols-outlined text-green-600 dark:text-green-400 text-4xl">check_circle</span>
            </div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Booking Confirmed!</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">Your shipment has been created successfully
            </p>
            <div class="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-4">
                <span class="text-xs text-gray-500 dark:text-gray-400">Order ID:</span>
                <span class="text-sm font-bold text-blue-600 dark:text-blue-400">{{ confirmedOrderId }}</span>
            </div>
            <div class="flex gap-2 justify-center flex-wrap">
                <button @click="openSlipWithData('bookingConfirmation', confirmedOrder, authStore.currentUser)" class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-colors">
                    <span class="material-symbols-outlined text-[16px]">receipt_long</span> Booking Slip
                </button>
                <button @click="openSlipWithData('instantQuotation', confirmedOrder, authStore.currentUser)" class="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold transition-colors">
                    <span class="material-symbols-outlined text-[16px]">calculate</span> Quotation
                </button>
            </div>
        </div>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const {
    authStore,
    confirmedOrder,
    confirmedOrderId,
    openSlipWithData,
    resetForm,
    showConfirmModal,
} = inject(createShipmentPageKey)
</script>
