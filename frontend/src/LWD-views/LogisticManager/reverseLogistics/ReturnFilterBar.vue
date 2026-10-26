<template>
    <!-- Filter Bar -->
    <div class="glass-panel rounded-xl p-3 border border-gray-200 dark:border-white/5 flex items-center gap-3 flex-wrap">
        <div class="flex gap-1 flex-wrap flex-1 min-w-0">
            <button v-for="tab in tabs" :key="tab.id"
                @click="activeStatus = tab.id"
                class="px-2.5 py-1 rounded-md text-[11px] font-bold transition-all flex items-center gap-1"
                :class="activeStatus === tab.id
                    ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10'">
                <span v-if="tab.dot" class="w-1.5 h-1.5 rounded-full shrink-0" :class="tab.dot"></span>
                {{ tab.label }}
            </button>
        </div>
        <div class="relative shrink-0">
            <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-[16px]">search</span>
            <input v-model="searchQuery" type="text" placeholder="Search claim, customer..."
                class="pl-8 pr-3 py-1.5 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary/50 text-gray-700 dark:text-gray-200 w-52">
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const { activeStatus, searchQuery, tabs } = inject(reverseLogisticsPageKey)
</script>
