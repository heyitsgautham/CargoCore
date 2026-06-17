<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between flex-wrap gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
                    <span class="material-symbols-outlined text-white">smart_toy</span>
                </div>
                <div>
                    <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        Cargo-Core AI Intelligence
                    </h2>
                    <p class="text-xs text-gray-400 mt-0.5">Powered by Gemini · Context-aware logistics assistant</p>
                </div>
            </div>

            <!-- Session Controls -->
            <div class="flex items-center gap-2">
                <router-link to="/logistic/recovery-tickets"
                    class="relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-yellow-600/20 border border-yellow-500/30 text-xs text-yellow-300 hover:bg-yellow-600/30 transition-colors"
                >
                    <span class="material-symbols-outlined text-[16px]">healing</span>
                    Recovery Tickets
                    <span
                        v-if="recoveryCount > 0"
                        class="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center leading-none"
                    >{{ recoveryCount }}</span>
                </router-link>
                <button
                    @click="showSessions = !showSessions"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 hover:bg-white/10 transition-colors"
                >
                    <span class="material-symbols-outlined text-[16px]">history</span>
                    History
                </button>
                <button
                    @click="newSession"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-xs text-blue-300 hover:bg-blue-600/30 transition-colors"
                >
                    <span class="material-symbols-outlined text-[16px]">add</span>
                    New Chat
                </button>
            </div>
        </div>

        <div class="flex gap-4" :class="showSessions ? 'items-start' : ''">
            <!-- Session History Sidebar -->
            <transition name="slide-left">
                <div v-if="showSessions" class="w-64 flex-shrink-0 glass-panel rounded-2xl overflow-hidden">
                    <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                        <span class="text-sm font-semibold text-white">Past Conversations</span>
                        <span v-if="sessionsLoading" class="w-3 h-3 rounded-full border-2 border-blue-400 border-t-transparent animate-spin"></span>
                    </div>
                    <div class="max-h-[540px] overflow-y-auto divide-y divide-white/5">
                        <div v-if="sessions.length === 0 && !sessionsLoading" class="px-4 py-6 text-center text-xs text-gray-500">
                            No past sessions yet
                        </div>
                        <button
                            v-for="s in sessions"
                            :key="s.session_id"
                            @click="loadSession(s.session_id)"
                            class="w-full text-left px-4 py-3 hover:bg-white/5 transition-colors"
                            :class="store.aiSessionId === s.session_id ? 'bg-blue-500/10 border-l-2 border-blue-400' : ''"
                        >
                            <p class="text-xs font-medium text-gray-200 truncate">{{ s.preview || 'Chat session' }}</p>
                            <p class="text-[10px] text-gray-500 mt-0.5">{{ s.created_at ? new Date(s.created_at).toLocaleDateString() : '' }}</p>
                        </button>
                    </div>
                </div>
            </transition>

            <!-- Main Chat Panel -->
            <div class="flex-1 glass-panel rounded-2xl overflow-hidden relative" style="height: 600px; display:flex; flex-direction:column;">
                <!-- Background gradient -->
                <div class="absolute inset-0 bg-gradient-to-b from-blue-50/5 to-transparent pointer-events-none z-0"></div>

                <!-- Active session badge -->
                <div v-if="store.aiSessionId" class="px-5 py-2 border-b border-white/5 bg-white/3 flex items-center gap-2 z-10 relative">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                    <span class="text-[11px] text-gray-400">Session active · <span class="font-mono text-gray-500">{{ String(store.aiSessionId).slice(0,8) }}…</span></span>
                    <button @click="escalateChat" class="ml-auto text-[10px] px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25 transition-colors">
                        Escalate to Human
                    </button>
                </div>

                <!-- Chat History -->
                <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-5 relative z-10 scroll-smooth">
                    <!-- Welcome message when empty -->
                    <div v-if="store.aiMessages.length === 0" class="flex flex-col items-center justify-center h-full gap-4 text-center opacity-60">
                        <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center shadow-xl">
                            <span class="material-symbols-outlined text-white text-3xl">smart_toy</span>
                        </div>
                        <div>
                            <p class="text-gray-300 font-semibold">Ask me anything</p>
                            <p class="text-gray-500 text-sm mt-1">Fleet status, inventory, revenue, route optimisation…</p>
                        </div>
                    </div>

                    <!-- Messages -->
                    <div
                        v-for="(msg, index) in store.aiMessages"
                        :key="msg.id || index"
                        class="flex gap-3"
                        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
                    >
                        <!-- Avatar -->
                        <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold"
                            :class="msg.role === 'ai' ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg shadow-purple-500/20' : 'bg-gray-700 text-gray-200'">
                            {{ msg.role === 'ai' ? 'AI' : 'ME' }}
                        </div>

                        <div class="space-y-1 max-w-[78%]">
                            <div class="p-4 rounded-2xl text-sm leading-relaxed shadow-sm"
                                :class="msg.role === 'ai'
                                    ? 'bg-white/5 border border-white/10 rounded-tl-none text-gray-200'
                                    : 'bg-blue-600/20 border border-blue-500/30 rounded-tr-none text-white'">
                                <div v-html="msg.text"></div>

                                <!-- Structured data table -->
                                <div v-if="msg.data && Object.keys(msg.data).length" class="mt-3 p-3 bg-black/30 rounded-lg border border-white/5 text-xs">
                                    <div v-for="(val, key) in msg.data" :key="key" class="flex justify-between mb-1 last:mb-0">
                                        <span class="text-gray-400 capitalize">{{ String(key).replace(/_/g, ' ') }}:</span>
                                        <span class="text-white font-bold">{{ val }}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="text-[10px] text-gray-500 px-1" :class="msg.role === 'user' ? 'text-right' : ''">{{ msg.time }}</div>
                        </div>
                    </div>

                    <!-- Typing indicator -->
                    <div v-if="isTyping" class="flex gap-3 animate-pulse">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0 flex items-center justify-center text-xs font-bold text-white">AI</div>
                        <div class="bg-white/5 border border-white/10 p-4 rounded-2xl rounded-tl-none flex items-center gap-1.5">
                            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
                            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
                            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
                        </div>
                    </div>
                </div>

                <!-- Escalation success banner -->
                <transition name="fade">
                    <div v-if="escalated" class="mx-4 mb-2 p-3 bg-amber-500/15 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-center gap-2 z-10 relative">
                        <span class="material-symbols-outlined text-[16px]">support_agent</span>
                        Conversation escalated to a human agent!
                    </div>
                </transition>

                <!-- Input Area -->
                <div class="p-5 pt-2 relative z-10 border-t border-white/5">
                    <!-- Suggestion chips -->
                    <div v-if="store.aiSuggestionChips.length" class="flex gap-2 mb-3 overflow-x-auto no-scrollbar pb-1">
                        <button
                            v-for="chip in store.aiSuggestionChips"
                            :key="chip"
                            @click="sendChip(chip)"
                            class="whitespace-nowrap px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-xs text-gray-300 transition-colors flex-shrink-0"
                        >
                            {{ chip }}
                        </button>
                    </div>

                    <div class="relative">
                        <textarea
                            v-model="userInput"
                            @keydown.enter.exact.prevent="handleSend"
                            rows="1"
                            placeholder="Ask about fleet, inventory, deliveries, revenue…"
                            style="resize:none; field-sizing:content; max-height:120px;"
                            class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-5 pr-14 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:bg-white/8 transition-all shadow-inner text-sm"
                        ></textarea>
                        <button
                            @click="handleSend"
                            :disabled="!userInput.trim() || isTyping"
                            class="absolute right-2.5 bottom-2.5 w-9 h-9 flex items-center justify-center bg-blue-600 rounded-lg text-white hover:bg-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            <span class="material-symbols-outlined text-[18px]">send</span>
                        </button>
                    </div>
                    <p class="text-[10px] text-gray-600 mt-2 text-center">Press <kbd class="px-1 py-0.5 rounded bg-white/10 text-gray-400">Enter</kbd> to send · <kbd class="px-1 py-0.5 rounded bg-white/10 text-gray-400">Shift+Enter</kbd> for new line</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { fetchSessions, fetchConversation, escalateConversation, fetchRecoveryTicketsCount } from '@/utils/aiApi'

