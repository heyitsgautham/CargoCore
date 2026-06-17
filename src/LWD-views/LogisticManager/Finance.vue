<template>
    <div class="flex flex-col gap-4">
        <!-- Header -->
        <div class="flex justify-between items-center bg-slate-800/80 p-4 rounded-xl shadow-sm border border-white/10">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">account_balance_wallet</span>
                    Finance & Payroll
                </h2>
                <p class="text-xs text-gray-500 mt-1">Manage cash flow, reconcile COD, and process payments across all departments.</p>
            </div>
            <div class="flex gap-3">
                <div class="relative group">
                    <button @click="openPayrollModal" :disabled="!filteredUsers.some(u => u.pending_payout > 0)"
                        class="bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-emerald-400/20">
                        <span class="material-symbols-outlined">payments</span> Pay All Due
                    </button>
                    <div v-if="!filteredUsers.some(u => u.pending_payout > 0)" class="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-48 bg-black/80 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none text-center">
                        No pending payouts
                    </div>
                </div>
                <button @click="openBulkActionModal" 
                    class="bg-slate-800 hover:bg-slate-700 dark:bg-purple-600 dark:hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-slate-700 dark:border-purple-400/20">
                    <span class="material-symbols-outlined">auto_fix_high</span> Smart Bonus/Deduct
                </button>
                <button @click="openTransactionModal" 
                    class="bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 border border-slate-700 dark:border-primary/30">
                    <span class="material-symbols-outlined">add_circle</span> New Record
                </button>
            </div>
        </div>

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

        <!-- Tabs Navigation -->
        <div class="flex gap-1 bg-slate-100 dark:bg-slate-800/70 p-1 rounded-lg self-start border border-gray-200 dark:border-white/10 shadow-sm">
            <button v-for="tab in tabs" :key="tab.id"
                @click="activeTab = tab.id"
                class="px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-1.5"
                :class="activeTab === tab.id ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-600 dark:text-white' : 'text-slate-600 hover:text-slate-900 hover:bg-white/70 dark:text-slate-300 dark:hover:text-white dark:hover:bg-white/5'">
                <span class="material-symbols-outlined text-[16px]">{{ tab.icon }}</span>
                {{ tab.label }}
            </button>
        </div>

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

        <!-- Smart Bonus/Deduct Modal -->
         <Teleport to="body">
            <div v-if="showBulkActionModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div class="bg-slate-900 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-scale-in border border-white/10">
                    <div class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-800/80">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                                <span class="material-symbols-outlined">auto_fix_high</span>
                            </div>
                            <div>
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white">Smart Bonus & Deductions</h3>
                                <p class="text-xs text-gray-500">Apply financial adjustments to multiple staff members based on criteria.</p>
                            </div>
                        </div>
                        <button @click="showBulkActionModal = false" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    
                    <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 h-[400px] overflow-y-auto custom-scrollbar">
                        <!-- Left: Filters & Actions -->
                        <div class="space-y-4">
                            <div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-2">Target Group</label>
                                <select v-model="bulkForm.role" class="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-purple-500/50 text-slate-100">
                                    <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Staff</option>
                                    <option value="Driver" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Drivers Only</option>
                                    <option value="Dispatcher" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Dispatchers Only</option>
                                    <option value="Warehouse Manager" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Warehouse Managers</option>
                                </select>
                            </div>

                            <div class="bg-slate-800/80 p-3 rounded-lg border border-white/10 space-y-3">
                                <p class="text-xs font-bold text-gray-500 uppercase">Performance Criteria</p>
                                <div class="flex items-center gap-2">
                                    <input type="checkbox" v-model="bulkForm.filterByRating" class="rounded text-purple-600 focus:ring-purple-500 border-gray-300">
                                    <span class="text-sm text-gray-700 dark:text-gray-300">Rating Above</span>
                                    <input type="number" step="0.1" max="5" min="0" v-model="bulkForm.minRating" :disabled="!bulkForm.filterByRating" class="w-16 bg-slate-950 border border-white/10 rounded px-2 py-1 text-xs text-slate-100">
                                </div>
                                <div class="flex items-center gap-2">
                                    <input type="checkbox" v-model="bulkForm.filterByTrips" class="rounded text-purple-600 focus:ring-purple-500 border-gray-300">
                                    <span class="text-sm text-gray-700 dark:text-gray-300">Completed Trips ></span>
                                    <input type="number" v-model="bulkForm.minTrips" :disabled="!bulkForm.filterByTrips" class="w-16 bg-slate-950 border border-white/10 rounded px-2 py-1 text-xs text-slate-100">
                                </div>
                            </div>

                            <div class="pt-4 border-t border-white/10">
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-2">Action Type</label>
                                <div class="grid grid-cols-2 gap-2 mb-3">
                                    <button @click="bulkForm.type = 'Bonus'" 
                                        class="py-2 rounded-lg text-sm font-bold border transition-colors flex items-center justify-center gap-1"
                                        :class="bulkForm.type === 'Bonus' ? 'bg-green-500/15 text-green-300 border-green-500/30' : 'bg-slate-900 text-slate-300 border-white/10 hover:bg-slate-800'">
                                        <span class="material-symbols-outlined text-[16px]">add_circle</span> Bonus
                                    </button>
                                    <button @click="bulkForm.type = 'Deduction'" 
                                        class="py-2 rounded-lg text-sm font-bold border transition-colors flex items-center justify-center gap-1"
                                        :class="bulkForm.type === 'Deduction' ? 'bg-red-500/15 text-red-300 border-red-500/30' : 'bg-slate-900 text-slate-300 border-white/10 hover:bg-slate-800'">
                                        <span class="material-symbols-outlined text-[16px]">remove_circle</span> Deduct
                                    </button>
                                </div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Amount (₹)</label>
                                <input v-model.number="bulkForm.amount" type="number" class="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-purple-500/50 font-mono font-bold text-lg text-slate-100">
                                <input v-model="bulkForm.reason" type="text" placeholder="Reason (e.g. Performance Bonus)" class="w-full mt-2 bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-purple-500/50 text-slate-100 placeholder:text-slate-400">
                            </div>
                        </div>

                        <!-- Right: Preview Users -->
                        <div class="flex flex-col h-full bg-slate-800/80 rounded-xl border border-white/10 overflow-hidden">
                            <div class="p-3 border-b border-white/10 bg-slate-800 flex justify-between items-center">
                                <span class="text-xs font-bold uppercase text-gray-500">Affected Users ({{ bulkTargetUsers.length }})</span>
                                <span class="text-xs font-mono font-bold" :class="bulkForm.type === 'Bonus' ? 'text-green-600' : 'text-red-600'">
                                    Total: ₹{{ (bulkTargetUsers.length * bulkForm.amount).toLocaleString() }}
                                </span>
                            </div>
                            <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                                <div v-for="user in bulkTargetUsers" :key="user.username" class="flex items-center gap-2 p-2 rounded bg-slate-900 border border-white/10 transition-all hover:translate-x-1">
                                    <img :src="user.avatar" class="w-8 h-8 rounded-full bg-gray-200">
                                    <div class="flex-1 min-w-0">
                                        <p class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ user.name }}</p>
                                        <p class="text-[10px] text-gray-500 truncate">{{ user.role }} • Rating: {{ user.rating || 'N/A' }}</p>
                                    </div>
                                    <span class="text-xs font-bold" :class="bulkForm.type === 'Bonus' ? 'text-green-600' : 'text-red-600'">
                                        {{ bulkForm.type === 'Bonus' ? '+' : '-' }}₹{{ bulkForm.amount }}
                                    </span>
                                </div>
                                <div v-if="bulkTargetUsers.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400 p-4 text-center">
                                    <span class="material-symbols-outlined text-3xl mb-2">groups</span>
                                    <p class="text-xs">No users match criteria</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="p-4 bg-slate-800/80 flex justify-end gap-2 border-t border-white/10">
                        <button @click="showBulkActionModal = false" class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900">Cancel</button>
                        <button @click="applyBulkAction" :disabled="bulkTargetUsers.length === 0 || bulkForm.amount <= 0 || bulkApplying"
                            class="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold rounded-lg shadow-lg shadow-purple-500/20 transition-all flex items-center gap-2">
                            <span v-if="bulkApplying" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                            <span v-else class="material-symbols-outlined text-[18px]">done_all</span>
                            {{ bulkApplying ? 'Applying...' : `Apply to ${bulkTargetUsers.length} Users` }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

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
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import salarySlipTemplate from '../../../html-slips/SalarySlip.html?raw'

const store = useLogisticStore()
const {
    filteredTransactions,
    filteredUsers,
    activeFinanceSummary,
    filteredFinanceCodRecords,
    filteredFinanceStaffRecords,
    filteredFinanceDriverRecords,
    initialized,
    isLoading,
} = storeToRefs(store)

const financeLoaded = computed(() => initialized.value && !isLoading.value)
const { openSlipWithData, prefetchSlips } = useSlipPrinter()

onMounted(() => {
    store.initialize().catch(() => {})
    store.fetchFinanceSummary(store.activeWarehouse).catch(() => {})
    prefetchSlips(['bookingConfirmation', 'financeTransaction']).catch(() => {})
})

// View State
const activeTab = ref('overview') // overview, cod, staff, drivers
const searchQuery = ref('')
const expandedRow = ref(null)
const showTransactionModal = ref(false)
const reconcileModalOpen = ref(false)
const selectedItem = ref(null)
const reconcileAmount = ref(0)
const newTx = ref({ desc: '', type: 'Expense', amount: 0, hubId: null })

// Payroll Modal State
const showPayrollModal = ref(false)
const payrollProcessing = ref(false)
const payrollSuccess = ref(false)
const payrollSummary = ref({ count: 0, total: 0, pendingUsers: [] })

// Single Payment State
const showPaymentModal = ref(false)
const paymentTarget = ref(null)
const paymentProcessing = ref(false)
const paymentSuccess = ref(false)

// Bulk Action State
const showBulkActionModal = ref(false)
const bulkApplying = ref(false)
const bulkForm = ref({
    type: 'Bonus', // Bonus or Deduct
    amount: 0,
    reason: '',
    role_filter: 'All', // All, Driver, warehouse_staff
    min_rating: 0,
    min_trips: 0
})

// Bulk Computed Logic
const bulkTargetUsers = computed(() => {
    if (!bulkForm.value.min_rating && !bulkForm.value.min_trips && bulkForm.value.role_filter === 'All') {
        return [] // Safety: Don't select everyone by default if no filters
    }

    return filteredUsers.value.filter(user => {
        // 1. Role Filter
        if (bulkForm.value.role_filter !== 'All' && user.role !== bulkForm.value.role_filter) return false
        
        const topDriver = store.topDrivers.find(driver => driver.name === user.name)
        const derivedRating = user.rating || topDriver?.rating || 4.0
        const derivedTrips = user.trips || topDriver?.trips || Math.max(0, Math.round(user.pending_payout / 50))

        // 3. Apply Filters
        if (bulkForm.value.min_rating > 0 && parseFloat(derivedRating) < bulkForm.value.min_rating) return false
        if (bulkForm.value.min_trips > 0 && derivedTrips < bulkForm.value.min_trips) return false

        return true
    }).map(u => ({
        ...u,
        _mockRating: u.rating || store.topDrivers.find(driver => driver.name === u.name)?.rating || 4.0,
        _mockTrips: u.trips || store.topDrivers.find(driver => driver.name === u.name)?.trips || Math.max(0, Math.round(u.pending_payout / 50))
    }))
})

// Bulk Methods
const openBulkActionModal = () => {
    bulkForm.value = {
        type: 'Bonus',
        amount: 50,
        reason: 'Performance Bonus',
        role_filter: 'Driver',
        min_rating: 4.5,
        min_trips: 10
    }
    showBulkActionModal.value = true
}

const applyBulkAction = async () => {
    if (!bulkTargetUsers.value.length || bulkApplying.value) return
    bulkApplying.value = true
    try {
        const isBonus = bulkForm.value.type === 'Bonus'
        const txType = isBonus ? 'Expense' : 'Income'
        const amountSign = isBonus ? -1 : 1
        const date = new Date().toISOString().split('T')[0]

        // Create one transaction record per affected user
        await Promise.all(bulkTargetUsers.value.map(user =>
            store.addTransaction({
                date,
                desc: `${bulkForm.value.type} – ${user.name}${bulkForm.value.reason ? ': ' + bulkForm.value.reason : ''}`,
                amount: bulkForm.value.amount * amountSign,
                type: txType,
                status: 'Completed',
                hubId: store.activeWarehouse
            })
        ))
        showBulkActionModal.value = false
    } catch (e) {
        alert(`Failed to apply: ${e.message || 'Unknown error'}`)
    } finally {
        bulkApplying.value = false
    }
}

const openPayrollModal = () => {
    payrollSuccess.value = false
    const pending = filteredUsers.value.filter(u => u.pending_payout > 0)
    
    if (pending.length === 0) {
        // Optional: show a toast or small notification instead of alert
        return
    }

    payrollSummary.value = {
        count: pending.length,
        total: pending.reduce((sum, u) => sum + u.pending_payout, 0),
        pendingUsers: pending
    }
    showPayrollModal.value = true
}

const confirmPayrollRun = async () => {
    payrollProcessing.value = true

    // Build per-user payout list for the backend
    const staffPayouts = filteredFinanceStaffRecords.value
        .filter(item => item.status === 'Pending' && item.amount > 0)
        .map(item => ({ user_id: item.userId, amount: item.amount, record_type: 'staff', name: item.name }))
    const driverPayouts = filteredFinanceDriverRecords.value
        .filter(item => item.status === 'Pending' && item.amount > 0)
        .map(item => ({ user_id: item.userId, amount: item.amount, record_type: 'driver', name: item.name }))

    try {
        await store.runPayroll([...staffPayouts, ...driverPayouts])

        // Update local record statuses so UI responds immediately without refresh
        filteredFinanceStaffRecords.value
            .filter(item => item.status === 'Pending')
            .forEach(item => store.markFinanceRecordPaid('staff', item.id))
        filteredFinanceDriverRecords.value
            .filter(item => item.status === 'Pending')
            .forEach(item => store.markFinanceRecordPaid('drivers', item.id))

        // Clear pending_payout on user objects
        payrollSummary.value.pendingUsers.forEach(u => { u.pending_payout = 0 })

        payrollSuccess.value = true
    } catch (e) {
        console.error('Payroll run failed:', e)
    } finally {
        payrollProcessing.value = false
    }
}

// Tabs Configuration
const tabs = [
    { id: 'overview', label: 'Overview', icon: 'dashboard' },
    { id: 'cod', label: 'COD Reconciliation', icon: 'payments' },
    { id: 'staff', label: 'Staff Payroll', icon: 'badge' },
    { id: 'drivers', label: 'Driver/Labor Payouts', icon: 'engineering' }
]

// Computed Data & Logic
const activeTabLabel = computed(() => {
    return tabs.find(t => t.id === activeTab.value)?.label || 'Transactions'
})

const totalRevenue = computed(() => activeFinanceSummary.value.total_revenue ??
    filteredTransactions.value
        .filter(t => t.amount > 0 && t.type !== 'CAPITAL_INVESTMENT')
        .reduce((sum, t) => sum + t.amount, 0))
const totalExpenses = computed(() => activeFinanceSummary.value.total_expenses ??
    Math.abs(filteredTransactions.value.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0)))
