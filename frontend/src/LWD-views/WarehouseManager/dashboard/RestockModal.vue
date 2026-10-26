<template>
    <!-- DYNAMIC RESTOCK MODAL -->
    <Teleport to="body">
        <div v-if="showRestockModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div
                class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl transform transition-all">
                <!-- Header -->
                <div
                    class="p-5 border-b border-gray-200 dark:border-white/10 flex justify-between items-center bg-gradient-to-r from-red-500/20 to-transparent">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 text-lg">
                        <span class="material-symbols-outlined text-red-600 dark:text-red-400">warning</span>
                        Critical Restock Required
                    </h3>
                    <button @click="showRestockModal = false"
                        class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Body -->
                <div class="p-5 max-h-[60vh] overflow-y-auto no-scrollbar">
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">The following SKUs have fallen below
                        their safety stock
                        thresholds and require immediate attention.</p>
                    <div class="space-y-3">
                        <div v-for="sku in criticalSkus" :key="sku.id"
                            class="flex justify-between items-center p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ sku.name }}</div>
                                <div class="text-[10px] text-gray-600 dark:text-gray-400 font-mono mt-0.5">{{ sku.id
                                    }}</div>
                            </div>
                            <div class="text-right">
                                <div class="text-sm text-red-600 dark:text-red-400 font-bold flex items-center gap-1 justify-end">
                                    {{ sku.current }} left
                                    <span class="material-symbols-outlined text-[14px]">arrow_downward</span>
                                </div>
                                <div class="text-[10px] text-gray-500">Min Threshold: {{ sku.min }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div
                    class="p-4 border-t border-gray-200 dark:border-white/10 flex gap-3 bg-gray-100 dark:bg-black/20">
                    <button @click="showRestockModal = false"
                        class="flex-1 py-2.5 text-sm font-bold text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 rounded-lg transition-colors">
                        Review Later
                    </button>
                    <button @click="processRestock"
                        class="flex flex-1 py-2.5 items-center justify-center gap-2 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors shadow-lg shadow-red-500/20">
                        <span class="material-symbols-outlined text-[18px]"
                            v-if="!isProcessingRestock">shopping_cart_checkout</span>
                        <span class="material-symbols-outlined text-[18px] animate-spin" v-else>sync</span>
                        {{ isProcessingRestock ? 'Processing...' : 'Authorize Restock All' }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const { criticalSkus, isProcessingRestock, processRestock, showRestockModal } = inject(wmDashboardPageKey)
</script>