const store = useLogisticStore()
const userInput = ref('')
const isTyping = ref(false)
const chatContainer = ref(null)
const showSessions = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)
const escalated = ref(false)
const recoveryCount = ref(0)

// ── Helpers ──────────────────────────────────────────────────────────────────

const scrollToBottom = async () => {
    await nextTick()
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function handleSend() {
    const text = userInput.value.trim()
    if (!text || isTyping.value) return
    userInput.value = ''
    isTyping.value = true
    await scrollToBottom()
    try {
        await store.askAi(text)
    } finally {
        isTyping.value = false
        await scrollToBottom()
    }
}

function sendChip(chipText) {
    userInput.value = chipText
    handleSend()
}

function newSession() {
    store.aiSessionId = null
    store.aiMessages = []
    showSessions.value = false
}

async function loadSessionList() {
    sessionsLoading.value = true
    try {
        const res = await fetchSessions()
        sessions.value = res?.sessions || []
    } catch (e) {
        console.warn('Could not load sessions:', e)
    } finally {
        sessionsLoading.value = false
    }
}

async function loadSession(sessionId) {
    try {
        const res = await fetchConversation(sessionId)
        store.aiSessionId = sessionId
        store.aiMessages = (res?.messages || []).map((m, i) => ({
            id: m.id || `msg-${i}`,
            role: m.role === 'assistant' ? 'ai' : m.role,
            text: m.content || m.text || '',
            data: m.data || null,
            time: m.created_at
                ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : '',
        }))
        showSessions.value = false
        await scrollToBottom()
    } catch (e) {
        console.warn('Could not load session:', e)
    }
}

async function escalateChat() {
    if (!store.aiSessionId) return
    try {
        await escalateConversation(store.aiSessionId, 'User requested human support from AI Intelligence page')
        escalated.value = true
        setTimeout(() => { escalated.value = false }, 4000)
    } catch (e) {
        console.warn('Escalation failed:', e)
    }
}

// ── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
    await loadSessionList()
    await scrollToBottom()
    try {
        const res = await fetchRecoveryTicketsCount()
        recoveryCount.value = res?.count ?? 0
    } catch {
        recoveryCount.value = 0
    }
})
</script>

<style scoped>
.slide-left-enter-active, .slide-left-leave-active { transition: all 0.3s ease; }
.slide-left-enter-from, .slide-left-leave-to { opacity: 0; transform: translateX(-20px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