const totalPayrollDue = computed(() =>
    [...filteredFinanceStaffRecords.value, ...filteredFinanceDriverRecords.value]
        .filter(item => item.status === 'Pending')
        .reduce((sum, item) => sum + (item.amount || 0), 0)
)
const capitalInflow = computed(() => activeFinanceSummary.value.capital_invested ??
    filteredTransactions.value.filter(t => t.type === 'CAPITAL_INVESTMENT').reduce((sum, t) => sum + t.amount, 0))
const pendingCOD = computed(() => filteredFinanceCodRecords.value
    .filter(item => item.status === 'Pending')
    .reduce((sum, item) => sum + (item.amount || 0), 0))

const reconcileDiff = computed(() => {
    if(!selectedItem.value) return 0
    return reconcileAmount.value - selectedItem.value.amount
})

const filteredItems = computed(() => {
    let items = []
    
    if (activeTab.value === 'overview') {
        items = filteredTransactions.value
    } else if (activeTab.value === 'cod') {
        items = filteredFinanceCodRecords.value
    } else if (activeTab.value === 'staff') {
        items = filteredFinanceStaffRecords.value
    } else if (activeTab.value === 'drivers') {
        items = filteredFinanceDriverRecords.value
    }

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        items = items.filter(i => 
            (i.desc && i.desc.toLowerCase().includes(q)) || 
            (i.name && i.name.toLowerCase().includes(q)) ||
            (i.id && i.id.toLowerCase().includes(q))
        )
    }
    return items
})

