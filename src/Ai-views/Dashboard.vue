<template>
    <div class="space-y-6">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            <div v-for="stat in stats" :key="stat.label"
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 p-4 md:p-6 rounded-xl flex items-center justify-between shadow-sm">
                <div>
                    <div class="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{{ stat.label }}</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</div>
                    <div class="text-xs mt-1" :class="stat.trendColor">{{ stat.trend }}</div>
                </div>
                <div class="w-12 h-12 rounded-lg flex items-center justify-center" :class="stat.iconBg">
                    <span class="material-symbols-outlined" :class="stat.iconColor">{{ stat.icon }}</span>
                </div>
            </div>
        </div>

        <div v-if="store.loadingDashboard" class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-white/5 p-6 text-sm text-gray-500 dark:text-gray-400">
            Loading live support dashboard...
        </div>

        <div v-else-if="store.error" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ store.error }}
        </div>

        <div v-else-if="dashboard" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 space-y-6">
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            Priority Conversations
                        </h3>
                        <router-link to="/ai/live-conversations"
                            class="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-bold transition-colors">
                            Open Live Inbox →
                        </router-link>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div
                            class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg flex items-center justify-between border border-gray-100 dark:border-white/5">
                            <div>
                                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ dashboard.stats.active_sessions }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">Active Sessions (24h)</div>
                            </div>
                            <span class="material-symbols-outlined text-gray-400">chat</span>
                        </div>
                        <div
                            class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 p-4 rounded-lg flex items-center justify-between">
                            <div>
                                <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ dashboard.stats.open_escalations }}</div>
                                <div class="text-xs text-red-500/70 dark:text-red-300/70">Open Escalations</div>
                            </div>
                            <span class="material-symbols-outlined text-red-500 dark:text-red-400">notification_important</span>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <div v-for="session in prioritySessions" :key="session.session_id"
                            class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 hover:border-purple-300 dark:hover:border-white/10 flex items-center justify-between transition-all">
                            <div class="flex items-center gap-3">
                                <div
                                    class="w-10 h-10 rounded-full bg-gradient-to-br from-gray-200 dark:from-gray-700 to-gray-300 dark:to-gray-600 flex items-center justify-center text-xs font-bold text-gray-700 dark:text-white">
                                    {{ initials(session.user_name) }}
                                </div>
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                        {{ session.user_name }}
                                        <span v-if="session.needs_human_attention"
                                            class="text-[10px] px-1.5 rounded uppercase bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300">
                                            Needs Human
                                        </span>
                                        <span v-if="session.escalation?.status === 'OPEN'"
                                            class="text-[10px] px-1.5 rounded uppercase bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400">
                                            Escalated
                                        </span>
                                    </div>
                                    <div class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[220px]">
                                        {{ session.last_message }}
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="text-right">
                                    <div class="text-[10px] text-gray-400">{{ formatTime(session.last_message_at) }}</div>
                                    <div class="text-xs font-bold"
                                        :class="session.sentiment === 'Negative' ? 'text-red-500' : 'text-green-500'">
                                        {{ session.sentiment || 'Neutral' }}
                                    </div>
                                </div>
                                <router-link :to="`/ai/live-conversations?sessionId=${session.session_id}`"
                                    class="p-2 rounded-full bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 hover:bg-purple-600 hover:text-white dark:hover:bg-purple-500 dark:hover:text-white transition-colors">
                                    <span class="material-symbols-outlined text-sm">forum</span>
                                </router-link>
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Live Support Activity</h3>
                    <div class="space-y-4 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
                        <div v-for="event in dashboard.activity_feed" :key="event.id"
                            class="flex gap-4 p-3 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                                :class="feedIconBg(event.type)">
                                <span class="material-symbols-outlined text-sm" :class="feedIconText(event.type)">
                                    {{ feedIcon(event.type) }}
                                </span>
                            </div>
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ event.title }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{{ event.description }}</div>
                                <div class="text-[10px] text-gray-400">{{ formatTime(event.created_at) }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="space-y-6">
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 p-6 rounded-xl text-center relative overflow-hidden shadow-sm">
                    <div class="absolute top-0 right-0 p-3 opacity-5">
                        <span class="material-symbols-outlined text-8xl text-gray-900 dark:text-white">mood</span>
                    </div>
                    <h3 class="font-bold text-gray-900 dark:text-white mb-6 relative z-10">Conversation Sentiment</h3>
                    <div class="space-y-6 text-left">
                        <div class="flex justify-between items-end">
                            <div>
                                <span class="text-5xl font-bold text-gray-900 dark:text-white block leading-none">{{ sentimentPositivePct }}%</span>
                                <span class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold tracking-widest mt-2 block">Positive / Neutral Mix</span>
                            </div>
                            <div class="text-right">
                                <span class="text-xl font-bold text-gray-900 dark:text-white block leading-none">{{ dashboard.stats.total_sessions }}</span>
                                <span class="text-xs text-gray-500 dark:text-gray-400 block mt-1">Total Sessions</span>
                            </div>
                        </div>

                        <div class="w-full h-4 rounded-full overflow-hidden flex bg-gray-100 dark:bg-white/5 shadow-inner">
                            <div class="bg-green-500 h-full" :style="{ width: `${sentimentPositivePct}%` }"></div>
                            <div class="bg-red-500 h-full" :style="{ width: `${100 - sentimentPositivePct}%` }"></div>
                        </div>

                        <div class="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 dark:border-white/5">
                            <div class="bg-green-50 dark:bg-green-500/10 p-2 rounded-lg border border-green-100 dark:border-green-500/20">
                                <div class="flex items-center gap-1.5 mb-1">
                                    <span class="w-2 h-2 rounded-full bg-green-500 shrink-0"></span>
                                    <span class="text-[10px] text-green-700 dark:text-green-400 font-bold uppercase truncate">Stable</span>
                                </div>
                                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ stableSessions }}</div>
                            </div>
                            <div class="bg-red-50 dark:bg-red-500/10 p-2 rounded-lg border border-red-100 dark:border-red-500/20">
                                <div class="flex items-center gap-1.5 mb-1">
                                    <span class="w-2 h-2 rounded-full bg-red-500 shrink-0"></span>
                                    <span class="text-[10px] text-red-700 dark:text-red-400 font-bold uppercase truncate">Negative</span>
                                </div>
                                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ negativeSessions }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 p-6 rounded-xl shadow-sm">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Recent Contact Form Requests</h3>
                    <div class="space-y-3">
                        <div v-for="submission in dashboard.recent_contact_submissions" :key="submission.id"
                            class="flex items-start gap-3 p-3 rounded-lg border border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5">
                            <span class="material-symbols-outlined shrink-0" :class="submission.priority === 'urgent' ? 'text-red-500' : 'text-purple-500'">mail</span>
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">
                                    {{ submission.name }}
                                    <span class="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300">
                                        {{ submission.reference_code }}
                                    </span>
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">{{ submission.subject }}</div>
                                <div class="text-[10px] text-gray-400 mt-1">{{ formatTime(submission.created_at) }}</div>
                            </div>
                        </div>
                        <router-link to="/ai/contact-forms"
                            class="inline-flex text-sm font-bold text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300">
                            Review all contact submissions →
                        </router-link>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'

