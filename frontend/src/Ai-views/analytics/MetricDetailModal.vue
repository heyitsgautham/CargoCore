<template>
    <div
        v-if="showActionModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="showActionModal = false"
    >
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex items-center gap-3 bg-gray-50 dark:bg-white/5">
                <span class="material-symbols-outlined text-2xl" :class="toneIconClass(selectedInsight?.tone || 'blue')">
                    {{ selectedInsight?.icon }}
                </span>
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedInsight?.title }}</h3>
            </div>
            <div class="p-6 space-y-4">
                <p class="text-sm text-gray-600 dark:text-gray-300">{{ selectedInsight?.text }}</p>

                <div class="bg-purple-50 dark:bg-purple-900/10 p-4 rounded-xl border border-purple-100 dark:border-purple-500/20">
                    <div class="flex items-center gap-2 mb-2 font-bold text-purple-900 dark:text-purple-300 text-sm">
                        <span class="material-symbols-outlined text-[18px]">assignment_add</span>
                        Recommended Execution
                    </div>
                    <p class="text-xs text-purple-800 dark:text-purple-400">
                        This action creates a backend follow-up ticket from the analytics insight so the support team can track it in the queue.
                    </p>
                </div>
            </div>
            <div class="p-6 border-t border-gray-100 dark:border-white/5 flex gap-3 bg-gray-50 dark:bg-white/5">
                <button
                    @click="showActionModal = false"
                    class="flex-1 py-2.5 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors border border-gray-200 dark:border-white/10 shadow-sm"
                    type="button"
                >
                    Close
                </button>
                <button
                    @click="executeAction"
                    class="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2 disabled:opacity-60"
                    :disabled="!selectedInsight || store.executingInsightId === selectedInsight.id"
                    type="button"
                >
                    <span class="material-symbols-outlined text-[18px]">bolt</span>
                    {{ store.executingInsightId === selectedInsight?.id ? 'Creating...' : 'Execute Now' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { aiAnalyticsPageKey } from './aiAnalyticsPageContext'

const {
    executeAction,
    selectedInsight,
    showActionModal,
    store,
    toneIconClass,
} = inject(aiAnalyticsPageKey)
</script>
