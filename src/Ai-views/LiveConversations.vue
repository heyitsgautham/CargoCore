<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col md:flex-row gap-6 overflow-hidden">
        <div
            class="w-full md:w-96 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-xl flex flex-col h-1/3 md:h-full shadow-sm">
            <div class="p-4 border-b border-gray-100 dark:border-white/5 space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="font-bold text-gray-900 dark:text-white">Active Chats</h3>
                    <div
                        class="bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 px-2 py-1 rounded text-xs font-bold">
                        {{ escalatedCount }} Escalated
                    </div>
                </div>
                <div class="relative">
                    <input v-model="searchQuery" type="text" placeholder="Search conversations..."
                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-purple-500 transition-colors">
                    <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-lg">search</span>
                </div>
                <div class="flex gap-2 overflow-x-auto no-scrollbar pb-1">
                    <button v-for="filter in chatFilters" :key="filter" @click="activeFilter = filter"
                        class="px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-colors"
                        :class="activeFilter === filter
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/10'">
                        {{ filter }}
                    </button>
                </div>
            </div>

            <div class="flex-1 overflow-y-auto custom-scrollbar">
                <div v-if="store.loadingSessions" class="p-6 text-center text-gray-400 text-sm">
                    Loading live conversations...
                </div>
                <div v-else-if="filteredSessions.length === 0" class="p-6 text-center text-gray-400 text-sm">
                    No conversations match your filter.
                </div>
                <div v-for="session in filteredSessions" :key="session.session_id"
                    class="p-4 border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
                    :class="selectedSession?.session?.session_id === session.session_id ? 'bg-purple-50 dark:bg-purple-500/10 border-l-4 border-l-purple-500' : ''"
                    @click="selectSession(session.session_id)">
                    <div class="flex justify-between items-start mb-1">
                        <div class="flex items-center gap-2">
                            <span v-if="session.escalation?.status === 'OPEN'"
                                class="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0"></span>
                            <span class="font-bold text-gray-900 dark:text-white text-sm">{{ session.user_name }}</span>
                        </div>
                        <span class="text-[10px] text-gray-400">{{ formatTime(session.last_message_at) }}</span>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate mb-2">{{ session.last_message }}</p>
                    <div class="flex gap-2 flex-wrap">
                        <span v-if="session.sentiment === 'Negative'"
                            class="px-1.5 py-0.5 rounded bg-red-100 text-red-600 dark:bg-red-500/10 dark:text-red-400 text-[10px]">Negative</span>
                        <span v-if="session.needs_human_attention"
                            class="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300 text-[10px]">Needs Human</span>
                        <span v-if="!session.human_agent_engaged"
                            class="px-1.5 py-0.5 rounded bg-purple-100 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400 text-[10px]">Bot
                            Active</span>
                        <span v-if="session.escalation?.status === 'OPEN'"
                            class="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400 text-[10px]">Escalated</span>
                    </div>
                </div>
            </div>
        </div>

        <div
            class="flex-1 min-w-0 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-xl flex flex-col h-2/3 md:h-full relative overflow-hidden shadow-sm">
            <div v-if="selectedSession" class="flex flex-col h-full">
                <div
                    class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-black/20">
                    <div class="flex items-center gap-3">
                        <div
                            class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                            {{ initials(selectedSession.session.user_name) }}
                        </div>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white">{{ selectedSession.session.user_name }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">
                                {{ selectedSession.session.user_role || 'Customer' }}
                                <span v-if="selectedSession.session.latest_order_tracking_code"> · Order #{{ selectedSession.session.latest_order_tracking_code }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button v-if="!selectedSession.session.human_agent_engaged && isSupportManager" @click="takeOver"
                            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg text-sm flex items-center gap-2 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                            :disabled="store.actionInFlight">
                            <span v-if="store.actionInFlight" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                            <span v-else class="material-symbols-outlined text-sm">front_hand</span>
                            <span class="hidden sm:inline">{{ store.actionInFlight ? 'Taking Over…' : 'Take Over' }}</span>
                        </button>
                        <button @click="showCustomerProfile = true"
                            class="p-2 border border-gray-200 dark:border-white/10 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                            title="View Profile">
                            <span class="material-symbols-outlined">person</span>
                        </button>
                        <button v-if="isSupportManager" @click="escalateChat"
                            class="p-2 border border-gray-200 dark:border-white/10 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                            title="Escalate"
                            :disabled="store.actionInFlight">
                            <span class="material-symbols-outlined">warning</span>
                        </button>
                    </div>
                </div>

                <div class="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 custom-scrollbar bg-gray-50/50 dark:bg-black/10">
                        <div v-if="selectedSession.session.sentiment === 'Negative'"
                            class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 p-3 rounded-lg flex items-start gap-3 mb-4 max-w-lg mx-auto">
                            <span class="material-symbols-outlined text-red-500 shrink-0">warning</span>
                            <div>
                                <div class="text-sm font-bold text-red-600 dark:text-red-400">Negative Sentiment Detected</div>
                                <div class="text-xs text-red-500/70 dark:text-red-300/70">This conversation includes frustration signals. Human follow-up is recommended.</div>
                            </div>
                        </div>
                    <div v-if="selectedSession.session.needs_human_attention"
                        class="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 p-3 rounded-lg flex items-start gap-3 mb-4 max-w-lg mx-auto">
                        <span class="material-symbols-outlined text-amber-500 shrink-0">support_agent</span>
                        <div>
                            <div class="text-sm font-bold text-amber-700 dark:text-amber-300">Support Manager Requested</div>
                            <div class="text-xs text-amber-600/80 dark:text-amber-200/80">{{ selectedSession.session.attention_reason || 'This conversation needs a Support Manager response.' }}</div>
                        </div>
                    </div>

                    <div v-for="message in selectedSession.messages" :key="message.id" class="flex gap-3"
                        :class="isSupportMessage(message) ? 'flex-row-reverse' : ''">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                            :class="avatarClass(message)">
                            <span class="material-symbols-outlined text-xs">{{ avatarIcon(message) }}</span>
                        </div>
                        <div class="max-w-[75%]">
                            <div class="text-[10px] text-gray-400 mb-1" :class="isSupportMessage(message) ? 'text-right' : ''">
                                {{ message.author_name }}
                            </div>
                            <div class="p-3 rounded-2xl text-sm shadow-sm"
                                :class="messageBubbleClass(message)">
                                {{ message.message }}
                            </div>
                            <div class="text-[10px] text-gray-400 mt-1" :class="isSupportMessage(message) ? 'text-right' : ''">
                                {{ formatMessageTime(message.created_at) }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-4 border-t border-gray-100 dark:border-white/5 bg-white dark:bg-black/20">
                    <div v-if="!isSupportManager" class="mb-3 rounded-lg border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                        Only the Support Manager can take over and reply in customer conversations.
                    </div>
                    <div class="flex gap-2 mb-2 overflow-x-auto custom-scrollbar pb-1">
                        <button v-for="suggestion in suggestions" :key="suggestion" @click="inputText = suggestion"
                            class="text-xs bg-gray-100 hover:bg-gray-200 dark:bg-white/5 dark:hover:bg-white/10 px-3 py-1.5 rounded-full text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-white/5 whitespace-nowrap transition-colors flex-shrink-0">
                            {{ suggestion }}
                        </button>
                    </div>
                    <div class="relative">
                        <input v-model="inputText" type="text" :placeholder="isSupportManager ? 'Type a Support Manager reply...' : 'Support Manager access required to reply...'"
                            @keyup.enter="sendMessage"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl pl-4 pr-12 py-3 text-gray-900 dark:text-white focus:outline-none focus:border-purple-500 transition-colors"
                            :disabled="!isSupportManager">
                        <button @click="sendMessage"
                            class="absolute right-2 top-2 p-1.5 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors disabled:opacity-50"
                            :disabled="store.actionInFlight || !inputText.trim() || !isSupportManager">
                            <span class="material-symbols-outlined text-sm">send</span>
                        </button>
                    </div>
                </div>
            </div>

            <div v-else class="flex flex-col items-center justify-center h-full text-center p-8">
                <div class="w-16 h-16 rounded-full bg-gray-100 dark:bg-white/5 flex items-center justify-center mb-4">
                    <span class="material-symbols-outlined text-4xl text-gray-400">chat_bubble_outline</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Select a Conversation</h3>
                <p class="max-w-xs text-gray-500 dark:text-gray-400">Choose a chat from the sidebar to view details,
                    take over from AI, or manage escalation.</p>
            </div>
        </div>

        <Teleport to="body">
            <div v-if="showCustomerProfile && selectedSession"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                @click.self="showCustomerProfile = false">
                <div
                    class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between">
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Customer Profile</h3>
                        <button @click="showCustomerProfile = false" class="text-gray-400 hover:text-gray-600">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="flex items-center gap-4">
                            <div
                                class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
                                {{ initials(selectedSession.session.user_name) }}
                            </div>
                            <div>
                                <h4 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedSession.session.user_name }}</h4>
                                <p class="text-gray-500">{{ selectedSession.session.user_role || 'Customer' }}</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                                <div class="text-xs text-gray-500 mb-1">Sentiment</div>
                                <div class="font-bold text-sm"
                                    :class="selectedSession.session.sentiment === 'Negative' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                                    {{ selectedSession.session.sentiment || 'Neutral' }}
                                </div>
                            </div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                                <div class="text-xs text-gray-500 mb-1">Latest Order</div>
                                <div class="font-bold text-sm text-gray-900 dark:text-white">
                                    {{ selectedSession.session.latest_order_tracking_code || 'N/A' }}
                                </div>
                            </div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                                <div class="text-xs text-gray-500 mb-1">Email</div>
                                <div class="font-bold text-sm text-gray-900 dark:text-white break-all">
                                    {{ selectedSession.session.user_email || 'N/A' }}
                                </div>
                            </div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                                <div class="text-xs text-gray-500 mb-1">Phone</div>
                                <div class="font-bold text-sm text-gray-900 dark:text-white">
                                    {{ selectedSession.session.user_phone || 'N/A' }}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="p-6 border-t border-gray-100 dark:border-white/5">
                        <button @click="showCustomerProfile = false"
                            class="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition-colors">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/authStore'
