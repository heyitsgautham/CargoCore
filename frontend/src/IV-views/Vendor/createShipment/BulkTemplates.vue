<template>
    <!-- Template Downloads -->
    <div class="glass-panel p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Download Templates</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button v-for="cat in categories" :key="cat.value" @click="downloadTemplate(cat.value)"
                class="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-white/10 hover:border-blue-500 hover:bg-blue-500/5 transition-all">
                <span class="material-symbols-outlined text-blue-500 text-2xl">{{ cat.icon }}</span>
                <div class="flex-1 text-left">
                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ cat.label }}</div>
                    <div class="text-xs text-gray-500">{{ cat.desc }}</div>
                </div>
                <span class="material-symbols-outlined text-gray-400">download</span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { categories, downloadTemplate } = inject(createShipmentPageKey)
</script>
