<template>
    <!-- AI Driver Suggestions -->
    <div class="glass-panel rounded-xl p-4">
        <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
            <span class="material-symbols-outlined text-purple-400 text-[18px]">auto_awesome</span>
            AI Driver Suggestions
            <span v-if="aiSuggestions.length" class="ml-auto bg-purple-500/20 text-purple-400 text-[10px] font-bold px-2 py-0.5 rounded-full">{{ aiSuggestions.length }}</span>
        </h3>

        <!-- Loading -->
        <div v-if="aiLoading" class="text-center py-6 text-gray-500 text-xs">
            <span class="material-symbols-outlined text-[28px] text-purple-400 block mb-2 animate-pulse">auto_awesome</span>
            Gemini is ranking drivers...
        </div>

        <div v-else-if="aiSuggestions.length === 0" class="text-center py-6 text-gray-500 text-xs">
            <span class="material-symbols-outlined text-[32px] text-gray-600 block mb-2">person_search</span>
            No unassigned orders or no drivers with live GPS right now.
        </div>

        <div v-for="s in aiSuggestions" :key="s.order_id"
            class="mb-2 p-3 rounded-lg border transition-all cursor-pointer"
            :class="selectedSuggestion?.order_id === s.order_id ? 'border-primary bg-primary/5' : 'border-gray-200 dark:border-white/10 hover:border-purple-500/40'"
            @click="highlightAiSuggestion(s)">

            <div class="flex items-start justify-between gap-2 mb-1.5">
                <div class="min-w-0">
                    <div class="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1.5 truncate">
                        <span class="w-2 h-2 rounded-full bg-green-400 shrink-0 inline-block"></span>
                        {{ s.suggested_driver_name }}
                    </div>
                    <div class="text-[10px] text-gray-400 mt-0.5 truncate">
                        <span class="font-mono text-primary">{{ s.order_tracking_code }}</span>
                        <span v-if="s.distance_km != null"> · {{ s.distance_km }}km away</span>
                    </div>
                    <div v-if="vehicleLabelForSuggestion(s)" class="text-[10px] text-emerald-400 mt-1 truncate">
                        Vehicle: {{ vehicleLabelForSuggestion(s) }}
                    </div>
                </div>
                <div class="flex flex-col items-end gap-1 shrink-0">
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        :class="priorityClass(s.priority)">{{ s.priority }}</span>
                    <span class="text-[10px] font-bold text-gray-500">{{ s.confidence }}% match</span>
                </div>
            </div>

            <!-- AI reason -->
            <div class="mb-2 p-2 rounded-lg text-[10px] leading-relaxed"
                :class="s.ai_powered ? 'bg-purple-500/5 border border-purple-500/15 text-purple-300' : 'bg-gray-100 dark:bg-white/5 text-gray-500'">
                <span v-if="s.ai_powered" class="material-symbols-outlined text-[10px] mr-0.5 align-middle text-purple-400">auto_awesome</span>
                {{ s.reason }}
            </div>

            <div class="text-[10px] text-gray-500 truncate mb-2">
                <span class="material-symbols-outlined text-[10px] align-middle text-orange-400">trip_origin</span>
                {{ s.pickup_addr }}
            </div>

            <button @click.stop="assignAiSuggestion(s)"
                :disabled="assigningId === s.order_id || !canAssignSuggestion(s)"
                class="w-full py-1.5 bg-primary hover:bg-primary/80 disabled:opacity-50 text-black text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1">
                <span class="material-symbols-outlined text-[14px]">{{ assigningId === s.order_id ? 'progress_activity' : 'person_add' }}</span>
                {{ assigningId === s.order_id ? 'Assigning...' : aiSuggestionActionLabel(s) }}
            </button>
        </div>
    </div>

</template>

<script setup>
import { inject } from 'vue'
import { clusteringPageKey } from './clusteringPageContext'

const {
    aiLoading,
    aiSuggestionActionLabel,
    aiSuggestions,
    assignAiSuggestion,
    assigningId,
    canAssignSuggestion,
    highlightAiSuggestion,
    priorityClass,
    selectedSuggestion,
    vehicleLabelForSuggestion,
} = inject(clusteringPageKey)
</script>
