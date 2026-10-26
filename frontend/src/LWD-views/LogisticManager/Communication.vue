<template>
    <div class="h-[calc(100vh-8rem)] flex gap-6">
        <!-- Conversation & Escalation Sidebar -->
        <ConversationSidebar />

        <!-- Active Chat / Ticket Area -->
        <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
            <template v-if="activeTab === 'chats' && activeChat">
                <ActiveChatPanel />
            </template>

            <!-- Escalation Detail View -->
            <template v-else-if="activeTab === 'escalations' && activeTicket">
                <EscalationDetail />
            </template>
            <div v-else class="flex-1 flex items-center justify-center text-gray-400">
                Select an item from the sidebar to view details.
            </div>
        </div>

        <!-- Profile Modal -->
        <ProfileModal />

        <!-- Delete Modal -->
        <DeleteChatModal />

        <!-- Broadcast Modal -->
        <BroadcastModal />
    </div>
</template>

<script setup>
import ConversationSidebar from './communication/ConversationSidebar.vue'
import ActiveChatPanel from './communication/ActiveChatPanel.vue'
import EscalationDetail from './communication/EscalationDetail.vue'
import ProfileModal from './communication/ProfileModal.vue'
import DeleteChatModal from './communication/DeleteChatModal.vue'
import BroadcastModal from './communication/BroadcastModal.vue'
import { communicationPageKey } from './communication/communicationPageContext'
import { ref, computed, nextTick, watch, onMounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import { storeToRefs } from 'pinia'

const store = useLogisticStore()
const authStore = useAuthStore()
const { filteredChats, filteredEscalations, escalations } = storeToRefs(store)

onMounted(() => {
    store.refresh().catch(() => {})
})

// Strip legacy "LM Driver: " prefix (for any old threads still on the backend)
function chatDisplayName(name) {
    if (!name) return ''
    return String(name).startsWith('LM Driver: ') ? String(name).slice('LM Driver: '.length) : String(name)
}

const activeTab = ref('chats')
const activeChatId = ref(null)
const activeTicketId = ref(null)
const searchQuery = ref('')
const messageInput = ref('')
const chatHistoryContainer = ref(null)
const ticketActionPending = ref(false)

// New Chat contact picker
const isNewChatOpen = ref(false)
const contactSearchQuery = ref('')
const newChatLoading = ref(false)

const filteredContactDrivers = computed(() => {
    const q = contactSearchQuery.value.toLowerCase()
    return store.drivers.filter((d) => !q || d.name?.toLowerCase().includes(q))
})

const filteredContactWMs = computed(() => {
    const q = contactSearchQuery.value.toLowerCase()
    return store.warehouseManagerUsers.filter((u) => !q || u.name?.toLowerCase().includes(q))
})

const startChatWith = async (contact, type) => {
    isNewChatOpen.value = false
    contactSearchQuery.value = ''
    newChatLoading.value = true
    try {
        let thread
        if (type === 'driver') {
            thread = await store.ensureManagerDriverThread(contact)
        } else {
            // For WMs find or create a thread by name
            const existing = store.chats.find((c) => c.name === contact.name)
            if (existing) {
                thread = existing
            } else {
                thread = await store.createChatThread(contact.name, contact.mobile || null, contact.hubId || null)
            }
        }
        activeTab.value = 'chats'
        activeChatId.value = thread.id
        await nextTick()
        scrollToBottom()
    } catch (e) {
        console.warn('[Communication] startChatWith failed:', e)
    } finally {
        newChatLoading.value = false
    }
}
const isMenuOpen = ref(false)
const menuButtonRef = ref(null)
const menuPosition = ref({ top: 0, right: 0 })

const toggleMenu = () => {
    if (!isMenuOpen.value && menuButtonRef.value) {
        const rect = menuButtonRef.value.getBoundingClientRect()
        menuPosition.value = {
            top: rect.bottom + 8,
            right: window.innerWidth - rect.right
        }
    }
    isMenuOpen.value = !isMenuOpen.value
}

const isProfileModalOpen = ref(false)
const isDeleteModalOpen = ref(false)
const isBroadcastModalOpen = ref(false)

const broadcastForm = ref({
    audience: 'all',
    type: 'info',
    message: ''
})

const activeChat = computed(() => {
    return activeChatId.value != null ? (filteredChats.value.find(c => c.id === activeChatId.value) ?? null) : null
})

const activeChatDriver = computed(() => {
    if (!activeChat.value) return null
    const name = chatDisplayName(activeChat.value.name)
    return store.drivers.find(d => d.name === name) || null
})

const activeTicket = computed(() => {
    return activeTicketId.value != null ? (filteredEscalations.value?.find(t => t.id === activeTicketId.value) ?? null) : null
})

const displayChats = computed(() => {
    if (activeTab.value !== 'chats') return []
    if (!searchQuery.value) return filteredChats.value
    return filteredChats.value.filter(c => c.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
})

const displayEscalations = computed(() => {
    if (activeTab.value !== 'escalations') return []
    if (!searchQuery.value) return filteredEscalations.value || []

    const query = searchQuery.value.toLowerCase()
    return (filteredEscalations.value || []).filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.from.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query)
    )
})

