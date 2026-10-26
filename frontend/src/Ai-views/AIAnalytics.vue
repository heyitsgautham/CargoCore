<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">AI Performance Analytics</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Live support analytics powered by conversations, escalations, and support workload data
                </p>
            </div>
            <div class="flex gap-2 bg-gray-100 dark:bg-white/5 p-1 rounded-lg">
                <button
                    v-for="range in timeRanges"
                    :key="range"
                    @click="activeRange = range"
                    class="px-4 py-1.5 text-xs font-bold rounded-md transition-all"
                    :class="activeRange === range
                        ? 'bg-white dark:bg-gray-800 text-purple-600 dark:text-purple-400 shadow-sm'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'"
                >
                    {{ range }}
                </button>
            </div>
        </div>

        <div
            v-if="store.loadingAnalytics && !analytics"
            class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-black/20 p-6 text-sm text-gray-500 dark:text-gray-400"
        >
            Loading AI analytics...
        </div>

        <div
            v-else-if="store.error && !analytics"
            class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300"
        >
            {{ store.error }}
        </div>

        <template v-else-if="analytics">
            <KpiCards />

            <AnalyticsCharts />

            <h3 class="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-xs pt-4 mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px] text-purple-500">auto_awesome</span>
                Direct AI Insights
            </h3>
            <InsightCards />
        </template>

        <Teleport to="body">
            <MetricDetailModal />
        </Teleport>
    </div>
</template>

<script setup>
import KpiCards from './analytics/KpiCards.vue'
import AnalyticsCharts from './analytics/AnalyticsCharts.vue'
import InsightCards from './analytics/InsightCards.vue'
import MetricDetailModal from './analytics/MetricDetailModal.vue'
import { aiAnalyticsPageKey } from './analytics/aiAnalyticsPageContext'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, provide } from 'vue'
import Chart from 'chart.js/auto'

import { useToast } from '@/composables/useToast'
import { useAiSupportStore } from '@/stores/aiSupportStore'

const store = useAiSupportStore()
const toast = useToast()

const showActionModal = ref(false)
const selectedInsight = ref(null)
const activeRange = ref('7D')
const timeRanges = ['24H', '7D', '30D', '90D']

const resolutionCanvas = ref(null)
const escalationCanvas = ref(null)
const sentimentCanvas = ref(null)

const cssVarColors = ['#9333ea', '#3b82f6', '#10b981', '#f59e0b', '#6b7280']

const analytics = computed(() => store.analytics)

let resolutionChart = null
let escalationChart = null
let sentimentChart = null
let themeObserver = null

function destroyCharts() {
    resolutionChart?.destroy()
    escalationChart?.destroy()
    sentimentChart?.destroy()
    resolutionChart = null
    escalationChart = null
    sentimentChart = null
}

function metricTrendClass(direction) {
    if (direction === 'positive') return 'text-green-600 dark:text-green-400'
    if (direction === 'negative') return 'text-red-500 dark:text-red-400'
    return 'text-blue-500 dark:text-blue-400'
}

function metricTrendIcon(direction) {
    if (direction === 'positive') return 'trending_up'
    if (direction === 'negative') return 'trending_down'
    return 'info'
}

function toneCardClass(tone) {
    if (tone === 'purple') return 'bg-white dark:bg-black/20 border-purple-200 dark:border-purple-500/20 shadow-sm border-l-4 border-l-purple-500'
    if (tone === 'amber') return 'bg-white dark:bg-black/20 border-amber-200 dark:border-amber-500/20 shadow-sm border-l-4 border-l-amber-500'
    if (tone === 'red') return 'bg-white dark:bg-black/20 border-red-200 dark:border-red-500/20 shadow-sm border-l-4 border-l-red-500'
    if (tone === 'green') return 'bg-white dark:bg-black/20 border-green-200 dark:border-green-500/20 shadow-sm border-l-4 border-l-green-500'
    return 'bg-white dark:bg-black/20 border-blue-200 dark:border-blue-500/20 shadow-sm border-l-4 border-l-blue-500'
}

