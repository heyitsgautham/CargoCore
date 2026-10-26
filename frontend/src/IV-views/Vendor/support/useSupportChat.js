// The vendor's AI support chat: pick a shipment or none, keep the session across reloads,
// send messages, poll for agent replies and lock input once a human takes over.
import { ref, computed, nextTick } from 'vue'
import { sendChat, fetchConversation } from '@/utils/aiApi'
import { escapeHtml, formatChatText } from '@/utils/html'

export function useSupportChat({ SESSION_KEY, activeTab, store }) {
    // ── AI Chat ───────────────────────────────────────────────────────────────────
    const chatMessages = ref([])
    const userInput = ref('')
    const isTyping = ref(false)
    const chatContainer = ref(null)
    const sessionId = ref(null)
    const unreadCount = ref(0)
    const humanHandoffLocked = ref(false)
    const selectedShipment = ref(null)
    const chatStarted = ref(false)
    let lastLoadedAt = null
    let pollTimer = null

    // Shipments eligible for support chat (not delivered / cancelled)
    const selectableShipments = computed(() =>
        store.shipments.filter(s => !['delivered', 'cancelled'].includes(s.statusKey))
    )

    function shipmentStatusBadge(statusKey) {
        return {
            pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300',
            warehouse: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300',
            transit: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
            delivery: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300',
        }[statusKey] || 'bg-gray-100 text-gray-600 dark:bg-white/10 dark:text-gray-300'
    }

    function saveSession() {
        if (chatStarted.value) {
            sessionStorage.setItem(SESSION_KEY, JSON.stringify({
                shipmentId: selectedShipment.value?.backendId ?? null,
                sessionId: sessionId.value,
            }))
        }
    }

    async function restoreSession() {
        const raw = sessionStorage.getItem(SESSION_KEY)
        if (!raw) return false
        try {
            const saved = JSON.parse(raw)
            if (saved === null || typeof saved !== 'object') return false

            if (saved.shipmentId) {
                if (!store.shipments.length) {
                    try { await store.fetchShipments() } catch { /* ignore */ }
                }
                const shipment = store.shipments.find(s => s.backendId === saved.shipmentId)
                if (!shipment) { sessionStorage.removeItem(SESSION_KEY); return false }
                selectedShipment.value = shipment
            } else {
                selectedShipment.value = null
            }

            chatStarted.value = true

            if (!saved.sessionId) return true

            sessionId.value = saved.sessionId
            try {
                const data = await fetchConversation(saved.sessionId)
                const hist = Array.isArray(data?.messages) ? data.messages : []
                if (hist.length > 0) {
                    chatMessages.value = hist.map((m, i) => mapServerMsg(m, i))
                    lastLoadedAt = hist[hist.length - 1].created_at
                }
                if (data?.human_handoff_locked || hist.some(m => m.intent === 'support_session_closed')) {
                    humanHandoffLocked.value = true
                }
                startPolling()
            } catch { /* ignore — start fresh */ }
            await scrollToBottom()
            return true
        } catch {
            sessionStorage.removeItem(SESSION_KEY)
            return false
        }
    }

    function selectShipment(shipment) {
        selectedShipment.value = shipment
        chatStarted.value = true
        sessionId.value = null
        chatMessages.value = []
        humanHandoffLocked.value = false
        lastLoadedAt = null
        saveSession()
    }

    function startWithoutShipment() {
        selectedShipment.value = null
        chatStarted.value = true
        sessionId.value = null
        chatMessages.value = []
        humanHandoffLocked.value = false
        lastLoadedAt = null
        saveSession()
    }

    const quickChips = [
        'Show my pending shipments',
        'Do I have overdue invoices?',
        'What is my wallet balance?',
        'Talk to a human agent',
    ]

    const SUPPORT_PREFIX_RE = /^\[Support — ([^\]]+)\]\s*/

    function nowTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    function mapServerMsg(m, idx) {
        // Manager-closed session message
        if (m.intent === 'support_session_closed') {
            humanHandoffLocked.value = true
            return {
                id: `h-${m.created_at}-${idx}`,
                role: 'closed',
                text: formatChatText(m.message || 'Human support session has been closed.'),
                time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                createdAt: m.created_at,
            }
        }
        // agent_reply / support_message = actual human agent replied → orange Human Support bubble
        // handover = bot escalation notice → regular AI bubble
        if (['support_message', 'agent_reply'].includes(m.intent)) {
            return {
                id: `h-${m.created_at}-${idx}`,
                role: 'support',
                intent: m.intent,
                text: formatChatText((m.message || '').replace(SUPPORT_PREFIX_RE, '')),
                time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                createdAt: m.created_at,
            }
        }
        return {
            id: `h-${m.created_at}-${idx}`,
            role: m.role === 'user' ? 'user' : 'ai',
            intent: m.intent || null,
            text: formatChatText(m.message || ''),
            time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            createdAt: m.created_at,
        }
    }

    const scrollToBottom = async () => {
        await nextTick()
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }

    async function pollHistory() {
        if (!sessionId.value || isTyping.value) return
        try {
            const { messages: hist } = await fetchConversation(sessionId.value)
            if (!hist?.length) return
            const newHist = lastLoadedAt ? hist.filter(m => m.created_at > lastLoadedAt) : []
            if (!newHist.length) return
            const offset = hist.length - newHist.length
            const newMsgs = newHist.map((m, i) => mapServerMsg(m, offset + i))
            chatMessages.value.push(...newMsgs)
            lastLoadedAt = hist[hist.length - 1].created_at
            const supportCount = newMsgs.filter(m => m.role === 'support').length
            if (activeTab.value !== 'chat' && supportCount > 0) unreadCount.value += supportCount
            if (activeTab.value === 'chat') await scrollToBottom()
        } catch { /* ignore transient poll errors */ }
    }

    function startPolling() {
        if (pollTimer) clearInterval(pollTimer)
        pollTimer = setInterval(pollHistory, 8_000)
    }

    function stopPolling() {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    }

    function switchToChat() {
        activeTab.value = 'chat'
        unreadCount.value = 0
    }

    async function handleSend() {
        const text = userInput.value.trim()
        if (!text || isTyping.value) return
        userInput.value = ''
        chatMessages.value.push({ id: `u-${Date.now()}`, role: 'user', text: formatChatText(text), time: nowTime() })
        isTyping.value = true
        await scrollToBottom()
        try {
            const res = await sendChat(text, sessionId.value, {
                context: 'support_chat',
                ...(selectedShipment.value ? { orderId: selectedShipment.value.backendId } : {}),
            })
            if (res.session_id) {
                sessionId.value = res.session_id
                saveSession()
                if (!lastLoadedAt) {
                    lastLoadedAt = new Date().toISOString()
                    startPolling()
                } else {
                    lastLoadedAt = new Date().toISOString()
                }
            }

            if (res.human_handoff_locked) humanHandoffLocked.value = true

            if (res.intent === 'support_session_closed') {
                humanHandoffLocked.value = true
                chatMessages.value.push({
                    id: `closed-${Date.now()}`,
                    role: 'closed',
                    text: formatChatText(res.message || 'Human support session has been closed.'),
                    time: nowTime(),
                })
            } else if (res.intent === 'agent_waiting') {
                // Human agent has taken over — show a quiet status pill, not an AI bubble
                chatMessages.value.push({
                    id: `status-${Date.now()}`,
                    role: 'status',
                    text: formatChatText(res.message || 'Your message has been sent to the support agent.'),
                    time: nowTime(),
                })
            } else {
                // handover = bot escalation notice → regular AI bubble
                // agent_reply / support_message = actual human agent → orange Human Support bubble
                const msgText = res.message || "I'm here to help!"
                chatMessages.value.push({
                    id: `ai-${Date.now()}`,
                    role: ['agent_reply', 'support_message'].includes(res.intent) ? 'support' : 'ai',
                    intent: res.intent || null,
                    text: formatChatText(msgText),
                    time: nowTime(),
                })
            }
        } catch (err) {
            chatMessages.value.push({
                id: `err-${Date.now()}`,
                role: 'ai',
                text: `<span class="text-red-400">⚠ ${escapeHtml(err.message || 'Something went wrong. Please try again.')}</span>`,
                time: nowTime(),
            })
        } finally {
            isTyping.value = false
            await scrollToBottom()
        }
    }

    function sendChip(chip) {
        userInput.value = chip
        handleSend()
    }

    function startNewChat() {
        stopPolling()
        sessionStorage.removeItem(SESSION_KEY)
        chatMessages.value = []
        sessionId.value = null
        lastLoadedAt = null
        unreadCount.value = 0
        humanHandoffLocked.value = false
        selectedShipment.value = null
        chatStarted.value = false
    }

    /** Start a fresh chat about one shipment, dropping any saved session. */
    function startChatForShipment(shipment) {
        sessionStorage.removeItem(SESSION_KEY)
        selectedShipment.value = shipment || null
        chatStarted.value = true
        sessionId.value = null
        chatMessages.value = []
        humanHandoffLocked.value = false
        lastLoadedAt = null
        activeTab.value = 'chat'
    }

    return {
        chatMessages,
        userInput,
        isTyping,
        chatContainer,
        unreadCount,
        humanHandoffLocked,
        selectedShipment,
        chatStarted,
        selectableShipments,
        shipmentStatusBadge,
        restoreSession,
        selectShipment,
        startWithoutShipment,
        quickChips,
        stopPolling,
        switchToChat,
        handleSend,
        sendChip,
        startNewChat,
        startChatForShipment,
    }
}
