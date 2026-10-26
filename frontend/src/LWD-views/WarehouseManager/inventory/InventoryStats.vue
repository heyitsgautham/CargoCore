<template>
    <!-- Inventory Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ totalItems.toLocaleString() }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Total Items</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ lowStockCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Low Stock Alerts</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">98%</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Inventory Accuracy</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-orange-600 dark:text-orange-400">{{ fastMovingCount }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Fast-Moving SKUs</div>
        </div>
        <div class="glass-panel p-4 rounded-xl text-center">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ totalValue }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">Total Value</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const { fastMovingCount, lowStockCount, totalItems, totalValue } = inject(inventoryPageKey)
</script>