function toneIconClass(tone) {
    if (tone === 'purple') return 'text-purple-600 dark:text-purple-400'
    if (tone === 'amber') return 'text-amber-600 dark:text-amber-400'
    if (tone === 'red') return 'text-red-600 dark:text-red-400'
    if (tone === 'green') return 'text-green-600 dark:text-green-400'
    return 'text-blue-600 dark:text-blue-400'
}

function toneTitleClass(tone) {
    if (tone === 'purple') return 'text-purple-900 dark:text-purple-300'
    if (tone === 'amber') return 'text-amber-900 dark:text-amber-300'
    if (tone === 'red') return 'text-red-900 dark:text-red-300'
    if (tone === 'green') return 'text-green-900 dark:text-green-300'
    return 'text-blue-900 dark:text-blue-300'
}

function toneTextClass(tone) {
    if (tone === 'purple') return 'text-gray-600 dark:text-gray-400'
    if (tone === 'amber') return 'text-gray-600 dark:text-gray-400'
    if (tone === 'red') return 'text-gray-600 dark:text-gray-400'
    if (tone === 'green') return 'text-gray-600 dark:text-gray-400'
    return 'text-gray-600 dark:text-gray-400'
}

async function refreshAnalytics() {
    try {
        await store.loadAnalytics(activeRange.value)
    } catch (error) {
        toast.error(error.message || 'Failed to load analytics')
    }
}

function openActionModal(insight) {
    selectedInsight.value = insight
    showActionModal.value = true
}

async function executeAction() {
    if (!selectedInsight.value) return
    try {
        const result = await store.executeInsight(selectedInsight.value.id, activeRange.value)
        toast.success(`${result.message} (${result.ticket_reference_code})`)
        showActionModal.value = false
        selectedInsight.value = null
    } catch (error) {
        toast.error(error.message || 'Failed to create analytics follow-up ticket')
    }
}