import { useAiSupportStore } from '@/stores/aiSupportStore'

const store = useAiSupportStore()
let refreshTimer = null

onMounted(async () => {
    await store.loadDashboard()
    if (!store.sessionsLoaded) {
        await store.loadSessions()
    }
    refreshTimer = setInterval(() => {
        store.loadDashboard().catch(() => {})
        store.loadSessions().catch(() => {})
    }, 15000)
})

onUnmounted(() => {
    if (refreshTimer) clearInterval(refreshTimer)
})

const dashboard = computed(() => store.dashboard)
const prioritySessions = computed(() => {
    return (dashboard.value?.priority_sessions || []).filter((session) => {
        const role = String(session?.user_role || '').trim().toUpperCase()
        return role === 'INDIVIDUAL' || role === 'VENDOR'
    })
})

const stats = computed(() => {
    const current = dashboard.value?.stats
    return [
        {
            label: 'Total Sessions',
            value: current?.total_sessions ?? 0,
            trend: 'All tracked live support conversations',
            trendColor: 'text-gray-500 dark:text-gray-400',
            icon: 'forum',
            iconBg: 'bg-purple-100 dark:bg-purple-500/20',
            iconColor: 'text-purple-600 dark:text-purple-400',
        },
        {
            label: 'Active in 24h',
            value: current?.active_sessions ?? 0,
            trend: 'Customers who messaged recently',
            trendColor: 'text-green-600 dark:text-green-400',
            icon: 'schedule',
            iconBg: 'bg-blue-100 dark:bg-blue-500/20',
            iconColor: 'text-blue-600 dark:text-blue-400',
        },
        {
            label: 'Human Engaged',
            value: current?.human_engaged_sessions ?? 0,
            trend: `${current?.sessions_needing_human ?? 0} waiting for human action`,
            trendColor: 'text-green-600 dark:text-green-400',
            icon: 'support_agent',
            iconBg: 'bg-green-100 dark:bg-green-500/20',
            iconColor: 'text-green-600 dark:text-green-400',
        },
        {
            label: 'Open Contact Forms',
            value: current?.open_contact_forms ?? 0,
            trend: `${current?.new_contact_forms ?? 0} new submissions waiting`,
            trendColor: 'text-red-600 dark:text-red-400',
            icon: 'mark_email_unread',
            iconBg: 'bg-red-100 dark:bg-red-500/20',
            iconColor: 'text-red-600 dark:text-red-400',
        },
    ]
})

const negativeSessions = computed(() => {
    return prioritySessions.value.filter((item) => item.sentiment === 'Negative').length
})

const stableSessions = computed(() => {
    return prioritySessions.value.length - negativeSessions.value
})

const sentimentPositivePct = computed(() => {
    const total = prioritySessions.value.length
    if (!total) return 100
    return Math.max(0, Math.round((stableSessions.value / total) * 100))
})

function initials(name) {
    return (name || 'C')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() || '')
        .join('')
}

function formatTime(value) {
    const date = new Date(value)
    const diffSeconds = Math.floor((Date.now() - date.getTime()) / 1000)
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`
    return `${Math.floor(diffSeconds / 86400)}d ago`
}

function feedIcon(type) {
    if (type === 'contact_submission') return 'mail'
    if (type === 'escalation') return 'warning'
    return 'chat'
}

function feedIconBg(type) {
    if (type === 'contact_submission') return 'bg-purple-100 dark:bg-purple-500/20'
    if (type === 'escalation') return 'bg-red-100 dark:bg-red-500/20'
    return 'bg-blue-100 dark:bg-blue-500/20'
}

function feedIconText(type) {
    if (type === 'contact_submission') return 'text-purple-600 dark:text-purple-400'
    if (type === 'escalation') return 'text-red-600 dark:text-red-400'
    return 'text-blue-600 dark:text-blue-400'
}
</script>
