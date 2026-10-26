<template>
    <!-- Restock Modal -->
    <Teleport to="body">
        <div v-if="showRestockModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showRestockModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Request Material Restock</h3>
                    <button @click="showRestockModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4">
                    <div v-for="item in lowStockItems" :key="item.id"
                        class="flex items-center justify-between p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl">{{ item.emoji }}</span>
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                <div class="text-xs text-red-600 dark:text-red-400">Current: {{ item.stock }} / Threshold: {{ item.threshold }}</div>
                            </div>
                        </div>
                        <input type="number" v-model.number="restockForm[item.id]"
                            class="w-20 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center focus:outline-none focus:border-primary/50" />
                    </div>
                    <div v-if="lowStockItems.length === 0" class="text-center text-gray-500 py-4">
                        All materials are above threshold ✓
                    </div>
                    <div class="flex gap-3">
                        <button @click="submitRestock"
                            class="flex-1 bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            :disabled="restocking">
                            <span v-if="restocking" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                            {{ restocking ? 'Restocking...' : 'Submit Restock Request' }}
                        </button>
                        <button @click="escalateRestock"
                            class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-3 px-5 rounded-lg font-bold transition-colors">Escalate to Manager</button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { packingMaterialsPageKey } from './packingMaterialsPageContext'

const {
    escalateRestock,
    lowStockItems,
    restockForm,
    restocking,
    showRestockModal,
    submitRestock,
} = inject(packingMaterialsPageKey)
</script>
