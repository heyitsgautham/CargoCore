<template>
    <BaseModal :isOpen="cancelModal.show" @close="cancelModal.show = false">
        <template #title>Cancel Order</template>
        <div class="space-y-4">
            <div class="text-center py-3">
                <div
                    class="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center text-red-500 mx-auto mb-3">
                    <span class="material-symbols-outlined text-3xl">warning</span>
                </div>
                <p class="text-gray-700 dark:text-gray-300 text-sm">Are you sure you want to cancel <span
                        class="font-bold text-gray-900 dark:text-white">{{ cancelModal.order?.id }}</span>?</p>
            </div>
            <div v-if="cancelModal.order" class="p-4 rounded-lg text-sm space-y-2"
                :class="cancelModal.order.status === 'pending' ? 'bg-green-50 dark:bg-green-500/5 border border-green-200 dark:border-green-500/20' : 'bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20'">
                <div v-if="cancelModal.order.status === 'pending'"
                    class="text-green-700 dark:text-green-400 font-bold">
                    ✅ No cancellation fee — order hasn't been dispatched yet.</div>
                <div v-else>
                    <div class="text-amber-600 dark:text-amber-400 font-bold">⚠️ Cancellation fee applies</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        Status: <span class="font-bold">{{ cancelModal.order.status }}</span> · Progress: {{
                            cancelModal.order.progress }}%
                    </div>
                    <div class="text-base font-bold text-red-600 dark:text-red-400 mt-2">Fee: ₹{{
                        estimatedCancelFee.toLocaleString() }}</div>
                </div>
                <!-- Wallet refund info (only if order was paid) -->
                <div v-if="cancelModal.order.paymentStatus === 'paid' || cancelModal.order.paymentStatus === 'partial'"
                    class="mt-2 pt-2 border-t border-gray-200 dark:border-white/10">
                    <div class="text-green-700 dark:text-green-400 font-semibold text-xs flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">account_balance_wallet</span>
                        ₹{{ estimatedWalletRefund.toLocaleString() }} will be refunded to your wallet
                    </div>
                </div>
            </div>
        </div>
        <template #footer>
            <div class="flex gap-3 w-full">
                <button @click="doCancel"
                    class="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-bold">Confirm
                    Cancel</button>
                <button @click="cancelModal.show = false"
                    class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm">Keep
                    Order</button>
            </div>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { individualOrdersPageKey } from './individualOrdersPageContext'

const { cancelModal, doCancel, estimatedCancelFee, estimatedWalletRefund } = inject(individualOrdersPageKey)
</script>