import { useAiSupportStore } from '@/stores/aiSupportStore'

const route = useRoute()
const router = useRouter()
const store = useAiSupportStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const activeFilter = ref('All')
const inputText = ref('')
const showCustomerProfile = ref(false)
let refreshTimer = null

const chatFilters = ['All', 'Angry 😡', 'Bot Active', 'Escalated']
const isSupportManager = computed(() => {
    const role = authStore.userRole
    return role === 'LOGISTIC_MANAGER'
        || role === 'AI_AGENT'
        || role === 'AI_SUPPORT'
        || role === 'CUSTOMER_SUPPORT'
        || role === 'ai_agent'
        || role === 'ai_support'
        || role === 'customer_support'
})

const suggestions = [
    'I am checking this for you right now.',
    'Thank you for your patience while I review this.',
    'I have taken over this conversation and will assist you directly.',
    'Let me verify the shipment and refund status.',
    'Could you confirm the tracking code once more for me?',
    'I am escalating this internally so we can resolve it faster.',
]

const filteredSessions = computed(() => {
    let result = store.sessions

    if (activeFilter.value === 'Angry 😡') {
        result = result.filter((session) => session.sentiment === 'Negative')
    } else if (activeFilter.value === 'Bot Active') {
        result = result.filter((session) => !session.human_agent_engaged)
    } else if (activeFilter.value === 'Escalated') {
        result = result.filter((session) => session.escalation?.status === 'OPEN')
    }

    if (searchQuery.value.trim()) {
        const query = searchQuery.value.trim().toLowerCase()
        result = result.filter((session) =>
            session.user_name.toLowerCase().includes(query)
            || (session.user_email || '').toLowerCase().includes(query)
            || (session.last_message || '').toLowerCase().includes(query)
            || (session.latest_order_tracking_code || '').toLowerCase().includes(query)
        )
    }

    return result
})