// Actions
const toggleRow = (id) => {
    expandedRow.value = expandedRow.value === id ? null : id
}

const openTransactionModal = () => {
    newTx.value = { desc: '', type: 'Expense', amount: 0, hubId: store.activeWarehouse }
    showTransactionModal.value = true
}

const addTransaction = async () => {
    let finalAmount = Math.abs(newTx.value.amount)
    if (newTx.value.type !== 'Incoming') finalAmount = -finalAmount

    await store.addTransaction({
        hubId: newTx.value.hubId || store.activeWarehouse,
        desc: newTx.value.desc,
        type: newTx.value.type,
        amount: finalAmount,
        status: 'Completed'
    })
    showTransactionModal.value = false
}

const openReconcileModal = (item) => {
    selectedItem.value = item
    reconcileAmount.value = item.amount
    reconcileModalOpen.value = true
}

const confirmReconciliation = () => {
    store.markFinanceRecordPaid('cod', selectedItem.value.id)
    reconcileModalOpen.value = false
}

const payUser = (item) => {
    paymentTarget.value = item
    showPaymentModal.value = true
    paymentSuccess.value = false
    paymentProcessing.value = false
}

const confirmSinglePayment = async () => {
    paymentProcessing.value = true
    
    // Simulate transaction
    await new Promise(resolve => setTimeout(resolve, 1500))

    await store.addTransaction({
        hubId: store.activeWarehouse,
        date: new Date().toLocaleDateString(),
        desc: `Payout to ${paymentTarget.value.name}`,
        type: 'Expense',
        amount: -paymentTarget.value.amount,
        status: 'Completed'
    })

    store.markFinanceRecordPaid(activeTab.value === 'staff' ? 'staff' : 'drivers', paymentTarget.value.id)
    const targetUser = filteredUsers.value.find((user) => user.id === paymentTarget.value.userId)
    if (targetUser) targetUser.pending_payout = 0

    paymentProcessing.value = false
    paymentSuccess.value = true

    // Auto close
    setTimeout(() => {
        showPaymentModal.value = false
        paymentSuccess.value = false
        paymentTarget.value = null
    }, 2000)
}

