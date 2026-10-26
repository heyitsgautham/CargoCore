<template>
    <!-- Ready-for-dispatch alert banner -->
    <div v-if="readyCount > 0"
        class="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl animate-pulse">
        <span class="material-symbols-outlined text-emerald-400 text-[22px]">local_shipping</span>
        <div class="flex-1">
            <div class="font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                {{ readyCount }} order{{ readyCount > 1 ? 's' : '' }} ready for dispatch from warehouse!
            </div>
            <div class="text-[11px] text-emerald-600/70 dark:text-emerald-300/70">
                Warehouse Manager has completed packing & QC. Assign a driver now.
            </div>
        </div>
        <button @click="filterReady = !filterReady"
            class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
            :class="filterReady ? 'bg-emerald-500 text-white' : 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/30'">
            {{ filterReady ? 'Show All' : 'Show Ready Only' }}
        </button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const { filterReady, readyCount } = inject(pendingQueuePageKey)
</script>
