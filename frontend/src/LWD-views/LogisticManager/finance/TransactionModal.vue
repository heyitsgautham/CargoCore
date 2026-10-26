<template>
    <!-- Create Transaction Modal -->
    <Teleport to="body">
        <div v-if="showTransactionModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
            <div class="lm-transaction-modal bg-slate-950/98 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-scale-in border border-white/10 backdrop-blur-xl">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 class="text-lg font-bold text-white">Record Transaction</h3>
                    <button @click="showTransactionModal = false" class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4 bg-slate-950/95 text-slate-200">
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase mb-1">Description</label>
                        <input v-model="newTx.desc" type="text" placeholder="e.g. Office Rent Payment" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 text-gray-900 dark:text-white">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-300 uppercase mb-1">Category</label>
                            <select v-model="newTx.type" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 text-gray-900 dark:text-white">
                                <option value="Incoming" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Income</option>
                                <option value="Expense" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Expense</option>
                                <option value="Payroll" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Payroll Adjustment</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-300 uppercase mb-1">Amount (₹)</label>
                            <input v-model.number="newTx.amount" type="number" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 text-gray-900 dark:text-white">
                        </div>
                    </div>
                </div>
                <div class="p-4 bg-slate-900/90 flex justify-end gap-2 border-t border-white/10">
                    <button @click="showTransactionModal = false" class="px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:text-gray-200 rounded-lg border border-slate-700 dark:border-white/10">Cancel</button>
                    <button @click="addTransaction" class="px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:bg-primary/90 shadow-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">save</span> Save Record
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const { addTransaction, newTx, showTransactionModal } = inject(financePageKey)
</script>

<style scoped src="./Finance.css"></style>
