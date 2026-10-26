<template>
    <!-- Loading State -->
    <div v-if="loading" class="glass-panel rounded-xl p-8 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <div class="mt-2 text-gray-600 dark:text-gray-400">Loading inventory...</div>
    </div>

    <!-- Inventory Table -->
    <div v-else class="glass-panel rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 flex flex-wrap gap-4 items-center">
            <input v-model="searchQuery" type="text" placeholder="Search SKU, name, or location..."
                class="flex-1 min-w-[200px] bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 px-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
            <select v-model="categoryFilter"
                class="bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white">
                <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Categories</option>
                <option v-for="category in categoryOptions" :key="category" :value="category"
                    class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ category }}</option>
            </select>
            <select v-model="zoneFilter"
                class="bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white">
                <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Zones</option>
                <option value="A" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Zone A</option>
                <option value="B" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Zone B</option>
                <option value="C" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Zone C</option>
                <option value="D" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Zone D</option>
            </select>
            <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                <input type="checkbox" v-model="showFastMoving" class="accent-primary" />
                Fast-Moving Only
            </label>
        </div>

        <div class="overflow-auto max-h-[600px]">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase sticky top-0">
                    <tr>
                        <th class="p-4">SKU</th>
                        <th class="p-4">Product Name</th>
                        <th class="p-4">Category</th>
                        <th class="p-4">Dimensions (cm)</th>
                        <th class="p-4">Weight</th>
                        <th class="p-4">Location</th>
                        <th class="p-4">Stock Level</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="item in filteredInventory" :key="item.sku"
                        class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                        <td class="p-4 font-mono text-gray-600 dark:text-gray-300">{{ item.sku }}</td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <span class="font-bold text-gray-900 dark:text-white">{{ item.name }}</span>
                                <span v-if="item.fastMoving"
                                    class="px-1.5 py-0.5 bg-orange-500/20 text-orange-400 text-[9px] font-bold rounded border border-orange-500/20 animate-pulse">🔥
                                    FAST</span>
                            </div>
                        </td>
                        <td class="p-4 text-gray-600 dark:text-gray-400">{{ item.category }}</td>
                        <td class="p-4 text-gray-600 dark:text-gray-400 font-mono text-xs">{{ item.dimensions }}
                        </td>
                        <td class="p-4 text-gray-600 dark:text-gray-400">{{ item.weight }} kg</td>
                        <td class="p-4">
                            <div class="flex flex-col">
                                <span class="font-mono text-primary text-xs">{{ item.zone }}-{{ item.aisle }}-{{
                                    item.rack }}-{{ item.shelf }}-{{ item.bin }}</span>
                                <span class="text-[10px] text-gray-500">Zone {{ item.zone }} • Aisle {{ item.aisle
                                    }}</span>
                            </div>
                        </td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <div class="w-24 bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
                                    <div class="h-full" :class="item.stock < 20 ? 'bg-red-500' : 'bg-green-500'"
                                        :style="`width: ${item.stockPercentage}%`"></div>
                                </div>
                                <span :class="item.stock < 20 ? 'text-red-600 dark:text-red-400 font-bold' : 'text-gray-600 dark:text-gray-300'">{{
                                    item.stock }}</span>
                            </div>
                        </td>
                        <td class="p-4 flex gap-2">
                            <button @click="openEditModal(item)"
                                class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white"
                                title="Edit"><span
                                    class="material-symbols-outlined text-[18px]">edit</span></button>
                            <button @click="openMoveModal(item)"
                                class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white"
                                title="Move"><span
                                    class="material-symbols-outlined text-[18px]">move_down</span></button>
                            <button @click="printLabel(item)"
                                class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white"
                                title="Print Label"><span
                                    class="material-symbols-outlined text-[18px]">print</span></button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const {
    categoryFilter,
    categoryOptions,
    filteredInventory,
    loading,
    openEditModal,
    openMoveModal,
    printLabel,
    searchQuery,
    showFastMoving,
    zoneFilter,
} = inject(inventoryPageKey)
</script>
