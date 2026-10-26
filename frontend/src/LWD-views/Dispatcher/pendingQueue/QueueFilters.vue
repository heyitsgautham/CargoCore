<template>
    <!-- Filters -->
    <div class="glass-panel p-4 rounded-xl flex flex-wrap gap-3 items-center">
        <div class="relative flex-1 min-w-[200px]">
            <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-500 text-[18px]">search</span>
            <input v-model="searchQuery" type="text" placeholder="Search by Order ID, warehouse, type..."
                class="w-full bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-10 pr-4 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50">
        </div>
        <select v-model="filterPriority"
            class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50">
            <option value="" class="bg-white dark:bg-gray-800">All Priorities</option>
            <option value="URGENT" class="bg-white dark:bg-gray-800">Urgent</option>
            <option value="HIGH" class="bg-white dark:bg-gray-800">High</option>
            <option value="NORMAL" class="bg-white dark:bg-gray-800">Normal</option>
            <option value="LOW" class="bg-white dark:bg-gray-800">Low</option>
        </select>
        <select v-model="filterWarehouse"
            class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50">
            <option value="" class="bg-white dark:bg-gray-800">All Warehouses</option>
            <option v-for="wh in warehouses" :key="wh" :value="wh" class="bg-white dark:bg-gray-800">{{ wh }}</option>
        </select>
        <select v-model="filterFeasibility"
            class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50">
            <option value="" class="bg-white dark:bg-gray-800">All Status</option>
            <option value="feasible" class="bg-white dark:bg-gray-800">Feasible</option>
            <option value="infeasible" class="bg-white dark:bg-gray-800">Not Feasible</option>
            <option value="unchecked" class="bg-white dark:bg-gray-800">Unchecked</option>
        </select>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const {
    filterFeasibility,
    filterPriority,
    filterWarehouse,
    searchQuery,
    warehouses,
} = inject(pendingQueuePageKey)
</script>
