<template>
    <!-- Mark Arrived — Auto-Debit Confirmation Modal -->
    <Teleport to="body">
        <div v-if="showArriveConfirmModal && arriveConfirmAsn"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showArriveConfirmModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Confirm Mark as Arrived</h3>
                    <button @click="showArriveConfirmModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4">
                    <!-- Debit Warning Banner -->
                    <div class="flex items-start gap-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-300 dark:border-amber-500/30 rounded-xl p-4">
                        <span class="material-symbols-outlined text-amber-500 text-2xl flex-shrink-0 mt-0.5">account_balance_wallet</span>
                        <div>
                            <p class="text-sm font-bold text-amber-800 dark:text-amber-300">Wallet Auto-Debit Will Fire</p>
                            <p class="text-xs text-amber-700 dark:text-amber-400 mt-1">
                                Marking this order as <strong>Arrived</strong> will immediately trigger
                                auto-debit from the vendor's wallet.
                            </p>
                        </div>
                    </div>

                    <!-- Order Details -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase mb-1">ASN / Order</div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ arriveConfirmAsn.id }}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase mb-1">Vendor</div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ arriveConfirmAsn.supplier }}</div>
                        </div>
                        <div class="col-span-2 rounded-xl border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/10 p-4 text-center">
                            <div class="text-[11px] text-blue-600 dark:text-blue-400 uppercase font-bold mb-1">Amount to be Debited</div>
                            <div v-if="arriveConfirmAsn.totalAmount > 0"
                                class="text-3xl font-extrabold text-blue-700 dark:text-blue-300">
                                ₹{{ arriveConfirmAsn.totalAmount.toFixed(2) }}
                            </div>
                            <div v-else class="text-sm text-gray-500 dark:text-gray-400 italic">
                                Cost not yet estimated for this order
                            </div>
                        </div>
                    </div>

                    <p class="text-[11px] text-gray-500 dark:text-gray-400 text-center">
                        If the vendor has insufficient wallet balance, the order will go negative and they'll be notified to top up.
                    </p>
                </div>
                <div class="p-6 border-t border-gray-100 dark:border-white/5 flex justify-end gap-3">
                    <button @click="showArriveConfirmModal = false"
                        class="px-4 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors text-sm">
                        Cancel
                    </button>
                    <button @click="_doMarkArrived(arriveConfirmAsn)" :disabled="isMarkingArrived"
                        class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-colors text-sm flex items-center gap-2 disabled:opacity-50">
                        <span v-if="isMarkingArrived" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                        Confirm &amp; Mark Arrived
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { _doMarkArrived, arriveConfirmAsn, isMarkingArrived, showArriveConfirmModal } = inject(inboundPageKey)
</script>
