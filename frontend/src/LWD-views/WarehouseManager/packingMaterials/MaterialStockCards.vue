<template>
    <!-- Inventory Cards — from real inventory data -->
    <div v-if="packingItems.length === 0" class="glass-panel p-8 rounded-xl text-center text-gray-500">
        <span class="material-symbols-outlined text-4xl mb-2 opacity-50">inventory_2</span>
        <p>No packing materials found in inventory. Add items via the Inventory page.</p>
    </div>
    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div v-for="item in packingItems" :key="item.id"
            class="glass-panel p-4 rounded-xl text-center group hover:border-primary/30 transition-colors cursor-pointer"
            :class="item.stock <= item.threshold ? 'border-red-500/30 bg-red-900/5' : ''">
            <div class="text-3xl mb-2">{{ item.emoji }}</div>
            <div class="text-sm font-bold text-gray-900 dark:text-white leading-tight">{{ item.name }}</div>
            <div class="text-2xl font-bold mt-1"
                :class="item.stock <= item.threshold ? 'text-red-600 dark:text-red-400' : 'text-primary'">{{ item.stock }}</div>
            <div class="text-[10px] text-gray-500 uppercase">{{ item.unit }}</div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all"
                    :class="item.stock <= item.threshold ? 'bg-red-500' : 'bg-primary'"
                    :style="`width: ${Math.min((item.stock / item.max) * 100, 100)}%`"></div>
            </div>
            <div v-if="item.stock <= item.threshold" class="text-[10px] text-red-600 dark:text-red-400 mt-1 font-bold animate-pulse">⚠ LOW STOCK</div>
            <div class="text-[10px] text-gray-500 font-mono mt-1">{{ item.sku }}</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { packingMaterialsPageKey } from './packingMaterialsPageContext'

const { packingItems } = inject(packingMaterialsPageKey)
</script>
