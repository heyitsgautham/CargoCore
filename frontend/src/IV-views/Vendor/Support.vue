<template>
    <div class="min-h-[calc(100vh-8rem)] flex flex-col gap-6">

        <!-- Top Section -->
        <div class="flex flex-col md:flex-row gap-6 flex-1 min-h-[500px]">

            <SupportSidebar />

            <!-- MAIN CONTENT -->
            <div class="flex-1 flex flex-col min-w-0 glass-panel rounded-xl overflow-hidden">

                <!-- Tabs -->
                <div class="flex border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 shrink-0">
                    <button @click="activeTab = 'tickets'"
                        class="flex items-center gap-2 px-5 py-3 text-sm font-bold transition-colors border-b-2 -mb-px"
                        :class="activeTab === 'tickets'
                            ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-transparent'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                        <span class="material-symbols-outlined text-[16px]">confirmation_number</span>
                        Support Tickets
                        <span class="ml-1 text-[10px] bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400 px-1.5 py-0.5 rounded-full font-bold">{{ store.tickets.length }}</span>
                    </button>
                    <button @click="switchToChat"
                        class="flex items-center gap-2 px-5 py-3 text-sm font-bold transition-colors border-b-2 -mb-px"
                        :class="activeTab === 'chat'
                            ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-transparent'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                        <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                        AI Chat Support
                        <span v-if="unreadCount > 0"
                            class="ml-1 text-[10px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full font-bold animate-pulse">
                            {{ unreadCount }}
                        </span>
                    </button>
                </div>

                <TicketsTab />

                <!-- ── AI CHAT TAB ── -->
                <div v-if="activeTab === 'chat'" class="flex-1 flex flex-col overflow-hidden">

                    <!-- Step 1 shows until a chat starts, step 2 after -->
                    <ShipmentPicker v-if="!chatStarted" />
                    <SupportChat v-else />
                </div>
            </div>
        </div>

        <SupportFaq />

        <CreateTicketModal />

        <TicketDetailModal />
    </div>
</template>

<script setup>
import SupportSidebar from './support/SupportSidebar.vue'
import TicketsTab from './support/TicketsTab.vue'
import ShipmentPicker from './support/ShipmentPicker.vue'
import SupportChat from './support/SupportChat.vue'
import SupportFaq from './support/SupportFaq.vue'
import CreateTicketModal from './support/CreateTicketModal.vue'
import TicketDetailModal from './support/TicketDetailModal.vue'
import { vendorSupportPageKey } from './support/vendorSupportPageContext'
import { ref, computed, onMounted, onUnmounted, nextTick, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useVendorStore } from '@/stores/vendorStore'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { sendChat, fetchConversation } from '@/utils/aiApi'

ChartJS.register(ArcElement, Tooltip, Legend)

const store = useVendorStore()
const route = useRoute()
const SESSION_KEY = 'support_session_vendor'

// ── Tabs ──────────────────────────────────────────────────────────────────────
const activeTab = ref('tickets')

// ── Tickets ───────────────────────────────────────────────────────────────────
const statusFilter = ref('all')
const showCreateModal = ref(false)
const detailTicket = ref(null)
const replyText = ref('')
const openFaq = ref(null)
const loadingTickets = ref(false)

const faqList = [
    { q: 'How to bulk upload shipments?', a: 'Navigate to the "Bulk Upload" page. Download our CSV template, fill it out with your shipment details, and upload it back. The grid will auto-populate for review before final submission.' },
    { q: 'Where do I find my invoice & billing cycles?', a: 'Invoices are generated bi-weekly. You can access them under the Invoices section in your portal or request priority copies via Support.' },
    { q: 'Is there an API Integration guide available?', a: 'Yes. Enterprise partners have access to our RESTful API. Please contact priority support to receive your API keys and the latest swagger documentation link.' },
    { q: 'What is the damage claim process?', a: 'Open the specific shipment from your Tracking dashboard and use the "Report Issue" action button. Attach photos for faster resolution.' },
    { q: 'Can I set up recurring scheduled shipments?', a: 'Absolutely. Go to "Recurring Orders" to template a route and define a frequency schedule (e.g., Every Monday at 9AM).' },
]

const newTicket = ref({ subject: '', priority: 'Medium', shipmentId: '', message: '' })

const filteredTickets = computed(() => {
    if (statusFilter.value === 'all') return store.tickets
    return store.tickets.filter(t => t.status === statusFilter.value)
})

const openCount = computed(() => store.tickets.filter(t => t.status === 'Open').length)
const inProgressCount = computed(() => store.tickets.filter(t => t.status === 'In Progress').length)
const resolvedCount = computed(() => store.tickets.filter(t => t.status === 'Resolved').length)

const chartData = computed(() => ({
    labels: ['Open', 'In Progress', 'Resolved'],
    datasets: [{
        data: [openCount.value, inProgressCount.value, resolvedCount.value],
        backgroundColor: ['#EAB308', '#3B82F6', '#22C55E'],
        borderWidth: 0,
        hoverOffset: 4,
    }],
}))

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 12,
            titleFont: { size: 13, family: "'Inter', sans-serif" },
            bodyFont: { size: 12, family: "'Inter', sans-serif" },
            boxPadding: 6,
        },
    },
}

const toggleFaq = (idx) => { openFaq.value = openFaq.value === idx ? null : idx }

function priorityClass(p) {
    return { High: 'text-red-500', Medium: 'text-yellow-500', Low: 'text-green-500' }[p] || 'text-gray-500'
}

