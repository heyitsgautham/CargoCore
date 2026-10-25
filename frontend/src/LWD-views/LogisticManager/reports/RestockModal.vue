<template>
    <!-- Restock Modal -->
    <div v-if="restockModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
        <div
            class="bg-slate-950/98 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col max-h-[90vh] backdrop-blur-xl">
            <div
                class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                <h3 class="font-bold text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-600">inventory</span> Pending Restock Requests
                </h3>
                <button @click="restockModalOpen = false"
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 overflow-y-auto custom-scrollbar">
                <p class="text-sm text-gray-500 mb-4">Review pending restock requests from Warehouse Managers.</p>

                <div class="space-y-3">
                    <div v-if="restockItems.length === 0" class="text-center py-6 text-gray-500">No pending requests.</div>
                    <div v-for="item in restockItems" :key="item.id"
                        class="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-3 border rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                        :class="item._escalated ? 'border-orange-500/40 bg-orange-500/5' : 'border-gray-200 dark:border-white/10'">
                        <div
                            class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/20 text-blue-600 hidden sm:flex items-center justify-center font-bold text-xs shrink-0">
                            {{ item.item_name.substring(0, 2).toUpperCase() }}
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center gap-2 flex-wrap">
                                <h4 class="font-bold text-sm text-gray-900 dark:text-white">{{ item.item_name }} <span class="text-xs text-gray-400 font-mono">({{ item.item_sku }})</span></h4>
                                <span v-if="item._escalated" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-500/20 text-orange-500 border border-orange-500/30">⚑ ESCALATED</span>
                            </div>
                            <p class="text-xs text-gray-500 mt-1">
                                Requested Qty: <span class="font-mono font-bold">{{ item.quantity }}</span> by <span class="text-gray-800 dark:text-gray-300 font-medium">{{ item.requested_by_name || 'Manager' }}</span>
                            </p>
                            <p v-if="item._escalated" class="text-xs text-orange-400 mt-1">⚠ Warehouse Manager flagged this as urgent</p>

                            <!-- Funding Source Picker -->
                            <div class="mt-2 flex gap-2">
                                <button
                                    @click="item._fundingSource = 'APP_REVENUE'"
                                    class="px-2 py-1 rounded text-[10px] font-bold border transition-colors"
                                    :class="(!item._fundingSource || item._fundingSource === 'APP_REVENUE') ? 'bg-green-100 border-green-400 text-green-700 dark:bg-green-500/20 dark:border-green-500 dark:text-green-400' : 'border-gray-300 dark:border-white/20 text-gray-500'"
                                >💰 App Revenue</button>
                                <button
                                    @click="item._fundingSource = 'OFFLINE_CAPITAL'"
                                    class="px-2 py-1 rounded text-[10px] font-bold border transition-colors"
                                    :class="item._fundingSource === 'OFFLINE_CAPITAL' ? 'bg-blue-100 border-blue-400 text-blue-700 dark:bg-blue-500/20 dark:border-blue-500 dark:text-blue-400' : 'border-gray-300 dark:border-white/20 text-gray-500'"
                                >🏦 Offline Capital</button>
                            </div>
                        </div>
                        <div class="flex w-full sm:w-auto mt-2 sm:mt-0 gap-2 shrink-0">
                            <button @click="resolveRestock(item.id, 'APPROVED', item._fundingSource)" class="flex-1 sm:flex-none px-4 py-1.5 bg-green-50 dark:bg-green-500/10 text-green-600 hover:bg-green-500 hover:text-white rounded border border-green-200 dark:border-green-500/20 text-xs font-bold transition-colors">Approve</button>
                            <button @click="resolveRestock(item.id, 'REJECTED', null)" class="flex-1 sm:flex-none px-4 py-1.5 bg-red-50 dark:bg-red-500/10 text-red-600 hover:bg-red-500 hover:text-white rounded border border-red-200 dark:border-red-500/20 text-xs font-bold transition-colors">Reject</button>
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="p-4 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                <button @click="restockModalOpen = false"
                    class="px-4 py-2 text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 rounded-lg font-bold text-sm">Close</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const { resolveRestock, restockItems, restockModalOpen } = inject(reportsPageKey)
</script>

<style scoped src="./Reports.css"></style>
