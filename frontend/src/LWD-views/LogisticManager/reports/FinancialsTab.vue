<template>
    <!-- 2. FINANCIAL LEDGER -->
    <div v-if="activeTab === 'financials'" class="space-y-6 animate-fade-in">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Revenue Split -->
            <div
                class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Revenue Stream</h3>
                <div class="h-74 relative flex justify-center">
                    <Doughnut :data="revenueStreamData" :options="doughnutOptions" />
                </div>
            </div>
            <!-- Recon Breakdown -->
            <div
                class="lg:col-span-2 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Payment Reconciliation (COD vs Digital)
                </h3>
                <div class="h-74 relative">
                    <Bar :data="paymentReconData" :options="chartOptions" />
                </div>
            </div>
        </div>

        <!-- Fuel Audit Chart -->
        <div
            class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-orange-500">local_gas_station</span>
                Fuel Expense Audit (Receipts vs GPS)
            </h3>
            <div class="h-74 w-full relative">
                <Line :data="fuelAuditData" :options="chartOptions" />
            </div>
            <div
                class="mt-4 p-3 bg-orange-50 dark:bg-orange-500/10 border border-orange-100 dark:border-orange-500/20 rounded-lg flex items-center gap-3">
                <span class="material-symbols-outlined text-orange-600">visibility</span>
                <p class="text-xs text-orange-800 dark:text-orange-300" v-if="fuelAnomalyText">
                    <strong>Anomaly Detected:</strong> {{ fuelAnomalyText }}
                </p>
                <p class="text-xs text-green-700 dark:text-green-400" v-else>
                    <strong>No fuel anomalies detected.</strong> All vehicle mileage reports match GPS logs.
                </p>
            </div>
        </div>

        <!-- Payment Ledger -->
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
            <div
                class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5 flex justify-between">
                <h3 class="font-bold text-gray-900 dark:text-white">Live Payment Ledger</h3>
                <button class="text-xs text-primary font-bold hover:underline">View All</button>
            </div>
            <table class="w-full text-left text-xs">
                <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-4">Customer</th>
                        <th class="p-4">Transaction ID</th>
                        <th class="p-4 text-right">Amount</th>
                        <th class="p-4 text-right">Date</th>
                        <th class="p-4">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="tx in store.filteredTransactions" :key="tx.id"
                        class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-4 font-bold text-gray-900 dark:text-white">{{ tx.desc }}</td>
                        <td class="p-4 font-mono text-gray-500">{{ tx.id }}</td>
                        <td class="p-4 text-right font-mono font-bold"
                            :class="tx.amount > 0 ? 'text-green-600' : 'text-red-500'">₹{{ Math.abs(tx.amount)
                            }}</td>
                        <td class="p-4 text-right font-mono">{{ tx.date }}</td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] uppercase font-bold"
                                :class="tx.status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                                {{ tx.status }}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Procurement vs Capital Chart -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-emerald-500">inventory_2</span>
                    Procurement vs Capital Funding
                </h3>
                <div class="h-64 relative flex justify-center">
                    <Doughnut :data="procurementCapitalData" :options="doughnutOptions" />
                </div>
                <div class="mt-4 grid grid-cols-2 gap-3 text-center text-xs">
                    <div class="p-3 bg-orange-50 dark:bg-orange-500/10 rounded-xl">
                        <p class="text-orange-700 dark:text-orange-400 font-bold text-lg">₹{{ (financeSummary?.procurement_expenses || 0).toLocaleString() }}</p>
                        <p class="text-gray-500 mt-1">Procurement Spent</p>
                    </div>
                    <div class="p-3 bg-blue-50 dark:bg-blue-500/10 rounded-xl">
                        <p class="text-blue-700 dark:text-blue-400 font-bold text-lg">₹{{ (financeSummary?.capital_invested || 0).toLocaleString() }}</p>
                        <p class="text-gray-500 mt-1">Capital Invested</p>
                    </div>
                </div>
            </div>

            <!-- Log Investment Panel -->
            <div class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-blue-500">add_card</span>
                        Capital Investment Log
                    </h3>
                    <button @click="investmentModalOpen = true"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-2 shadow-sm">
                        <span class="material-symbols-outlined text-[16px]">add</span> Log Investment
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2">
                    <div v-if="capitalTransactions.length === 0" class="text-center py-8 text-gray-400 text-sm">No capital investments logged yet.</div>
                    <div v-for="tx in capitalTransactions" :key="tx.id"
                        class="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-500/10 rounded-xl border border-blue-100 dark:border-blue-500/20">
                        <div>
                            <p class="font-bold text-sm text-gray-900 dark:text-white">{{ tx.desc }}</p>
                            <p class="text-xs text-gray-500 mt-0.5">{{ tx.date }}</p>
                        </div>
                        <span class="font-mono font-bold text-blue-600 dark:text-blue-400">+₹{{ tx.amount.toLocaleString() }}</span>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    capitalTransactions,
    chartOptions,
    doughnutOptions,
    financeSummary,
    fuelAnomalyText,
    fuelAuditData,
    investmentModalOpen,
    paymentReconData,
    procurementCapitalData,
    revenueStreamData,
    store,
} = inject(reportsPageKey)
</script>

<style scoped src="./Reports.css"></style>
