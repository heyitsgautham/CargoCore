<template>
    <!-- Payroll Confirmation Modal -->
    <Teleport to="body">
        <div v-if="showPayrollModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-scale-in">
                <template v-if="!payrollSuccess">
                    <div class="p-6 border-b border-gray-100 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-green-600">payments</span>
                            Confirm Payroll Run
                        </h3>
                        <button @click="showPayrollModal = false" :disabled="payrollProcessing" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/20 p-4 rounded-lg flex gap-3">
                            <span class="material-symbols-outlined text-yellow-600 text-2xl">warning</span>
                            <div>
                                <h4 class="font-bold text-yellow-800 dark:text-yellow-400 text-sm">Action Confirmation</h4>
                                <p class="text-xs text-yellow-700 dark:text-yellow-300/80 mt-1">This will process payouts for all staff with pending balances. This action cannot be undone.</p>
                            </div>
                        </div>

                        <div class="flex justify-between items-center py-2 border-b border-gray-100 dark:border-white/5">
                            <span class="text-sm text-gray-500">Total Employees</span>
                            <span class="font-bold text-gray-900 dark:text-white">{{ payrollSummary.count }}</span>
                        </div>
                        <div class="flex justify-between items-center py-2">
                            <span class="text-lg font-bold text-gray-900 dark:text-white">Total Payout</span>
                            <span class="text-2xl font-mono font-bold text-green-600">₹{{ payrollSummary.total.toLocaleString() }}</span>
                        </div>

                        <div class="max-h-32 overflow-y-auto custom-scrollbar bg-gray-50 dark:bg-black/20 p-2 rounded text-xs space-y-1">
                            <div v-for="u in payrollSummary.pendingUsers" :key="u.id" class="flex justify-between">
                                <span class="text-gray-600 dark:text-gray-400">{{ u.name }}</span>
                                <span class="font-mono font-bold">₹{{ u.pending_payout }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-50 dark:bg-white/5 flex justify-end gap-2">
                        <button @click="showPayrollModal = false" :disabled="payrollProcessing" class="px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:text-gray-200 rounded-lg border border-slate-700 dark:border-white/10 disabled:opacity-50">Cancel</button>
                        <button @click="confirmPayrollRun" :disabled="payrollProcessing" class="px-6 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 shadow-sm flex items-center gap-2 justify-center min-w-[160px] disabled:opacity-75 disabled:cursor-wait">
                            <span v-if="!payrollProcessing" class="material-symbols-outlined text-[18px]">check_circle</span>
                            <span v-if="payrollProcessing" class="animate-spin material-symbols-outlined text-[18px]">progress_activity</span>
                            {{ payrollProcessing ? 'Processing Batch...' : 'Confirm Payout' }}
                        </button>
                    </div>
                </template>

                <!-- Payroll Success State -->
                <template v-else>
                    <div class="p-8 flex flex-col items-center justify-center text-center space-y-4">
                        <div class="w-20 h-20 rounded-full bg-green-100 text-green-600 flex items-center justify-center animate-bounce-short">
                            <span class="material-symbols-outlined text-5xl">checklist</span>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Batch Payment Complete!</h3>
                            <p class="text-sm text-gray-500 mt-1">Successfully processed payouts for {{ payrollSummary.count }} employees.</p>
                        </div>
                        <div class="w-full bg-gray-50 dark:bg-white/5 p-4 rounded-lg mt-4 border border-dashed border-gray-200 dark:border-white/10">
                            <p class="text-xs text-gray-400 uppercase font-bold tracking-wider">Total Disbursed</p>
                            <p class="text-3xl font-bold font-mono text-gray-900 dark:text-white mt-1">₹{{ payrollSummary.total.toLocaleString() }}</p>
                        </div>
                        <button @click="showPayrollModal = false" class="w-full py-3 bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white rounded-lg font-bold text-sm mt-4 transition-colors shadow-lg border border-slate-700 dark:border-primary/30">
                            Close & Return to Dashboard
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
    confirmPayrollRun,
    payrollProcessing,
    payrollSuccess,
    payrollSummary,
    showPayrollModal,
} = inject(financePageKey)
</script>
