<template>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
            v-for="insight in analytics.insights"
            :key="insight.id"
            class="p-5 rounded-xl border flex gap-4 transition-all hover:shadow-md"
            :class="toneCardClass(insight.tone)"
        >
            <span class="material-symbols-outlined text-3xl shrink-0 mt-0.5" :class="toneIconClass(insight.tone)">
                {{ insight.icon }}
            </span>
            <div>
                <h4 class="font-bold mb-1" :class="toneTitleClass(insight.tone)">{{ insight.title }}</h4>
                <p class="text-sm leading-relaxed" :class="toneTextClass(insight.tone)">{{ insight.text }}</p>
                <button
                    v-if="!insight.executed"
                    @click="openActionModal(insight)"
                    class="mt-3 text-xs font-bold flex items-center gap-1 transition-colors"
                    :class="toneTitleClass(insight.tone) + ' hover:opacity-80'"
                    type="button"
                >
                    {{ insight.action_label }}
                    <span class="material-symbols-outlined text-[12px]">arrow_forward</span>
                </button>
                <div v-else class="mt-3 text-xs font-bold flex items-center gap-1 text-green-600 dark:text-green-400">
                    <span class="material-symbols-outlined text-[14px]">check_circle</span>
                    Follow-up Ticket Created
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { aiAnalyticsPageKey } from './aiAnalyticsPageContext'

const {
    analytics,
    openActionModal,
    toneCardClass,
    toneIconClass,
    toneTextClass,
    toneTitleClass,
} = inject(aiAnalyticsPageKey)
</script>
