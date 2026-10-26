<template>
    <!-- Tabs Navigation -->
    <div class="flex gap-1 bg-slate-100 dark:bg-slate-800/70 p-1 rounded-lg self-start border border-gray-200 dark:border-white/10 shadow-sm">
        <button v-for="tab in tabs" :key="tab.id"
            @click="activeTab = tab.id"
            class="px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-1.5"
            :class="activeTab === tab.id ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-600 dark:text-white' : 'text-slate-600 hover:text-slate-900 hover:bg-white/70 dark:text-slate-300 dark:hover:text-white dark:hover:bg-white/5'">
            <span class="material-symbols-outlined text-[16px]">{{ tab.icon }}</span>
            {{ tab.label }}
        </button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { financePageKey } from './financePageContext'

const { activeTab, tabs } = inject(financePageKey)
</script>
