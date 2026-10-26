<template>
    <!-- Slip downloads for delivered orders -->
    <div v-if="activeMove?.status === 'delivered'" class="flex gap-2">
        <button @click="openSlipWithData('proofOfDelivery', activeMove, authStore.currentUser)"
            class="flex-1 py-2.5 bg-green-500/10 hover:bg-green-500/20 text-green-600 dark:text-green-400 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-sm">verified</span> PoD
        </button>
        <button @click="openSlipWithData('finalTaxInvoice', activeMove, authStore.currentUser)"
            class="flex-1 py-2.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-sm">request_quote</span> Invoice
        </button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove, authStore, openSlipWithData } = inject(customerTrackingPageKey)
</script>
