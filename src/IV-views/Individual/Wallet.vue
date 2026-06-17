<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                <span class="material-symbols-outlined text-green-600">account_balance_wallet</span>
                My Wallet
            </h2>
        </div>

        <!-- Wallet Balance Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="glass-panel p-6 rounded-xl bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm text-gray-600 dark:text-gray-400 font-medium">Current Balance</div>
                    <span class="material-symbols-outlined text-green-600 text-2xl">account_balance</span>
                </div>
                <div class="text-3xl font-bold text-green-600 dark:text-green-400">
                    ₹{{ walletData.balance.toLocaleString() }}
                </div>
            </div>

            <div class="glass-panel p-6 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm text-gray-600 dark:text-gray-400 font-medium">Total Credits</div>
                    <span class="material-symbols-outlined text-blue-600 text-2xl">add_circle</span>
                </div>
                <div class="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    ₹{{ walletData.total_credits.toLocaleString() }}
                </div>
            </div>

            <div class="glass-panel p-6 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm text-gray-600 dark:text-gray-400 font-medium">Total Debits</div>
                    <span class="material-symbols-outlined text-amber-600 text-2xl">remove_circle</span>
                </div>
                <div class="text-3xl font-bold text-amber-600 dark:text-amber-400">
                    ₹{{ walletData.total_debits.toLocaleString() }}
                </div>
            </div>
        </div>

        <!-- Wallet Info Banner -->
        <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500 bg-green-500/5">
            <div class="flex items-start gap-3">
                <span class="material-symbols-outlined text-green-600">info</span>
                <div class="flex-1">
                    <div class="font-bold text-gray-900 dark:text-white mb-1">How Wallet Works</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                        Your wallet balance can be used to pay for orders. When you cancel a paid order,
                        refunds are automatically credited to your wallet after deducting applicable cancellation fees.
                    </div>
                </div>
            </div>
        </div>

        <!-- Transaction History -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 sm:p-5 border-b border-gray-200 dark:border-white/5 flex items-center justify-between">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-600">history</span>
                    Transaction History
                </h3>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                    Last {{ walletData.transactions.length }} transactions
                </div>
            </div>

            <div v-if="walletData.transactions.length === 0" class="p-10 text-center">
                <span class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-6xl mb-3 block">receipt_long</span>
                <div class="text-gray-500 dark:text-gray-400 font-medium">No transactions yet</div>
                <div class="text-sm text-gray-400 dark:text-gray-500 mt-1">Your wallet transactions will appear here</div>
            </div>

            <div v-else class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-white/5">
                            <th class="py-3 px-5 font-medium">Date</th>
                            <th class="py-3 px-5 font-medium">Type</th>
                            <th class="py-3 px-5 font-medium hidden sm:table-cell">Order</th>
                            <th class="py-3 px-5 font-medium hidden md:table-cell">Description</th>
                            <th class="py-3 px-5 font-medium text-right">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tx in walletData.transactions" :key="tx.id"
                            class="border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="py-3 px-5 text-gray-600 dark:text-gray-400 text-xs">
                                {{ formatDate(tx.created_at) }}
                            </td>
                            <td class="py-3 px-5">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-sm"
                                        :class="tx.transaction_kind === 'CREDIT' ? 'text-green-600' : 'text-amber-600'">
                                        {{ tx.transaction_kind === 'CREDIT' ? 'add_circle' : 'remove_circle' }}
                                    </span>
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                        :class="tx.transaction_kind === 'CREDIT'
                                            ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400'
                                            : 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400'">
                                        {{ tx.transaction_kind }}
                                    </span>
                                </div>
                            </td>
                            <td class="py-3 px-5 hidden sm:table-cell">
                                <span v-if="tx.tracking_code"
                                    class="font-mono text-xs font-bold text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded">
                                    {{ tx.tracking_code }}
                                </span>
                                <span v-else class="text-gray-400 dark:text-gray-600 text-xs">—</span>
                            </td>
                            <td class="py-3 px-5 text-gray-600 dark:text-gray-400 text-xs hidden md:table-cell max-w-xs truncate">
                                {{ tx.description }}
                            </td>
                            <td class="py-3 px-5 text-right">
                                <span class="font-bold font-mono"
                                    :class="tx.transaction_kind === 'CREDIT'
                                        ? 'text-green-600 dark:text-green-400'
                                        : 'text-amber-600 dark:text-amber-400'">
                                    {{ tx.transaction_kind === 'CREDIT' ? '+' : '-' }}₹{{ tx.amount.toLocaleString() }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'
import apiClient from '@/config/api'

const store = useIndividualStore()

const walletData = ref({
    balance: 0,
    total_credits: 0,
    total_debits: 0,
    transactions: []
})

async function fetchWallet() {
    try {
        const response = await apiClient.get('/api/v1/customer/wallet')
        walletData.value = response.data
        store.walletBalance = Number(response.data?.balance ?? 0)
        store.pendingTransportCharge = Number(response.data?.pending_transport_charge ?? 0)
    } catch (error) {
        console.error('Failed to fetch wallet:', error)
    }
}

async function backfillDebits() {
    try {
        await apiClient.post('/api/v1/customer/wallet/backfill-debits')
    } catch {
        // non-fatal — old payments simply won't appear if backfill fails
    }
}

watch(() => store.walletBalance, (nextBalance) => {
    walletData.value.balance = Number(nextBalance ?? 0)
})

function formatDate(dateString) {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(date)
}

onMounted(async () => {
    await backfillDebits()
    await fetchWallet()
})
</script>