const TRACKING_CODE_REGEX = /\b([A-Z]{2,5}-[A-Z0-9]{4,})\b/i

const extractTrackingCode = (value) => {
    const match = String(value || '').match(TRACKING_CODE_REGEX)
    return match?.[1]?.toUpperCase() || ''
}

const findRelatedOrder = (item) => {
    if (item.relatedOrder) return item.relatedOrder
    const metadata = item.metadataJson || {}
    const trackingCode = (
        item.desc === item.id
            ? item.desc
            : metadata.tracking_code || extractTrackingCode(item.desc) || extractTrackingCode(item.id)
    )
    if (!trackingCode) return null
    return filteredTransactions.value.find(tx => tx.relatedOrder?.tracking_code === trackingCode)?.relatedOrder || null
}

const isPayrollSlip = (item) => (
    activeTab.value === 'staff'
    || activeTab.value === 'drivers'
    || item.type === 'PAYROLL_RUN'
)

const isBookingSlip = (item) => ['REVENUE_ONLINE', 'REVENUE_COD', 'COD'].includes(item.type)

const buildBookingSlipPayload = (item) => {
    const order = findRelatedOrder(item)
    if (!order) return null

    return {
        order: {
            id: order.tracking_code || order.id,
            createdAt: order.created_at || item.date,
            eta: order.scheduled_at || order.created_at || item.date,
            serviceTimeBlock: order.service_time_block || 'Flexible',
            origin: order.pickup_addr || '—',
            destination: order.delivery_addr || '—',
            amount: Number(order.total_amount ?? Math.abs(item.amount || 0)),
            paidAmount: Number(order.paid_amount ?? Math.abs(item.amount || 0)),
            paymentMode: order.payment_mode || item.metadataJson?.payment_mode || txTypeLabel(item.type),
            laborCount: Number(order.labor_count || 0),
            vehicleType: order.vehicle_type || order.assigned_vehicle_code || 'Assigned vehicle',
        },
        user: {
            name: order.customer_name || 'Customer',
            phone: order.customer_phone || '—',
            email: order.customer_email || '—',
        },
    }
}

