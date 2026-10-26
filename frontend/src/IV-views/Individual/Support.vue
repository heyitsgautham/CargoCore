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
            <OrderPicker />
        </div>

        <!-- ── STEP 2: Chat Interface ──────────────────────────────────────── -->
        <div v-else-if="chatStarted" class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Chat Panel -->
            <SupportChatPanel />

            <!-- Side panel -->
            <SupportSidePanel />
        </div>
    </div>
</template>

<script setup>
import OrderPicker from './support/OrderPicker.vue'
import SupportChatPanel from './support/SupportChatPanel.vue'
import SupportSidePanel from './support/SupportSidePanel.vue'
import { individualSupportPageKey } from './support/individualSupportPageContext'
import { computed, nextTick, onMounted, onUnmounted, ref, provide } from 'vue'
import { sendChat, fetchConversation } from '@/utils/aiApi'
import { formatChatText } from '@/utils/html'
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
            html: sender === 'user' ? '' : formatChatText(m.message || m.text || ''),
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
            html: formatChatText(intro),
            time: nowTime(),
        },
        {
            id: ++msgId, sender: 'bot',
            text: 'You can ask about tracking, rescheduling, address changes, payments, or request human support.',
            html: formatChatText('You can ask about tracking, rescheduling, address changes, payments, or request human support.'),
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
                html: formatChatText(m.message || m.text || ''),
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
                html: formatChatText(msgText),
                time: nowTime(),
            })
        }
    } catch (error) {
        messages.value.push({
            id: ++msgId, sender: 'bot',
            text: error instanceof Error ? error.message : 'Support is temporarily unavailable. Please try again.',
            html: formatChatText(error instanceof Error ? error.message : 'Support is temporarily unavailable. Please try again.'),
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

provide(individualSupportPageKey, {
    chatContainer,
    humanHandoffLocked,
    loadingOrders,
    messages,
    newMessage,
    quickActions,
    resetSession,
    selectOrder,
    selectableOrders,
    selectedOrder,
    sendMessage,
    sendQuickAction,
    serviceMods,
    startWithoutOrder,
    statusBadgeClass,
    statusTextClass,
    typing,
})
</script>
