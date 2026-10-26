<template>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm">
            <div class="flex justify-between items-center mb-6 gap-4">
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white">AI Resolution vs Human Escalation</h3>
                    <p class="text-xs text-gray-500 mt-1">
                        Period trend of AI-resolved conversations versus escalations
                    </p>
                </div>
                <button
                    @click="exportCsv"
                    class="p-2 bg-gray-50 dark:bg-white/5 rounded-lg text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors tooltip-trigger relative"
                    type="button"
                >
                    <span class="material-symbols-outlined text-[18px]">download</span>
                    <span class="tooltip">Export CSV</span>
                </button>
            </div>
            <div class="h-[500px] w-full relative">
                <canvas ref="resolutionCanvas"></canvas>
            </div>
        </div>

        <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm flex flex-col">
            <div class="mb-6">
                <h3 class="font-bold text-gray-900 dark:text-white">Top Escalation Drivers</h3>
                <p class="text-xs text-gray-500 mt-1">Most common reasons the AI flow needs staff intervention</p>
            </div>
            <div class="h-[220px] w-full relative flex-1">
                <canvas ref="escalationCanvas"></canvas>
            </div>

            <div class="mt-4 space-y-2">
                <div
                    v-for="(reason, index) in analytics.escalation_reasons"
                    :key="reason.label"
                    class="flex items-center justify-between text-xs"
                >
                    <div class="flex items-center gap-2">
                        <span
                            class="w-3 h-3 rounded-full shadow-sm"
                            :style="{ backgroundColor: cssVarColors[index % cssVarColors.length] }"
                        ></span>
                        <span class="text-gray-700 dark:text-gray-300 font-medium">{{ reason.label }}</span>
                    </div>
                    <span class="font-bold text-gray-900 dark:text-white">{{ reason.pct }}%</span>
                </div>
            </div>
        </div>

        <div class="lg:col-span-3 bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm">
            <div class="mb-6">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-500">sentiment_satisfied</span>
                    Conversation Sentiment Score
                </h3>
                <p class="text-xs text-gray-500 mt-1">Average sentiment score after conversation (Bot vs Human)</p>
            </div>
            <div class="h-[250px] w-full relative">
                <canvas ref="sentimentCanvas"></canvas>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { aiAnalyticsPageKey } from './aiAnalyticsPageContext'

const {
    analytics,
    cssVarColors,
    escalationCanvas,
    exportCsv,
    resolutionCanvas,
    sentimentCanvas,
} = inject(aiAnalyticsPageKey)
</script>

<style scoped src="./AIAnalytics.css"></style>
