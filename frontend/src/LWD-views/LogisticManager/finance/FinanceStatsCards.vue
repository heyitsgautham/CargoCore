<template>
    <!-- Dynamic Stats Cards — compact single row -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div class="glass-panel px-4 py-3 rounded-xl border border-gray-200 dark:border-white/5 flex items-center gap-3 hover:border-primary/30 transition-colors">
            <span class="material-symbols-outlined text-2xl text-green-500 shrink-0">payments</span>
            <div class="min-w-0">
                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Revenue (MTD)</p>
                <p v-if="financeLoaded" class="text-lg font-bold text-gray-900 dark:text-white leading-tight">₹{{ totalRevenue.toLocaleString() }}</p>
                <div v-else class="h-6 w-20 bg-white/10 animate-pulse rounded mt-1"></div>
            </div>
        </div>
        <div class="glass-panel px-4 py-3 rounded-xl border border-gray-200 dark:border-white/5 flex items-center gap-3 hover:border-red-500/30 transition-colors">
            <span class="material-symbols-outlined text-2xl text-red-500 shrink-0">account_balance_wallet</span>
            <div class="min-w-0">
                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Expenses</p>
                <p v-if="financeLoaded" class="text-lg font-bold text-gray-900 dark:text-white leading-tight">₹{{ Math.abs(totalExpenses).toLocaleString() }}</p>
                <div v-else class="h-6 w-20 bg-white/10 animate-pulse rounded mt-1"></div>
            </div>
        </div>
        <div class="glass-panel px-4 py-3 rounded-xl border border-gray-200 dark:border-white/5 flex items-center gap-3 hover:border-blue-500/30 transition-colors">
            <span class="material-symbols-outlined text-2xl text-blue-500 shrink-0">local_shipping</span>
            <div class="min-w-0">
                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Pending COD</p>
                <p class="text-lg font-bold text-gray-900 dark:text-white leading-tight">₹{{ pendingCOD.toLocaleString() }}</p>
            </div>
        </div>
        <div class="glass-panel px-4 py-3 rounded-xl border border-gray-200 dark:border-white/5 flex items-center gap-3 hover:border-orange-500/30 transition-colors">
            <span class="material-symbols-outlined text-2xl text-orange-500 shrink-0">group</span>
            <div class="min-w-0">
                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Payroll Due</p>
                <p v-if="financeLoaded" class="text-lg font-bold text-gray-900 dark:text-white leading-tight">₹{{ totalPayrollDue.toLocaleString() }}</p>
                <div v-else class="h-6 w-20 bg-white/10 animate-pulse rounded mt-1"></div>
            </div>
        </div>
        <div class="glass-panel px-4 py-3 rounded-xl border border-purple-200 dark:border-purple-500/20 flex items-center gap-3 hover:border-purple-500/50 transition-colors bg-purple-500/5">
            <span class="material-symbols-outlined text-2xl text-purple-400 shrink-0">add_card</span>
            <div class="min-w-0">
                <p class="text-[10px] text-purple-400 uppercase font-bold tracking-wider">Capital Inflow</p>
                <p v-if="financeLoaded" class="text-lg font-bold text-purple-300 leading-tight">₹{{ capitalInflow.toLocaleString() }}</p>
                <div v-else class="h-6 w-20 bg-purple-400/20 animate-pulse rounded mt-1"></div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const {
    capitalInflow,
    financeLoaded,
    pendingCOD,
    totalExpenses,
    totalPayrollDue,
    totalRevenue,
} = inject(financePageKey)
</script>