function csvRow(values) {
    return values
        .map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`)
        .join(',')
}

function exportCsv() {
    if (!analytics.value) return

    const rows = [
        csvRow(['Section', 'Label', 'Value']),
        ...analytics.value.metrics.map((metric) => csvRow(['Metric', metric.label, metric.formatted_value])),
        ...analytics.value.escalation_reasons.map((reason) => csvRow(['Escalation Driver', reason.label, `${reason.pct}% (${reason.count})`])),
        ...analytics.value.resolution_chart.labels.map((label, index) =>
            csvRow([
                'Resolution Trend',
                label,
                `AI Resolved=${analytics.value.resolution_chart.ai_resolved[index]} | Human Escalated=${analytics.value.resolution_chart.human_escalated[index]}`,
            ]),
        ),
        ...analytics.value.sentiment_chart.labels.map((label, index) =>
            csvRow([
                'Sentiment Trend',
                label,
                `AI=${analytics.value.sentiment_chart.ai_handled[index]} | Human=${analytics.value.sentiment_chart.human_handled[index]}`,
            ]),
        ),
    ]

    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ai-support-analytics-${activeRange.value.toLowerCase()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
}

async function renderCharts() {
    await nextTick()
    if (!analytics.value || !resolutionCanvas.value || !escalationCanvas.value || !sentimentCanvas.value) return

    destroyCharts()

    const isDark = document.documentElement.classList.contains('dark')
    const textColor = isDark ? '#9ca3af' : '#6b7280'
    const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'

    const resolutionCtx = resolutionCanvas.value.getContext('2d')
    const escalationCtx = escalationCanvas.value.getContext('2d')
    const sentimentCtx = sentimentCanvas.value.getContext('2d')

    const gradientAI = resolutionCtx.createLinearGradient(0, 0, 0, 300)
    gradientAI.addColorStop(0, 'rgba(147, 51, 234, 0.4)')
    gradientAI.addColorStop(1, 'rgba(147, 51, 234, 0)')

    resolutionChart = new Chart(resolutionCtx, {
        type: 'line',
        data: {
            labels: analytics.value.resolution_chart.labels,
            datasets: [
                {
                    label: 'Automated by AI',
                    data: analytics.value.resolution_chart.ai_resolved,
                    borderColor: '#9333ea',
                    backgroundColor: gradientAI,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#9333ea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Escalated to Human',
                    data: analytics.value.resolution_chart.human_escalated,
                    borderColor: '#f43f5e',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.35,
                    pointBackgroundColor: '#f43f5e',
                    pointRadius: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { color: textColor, usePointStyle: true, boxWidth: 8 },
                },
                tooltip: {
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    titleColor: isDark ? '#f3f4f6' : '#111827',
                    bodyColor: isDark ? '#d1d5db' : '#4b5563',
                    borderColor: isDark ? '#374151' : '#e5e7eb',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                },
            },
            scales: {
                y: {
                    grid: { color: gridColor, drawBorder: false },
                    ticks: { color: textColor, font: { size: 11 } },
                    beginAtZero: true,
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { color: textColor, font: { size: 11 } },
                },
            },
        },
    })

    escalationChart = new Chart(escalationCtx, {
        type: 'doughnut',
        data: {
            labels: analytics.value.escalation_reasons.map((reason) => reason.label),
            datasets: [
                {
                    data: analytics.value.escalation_reasons.map((reason) => reason.pct),
                    backgroundColor: cssVarColors,
                    borderWidth: isDark ? 2 : 0,
                    borderColor: isDark ? '#111827' : '#fff',
                    hoverOffset: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => ` ${context.label}: ${context.raw}%`,
                    },
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    titleColor: isDark ? '#f3f4f6' : '#111827',
                    bodyColor: isDark ? '#d1d5db' : '#4b5563',
                    borderColor: isDark ? '#374151' : '#e5e7eb',
                    borderWidth: 1,
                    padding: 10,
                },
            },
        },
    })

    sentimentChart = new Chart(sentimentCtx, {
        type: 'bar',
        data: {
            labels: analytics.value.sentiment_chart.labels,
            datasets: [
                {
                    label: 'Human Handled',
                    data: analytics.value.sentiment_chart.human_handled,
                    backgroundColor: '#3b82f6',
                    borderRadius: 4,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8,
                },
                {
                    label: 'AI Handled',
                    data: analytics.value.sentiment_chart.ai_handled,
                    backgroundColor: '#a855f7',
                    borderRadius: 4,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { color: textColor, usePointStyle: true, boxWidth: 8 },
                },
                tooltip: {
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    titleColor: isDark ? '#f3f4f6' : '#111827',
                    bodyColor: isDark ? '#d1d5db' : '#4b5563',
                    borderColor: isDark ? '#374151' : '#e5e7eb',
                    borderWidth: 1,
                },
            },
            scales: {
                y: {
                    grid: { color: gridColor, drawBorder: false },
                    ticks: { color: textColor },
                    max: 100,
                    beginAtZero: true,
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { color: textColor },
                },
            },
        },
    })
}

watch(activeRange, async () => {
    await refreshAnalytics()
})

watch(analytics, async () => {
    await renderCharts()
})

onMounted(async () => {
    await refreshAnalytics()

    themeObserver = new MutationObserver(async (mutations) => {
        if (mutations.some((mutation) => mutation.attributeName === 'class')) {
            await renderCharts()
        }
    })
    themeObserver.observe(document.documentElement, { attributes: true })
})

onBeforeUnmount(() => {
    themeObserver?.disconnect()
    destroyCharts()
})

provide(aiAnalyticsPageKey, {
    analytics,
    cssVarColors,
    escalationCanvas,
    executeAction,
    exportCsv,
    metricTrendClass,
    metricTrendIcon,
    openActionModal,
    resolutionCanvas,
    selectedInsight,
    sentimentCanvas,
    showActionModal,
    store,
    toneCardClass,
    toneIconClass,
    toneTextClass,
    toneTitleClass,
})
</script>

<style scoped src="./analytics/AIAnalytics.css"></style>
