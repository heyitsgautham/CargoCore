<template>
    <!-- Log Investment Modal -->
    <div v-if="investmentModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
        <div
            class="bg-slate-950/98 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden border border-white/10 backdrop-blur-xl">
            <div class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                <h3 class="font-bold text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">add_card</span> Log Capital Investment
                </h3>
                <button @click="investmentModalOpen = false" class="text-gray-400 hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Amount (₹) *</label>
                    <input v-model.number="investmentForm.amount" type="number" min="1" placeholder="e.g. 10000"
                        class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Description *</label>
                    <input v-model="investmentForm.description" type="text" placeholder="e.g. Vendor payment — offline"
                        class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Funding Source</label>
                    <select v-model="investmentForm.funding_source"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50">
                        <option value="APP_REVENUE">💰 App Revenue</option>
                        <option value="OFFLINE_CAPITAL">🏦 Offline Capital</option>
                        <option value="BANK_TRANSFER">🏧 Bank Transfer</option>
                        <option value="OWNER_EQUITY">🤝 Owner Equity</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Date</label>
                    <input v-model="investmentForm.investment_date" type="date"
                        class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                </div>
            </div>
            <div class="p-4 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                <button @click="investmentModalOpen = false"
                    class="px-4 py-2 text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 rounded-lg font-bold text-sm">Cancel</button>
                <button @click="submitInvestment" :disabled="investmentSubmitting"
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-bold text-sm flex items-center gap-2">
                    <span v-if="investmentSubmitting" class="animate-spin material-symbols-outlined text-[16px]">progress_activity</span>
                    {{ investmentSubmitting ? 'Saving...' : 'Log Investment' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const { investmentForm, investmentModalOpen, investmentSubmitting, submitInvestment } = inject(reportsPageKey)
</script>