const scrollToBottom = async () => {
    await nextTick()
    if (chatHistoryContainer.value) {
        chatHistoryContainer.value.scrollTop = chatHistoryContainer.value.scrollHeight
    }
}

const sendMessage = async () => {
    const text = messageInput.value.trim()
    if (!text || !activeChat.value) return

    // Optimistic update for instant UI feedback
    activeChat.value.messages.push({
        id: Date.now(),
        text: text,
        sender: 'me',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    activeChat.value.lastMessage = text
    activeChat.value.time = 'Just now'
    messageInput.value = ''
    scrollToBottom()

    // Persist to backend
    try {
        await store.sendChatMessage(activeChat.value.id, text)
    } catch (e) {
        console.warn('[Communication] sendChatMessage failed:', e)
    }
}

// Watch active chat to scroll on change
watch(activeChatId, () => {
    scrollToBottom()
})

const handleViewProfile = () => {
    isMenuOpen.value = false
    isProfileModalOpen.value = true
}

const handleMuteChat = async () => {
    isMenuOpen.value = false
    if (activeChat.value) {
        const newMuted = !activeChat.value.muted
        activeChat.value.muted = newMuted // optimistic
        try {
            await store.muteChatThread(activeChat.value.id, newMuted)
        } catch (e) {
            console.warn('[Communication] muteChatThread failed:', e)
        }
    }
}

const handleDeleteChat = () => {
    isMenuOpen.value = false
    isDeleteModalOpen.value = true
}

const confirmDeleteChat = async () => {
    if (activeChat.value) {
        const deletedId = activeChat.value.id
        try {
            await store.deleteChatThread(deletedId)
        } catch (e) {
            console.warn('[Communication] deleteChatThread failed:', e)
            const idx = store.chats.findIndex(c => c.id === deletedId)
            if (idx !== -1) store.chats.splice(idx, 1)
        }
        activeChatId.value = store.chats.length > 0 ? store.chats[0].id : null
    }
    isDeleteModalOpen.value = false
}

import { resolveEscalationCenter } from '@/utils/aiApi'

function extractRestockRequestId(ticket) {
    const details = String(ticket?.actionDetails || '')
    const match = details.match(/\[ref:([0-9a-fA-F-]{36})\]/)
    return match?.[1] || null
}

function isRestockEscalation(ticket) {
    return Boolean(extractRestockRequestId(ticket)) && /restock/i.test(String(ticket?.title || ''))
}

async function resolveRestockEscalation(ticket, ticketStatus) {
    const requestId = extractRestockRequestId(ticket)
    if (!requestId) throw new Error('Restock request reference not found')

    const response = await fetch(apiUrl(`api/v1/inventory/restock-requests/${requestId}/status`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: ticketStatus === 'Approved' ? 'APPROVED' : 'REJECTED',
            manager_notes: ticketStatus === 'Approved'
                ? 'Approved by Logistics Manager via Communication Center'
                : 'Rejected by Logistics Manager via Communication Center',
            funding_source: 'APP_REVENUE',
        }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        const detail = String(error.detail || '')
        if (response.status === 400 && /already processed/i.test(detail)) {
            await resolveGenericLogisticsEscalation(ticket, 'Resolved')
            return
        }
        throw new Error(detail || 'Failed to update restock request')
    }
}

async function resolveGenericLogisticsEscalation(ticket, ticketStatus) {
    const response = await fetch(apiUrl(`api/v1/logistics/escalations/${ticket.id}`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: ticketStatus === 'Approved'
                ? 'APPROVED'
                : ticketStatus === 'Denied'
                    ? 'REJECTED'
                    : 'RESOLVED',
        }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Failed to update escalation')
    }
}

const resolveTicket = async (ticketStatus) => {
    const ticketId = activeTicketId.value
    const ticket = activeTicket.value
    if (!ticketId || !ticket || ticketActionPending.value) return

    ticketActionPending.value = true
    try {
        if (isRestockEscalation(ticket)) {
            await resolveRestockEscalation(ticket, ticketStatus)
        } else if (String(ticket.id).includes('-')) {
            await resolveGenericLogisticsEscalation(ticket, ticketStatus)
        } else {
            await resolveEscalationCenter(ticketId)
        }

        const remaining = (escalations.value || []).filter(t => t.id !== ticketId)
        escalations.value = remaining
        activeTicketId.value = remaining.length > 0 ? remaining[0].id : null
        store.refresh().catch(() => {})
    } catch (e) {
        console.error('Failed to resolve ticket:', e)
    } finally {
        ticketActionPending.value = false
    }
}

const broadcastSuccess = ref(false)
const broadcastError = ref(false)
const sendBroadcast = async () => {
    const { audience, type, message } = broadcastForm.value
    if (!message.trim()) return
    isBroadcastModalOpen.value = false
    try {
        await store.sendBroadcast({ audience, type, message })
        broadcastSuccess.value = true
        setTimeout(() => { broadcastSuccess.value = false }, 4000)

        const titleMap = { info: 'System Broadcast', warning: '⚠️ System Warning', emergency: '🚨 Emergency Alert' }
        const typeMap = { info: 'info', warning: 'warning', emergency: 'alert' }
        store.notifications.unshift({
            id: Date.now().toString(),
            title: `[Broadcast Sent] ${titleMap[type] ?? 'System Broadcast'}`,
            message: `Broadcast sent: ${message}`,
            time: new Date().toISOString(),
            read: false,
            type: typeMap[type] ?? 'info',
        })
    } catch (e) {
        broadcastError.value = true
        setTimeout(() => { broadcastError.value = false }, 4000)
        console.warn('[Communication] sendBroadcast failed:', e)
    }
    broadcastForm.value.message = ''
}

provide(communicationPageKey, {
    activeChat,
    activeChatDriver,
    activeChatId,
    activeTab,
    activeTicket,
    activeTicketId,
    broadcastForm,
    chatDisplayName,
    chatHistoryContainer,
    confirmDeleteChat,
    contactSearchQuery,
    displayChats,
    displayEscalations,
    filteredContactDrivers,
    filteredContactWMs,
    filteredEscalations,
    handleDeleteChat,
    handleMuteChat,
    handleViewProfile,
    isBroadcastModalOpen,
    isDeleteModalOpen,
    isMenuOpen,
    isNewChatOpen,
    isProfileModalOpen,
    menuButtonRef,
    menuPosition,
    messageInput,
    resolveTicket,
    searchQuery,
    sendBroadcast,
    sendMessage,
    startChatWith,
    ticketActionPending,
    toggleMenu,
})
</script>