const financeSlipTitle = (item) => {
    if (item.type === 'EXPENSE_DRIVER') return 'Driver Shift Fee Slip'
    if (item.type === 'EXPENSE_FUEL' || item.type === 'FUEL_EXPENSE') return 'Fuel Expense Slip'
    if (item.type === 'REVENUE_RETURN_CHARGE') return 'Transport Charge Slip'
    if (item.type === 'REVENUE_REFUND' && item.desc?.toLowerCase().includes('damage')) return 'Damage Return Refund Slip'
    if (item.type === 'REVENUE_REFUND') return 'Refund / Reversal Slip'
    if (item.type === 'DRIVER_CASHOUT') return 'Driver Cashout Slip'
    if (item.type === 'CAPITAL_INVESTMENT') return 'Capital Investment Slip'
    return 'Finance Transaction Slip'
}

const buildFinanceSlipPayload = (item) => {
    const metadata = item.metadataJson || {}
    const relatedOrder = findRelatedOrder(item)
    const trackingCode = relatedOrder?.tracking_code || metadata.tracking_code || extractTrackingCode(item.desc)
    const beneficiary = metadata.driver_name
        || relatedOrder?.customer_name
        || item.name
        || 'Cargo-Core Ledger'

    return {
        ...item,
        metadataJson: metadata,
        relatedOrder,
        slipTitle: financeSlipTitle(item),
        typeLabel: txTypeLabel(item.type),
        beneficiary,
        transactionCode: item.transactionCode || item.id,
        notes: trackingCode
            ? `${item.desc}. Linked reference: ${trackingCode}.`
            : `${item.desc}.`,
    }
}

