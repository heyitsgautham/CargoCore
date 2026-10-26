<template>
    <!-- Main Content Area -->
    <div class="glass-panel rounded-xl overflow-hidden flex flex-col border border-gray-200 dark:border-white/5 relative" style="height: calc(100vh - 18rem)">
        <!-- Filter Bar -->
        <div class="p-4 border-b border-gray-200 dark:border-white/10 flex justify-between items-center bg-slate-50 dark:bg-slate-800/70">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                {{ activeTabLabel }}
            </h3>
            <div class="flex gap-2">
                <div class="relative">
                    <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input v-model="searchQuery" type="text" placeholder="Search records..." 
                        class="pl-9 pr-4 py-1.5 bg-white dark:bg-slate-900/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 text-slate-700 dark:text-slate-200 placeholder:text-slate-400 w-64 shadow-sm">
                </div>
            </div>
        </div>

        <div class="flex-1 overflow-auto custom-scrollbar bg-white dark:bg-slate-900/70">
            <table class="w-full text-left text-sm border-separate border-spacing-0">
                <thead class="bg-slate-100 dark:bg-slate-800 sticky top-0 z-10 shadow-sm">
                    <tr class="text-gray-500 dark:text-gray-400 uppercase tracking-wider text-[10px]">
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10">Ref ID</th>
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10">Date</th>
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10">
                            {{ activeTab === 'cod' ? 'Driver / Route' : 'Beneficiary / Description' }}
                        </th>
                        <th v-if="activeTab !== 'cod'" class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10">Role/Category</th>
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10 text-right">Amount</th>
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10 text-right">Status</th>
                        <th class="py-3 px-4 font-medium border-b border-gray-200 dark:border-white/10 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <template v-for="item in filteredItems" :key="item.id">
                        <!-- Main Row -->
                        <tr @click="toggleRow(item.id)"
                            class="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors cursor-pointer group"
                            :class="expandedRow === item.id ? 'bg-primary/5 dark:bg-primary/10' : ''">
                            <td class="py-4 px-4 font-mono text-gray-600 dark:text-gray-300 text-xs flex items-center gap-2">
                                <span class="material-symbols-outlined text-gray-400 transition-transform text-sm"
                                    :class="expandedRow === item.id ? 'rotate-90 text-primary' : ''">chevron_right</span>
                                {{ item.id }}
                            </td>
                            <td class="py-4 px-4 text-gray-500 dark:text-gray-400">{{ item.date }}</td>
                            <td class="py-4 px-4 font-medium text-gray-900 dark:text-white">
                                <div class="flex items-center gap-2">
                                    <div v-if="item.avatar" class="w-8 h-8 rounded-full overflow-hidden bg-gray-200 shrink-0">
                                        <img :src="item.avatar" class="w-full h-full object-cover">
                                    </div>
                                    <span>{{ item.desc || item.name }}</span>
                                </div>
                            </td>
                            <td v-if="activeTab !== 'cod'" class="py-4 px-4">
                                <span class="px-2 py-0.5 rounded text-[11px] border"
                                    :class="item.type === 'REVENUE_REFUND'
                                        ? 'bg-red-500/10 text-red-400 border-red-500/30'
                                        : item.type === 'PAYROLL_RUN'
                                        ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                                        : 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/10 dark:text-slate-300 dark:border-white/10'">
                                    {{ item.role || txTypeLabel(item.type) }}
                                </span>
                            </td>
                            <td class="py-4 px-4 font-bold font-mono text-right"
                                :class="item.amount > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
                                {{ item.amount > 0 ? '+' : '' }}{{ item.amount.toLocaleString() }}
                            </td>
                            <td class="py-4 px-4 text-right">
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                                    :class="{
                                        'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:text-green-400': item.status === 'Completed' || item.status === 'Paid',
                                        'bg-yellow-50 border-yellow-200 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400': item.status === 'Pending',
                                        'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:text-red-400': item.status === 'Overdue'
                                    }">
                                    {{ item.status }}
                                </span>
                            </td>
                            <td class="py-4 px-4 text-right">
                                <button v-if="item.status === 'Pending' && activeTab === 'cod'" 
                                    @click.stop="openReconcileModal(item)"
                                    class="text-xs bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded transition-colors shadow-sm">
                                    Reconcile
                                </button>
                                <button v-else-if="item.status === 'Pending' && (activeTab === 'staff' || activeTab === 'drivers')"
                                    @click.stop="payUser(item)"
                                    class="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded transition-colors shadow-sm flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">payments</span> Pay
                                </button>
                                <button v-else
                                    @click.stop="downloadSlip(item)"
                                    class="text-gray-400 hover:text-primary transition-colors tooltip" title="Download Slip">
                                    <span class="material-symbols-outlined text-[20px]">download</span>
                                </button>
                            </td>
                        </tr>

                        <!-- Expanded Detail Row -->
                        <tr v-if="expandedRow === item.id" class="bg-slate-50/80 dark:bg-white/[0.03]">
                            <td :colspan="activeTab === 'cod' ? 6 : 7" class="p-4 border-b border-gray-200 dark:border-white/10">
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm ml-8">
                                    <div class="space-y-2">
                                        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest">Transaction Details</p>
                                        <div class="grid grid-cols-2 gap-y-1 text-gray-600 dark:text-gray-400">
                                            <span>Transaction ID:</span> <span class="font-mono text-gray-900 dark:text-white">{{ item.id }}</span>
                                            <span>Date processed:</span> <span>{{ item.date }}</span>
                                            <span>Payment Method:</span> <span>Direct Deposit</span>
                                            <span>Reference:</span> <span>#REF-{{ Math.floor(Math.random()*10000) }}</span>
                                        </div>
                                    </div>
                                    <div class="space-y-2">
                                        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest">Breakdown</p>
                                        <div class="bg-white dark:bg-slate-900/80 p-3 rounded border border-gray-200 dark:border-white/10 space-y-1 shadow-sm">
                                            <div class="flex justify-between text-gray-600 dark:text-gray-400">
                                                <span>Base Amount</span>
                                                <span>₹{{ Math.abs(item.amount * 0.9).toFixed(2) }}</span>
                                            </div>
                                            <div class="flex justify-between text-gray-600 dark:text-gray-400">
                                                <span>Tax / Deductions</span>
                                                <span>₹{{ Math.abs(item.amount * 0.1).toFixed(2) }}</span>
                                            </div>
                                            <div class="border-t border-gray-200 dark:border-white/10 pt-1 mt-1 flex justify-between font-bold text-gray-900 dark:text-white">
                                                <span>Total</span>
                                                <span>₹{{ Math.abs(item.amount).toLocaleString() }}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex flex-col justify-end items-start gap-2">
                                        <button @click="downloadSlip(item)" class="text-xs text-primary hover:underline flex items-center gap-1">
                                            <span class="material-symbols-outlined text-[16px]">description</span> Download Invoice/Slip
                                        </button>
                                         <button class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1">
                                            <span class="material-symbols-outlined text-[16px]">report</span> Report Issue
                                        </button>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </template>

                    <tr v-if="filteredItems.length === 0">
                        <td :colspan="activeTab === 'cod' ? 6 : 7" class="py-12 text-center text-gray-500 flex flex-col items-center justify-center">
                            <span class="material-symbols-outlined text-4xl mb-2 opacity-20">inbox</span>
                            No records found for this category.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const {
    activeTab,
    activeTabLabel,
    downloadSlip,
    expandedRow,
    filteredItems,
    openReconcileModal,
    payUser,
    searchQuery,
    toggleRow,
    txTypeLabel,
} = inject(financePageKey)
</script>
