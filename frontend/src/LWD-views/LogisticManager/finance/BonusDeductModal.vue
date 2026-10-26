<template>
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
                            <div v-for="user in bulkTargetUsers" :key="user.id" class="flex items-center gap-2 p-2 rounded bg-slate-900 border border-white/10 transition-all hover:translate-x-1">
                                <img :src="user.avatar" class="w-8 h-8 rounded-full bg-gray-200">
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ user.name }}</p>
                                    <p class="text-[10px] text-gray-500 truncate">{{ user.role }} • Rating: {{ formatBulkRating(user.rating) }}</p>
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
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const {
    applyBulkAction,
    bulkApplying,
    bulkForm,
    bulkTargetUsers,
    formatBulkRating,
    showBulkActionModal,
} = inject(financePageKey)
</script>