const openSalarySlip = (item) => {
    const now = new Date()
    const period = now.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
    const paymentDate = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    const shortDate = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

    const net = Math.round(Math.abs(item.amount || 0))
    const profTax = 200
    const tds = Math.round(net * 0.1)
    const totalDeductions = profTax + tds
    const gross = net + totalDeductions
    const basic = Math.round(gross * 0.70)
    const hra = Math.round(gross * 0.20)
    const transport = 2500
    const special = Math.max(0, gross - basic - hra - transport)

    const empId = (item.userId || item.id || '').slice(0, 6).toUpperCase()
    const name = item.name || 'Employee'
    const role = item.role || 'Staff'

    const html = salarySlipTemplate
        // meta & title
        .replace('Salary Slip – February 2026', `Salary Slip – ${period}`)
        .replace('For the month of February 2026', `For the month of ${period}`)
        // employee details
        .replace('Siddarth S', name)
        .replace('WM001', empId)
        .replace('Warehouse Manager', role)
        .replace('28 February 2026', paymentDate)
        // earnings
        .replace('42,000</td>', `${basic.toLocaleString('en-IN')}</td>`)
        .replace('12,000</td>', `${hra.toLocaleString('en-IN')}</td>`)
        .replace('2,500</td>', `${transport.toLocaleString('en-IN')}</td>`)
        .replace('3,500</td>', `${special.toLocaleString('en-IN')}</td>`)
        .replace('₹60,000</td>', `₹${gross.toLocaleString('en-IN')}</td>`)
        // deductions
        .replace('200</td>', `${profTax}</td>`)
        .replace('4,200</td>', `${tds.toLocaleString('en-IN')}</td>`)
        .replace('₹4,400</td>', `₹${totalDeductions.toLocaleString('en-IN')}</td>`)
        // net pay
        .replace('₹55,600</div>', `₹${net.toLocaleString('en-IN')}</div>`)
        // signature date
        .replace('28 Feb 2026', shortDate)

    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const win = window.open(url, '_blank')
    if (win) win.addEventListener('load', () => URL.revokeObjectURL(url))
}

