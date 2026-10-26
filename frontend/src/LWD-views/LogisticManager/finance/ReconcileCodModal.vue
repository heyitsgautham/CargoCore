<template>
    <!-- Reconcile COD Modal -->
    <Teleport to="body">
        <div v-if="reconcileModalOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-scale-in">
                <div class="p-6 border-b border-gray-100 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <div>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Reconcile COD Payment</h3>
                        <p class="text-xs text-gray-500">Confirm cash collection from driver</p>
                    </div>
                    <button @click="reconcileModalOpen = false" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div v-if="selectedItem" class="p-6 space-y-4">
                    <div class="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-100 dark:border-blue-500/20">
                        <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-400">
                            <span class="material-symbols-outlined">local_shipping</span>
                        </div>
                        <div>
                            <p class="text-sm font-bold text-gray-900 dark:text-white">{{ selectedItem.desc }}</p>
                            <p class="text-xs text-gray-500">{{ selectedItem.date }} • ID: {{ selectedItem.id }}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Expected Amount</label>
                            <div class="w-full bg-gray-100 dark:bg-white/5 border border-transparent rounded-lg px-4 py-2 text-sm text-gray-500 font-mono">
                                ₹{{ selectedItem.amount.toLocaleString() }}
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Counted Cash</label>
                            <input v-model.number="reconcileAmount" type="number" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 text-gray-900 dark:text-white font-mono">
                        </div>
                    </div>

                    <div v-if="reconcileDiff !== 0" class="p-3 rounded text-xs font-bold flex items-center gap-2"
                         :class="reconcileDiff > 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
                        <span class="material-symbols-outlined text-[16px]">{{ reconcileDiff > 0 ? 'add_circle' : 'warning' }}</span>
                        {{ reconcileDiff > 0 ? `Surplus of ₹${reconcileDiff}` : `Shortage of ₹${Math.abs(reconcileDiff)}` }}
                    </div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 flex justify-end gap-2">
                    <button @click="reconcileModalOpen = false" class="px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:text-gray-200 rounded-lg border border-slate-700 dark:border-white/10">Cancel</button>
                    <button @click="confirmReconciliation" class="px-6 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:bg-primary/90 shadow-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">verified</span> Confirm & Close
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const {
    confirmReconciliation,
    reconcileAmount,
    reconcileDiff,
    reconcileModalOpen,
    selectedItem,
} = inject(financePageKey)
</script>
