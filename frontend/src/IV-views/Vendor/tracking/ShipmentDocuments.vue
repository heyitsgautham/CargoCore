<template>
    <!-- Row 2: Documents (full width) -->
    <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-start justify-between gap-3 mb-3">
            <div>
                <h4 class="text-sm font-bold text-gray-900 dark:text-white">Documents</h4>
                <p class="text-xs text-gray-400 mt-1">Only ready-to-download shipment documents are shown here.</p>
            </div>
        </div>
        <div v-if="availableDocuments.length > 0" class="flex gap-3 flex-wrap">
            <button v-for="doc in availableDocuments" :key="doc.key" @click="doc.action()"
                class="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 cursor-pointer transition-all group flex-1 min-w-[220px] text-left"
                :class="doc.hoverClass">
                <span class="material-symbols-outlined text-xl" :class="doc.iconClass">{{ doc.icon }}</span>
                <div class="flex-1 min-w-0">
                    <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate">{{ doc.label }}</div>
                    <div class="text-[10px] text-gray-400 mt-0.5 truncate">{{ doc.description }}</div>
                </div>
                <span class="material-symbols-outlined text-gray-400 text-sm transition-colors" :class="doc.downloadClass">download</span>
            </button>
        </div>
        <div v-else class="rounded-xl border border-dashed border-gray-200 dark:border-white/10 bg-gray-50/60 dark:bg-white/5 px-4 py-5 text-sm text-gray-400">
            No downloadable documents are available for this shipment yet.
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { availableDocuments } = inject(vendorTrackingPageKey)
</script>