const downloadSlip = async (item) => {
    if (isPayrollSlip(item)) {
        openSalarySlip(item)
        return
    }

    if (isBookingSlip(item)) {
        const bookingPayload = buildBookingSlipPayload(item)
        if (bookingPayload) {
            await openSlipWithData('bookingConfirmation', bookingPayload.order, bookingPayload.user)
            return
        }
    }

    await openSlipWithData('financeTransaction', buildFinanceSlipPayload(item))
}

const TX_TYPE_LABELS = {
    'REVENUE_ONLINE': 'Online Payment',
    'REVENUE_COD': 'COD Collection',
    'REVENUE_RETURN_CHARGE': 'Return Transport Charge',
    'REVENUE_REFUND': 'Refund / Reversal',
    'EXPENSE_DRIVER': 'Driver Cost',
    'EXPENSE_LABOUR': 'Labour Cost',
    'EXPENSE_FUEL': 'Fuel',
    'FUEL_EXPENSE': 'Fuel Receipt',
    'EXPENSE_WAREHOUSE': 'Warehouse',
    'EXPENSE_PROCUREMENT': 'Procurement',
    'PAYROLL_RUN': 'Payroll',
    'DRIVER_CASHOUT': 'Driver Cashout',
    'CAPITAL_INVESTMENT': 'Capital Investment',
    'COD': 'COD Collection',
    'Expense': 'Expense',
    'Incoming': 'Income',
    'Payroll': 'Payroll',
}
const txTypeLabel = (type) => TX_TYPE_LABELS[type] || type


</script>

<style scoped>
.lm-transaction-modal {
    color: #e2e8f0;
}

.lm-transaction-modal :deep(label) {
    color: #cbd5e1 !important;
}

.lm-transaction-modal :deep(input),
.lm-transaction-modal :deep(select),
.lm-transaction-modal :deep(textarea) {
    background-color: rgba(15, 23, 42, 0.92) !important;
    color: #f8fafc !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color-scheme: dark;
}

.lm-transaction-modal :deep(input::placeholder),
.lm-transaction-modal :deep(textarea::placeholder) {
    color: #94a3b8 !important;
}

.lm-transaction-modal :deep(option) {
    background-color: rgb(15 23 42) !important;
    color: #f8fafc !important;
}

.lm-transaction-modal :deep(.text-gray-400),
.lm-transaction-modal :deep(.text-gray-500) {
    color: #94a3b8 !important;
}

.lm-transaction-modal :deep(input[type='date']::-webkit-calendar-picker-indicator) {
    filter: invert(1);
    opacity: 0.85;
}
</style>


