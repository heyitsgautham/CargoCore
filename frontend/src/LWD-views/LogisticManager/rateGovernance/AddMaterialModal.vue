<template>
    <!-- Add Material Modal -->
    <div v-if="showAddMaterialModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">Add New Packing Material</h3>
                <button @click="showAddMaterialModal = false" class="text-gray-400 hover:text-gray-600">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Material Name *</label>
                    <input type="text" v-model="newMaterial.name" placeholder="e.g., Foam Sheet"
                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rate (₹) *</label>
                        <input type="number" v-model.number="newMaterial.rate" placeholder="50"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unit</label>
                        <select v-model="newMaterial.unit"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm">
                            <option value="pcs">pcs</option>
                            <option value="m">m (meter)</option>
                            <option value="kg">kg</option>
                            <option value="roll">roll</option>
                            <option value="sheet">sheet</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
                <button @click="showAddMaterialModal = false"
                    class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg">
                    Cancel
                </button>
                <button @click="addMaterial" :disabled="!newMaterial.name || !newMaterial.rate"
                    class="px-4 py-2 text-sm font-medium bg-primary hover:bg-primary/90 disabled:opacity-50 text-white rounded-lg">
                    Add Material
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { addMaterial, newMaterial, showAddMaterialModal } = inject(rateGovernancePageKey)
</script>
