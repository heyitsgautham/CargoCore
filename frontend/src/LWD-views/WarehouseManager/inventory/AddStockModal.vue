<template>
    <!-- Add Stock Modal -->
    <Teleport to="body">
        <div v-if="showAddModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showAddModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10 overflow-hidden">

                <!-- Modal Header -->
                <div class="p-5 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-xl bg-primary/15 flex items-center justify-center">
                            <span class="material-symbols-outlined text-primary text-[20px]">inventory_2</span>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-base">Add New Stock</h3>
                            <p class="text-[11px] text-gray-500">Fill in the details below to add an item</p>
                        </div>
                    </div>
                    <button @click="showAddModal = false"
                        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>

                <div class="p-5 space-y-5">

                    <!-- Item Identity -->
                    <div>
                        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Item Identity</p>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">SKU <span class="text-red-400">*</span></label>
                                <input type="text" v-model="addForm.sku" placeholder="e.g. ELEC-0042"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 font-mono text-sm transition-all" />
                            </div>
                            <div>
                                <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Product Name <span class="text-red-400">*</span></label>
                                <input type="text" v-model="addForm.name" placeholder="e.g. Wireless Keyboard"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 text-sm transition-all" />
                            </div>
                        </div>
                    </div>

                    <!-- Category -->
                    <div>
                        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Category</p>
                        <div class="flex gap-2">
                            <select v-model="addForm.category"
                                class="flex-1 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 text-sm transition-all">
                                <option value="" disabled class="bg-white dark:bg-gray-800">— Select a category —</option>
                                <option v-for="cat in categoryOptions" :key="cat" :value="cat"
                                    class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ cat }}</option>
                            </select>
                            <button @click="showAddCategoryModal = true"
                                class="flex items-center gap-1.5 px-4 py-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-xl text-sm font-bold transition-colors whitespace-nowrap">
                                <span class="material-symbols-outlined text-[16px]">add_circle</span>
                                New
                            </button>
                        </div>
                    </div>

                    <!-- Quantity & Weight -->
                    <div>
                        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Stock Details</p>
                        <div class="grid grid-cols-3 gap-3">
                            <div>
                                <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Quantity</label>
                                <input type="number" v-model.number="addForm.stock" min="0" placeholder="0"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 text-sm transition-all" />
                            </div>
                            <div>
                                <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Weight (kg)</label>
                                <input type="number" step="0.1" v-model.number="addForm.weight" min="0" placeholder="0.0"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 text-sm transition-all" />
                            </div>
                            <div>
                                <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Zone</label>
                                <select v-model="addForm.zone"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm transition-all">
                                    <option v-for="z in ['A', 'B', 'C', 'D']" :key="z" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ z }}</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="flex gap-3 pt-1">
                        <button @click="showAddModal = false"
                            class="flex-1 py-3 rounded-xl border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 font-bold text-sm hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            Cancel
                        </button>
                        <button @click="addNewStock" :disabled="!addForm.sku || !addForm.name || !addForm.category"
                            class="flex-2 flex-[2] py-3 rounded-xl bg-primary hover:bg-primary-dark text-background-dark font-bold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                            <span class="material-symbols-outlined text-[18px]">add_circle</span>
                            Add to Inventory
                        </button>
                    </div>

                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const {
    addForm,
    addNewStock,
    categoryOptions,
    showAddCategoryModal,
    showAddModal,
} = inject(inventoryPageKey)
</script>
