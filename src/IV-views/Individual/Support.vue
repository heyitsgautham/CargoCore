<template>
    <div class="space-y-6">

        <!-- Header -->
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-green-500">support_agent</span>
                AI Support Chat
            </h2>
            <button
                v-if="chatStarted"
                @click="resetSession"
                class="inline-flex items-center gap-2 self-start rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-50 dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
            >
                <span class="material-symbols-outlined text-[18px]">add_comment</span>
                New Chat
            </button>
        </div>

        <!-- ── STEP 1: Order Picker ─────────────────────────────────────────── -->
        <div v-if="!chatStarted" class="glass-panel rounded-xl p-6 max-w-lg mx-auto">
            <div class="flex flex-col items-center text-center gap-3 mb-6">
                <div class="w-14 h-14 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center">
                    <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
                </div>
                <div>
                    <p class="font-bold text-gray-900 dark:text-white">Start Support Chat</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Select an active order for context, or start a general chat without one.
                    </p>
                </div>
            </div>

            <div v-if="loadingOrders" class="flex justify-center py-6 text-sm text-gray-400">
                Loading your orders…
            </div>

            <template v-else>
                <div v-if="selectableOrders.length > 0" class="space-y-2 mb-4">
                    <p class="text-xs font-bold uppercase tracking-wide text-gray-400 mb-3">Your Active Orders</p>
                    <button
                        v-for="order in selectableOrders"
                        :key="order.backendId"
                        @click="selectOrder(order)"
                        class="w-full flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/60 hover:bg-green-50/50 dark:hover:bg-white/8 transition-all group"
                    >
                        <div class="text-left">
                            <div class="font-bold text-sm text-gray-900 dark:text-white font-mono">{{ order.trackingCode || order.id }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ order.id !== order.trackingCode ? order.id : '' }}</div>
                        </div>
                        <div class="flex items-center gap-3">
                            <span
                                class="text-[11px] font-bold uppercase px-2 py-0.5 rounded-full"
                                :class="statusBadgeClass(order.status)"
                            >{{ order.status }}</span>
                            <span class="material-symbols-outlined text-gray-400 group-hover:text-green-500 transition-colors text-[18px]">arrow_forward</span>
                        </div>
                    </button>
                </div>
                <div v-else class="text-center py-4 mb-4">
                    <span class="material-symbols-outlined text-4xl text-gray-300 dark:text-white/20 mb-2 block">inbox</span>
                    <p class="text-sm text-gray-500 dark:text-gray-400">No active orders found.</p>
                </div>

                <!-- Chat without order -->
                <div class="pt-3 border-t border-gray-200 dark:border-white/10">
                    <button
                        @click="startWithoutOrder"
                        class="w-full flex items-center justify-center gap-2 p-3 rounded-xl border border-dashed border-gray-300 dark:border-white/15 bg-gray-50 dark:bg-white/5 hover:border-green-500/60 hover:bg-green-50/30 dark:hover:bg-white/8 transition-all text-sm text-gray-600 dark:text-gray-400 hover:text-green-700 dark:hover:text-green-400"
                    >
                        <span class="material-symbols-outlined text-[18px]">chat</span>
                        Chat without selecting an order
                    </button>
                </div>
            </template>
        </div>

        <!-- ── STEP 2: Chat Interface ──────────────────────────────────────── -->
        <div v-else-if="chatStarted" class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Chat Panel -->
            <div class="lg:col-span-2 glass-panel rounded-xl flex flex-col" style="height: min(72vh, 620px);">

                <!-- Chat header -->
                <div class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center">
                        <span class="material-symbols-outlined text-white">smart_toy</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="font-bold text-gray-900 dark:text-white text-sm">Cargo-Core AI</div>
                        <div class="flex items-center gap-1 text-xs text-green-500">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500 inline-block"></span>
                            <template v-if="selectedOrder">Order: <span class="font-mono ml-1">{{ selectedOrder.trackingCode || selectedOrder.id }}</span></template>
                            <template v-else>General Support</template>
                        </div>
                    </div>
                    <button @click="resetSession" title="Change order / new chat"
                        class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined text-[18px]">close</span>
                    </button>
                </div>

                <!-- Session-closed banner -->
                <div v-if="humanHandoffLocked"
                    class="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 px-4 py-3 text-xs text-orange-700 dark:text-orange-300">
                    <span class="material-symbols-outlined text-[16px] mt-0.5 flex-shrink-0">lock</span>
                    <span>Your human support session has been resolved and closed. You can continue chatting with AI, but human support is no longer available for this session.</span>
                </div>

                <!-- Messages -->
                <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
                    <div
                        v-for="msg in messages"
                        :key="msg.id"
                        :class="msg.sender === 'user' ? 'flex justify-end' : 'flex justify-start'"
                    >
                        <!-- Session closed notice -->
                        <div v-if="msg.sender === 'closed'"
                            class="w-full flex justify-center">
                            <div class="flex items-center gap-2 px-4 py-2 rounded-full bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 text-xs text-orange-600 dark:text-orange-300">
                                <span class="material-symbols-outlined text-[14px]">lock</span>
                                {{ msg.text }}
                            </div>
                        </div>

                        <!-- Agent-waiting status pill (shown instead of AI reply when human has taken over) -->
                        <div v-else-if="msg.sender === 'status'"
                            class="w-full flex justify-center">
                            <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-white/10 text-xs text-gray-400 dark:text-gray-500">
                                <span class="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse inline-block"></span>
                                {{ msg.text }}
                            </div>
                        </div>

                        <!-- Regular message bubbles -->
                        <div
                            v-else-if="!['closed','status'].includes(msg.sender)"
                            class="max-w-[80%] sm:max-w-[70%]"
                        >
                            <div
                                class="p-3 rounded-xl text-sm"
                                :class="msg.sender === 'user'
                                    ? 'bg-green-600 text-white rounded-br-sm'
                                    : msg.sender === 'support'
                                        ? 'bg-orange-50 border border-orange-200 text-gray-900 dark:bg-orange-500/10 dark:border-orange-500/20 dark:text-white rounded-bl-sm'
                                        : 'bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-bl-sm'"
                            >
                                <!-- Human Support label (only for actual agent replies) -->
                                <div v-if="msg.sender === 'support'" class="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-orange-500">
                                    <span class="material-symbols-outlined text-[12px]">support_agent</span>
                                    Human Support
                                </div>
                                <!-- Escalating badge on bot bubble when handover was triggered -->
                                <div v-if="msg.sender === 'bot' && msg.intent === 'handover'" class="mb-1 flex items-center gap-1 text-[10px] font-semibold text-blue-500 dark:text-blue-400">
                                    <span class="material-symbols-outlined text-[12px]">escalator_warning</span>
                                    Connecting to Human Support…
                                </div>
                                <!-- Ticket-created badge when handover confirmed -->
                                <div v-if="msg.sender === 'bot' && msg.intent === 'handover'" class="mt-1 flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
                                    <span class="material-symbols-outlined text-[12px]">confirmation_number</span>
                                    Support ticket created — a manager will follow up shortly.
                                </div>
                                <p v-if="msg.sender === 'user'" class="whitespace-pre-wrap">{{ msg.text }}</p>
                                <div v-else class="whitespace-pre-wrap" v-html="msg.html || msg.text"></div>
                                <div
                                    class="text-[10px] mt-1"
                                    :class="msg.sender === 'user' ? 'text-green-200' : msg.sender === 'support' ? 'text-orange-400' : 'text-gray-400'"
                                >{{ msg.time }}</div>
                            </div>
                            <!-- "Not helpful?" link shown under each normal bot reply (not handover, not user msg) -->
                            <div v-if="msg.sender === 'bot' && msg.intent !== 'handover' && !humanHandoffLocked"
                                class="mt-1 flex items-center gap-1">
                                <button
                                    @click="sendQuickAction('I am not satisfied with this response. I need human support.')"
                                    class="flex items-center gap-1 text-[10px] text-gray-400 hover:text-orange-500 dark:hover:text-orange-400 transition-colors">
                                    <span class="material-symbols-outlined text-[12px]">thumb_down</span>
                                    Not helpful? Talk to a human
                                </button>
                            </div>
                        </div>
                    </div>

                    <div v-if="typing" class="flex justify-start">
                        <div class="bg-gray-100 dark:bg-white/10 px-4 py-2 rounded-xl text-gray-400 text-sm">
                            <span class="animate-pulse">● ● ●</span>
                        </div>
                    </div>
                </div>

                <!-- Input -->
                <div class="p-4 border-t border-gray-200 dark:border-white/5">
                    <div class="flex gap-2">
                        <input
                            v-model="newMessage"
                            @keyup.enter="sendMessage"
                            type="text"
                            placeholder="Type your message…"
                            class="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none text-sm"
                        />
                        <button
                            @click="sendMessage"
                            :disabled="typing || !newMessage.trim()"
                            class="px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span class="material-symbols-outlined text-sm">send</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Side panel -->
            <div class="space-y-4">
                <!-- Selected order info -->
                <div v-if="selectedOrder" class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Active Order</h3>
                    <div class="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                        <div class="flex justify-between">
                            <span>Order ID</span>
                            <span class="font-mono font-bold text-gray-900 dark:text-white">{{ selectedOrder.trackingCode || selectedOrder.id }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Status</span>
                            <span class="font-bold" :class="statusTextClass(selectedOrder.status)">{{ selectedOrder.status }}</span>
                        </div>
                        <div v-if="selectedOrder.pickupLocation || selectedOrder.from" class="flex justify-between">
                            <span>From</span>
                            <span class="text-right max-w-[140px] truncate">{{ selectedOrder.pickupLocation || selectedOrder.from }}</span>
                        </div>
                        <div v-if="selectedOrder.deliveryLocation || selectedOrder.to" class="flex justify-between">
                            <span>To</span>
                            <span class="text-right max-w-[140px] truncate">{{ selectedOrder.deliveryLocation || selectedOrder.to }}</span>
                        </div>
                    </div>
                    <button @click="resetSession"
                        class="mt-4 w-full text-xs text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors py-1.5 border border-gray-200 dark:border-white/10 rounded-lg hover:border-red-300 dark:hover:border-red-500/30">
                        Change Order
                    </button>
                </div>
                <!-- General chat (no order selected) -->
                <div v-else class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-2 text-sm">General Support</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Chatting without a linked order. You can ask general questions or request human support.</p>
                    <button @click="resetSession"
                        class="mt-4 w-full text-xs text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors py-1.5 border border-gray-200 dark:border-white/10 rounded-lg hover:border-red-300 dark:hover:border-red-500/30">
                        New Chat
                    </button>
                </div>

                <!-- Quick actions -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Quick Actions</h3>
                    <div class="space-y-2">
                        <button
                            v-for="action in quickActions"
                            :key="action.label"
                            @click="sendQuickAction(action.message)"
                            class="w-full text-left p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/5 hover:border-green-500/50 hover:bg-gray-100 dark:hover:bg-white/10 transition-all flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300"
                        >
                            <span class="material-symbols-outlined text-lg" :class="action.color">{{ action.icon }}</span>
                            {{ action.label }}
                        </button>
                    </div>
                </div>

                <!-- Service mods -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Service Modifications</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">Modify your selected order:</p>
                    <div class="space-y-2">
                        <button
                            v-for="mod in serviceMods"
                            :key="mod.label"
                            @click="sendQuickAction(mod.message)"
                            class="w-full text-left p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/5 hover:border-blue-500/50 hover:bg-gray-100 dark:hover:bg-white/10 transition-all flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300"
                        >
                            <span class="material-symbols-outlined text-lg" :class="mod.color">{{ mod.icon }}</span>
                            {{ mod.label }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { sendChat, fetchConversation } from '@/utils/aiApi'
import { useIndividualStore } from '@/stores/individualStore'

const store = useIndividualStore()
const SESSION_KEY = 'support_session_ind'

// ── Orders ────────────────────────────────────────────────────────────────────
const loadingOrders = ref(false)
const selectedOrder = ref(null)
const chatStarted = ref(false)

const selectableOrders = computed(() =>
    store.orders.filter(o => !['delivered', 'cancelled'].includes(o.status))
)

async function loadOrders() {
    if (store.orders.length > 0) return
    loadingOrders.value = true
    try {
        await store.fetchOrders()
    } finally {
        loadingOrders.value = false
    }
}

function selectOrder(order) {
    selectedOrder.value = order
    chatStarted.value = true
    sessionId.value = null
    messages.value = createWelcomeMessages()
    saveSession()
    scrollToBottom()
}

function startWithoutOrder() {
    selectedOrder.value = null
    chatStarted.value = true
    sessionId.value = null
    messages.value = createWelcomeMessages()
    saveSession()
    scrollToBottom()
}

// ── Session ───────────────────────────────────────────────────────────────────
// No localStorage — session is ephemeral to the current page visit.
const sessionId = ref(null)

// ── Chat state ────────────────────────────────────────────────────────────────
const newMessage = ref('')
const typing = ref(false)
const chatContainer = ref(null)
const messages = ref([])
const humanHandoffLocked = ref(false)
let msgId = 0
let pollTimer = null
let lastPollAt = null

// ── Session persistence ───────────────────────────────────────────────────────
function saveSession() {
    if (chatStarted.value) {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({
            orderId: selectedOrder.value?.backendId ?? null,
            sessionId: sessionId.value,
        }))
    }
}

function mapHistoryToMessages(hist) {
    return hist.map(m => {
        if (m.intent === 'support_session_closed') {
            return {
                id: ++msgId, sender: 'closed',
                text: m.message || 'Your human support session has been closed.',
                html: '',
                time: nowTime(m.created_at),
            }
        }
        const sender = m.role === 'user'
            ? 'user'
            : ['agent_reply', 'support_message'].includes(m.intent) ? 'support' : 'bot'
        return {
            id: ++msgId, sender,
            intent: m.intent || null,
            text: m.message || m.text || '',
            html: sender === 'user' ? '' : formatBotText(m.message || m.text || ''),
            time: nowTime(m.created_at),
        }
    })
}

async function restoreSession() {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return false
    try {
        const saved = JSON.parse(raw)
        // saved.orderId may be null (general chat) or a UUID (order-linked chat)
        if (saved === null || typeof saved !== 'object') return false

        if (saved.orderId) {
            if (store.orders.length === 0) {
                loadingOrders.value = true
                try { await store.fetchOrders() } finally { loadingOrders.value = false }
            }
            const order = store.orders.find(o => o.backendId === saved.orderId)
            if (!order) { sessionStorage.removeItem(SESSION_KEY); return false }
            selectedOrder.value = order
        } else {
            selectedOrder.value = null
        }

        chatStarted.value = true

        if (!saved.sessionId) {
            messages.value = createWelcomeMessages()
            return true
        }

        sessionId.value = saved.sessionId
        try {
            const data = await fetchConversation(saved.sessionId)
            const hist = Array.isArray(data?.messages) ? data.messages : []
            if (hist.length === 0) {
                messages.value = createWelcomeMessages()
            } else {
                messages.value = mapHistoryToMessages(hist)
                lastPollAt = hist[hist.length - 1].created_at
            }
            if (data?.human_handoff_locked || hist.some(m => m.intent === 'support_session_closed')) {
                humanHandoffLocked.value = true
            }
            startPolling()
        } catch {
            messages.value = createWelcomeMessages()
        }
        await scrollToBottom()
        return true
    } catch {
        sessionStorage.removeItem(SESSION_KEY)
        return false
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function nowTime(dateLike) {
    const d = dateLike ? new Date(dateLike) : new Date()
    return isNaN(d.getTime())
        ? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatBotText(raw) {
    return String(raw || '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n/g, '<br>')
}

async function scrollToBottom() {
    await nextTick()
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

function createWelcomeMessages() {
    const intro = selectedOrder.value
        ? `Hello! I'm the Cargo-Core AI assistant. I'm here to help you with order <b>${selectedOrder.value.trackingCode || selectedOrder.value.id}</b>.`
        : "Hello! I'm the Cargo-Core AI assistant. How can I help you today?"
    return [
        {
            id: ++msgId, sender: 'bot',
            text: intro.replace(/<[^>]+>/g, ''),
            html: formatBotText(intro),
            time: nowTime(),
        },
        {
            id: ++msgId, sender: 'bot',
            text: 'You can ask about tracking, rescheduling, address changes, payments, or request human support.',
            html: formatBotText('You can ask about tracking, rescheduling, address changes, payments, or request human support.'),
            time: nowTime(),
        },
    ]
}

// ── Polling ───────────────────────────────────────────────────────────────────
async function pollMessages() {
    if (!sessionId.value || typing.value) return
    try {
        const data = await fetchConversation(sessionId.value)
        const hist = Array.isArray(data?.messages) ? data.messages : []
        if (!hist.length) return

        const newItems = lastPollAt ? hist.filter(m => m.created_at > lastPollAt) : []
        if (!newItems.length) return

        for (const m of newItems) {
            // Detect manager-closed session
            if (m.intent === 'support_session_closed') {
                humanHandoffLocked.value = true
                messages.value.push({
                    id: ++msgId, sender: 'closed',
                    text: m.message || 'Your human support session has been closed.',
                    html: '',
                    time: nowTime(m.created_at),
                })
                continue
            }

            // handover = bot escalation notice (grey bot bubble)
            // agent_reply / support_message = actual human agent replied (orange Human Support bubble)
            const sender = m.role === 'user'
                ? 'user'
                : ['agent_reply', 'support_message'].includes(m.intent) ? 'support' : 'bot'

            messages.value.push({
                id: ++msgId, sender,
                text: m.message || '',
                html: formatBotText(m.message || m.text || ''),
                time: nowTime(m.created_at),
            })
        }

        lastPollAt = hist[hist.length - 1].created_at
        await scrollToBottom()
    } catch { /* ignore transient poll errors */ }
}

function startPolling() {
    stopPolling()
    pollTimer = setInterval(pollMessages, 8_000)
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// ── Send message ──────────────────────────────────────────────────────────────
async function sendMessage() {
    const text = newMessage.value.trim()
    if (!text || typing.value) return

    messages.value.push({ id: ++msgId, sender: 'user', text, html: '', time: nowTime() })
    newMessage.value = ''
    typing.value = true
    await scrollToBottom()

    try {
        const response = await sendChat(text, sessionId.value, {
            context: 'support_chat',
            ...(selectedOrder.value ? { orderId: selectedOrder.value.backendId } : {}),
        })

        sessionId.value = response?.session_id || sessionId.value
        saveSession()

        if (!lastPollAt) {
            lastPollAt = new Date().toISOString()
            startPolling()
        } else {
            lastPollAt = new Date().toISOString()
        }

        // Check if human handoff got locked
        if (response?.human_handoff_locked) {
            humanHandoffLocked.value = true
        }

        // Detect session-closed intent
        if (response?.intent === 'support_session_closed') {
            humanHandoffLocked.value = true
            messages.value.push({
                id: ++msgId, sender: 'closed',
                text: response.message || 'Your human support session has been closed.',
                html: '',
                time: nowTime(),
            })
        } else if (response?.intent === 'agent_waiting') {
            // Human agent has taken over — don't render an AI bubble, just a quiet status pill
            messages.value.push({
                id: ++msgId, sender: 'status',
                text: response.message || 'Your message has been sent to the support agent.',
                html: '',
                time: nowTime(),
            })
        } else {
            // handover = bot saying "connecting you..." → grey bot bubble
            // agent_reply / support_message = actual human agent → orange Human Support bubble
            const sender = ['agent_reply', 'support_message'].includes(response?.intent) ? 'support' : 'bot'
            const msgText = response?.message || 'How can I help you?'
            messages.value.push({
                id: ++msgId, sender,
                intent: response?.intent || null,
                text: msgText,
                html: formatBotText(msgText),
                time: nowTime(),
            })
        }
    } catch (error) {
        messages.value.push({
            id: ++msgId, sender: 'bot',
            text: error instanceof Error ? error.message : 'Support is temporarily unavailable. Please try again.',
            html: formatBotText(error instanceof Error ? error.message : 'Support is temporarily unavailable. Please try again.'),
            time: nowTime(),
        })
    } finally {
        typing.value = false
        await scrollToBottom()
    }
}

function sendQuickAction(message) {
    newMessage.value = message
    sendMessage()
}

// ── Reset ─────────────────────────────────────────────────────────────────────
function resetSession() {
    stopPolling()
    sessionStorage.removeItem(SESSION_KEY)
    selectedOrder.value = null
    chatStarted.value = false
    sessionId.value = null
    messages.value = []
    typing.value = false
    newMessage.value = ''
    humanHandoffLocked.value = false
    lastPollAt = null
}

// ── Styling helpers ───────────────────────────────────────────────────────────
function statusBadgeClass(status) {
    return {
        'in-transit': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
        dispatched: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300',
        pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300',
    }[status] || 'bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-300'
}

function statusTextClass(status) {
    return {
        'in-transit': 'text-blue-600 dark:text-blue-400',
        dispatched: 'text-indigo-600 dark:text-indigo-400',
        pending: 'text-yellow-600 dark:text-yellow-400',
    }[status] || 'text-gray-500'
}

// ── Quick actions ─────────────────────────────────────────────────────────────
const quickActions = [
    { label: 'Track my order', icon: 'gps_fixed', color: 'text-green-500', message: 'Where is my order right now?' },
    { label: 'Check ETA', icon: 'schedule', color: 'text-blue-500', message: 'What is the ETA for my order?' },
    { label: 'Download receipt', icon: 'receipt', color: 'text-purple-500', message: 'Can I get a receipt for this order?' },
    { label: 'Not satisfied? Talk to a human', icon: 'support_agent', color: 'text-orange-500', message: 'I am not satisfied. I need to talk to a human support agent.' },
]

const serviceMods = [
    { label: 'Change Address', icon: 'edit_location', color: 'text-amber-500', message: 'I need to correct my delivery address.' },
    { label: 'Reschedule Move', icon: 'event', color: 'text-blue-500', message: 'I want to reschedule my move.' },
    { label: 'Add Extra Helper', icon: 'person_add', color: 'text-green-500', message: 'I need to add 1 more helper to my move.' },
]

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
    const restored = await restoreSession()
    if (!restored) loadOrders()
})

onUnmounted(() => {
    stopPolling()
    // sessionStorage is intentionally kept so refresh restores the session.
    // User must click "New Chat" to fully reset.
})
</script>
