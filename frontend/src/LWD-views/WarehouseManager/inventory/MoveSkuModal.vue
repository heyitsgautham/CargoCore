<template>
    <!-- Move SKU Modal -->
    <Teleport to="body">
        <div v-if="showMoveModal && moveItem"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showMoveModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Move {{ moveItem.sku }}</h3>
                    <button @click="showMoveModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div
                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-center">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Current Location</div>
                        <div class="font-mono text-primary font-bold">{{ moveItem.zone }}-{{ moveItem.aisle }}-{{
                            moveItem.rack }}-{{ moveItem.shelf }}-{{ moveItem.bin }}</div>
                    </div>
                    <div class="text-center text-gray-500"><span
                            class="material-symbols-outlined">arrow_downward</span>
                    </div>
                    <div class="grid grid-cols-5 gap-2">
                        <div>
                            <label class="text-[10px] text-gray-600 dark:text-gray-400 block mb-1">Zone</label>
                            <select v-model="newLocation.zone"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm">
                                <option v-for="z in ['A', 'B', 'C', 'D']" :key="z" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ z }}</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-600 dark:text-gray-400 block mb-1">Aisle</label>
                            <input type="text" v-model="newLocation.aisle"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm" />
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-600 dark:text-gray-400 block mb-1">Rack</label>
                            <input type="text" v-model="newLocation.rack"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm" />
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-600 dark:text-gray-400 block mb-1">Shelf</label>
                            <input type="text" v-model="newLocation.shelf"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm" />
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-600 dark:text-gray-400 block mb-1">Bin</label>
                            <input type="text" v-model="newLocation.bin"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm" />
                        </div>
                    </div>
                    <button @click="confirmMove"
                        class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Confirm
                        Move</button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const { confirmMove, moveItem, newLocation, showMoveModal } = inject(inventoryPageKey)
</script>
