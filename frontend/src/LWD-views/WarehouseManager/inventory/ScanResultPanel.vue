<template>
    <!-- Search Results (Display inline when scan happens) -->
    <div v-if="scanResult" class="glass-panel rounded-xl p-6 border border-green-500/30 animate-fade-in relative">
        <button @click="clearScan"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-900 dark:hover:text-white">
            <span class="material-symbols-outlined">close</span>
        </button>
        <div class="flex items-start gap-4">
            <div
                class="w-12 h-12 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-2xl">check_circle</span>
            </div>
            <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">Scan Successful</h3>
                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ scanResult.name }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    <span class="font-mono text-primary mr-2">{{ scanResult.sku }}</span>
                    Stock: <span :class="scanResult.stock < 20 ? 'text-red-500' : 'text-green-500'">{{
                        scanResult.stock }}</span> — Zone {{ scanResult.zone }}
                </div>
                <div class="mt-4 flex gap-2">
                    <button @click="openEditModal(scanResult)"
                        class="px-3 py-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 rounded text-xs font-bold transition-colors">Edit
                        Item</button>
                    <button @click="openMoveModal(scanResult)"
                        class="px-3 py-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 rounded text-xs font-bold transition-colors">Move
                        Item</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const { clearScan, openEditModal, openMoveModal, scanResult } = inject(inventoryPageKey)
</script>
