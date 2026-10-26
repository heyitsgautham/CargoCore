<template>
    <!-- Single Payment Modal -->
    <Teleport to="body">
        <div v-if="showPaymentModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-scale-in">
                <!-- Default State -->
                <template v-if="!paymentSuccess">
                    <div class="p-6 border-b border-gray-100 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Process Payout</h3>
                        <button @click="showPaymentModal = false" :disabled="paymentProcessing" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="flex flex-col items-center">
                            <div class="w-16 h-16 rounded-full bg-gray-100 mb-3 overflow-hidden border-2 border-gray-200 shadow-inner">
                                <img v-if="paymentTarget?.avatar" :src="paymentTarget.avatar" class="w-full h-full object-cover">
                                <span v-else class="material-symbols-outlined text-3xl text-gray-400">person</span>
                            </div>
                            <h4 class="font-bold text-lg text-gray-900 dark:text-white">{{ paymentTarget?.name }}</h4>
                            <p class="text-xs text-gray-500 font-mono">{{ paymentTarget?.role }} • {{ paymentTarget?.id }}</p>
                        </div>

                        <div class="bg-gray-50 dark:bg-black/20 p-4 rounded-xl border border-dashed border-gray-200 dark:border-white/10 text-center">
                            <p class="text-xs font-bold uppercase text-gray-500 mb-1">Total Transfer Amount</p>
                            <p class="text-3xl font-bold font-mono text-gray-900 dark:text-white">₹{{ paymentTarget?.amount.toLocaleString() }}</p>
                        </div>

                        <p class="text-center text-xs text-gray-400 px-4">Funds will be transferred directly to the linked account ending in **4291.</p>
                    </div>
                    <div class="p-4 bg-gray-50 dark:bg-white/5 flex justify-end gap-2">
                        <button @click="showPaymentModal = false" :disabled="paymentProcessing" class="px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:text-gray-200 rounded-lg border border-slate-700 dark:border-white/10 disabled:opacity-50">Cancel</button>
                        <button @click="confirmSinglePayment" :disabled="paymentProcessing" class="px-6 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 shadow-sm flex items-center gap-2 min-w-[140px] justify-center disabled:opacity-75 disabled:cursor-wait">
                            <span v-if="!paymentProcessing" class="material-symbols-outlined text-[18px]">send_money</span>
                            <span v-if="paymentProcessing" class="animate-spin material-symbols-outlined text-[18px]">progress_activity</span>
                            {{ paymentProcessing ? 'Processing...' : 'Transfer Now' }}
                        </button>
                    </div>
                </template>

                <!-- Success State -->
                <template v-else>
                    <div class="p-8 flex flex-col items-center justify-center text-center space-y-4">
                        <div class="w-16 h-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center animate-bounce-short">
                            <span class="material-symbols-outlined text-4xl">check_circle</span>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Payment Successful!</h3>
                            <p class="text-sm text-gray-500 mt-1">Transaction ID: #tx-{{ Math.floor(Math.random()*100000) }}</p>
                        </div>
                        <div class="w-full bg-gray-50 dark:bg-white/5 p-4 rounded-lg mt-4">
                            <p class="text-xs text-gray-400">Total Paid</p>
                            <p class="text-lg font-bold font-mono text-gray-900 dark:text-white">₹{{ paymentTarget?.amount.toLocaleString() }}</p>
                        </div>
                        <button @click="showPaymentModal = false" class="w-full py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white rounded-lg font-bold text-sm mt-4 transition-colors border border-slate-700 dark:border-primary/30">
                            Close Receipt
                        </button>
                    </div>
                </template>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const {
    confirmSinglePayment,
    paymentProcessing,
    paymentSuccess,
    paymentTarget,
    showPaymentModal,
} = inject(financePageKey)
</script>
