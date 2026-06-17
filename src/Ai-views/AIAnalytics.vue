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

            <h3 class="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-xs pt-4 mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px] text-purple-500">auto_awesome</span>
                Direct AI Insights
            </h3>
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

        <Teleport to="body">
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
        </Teleport>
    </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
</script>

<style scoped>
.tooltip-trigger .tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 0.5rem;
    padding: 0.25rem 0.5rem;
    background: rgb(17 24 39);
    color: white;
    font-size: 10px;
    border-radius: 0.25rem;
    opacity: 0;
    white-space: nowrap;
    pointer-events: none;
    transition: opacity 150ms ease;
    z-index: 50;
}

.tooltip-trigger:hover .tooltip {
    opacity: 1;
}
</style>
