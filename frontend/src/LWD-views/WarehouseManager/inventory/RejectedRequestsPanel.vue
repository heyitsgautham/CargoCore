<template>
    <!-- Only show rejected requests panel if any -->
    <div v-if="rejectedMaterials.length > 0" class="glass-panel rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-red-50/50 dark:bg-red-900/10 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-red-500">info</span>
                <h3 class="font-bold text-gray-900 dark:text-white">Rejected Requests</h3>
            </div>
        </div>
        <div class="divide-y divide-gray-100 dark:divide-white/5">
            <div v-for="req in rejectedMaterials" :key="req.id" class="p-3 flex items-center justify-between">
                <div>
                    <span class="font-medium text-gray-900 dark:text-white line-through opacity-60">{{ req.material_name }}</span>
                    <span v-if="req.manager_notes" class="text-xs text-red-500 ml-2">• {{ req.manager_notes }}</span>
                </div>
                <span class="text-xs px-2 py-1 rounded-full font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                    REJECTED
                </span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const { rejectedMaterials } = inject(inventoryPageKey)
</script>