const selectedSession = computed(() => store.selectedSession)
const escalatedCount = computed(() => store.sessions.filter((session) => session.escalation?.status === 'OPEN').length)

onMounted(async () => {
    await store.loadSessions()
    const targetSessionId = route.query.sessionId || route.query.chatId
    if (targetSessionId) {
        await selectSession(targetSessionId)
    } else {
        store.clearSelectedSession()
    }
    refreshTimer = setInterval(async () => {
        try {
            await store.loadSessions(searchQuery.value)
            if (store.selectedSession?.session?.session_id) {
                await store.loadSessionDetail(store.selectedSession.session.session_id)
            }
        } catch {
            // keep the inbox usable during transient polling failures
        }
    }, 15000)
})

onUnmounted(() => {
    if (refreshTimer) clearInterval(refreshTimer)
})

watch(
    () => route.query.sessionId || route.query.chatId,
    async (sessionId) => {
        if (!sessionId) {
            store.clearSelectedSession()
            return
        }
        if (store.selectedSession?.session?.session_id === sessionId) return
        await selectSession(sessionId)
    },
)

async function selectSession(sessionId) {
    if (!sessionId) return
    const detail = await store.loadSessionDetail(sessionId)
    if (!detail) return
    router.replace({
        query: {
            ...route.query,
            sessionId,
        },
    })
}

async function sendMessage() {
    if (!isSupportManager.value) return
    if (!inputText.value.trim() || !selectedSession.value) return
    await store.sendReply(selectedSession.value.session.session_id, inputText.value.trim())
    inputText.value = ''
}

async function takeOver() {
    if (!isSupportManager.value) return
    if (!selectedSession.value) return
    await store.takeOver(selectedSession.value.session.session_id)
}

async function escalateChat() {
    if (!isSupportManager.value) return
    if (!selectedSession.value) return
    const reason = window.prompt('Why are you escalating this conversation?', 'Customer needs manual intervention')
    if (!reason) return
    await store.escalate(selectedSession.value.session.session_id, reason)
}

function initials(name) {
    return (name || 'C')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() || '')
        .join('')
}

function isSupportMessage(message) {
    return message.role === 'assistant'
}

function avatarClass(message) {
    if (message.author_role === 'agent') {
        return 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400'
    }
    if (message.author_role === 'ai') {
        return 'bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400'
    }
    return 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
}

function avatarIcon(message) {
    if (message.author_role === 'agent') return 'support_agent'
    if (message.author_role === 'ai') return 'smart_toy'
    return 'person'
}

function messageBubbleClass(message) {
    if (message.author_role === 'agent') {
        return 'bg-blue-600 text-white rounded-tr-none'
    }
    if (message.author_role === 'ai') {
        return 'bg-purple-600 text-white rounded-tr-none'
    }
    return 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-200 rounded-tl-none border border-gray-100 dark:border-white/5'
}

function formatMessageTime(value) {
    return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatTime(value) {
    const date = new Date(value)
    const diffSeconds = Math.floor((Date.now() - date.getTime()) / 1000)
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`
    return `${Math.floor(diffSeconds / 86400)}d ago`
}
</script>
