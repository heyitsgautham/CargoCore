<template>
    <!-- 3. Exceptions & Discounts -->
    <div class="glass-panel rounded-xl overflow-hidden border border-purple-100 dark:border-purple-500/20">
        <div
            class="p-4 bg-purple-50 dark:bg-purple-900/10 flex items-center justify-between border-b border-purple-100 dark:border-purple-500/20">
            <div class="flex items-center gap-2">
                <span
                    class="material-symbols-outlined text-purple-600 dark:text-purple-400">local_offer</span>
                <h3 class="font-bold text-purple-900 dark:text-purple-100">Discount Logic</h3>
            </div>
        </div>
        <div class="p-5 space-y-4">
            <div
                class="p-4 bg-white dark:bg-black/20 rounded-xl border border-gray-100 dark:border-white/5 flex flex-col h-[400px]">
                <div class="flex items-center justify-between mb-4 flex-shrink-0">
                    <div>
                        <span
                            class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-purple-500">smart_toy</span>
                            AI Generated Quotations
                        </span>
                        <p class="text-[10px] text-gray-500 mt-1 max-w-[250px]">Review and approve
                            AI-negotiated custom volumetric rates.</p>
                    </div>
                    <span
                        class="bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 text-[10px] font-bold px-2 py-0.5 rounded-full">{{
                            pendingQuotes.length }} Awaiting</span>
                </div>

                <!-- Empty State -->
                <div v-if="pendingQuotes.length === 0"
                    class="flex-1 flex flex-col items-center justify-center bg-gray-50/50 dark:bg-black/10 rounded-lg border border-dashed border-gray-200 dark:border-white/10">
                    <span class="material-symbols-outlined text-gray-400 text-4xl mb-2">done_all</span>
                    <p class="text-xs text-gray-500 font-medium">All AI quotations reviewed</p>
                </div>

                <!-- Quotes List -->
                <div v-else class="flex-1 overflow-y-auto pr-1 space-y-3 custom-scrollbar">
                    <div v-for="quote in pendingQuotes" :key="quote.id"
                        class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 shadow-sm hover:border-purple-300 dark:hover:border-purple-500/30 transition-colors">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <h4 class="text-xs font-bold text-gray-900 dark:text-white">{{
                                    quote.customer }}</h4>
                                <p class="text-[10px] text-gray-500 flex items-center gap-1 mt-0.5">
                                    <span class="material-symbols-outlined text-[12px]">route</span> {{
                                        quote.origin }} → {{ quote.dest }}
                                </p>
                            </div>
                            <div class="text-right">
                                <span class="text-xs font-bold text-purple-600 dark:text-purple-400">₹{{
                                    quote.aiQuote.toLocaleString() }}</span>
                                <p class="text-[10px] text-red-500 line-through">₹{{
                                    quote.originalPrice.toLocaleString() }}</p>
                            </div>
                        </div>

                        <div
                            class="grid grid-cols-2 gap-2 mb-3 bg-white dark:bg-white/5 p-2 rounded-md border border-gray-100 dark:border-white/5">
                            <div>
                                <span class="block text-[9px] text-gray-500 uppercase font-bold">Valid
                                    From</span>
                                <span class="text-[11px] text-gray-800 dark:text-gray-300 font-mono">{{
                                    quote.startDate }}</span>
                            </div>
                            <div>
                                <span class="block text-[9px] text-gray-500 uppercase font-bold">Valid
                                    Until</span>
                                <span class="text-[11px] text-gray-800 dark:text-gray-300 font-mono">{{
                                    quote.endDate }}</span>
                            </div>
                            <div class="col-span-2 mt-1">
                                <div class="flex justify-between items-end">
                                    <span
                                        class="block text-[9px] text-gray-500 uppercase font-bold">Discount
                                        Applied</span>
                                    <span
                                        class="text-[10px] text-purple-600 dark:text-purple-400 font-bold leading-none">{{
                                            quote.discount }}% OFF</span>
                                </div>
                                <div
                                    class="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-1.5 mt-1.5 overflow-hidden">
                                    <div class="bg-gradient-to-r from-purple-400 to-purple-600 h-1.5 rounded-full"
                                        :style="{ width: `${quote.discount}%` }"></div>
                                </div>
                            </div>
                        </div>

                        <div class="flex gap-2">
                            <button @click="approveQuote(quote.id)" :disabled="!isEditMode"
                                class="flex-1 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:hover:bg-green-900/40 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 rounded py-1.5 text-[11px] font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">check</span> Approve
                            </button>
                            <button @click="denyQuote(quote.id)" :disabled="!isEditMode"
                                class="flex-1 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 rounded py-1.5 text-[11px] font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">close</span> Deny
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="bg-red-50 dark:bg-red-900/10 p-3 rounded-lg flex items-start gap-2 border border-red-100 dark:border-red-500/20">
                <span class="material-symbols-outlined text-red-500 text-[16px] mt-0.5">lock</span>
                <p class="text-[10px] text-red-800 dark:text-red-200">Dispatchers and Warehouse Managers are
                    <strong>hard-locked</strong> from modifying price quotes.
                </p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { approveQuote, denyQuote, isEditMode, pendingQuotes } = inject(rateGovernancePageKey)
</script>
