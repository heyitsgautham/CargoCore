<template>
    <!-- Create Category Modal -->
    <Teleport to="body">
        <div v-if="showAddCategoryModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
            @click.self="showAddCategoryModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-sm border border-gray-200 dark:border-white/10 overflow-hidden">
                <!-- Header -->
                <div class="p-5 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-xl bg-yellow-500/15 flex items-center justify-center">
                            <span class="material-symbols-outlined text-yellow-500 text-[20px]">folder_open</span>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-base">New Category</h3>
                            <p class="text-[11px] text-gray-500">Create a custom inventory category</p>
                        </div>
                    </div>
                    <button @click="showAddCategoryModal = false"
                        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>
                <!-- Body -->
                <div class="p-5 space-y-4">
                    <div>
                        <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Category Name</label>
                        <input type="text" v-model="newCategoryName" placeholder="e.g. Electronics, Fertilizer, Tools…" autofocus
                            @keyup.enter="createCategory"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 text-sm transition-all" />
                    </div>
                    <div class="flex gap-3">
                        <button @click="showAddCategoryModal = false"
                            class="flex-1 py-3 rounded-xl border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 font-bold text-sm hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            Cancel
                        </button>
                        <button @click="createCategory" :disabled="!newCategoryName.trim()"
                            class="flex-[2] py-3 rounded-xl bg-primary hover:bg-primary-dark text-background-dark font-bold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                            <span class="material-symbols-outlined text-[18px]">add_circle</span>
                            Create Category
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

const { createCategory, newCategoryName, showAddCategoryModal } = inject(inventoryPageKey)
</script>
