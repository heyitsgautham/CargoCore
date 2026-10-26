<template>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
        <div
            v-for="metric in analytics.metrics"
            :key="metric.id"
            class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-4 md:p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow"
        >
            <div class="flex items-center gap-2 mb-3">
                <span class="p-2 rounded-lg bg-gray-50 dark:bg-white/5 flex items-center justify-center">
                    <span class="material-symbols-outlined text-gray-600 dark:text-gray-300 text-[18px]">
                        {{ metric.icon }}
                    </span>
                </span>
                <div class="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">
                    {{ metric.label }}
                </div>
            </div>
            <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ metric.formatted_value }}</div>
            <div
                class="text-xs mt-2 flex items-center gap-1 font-bold"
                :class="metricTrendClass(metric.trend_direction)"
            >
                <span class="material-symbols-outlined text-[14px]">{{ metricTrendIcon(metric.trend_direction) }}</span>
                {{ metric.trend }}
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { aiAnalyticsPageKey } from './aiAnalyticsPageContext'

const { analytics, metricTrendClass, metricTrendIcon } = inject(aiAnalyticsPageKey)
</script>