function priorityBorderClass(p) {
    return {
        High: 'border-red-500 bg-red-500/10 text-red-500',
        Medium: 'border-yellow-500 bg-yellow-500/10 text-yellow-500',
        Low: 'border-green-500 bg-green-500/10 text-green-500',
    }[p]
}

function ticketStatusClass(s) {
    return {
        Open: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
        'In Progress': 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
        Resolved: 'bg-green-500/20 text-green-600 dark:text-green-400',
    }[s] || 'bg-gray-500/20 text-gray-500'
}

function openCreateModal() {
    newTicket.value = { subject: '', priority: 'Medium', shipmentId: '', message: '' }
    showCreateModal.value = true
}

async function submitTicket() {
    if (!newTicket.value.subject || !newTicket.value.message) return
    await store.addTicket({
        subject: newTicket.value.subject,
        priority: newTicket.value.priority,
        shipmentId: newTicket.value.shipmentId || null,
        message: newTicket.value.message,
    })
    showCreateModal.value = false
    showToast('Ticket created successfully')
}

function openTicketDetail(t) {
    detailTicket.value = t
    replyText.value = ''
}

async function sendReply() {
    if (!replyText.value.trim() || !detailTicket.value) return
    const ticketId = detailTicket.value.id
    await store.replyTicket(ticketId, replyText.value.trim())
    replyText.value = ''
    const updated = store.tickets.find(t => t.id === ticketId)
    if (updated) detailTicket.value = updated
}

async function markResolved(t) {
    await store.resolveTicket(t.id)
    showToast(`Ticket ${t.id} resolved`)
}

function showToast(msg) {
    const el = document.createElement('div')
    el.className = 'fixed right-4 bottom-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    el.textContent = msg
    document.body.appendChild(el)
    setTimeout(() => el.remove(), 3000)
}

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

function formatText(raw) {
    return String(raw)
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n/g, '<br>')
}

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
            text: formatText(m.message || 'Human support session has been closed.'),
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
            text: formatText((m.message || '').replace(SUPPORT_PREFIX_RE, '')),
            time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            createdAt: m.created_at,
        }
    }
    return {
        id: `h-${m.created_at}-${idx}`,
        role: m.role === 'user' ? 'user' : 'ai',
        intent: m.intent || null,
        text: formatText(m.message || ''),
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
    chatMessages.value.push({ id: `u-${Date.now()}`, role: 'user', text, time: nowTime() })
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
                text: formatText(res.message || 'Human support session has been closed.'),
                time: nowTime(),
            })
        } else if (res.intent === 'agent_waiting') {
            // Human agent has taken over — show a quiet status pill, not an AI bubble
            chatMessages.value.push({
                id: `status-${Date.now()}`,
                role: 'status',
                text: res.message || 'Your message has been sent to the support agent.',
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
                text: formatText(msgText),
                time: nowTime(),
            })
        }
    } catch (err) {
        chatMessages.value.push({
            id: `err-${Date.now()}`,
            role: 'ai',
            text: `<span class="text-red-400">⚠ ${err.message || 'Something went wrong. Please try again.'}</span>`,
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

onMounted(async () => {
    loadingTickets.value = true
    try { await store.fetchTickets() } catch { /* ignore */ } finally { loadingTickets.value = false }

    // Ensure shipments are loaded for the chat picker
    if (!store.shipments.length) {
        try { await store.fetchShipments() } catch { /* ignore */ }
    }

    // ── Deep-link from Tracking "Need Help?" banner ──
    // Expects: ?tab=chat&shipmentId=<backendId or tracking code>
    const qTab = route.query.tab
    const qShipmentId = route.query.shipmentId

    if (qTab === 'chat' && qShipmentId) {
        // Find the shipment by backendId or tracking code
        const shipment = store.shipments.find(
            s => String(s.backendId) === String(qShipmentId) || s.id === String(qShipmentId)
        )
        // Clear any saved session so we start fresh for this order
        sessionStorage.removeItem(SESSION_KEY)
        selectedShipment.value = shipment || null
        chatStarted.value = true
        sessionId.value = null
        chatMessages.value = []
        humanHandoffLocked.value = false
        lastLoadedAt = null
        activeTab.value = 'chat'
        return  // skip generic session restore
    }

    // Restore any previous chat session (survives page refresh via sessionStorage)
    await restoreSession()
})

onUnmounted(() => {
    stopPolling()
    // sessionStorage is intentionally kept so refresh restores the session.
    // User must click the "+" / new-chat button to fully reset.
})

provide(vendorSupportPageKey, {
    activeTab,
    chartData,
    chartOptions,
    chatContainer,
    chatMessages,
    chatStarted,
    detailTicket,
    faqList,
    filteredTickets,
    handleSend,
    humanHandoffLocked,
    inProgressCount,
    isTyping,
    loadingTickets,
    markResolved,
    newTicket,
    openCount,
    openCreateModal,
    openFaq,
    openTicketDetail,
    priorityBorderClass,
    priorityClass,
    quickChips,
    replyText,
    resolvedCount,
    selectShipment,
    selectableShipments,
    selectedShipment,
    sendChip,
    sendReply,
    shipmentStatusBadge,
    showCreateModal,
    startNewChat,
    startWithoutShipment,
    statusFilter,
    store,
    submitTicket,
    ticketStatusClass,
    toggleFaq,
    userInput,
})
</script>
