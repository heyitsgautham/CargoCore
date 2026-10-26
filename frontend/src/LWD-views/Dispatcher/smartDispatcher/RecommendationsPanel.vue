<template>
    <div class="glass-panel p-6 rounded-xl flex flex-col h-[540px]">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">lightbulb</span>
            AI Dispatch Suggestions
        </h3>
        <div class="space-y-4 flex-1 overflow-y-auto no-scrollbar pr-2">
            <div v-if="suggestions.length === 0" class="text-center py-8 text-gray-500 text-sm">
                <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
                No dispatch exceptions right now. Released orders are covered.
            </div>
            <div v-for="suggestion in suggestions.filter(s => !ignoredSuggestions.has(s.id))" :key="suggestion.id"
                class="p-4 bg-gray-50 dark:bg-white/5 border rounded-xl transition-all cursor-pointer group"
                :class="appliedSuggestions.has(suggestion.id) ? 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-900/10' : 'border-gray-200 dark:border-white/5 hover:border-primary/30'">
                <div class="flex justify-between items-start mb-2">
                    <div :class="suggestion.color" class="font-bold text-sm">
                        {{ appliedSuggestions.has(suggestion.id) ? '✓ ' : '' }}{{ suggestion.title }}
                    </div>
                    <div class="text-xs text-gray-600 dark:text-gray-400">
                        Confidence: <span
                            :class="suggestion.confidence >= 90 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'"
                            class="font-bold">{{ suggestion.confidence }}%</span>
                    </div>
                </div>
                <div class="text-sm text-gray-700 dark:text-gray-300 mb-2" v-html="suggestion.message"></div>
                <div v-if="suggestion.explanation"
                    class="mb-2 p-2 bg-blue-500/10 dark:bg-blue-500/5 border border-blue-500/30 dark:border-blue-500/10 rounded text-[11px] text-blue-700 dark:text-blue-300">
                    <span class="font-bold">Why:</span> {{ suggestion.explanation }}
                </div>
                <div v-if="!appliedSuggestions.has(suggestion.id)" class="flex gap-2">
                    <button v-for="action in suggestion.actions" :key="action.label"
                        @click="applySuggestion(suggestion, action.label)" :class="action.class"
                        class="px-3 py-1 rounded text-xs font-bold transition-colors">{{ action.label
                        }}</button>
                </div>
                <div v-else
                    class="text-[10px] text-green-600 dark:text-green-400 font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">check_circle</span>
                    Applied successfully
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { smartDispatcherPageKey } from './smartDispatcherPageContext'

const { appliedSuggestions, applySuggestion, ignoredSuggestions, suggestions } = inject(smartDispatcherPageKey)
</script>
