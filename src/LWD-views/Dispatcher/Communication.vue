<template>
    <div class="h-[calc(100vh-8rem)] flex gap-6">
        <!-- Contact List Sidebar -->
        <div class="w-80 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <!-- Contact Type Tabs -->
                <div class="flex gap-1 mb-3">
                    <button v-for="tab in contactTabs" :key="tab.key" @click="contactType = tab.key"
                        :class="contactType === tab.key ? 'bg-primary text-black dark:text-black border-primary shadow-md' : 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10'"
                        class="flex-1 text-[10px] font-bold py-1.5 rounded border transition-colors">{{ tab.label }}</button>
                </div>
                <div class="relative">
                    <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-500">search</span>
                    <input type="text" v-model="searchQuery" placeholder="Find contact..."
                        class="w-full bg-white dark:bg-black/40 border-2 border-gray-300 dark:border-white/10 rounded-lg py-2 pl-10 pr-4 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50">
                </div>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar">
                <div v-for="contact in filteredContacts" :key="contact.id"
                    class="p-4 border-b border-gray-200 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors flex items-center gap-3"
                    :class="activeChat === contact.id ? 'bg-gray-50 dark:bg-white/5 border-l-2 border-l-primary' : ''"
                    @click="activeChat = contact.id">
                    <div class="relative">
                        <div v-if="contact.type === 'warehouse'"
                            class="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                            <span class="material-symbols-outlined text-blue-400 text-[18px]">warehouse</span>
                        </div>
                        <img v-else :src="contact.avatar" class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700">
                        <span class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border border-white dark:border-black"
                            :class="contact.online ? 'bg-green-500' : 'bg-gray-500'"></span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-center">
                            <div class="font-bold text-gray-900 dark:text-white text-sm truncate">{{ contact.name }}</div>
                            <span v-if="contact.unread" class="min-w-[16px] h-4 bg-primary rounded-full text-[9px] text-black font-bold flex items-center justify-center px-1">{{ contact.unread }}</span>
                        </div>
                        <div class="text-[10px] text-gray-500 truncate">{{ formatContactPreview(contact.lastMessage) }}</div>
                        <div class="text-[9px] mt-0.5 font-semibold px-1.5 py-0.5 rounded-full inline-block" :class="contact.type === 'warehouse' ? 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400'">
                            {{ contact.type === 'warehouse' ? 'Warehouse' : contact.role || 'Driver' }}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Active Chat Area -->
        <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-100 dark:bg-black/20">
                <div class="flex items-center gap-3">
                    <div v-if="activeContact?.type === 'warehouse'" class="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <span class="material-symbols-outlined text-blue-400 text-[18px]">warehouse</span>
                    </div>
                    <img v-else :src="activeContact?.avatar" class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700">
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ activeContact?.name || 'Select a contact' }}</div>
                        <div v-if="activeContact?.phone" class="text-[11px] text-gray-500 dark:text-gray-400">{{ activeContact.phone }}</div>
                        <div class="text-xs text-green-600 dark:text-green-400">{{ activeContact?.status || '' }}</div>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button @click="showRouteModal = true"
                        class="p-2 hover:bg-blue-100 dark:hover:bg-blue-500/20 rounded-full text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 transition-colors"
                        title="Push Route Update">
                        <span class="material-symbols-outlined">route</span>
                    </button>
                    <button @click="showUrgentModal = true"
                        class="p-2 hover:bg-red-100 dark:hover:bg-red-500/20 rounded-full text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 transition-colors"
                        title="Urgent Instruction">
                        <span class="material-symbols-outlined">priority_high</span>
                    </button>
                    <button @click="showLog = !showLog" class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                        title="Communication Log"><span class="material-symbols-outlined">history</span></button>
                </div>
            </div>

            <!-- Route Update / Urgent Instruction Banners -->
            <div v-if="routeUpdateSent" class="px-4 py-2 bg-blue-100 dark:bg-blue-500/10 border-b border-blue-500/20 flex items-center gap-2 text-xs text-blue-700 dark:text-blue-300">
                <span class="material-symbols-outlined text-[16px]">check_circle</span>
                Route update pushed to driver at {{ new Date().toLocaleTimeString() }}
            </div>
            <div v-if="urgentSent" class="px-4 py-2 bg-red-100 dark:bg-red-500/10 border-b border-red-500/20 flex items-center gap-2 text-xs text-red-700 dark:text-red-300">
                <span class="material-symbols-outlined text-[16px]">warning</span>
                Urgent instruction sent – awaiting acknowledgment
            </div>

            <div class="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 dark:bg-black/10" ref="chatAreaRef">
                <!-- Messages -->
                <div v-for="msg in renderedMessages" :key="msg.id" :class="isDispatcherMsg(msg) ? 'flex gap-3 flex-row-reverse' : 'flex gap-3'">
                    <template v-if="msg.type === 'system'">
                        <div class="w-full flex justify-center">
                            <div class="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-[10px] text-blue-400">
                                {{ msg.text }}
                            </div>
                        </div>
                    </template>
                    <template v-else-if="msg.action">
                        <div v-if="isDispatcherMsg(msg)" class="w-8 h-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center text-[10px] text-black font-bold">DISP</div>
                        <div v-else-if="activeContact?.type === 'warehouse'" class="w-8 h-8 rounded-full bg-blue-500/20 flex-shrink-0 flex items-center justify-center">
                            <span class="material-symbols-outlined text-blue-400 text-[14px]">warehouse</span>
                        </div>
                        <img v-else-if="!isDispatcherMsg(msg)" :src="activeContact?.avatar" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex-shrink-0">
                        <div class="max-w-[76%]">
                            <div class="rounded-2xl border p-4 shadow-sm"
                                :class="msg.action.kind === 'route'
                                    ? (isDispatcherMsg(msg)
                                        ? 'rounded-tr-none bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-400/20'
                                        : 'rounded-tl-none bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-400/20')
                                    : (isDispatcherMsg(msg)
                                        ? 'rounded-tr-none bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-400/20'
                                        : 'rounded-tl-none bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-400/20')">
                                <div class="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em]"
                                    :class="msg.action.kind === 'route' ? 'text-blue-700 dark:text-blue-300' : 'text-red-600 dark:text-red-300'">
                                    <span class="material-symbols-outlined text-[16px]">{{ msg.action.kind === 'route' ? 'route' : 'priority_high' }}</span>
                                    {{ msg.action.title }}
                                </div>
                                <div class="mt-2 whitespace-pre-line text-sm"
                                    :class="msg.action.kind === 'route' ? 'text-slate-700 dark:text-slate-100' : 'text-slate-700 dark:text-slate-100'">
                                    {{ msg.action.body }}
                                </div>
                            </div>
                            <div class="text-[9px] text-gray-500 dark:text-gray-600 mt-1" :class="isDispatcherMsg(msg) ? 'text-right' : ''">{{ msg.time }}</div>
                        </div>
                    </template>
                    <template v-else-if="isDispatcherMsg(msg)">
                        <div class="w-8 h-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center text-[10px] text-black font-bold">DISP</div>
                        <div class="max-w-[70%]">
                            <div class="bg-emerald-100 dark:bg-primary/20 border border-emerald-200 dark:border-primary/30 p-3 rounded-xl rounded-tr-none text-gray-900 dark:text-white text-sm break-words">{{ msg.text }}</div>
                            <div class="text-[9px] text-gray-500 dark:text-gray-600 mt-1 text-right">{{ msg.time }}</div>
                        </div>
                    </template>
                    <template v-else>
                        <div v-if="activeContact?.type === 'warehouse'" class="w-8 h-8 rounded-full bg-blue-500/20 flex-shrink-0 flex items-center justify-center">
                            <span class="material-symbols-outlined text-blue-400 text-[14px]">warehouse</span>
                        </div>
                        <img v-else :src="activeContact?.avatar" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex-shrink-0">
                        <div class="max-w-[70%]">
                            <div class="bg-gray-200 dark:bg-white/5 border border-gray-300 dark:border-white/10 p-3 rounded-xl rounded-tl-none text-gray-800 dark:text-gray-300 text-sm break-words">{{ msg.text }}</div>
                            <div class="text-[9px] text-gray-500 dark:text-gray-600 mt-1">{{ msg.time }}</div>
                        </div>
                    </template>
                </div>
            </div>

            <div class="p-4 bg-gray-100 dark:bg-black/20 border-t border-gray-200 dark:border-white/5">
                <div class="relative flex gap-2 items-stretch">
                    <input v-model="newMessage" type="text" :placeholder="'Message ' + (activeContact?.name || '...') + '...'"
                        class="flex-1 bg-white dark:bg-white/5 border-2 border-gray-300 dark:border-white/10 rounded-full py-3 pl-4 pr-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50"
                        @keyup.enter="sendMessage" :disabled="isSendingMsg">
                    <button @click="sendMessage" :disabled="!newMessage.trim() || isSendingMsg"
                        class="px-4 bg-primary rounded-full text-black hover:scale-105 transition-transform disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 flex-shrink-0 flex items-center justify-center">
                        <span class="material-symbols-outlined text-[20px]">{{ isSendingMsg ? 'hourglass_empty' : 'send' }}</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Communication Log Panel -->
        <div v-if="showLog" class="w-72 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Communication Log</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-600 mt-1">All interactions archived</div>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2">
                <div v-for="log in commLog" :key="log.id"
                    class="p-2 rounded-lg text-[10px] border border-gray-200 dark:border-white/5"
                    :class="log.type === 'urgent' ? 'bg-red-100 dark:bg-red-500/5 border-red-500/20 dark:border-red-500/10' : log.type === 'route' ? 'bg-blue-100 dark:bg-blue-500/5 border-blue-500/20 dark:border-blue-500/10' : 'bg-gray-50 dark:bg-white/5'">
                    <div class="flex justify-between">
                        <span class="font-bold" :class="log.type === 'urgent' ? 'text-red-600 dark:text-red-400' : log.type === 'route' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'">{{ log.action }}</span>
                        <span class="text-gray-600 dark:text-gray-400">{{ log.time }}</span>
                    </div>
                    <div class="text-gray-600 dark:text-gray-400 mt-0.5">{{ log.contact }} – {{ log.detail }}</div>
                </div>
            </div>
        </div>

        <!-- Route Update Modal -->
        <Teleport to="body">
        <div v-if="showRouteModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showRouteModal = false">
            <div class="w-full max-w-md m-4 rounded-3xl border border-slate-200/70 dark:border-white/10 bg-white/95 dark:bg-slate-950/95 shadow-[0_32px_80px_rgba(15,23,42,0.32)] dark:shadow-[0_32px_80px_rgba(0,0,0,0.5)] backdrop-blur-xl overflow-hidden">
                <div class="px-6 pt-6 pb-4 border-b border-slate-200/80 dark:border-white/10 bg-gradient-to-br from-blue-50 to-white dark:from-blue-500/10 dark:to-transparent">
                    <div class="inline-flex items-center gap-2 rounded-full border border-blue-200 dark:border-blue-400/20 bg-blue-100/80 dark:bg-blue-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-blue-700 dark:text-blue-300">
                        <span class="material-symbols-outlined text-[16px]">route</span>
                        Route Sync
                    </div>
                    <h3 class="mt-4 text-xl font-bold text-slate-900 dark:text-white">Push Route Update</h3>
                    <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">Send a route update to <span class="font-bold text-slate-900 dark:text-white">{{ activeContact?.name }}</span></p>
                </div>
                <div class="p-6">
                    <textarea v-model="routeUpdateMsg" rows="2" placeholder="Optional: Add route notes..."
                        class="mb-4 min-h-28 w-full resize-none rounded-2xl border border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-white/5 px-4 py-3 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-blue-400 dark:focus:border-blue-400/50 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-500/10"></textarea>
                    <div class="flex gap-3">
                        <button @click="confirmRouteUpdate" class="flex-1 rounded-2xl bg-blue-500 py-3 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition-colors hover:bg-blue-600">Push Update</button>
                        <button @click="showRouteModal = false" class="flex-1 rounded-2xl border border-slate-300 dark:border-white/10 bg-slate-100 py-3 text-sm text-slate-700 transition-colors hover:bg-slate-200 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
        </Teleport>

        <!-- Urgent Instruction Modal -->
        <Teleport to="body">
        <div v-if="showUrgentModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showUrgentModal = false">
            <div class="w-full max-w-md m-4 rounded-3xl border border-red-200/80 dark:border-red-500/20 bg-white/95 dark:bg-slate-950/95 shadow-[0_32px_80px_rgba(15,23,42,0.32)] dark:shadow-[0_32px_80px_rgba(0,0,0,0.5)] backdrop-blur-xl overflow-hidden">
                <div class="px-6 pt-6 pb-4 border-b border-red-200/80 dark:border-red-500/20 bg-gradient-to-br from-red-50 to-white dark:from-red-500/10 dark:to-transparent">
                    <div class="inline-flex items-center gap-2 rounded-full border border-red-200 dark:border-red-400/20 bg-red-100/80 dark:bg-red-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-red-700 dark:text-red-300">
                        <span class="material-symbols-outlined text-[16px]">priority_high</span>
                        High Priority
                    </div>
                    <h3 class="mt-4 text-xl font-bold text-red-600 dark:text-red-400">Send Urgent Instruction</h3>
                    <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">Send urgent instructions to <span class="font-bold text-slate-900 dark:text-white">{{ activeContact?.name }}</span></p>
                </div>
                <div class="p-6">
                    <textarea v-model="urgentInstructionMsg" rows="3" placeholder="Type urgent instruction..."
                        class="mb-4 min-h-32 w-full resize-none rounded-2xl border border-red-200 dark:border-red-500/20 bg-red-50/70 dark:bg-red-500/5 px-4 py-3 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-red-400 dark:focus:border-red-400/50 focus:ring-4 focus:ring-red-100 dark:focus:ring-red-500/10"></textarea>
                    <div class="flex gap-3">
                        <button @click="confirmUrgentInstruction" :disabled="!urgentInstructionMsg.trim()" class="flex-1 rounded-2xl bg-red-500 py-3 text-sm font-bold text-white shadow-lg shadow-red-500/20 transition-colors hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-40">Send Urgent</button>
                        <button @click="showUrgentModal = false" class="flex-1 rounded-2xl border border-slate-300 dark:border-white/10 bg-slate-100 py-3 text-sm text-slate-700 transition-colors hover:bg-slate-200 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useToast } from '@/composables/useToast'

const store = useDispatcherStore()
const toast = useToast()
const ROUTE_UPDATE_PREFIX = 'ROUTE UPDATE'
const URGENT_INSTRUCTION_PREFIX = 'URGENT INSTRUCTION'

// Identifies messages sent by the dispatcher (supports both 'dispatch' and 'Dispatcher')
function isDispatcherMsg(msg) {
    return msg.from === 'dispatch' || msg.from?.toLowerCase() === 'dispatcher'
}

function parseDispatchAction(text) {
    const raw = String(text || '').trim()
    if (!raw) return null

    if (raw === ROUTE_UPDATE_PREFIX || raw.startsWith(`${ROUTE_UPDATE_PREFIX}\n`)) {
        const body = raw.slice(ROUTE_UPDATE_PREFIX.length).trim() || 'Updated route pushed to navigation.'
        return { kind: 'route', title: 'Route Update', body }
    }

    if (raw === URGENT_INSTRUCTION_PREFIX || raw.startsWith(`${URGENT_INSTRUCTION_PREFIX}\n`)) {
        const body = raw.slice(URGENT_INSTRUCTION_PREFIX.length).trim() || 'Immediate dispatcher instruction received.'
        return { kind: 'urgent', title: 'Urgent Instruction', body }
    }

    return null
}

function formatContactPreview(text) {
    const action = parseDispatchAction(text)
    if (!action) return text || 'No messages yet'
    const firstLine = action.body.split('\n')[0] || action.title
    return `${action.title}: ${firstLine}`
}

function buildRouteUpdateMessage(notes) {
    const lines = [ROUTE_UPDATE_PREFIX, 'Updated route pushed to your navigation.']
    if (notes) lines.push(`Notes: ${notes}`)
    return lines.join('\n')
}

function buildUrgentInstructionMessage(text) {
    return [URGENT_INSTRUCTION_PREFIX, text].join('\n')
}

let _refreshInterval = null
onMounted(() => {
    store.initialize().catch(() => {})
    // Poll for new messages every 8s so dispatcher sees driver replies in near-real-time
    _refreshInterval = setInterval(() => store.fetchContacts().catch(() => {}), 8000)
})
onUnmounted(() => { if (_refreshInterval) clearInterval(_refreshInterval) })

const activeChat = ref(null)
const contactType = ref('all')
const searchQuery = ref('')
const newMessage = ref('')
const isSendingMsg = ref(false)
const showLog = ref(false)
const routeUpdateSent = ref(false)
const urgentSent = ref(false)
const chatAreaRef = ref(null)
const showRouteModal = ref(false)
const showUrgentModal = ref(false)
const routeUpdateMsg = ref('')
const urgentInstructionMsg = ref('')

const contactTabs = [
    { key: 'all', label: 'All' },
    { key: 'driver', label: 'Drivers' },
    { key: 'warehouse', label: 'Warehouse' }
]

const contacts = computed(() => store.dispatcherContacts)

// Set first contact as active once loaded
watch(contacts, (list) => {
    if (list.length && activeChat.value === null) activeChat.value = list[0].id
}, { immediate: true })

const filteredContacts = computed(() => {
    return contacts.value.filter(c => {
        const matchType = contactType.value === 'all' || c.type === contactType.value
        const matchSearch = c.name.toLowerCase().includes(searchQuery.value.toLowerCase())
        return matchType && matchSearch
    })
})

const activeContact = computed(() => contacts.value.find(c => c.id === activeChat.value))

// Per-contact message history — seeded from backend thread messages
const messageHistory = ref({})

function messagesFromThread(thread) {
    return (thread.messages || []).map(m => ({
        id: String(m.id || Date.now()),
        from: m.sender || m.from || 'driver',
        text: m.text || '',
        time: m.time || '',
        type: 'text',
    }))
}

// When contacts load, seed message history from backend data
watch(contacts, (list) => {
    list.forEach(c => {
        if (c.messages?.length && !messageHistory.value[c.id]) {
            messageHistory.value[c.id] = messagesFromThread(c)
        }
    })
}, { immediate: true, deep: true })

// When switching contacts, load their messages if available
watch(activeChat, (newId) => {
    if (!newId) return
    const contact = contacts.value.find(c => c.id === newId)
    if (contact?.messages?.length && !messageHistory.value[newId]) {
        messageHistory.value[newId] = messagesFromThread(contact)
    }
})

const currentMessages = computed(() => messageHistory.value[activeChat.value] || [])
const renderedMessages = computed(() => currentMessages.value.map(msg => ({
    ...msg,
    action: msg.type === 'system' ? null : parseDispatchAction(msg.text),
})))

const commLog = ref([])

function addSystemMessage(text) {
    if (!messageHistory.value[activeChat.value]) messageHistory.value[activeChat.value] = []
    messageHistory.value[activeChat.value].push({ id: Date.now(), from: 'system', text, time: '', type: 'system' })
}

async function ensureActiveThread(contact, contactId) {
    let threadId = contact?.threadId

    if (!threadId) {
        const threadName = contact?.type === 'driver'
            ? `Driver: ${contact?.name || 'Unknown'}`
            : (contact?.name || 'Unknown')
        const newThread = await store.createChatForContact(threadName, contact?.phone || null)
        if (newThread) {
            threadId = String(newThread.id)
            messageHistory.value[threadId] = messageHistory.value[contactId] || []
            delete messageHistory.value[contactId]
            await store.fetchContacts()
        }
    }

    return threadId
}

async function sendThreadMessage(text, { optimistic = false } = {}) {
    const contact = activeContact.value
    const contactId = activeChat.value
    if (!contact || !contactId) throw new Error('No active contact selected')

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    let tempId = null

    if (optimistic) {
        if (!messageHistory.value[contactId]) messageHistory.value[contactId] = []
        tempId = `temp-${Date.now()}`
        messageHistory.value[contactId].push({ id: tempId, from: 'dispatch', text, time: now, type: 'text' })
        nextTick(() => { if (chatAreaRef.value) chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight })
    }

    isSendingMsg.value = true
    try {
        const threadId = await ensureActiveThread(contact, contactId)
        if (!threadId) throw new Error('Unable to create a chat thread')

        const updated = await store.sendDispatchMessage(threadId, text)
        if (!updated) throw new Error('Message send failed')

        messageHistory.value[String(updated.id) || threadId] = messagesFromThread(updated)
        await store.fetchContacts().catch(() => {})
        return now
    } catch (error) {
        if (optimistic && tempId) {
            const activeMessages = messageHistory.value[contactId] || []
            messageHistory.value[contactId] = activeMessages.filter(msg => msg.id !== tempId)
        }
        throw error
    } finally {
        isSendingMsg.value = false
        nextTick(() => { if (chatAreaRef.value) chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight })
    }
}

async function confirmRouteUpdate() {
    const notes = routeUpdateMsg.value.trim()
    try {
        const now = await sendThreadMessage(buildRouteUpdateMessage(notes))
        routeUpdateSent.value = true
        commLog.value.unshift({
            id: Date.now(),
            action: 'Route Update Pushed',
            type: 'route',
            contact: activeContact.value?.name,
            detail: notes || 'Updated route sent',
            time: now,
        })
        showRouteModal.value = false
        routeUpdateMsg.value = ''
        setTimeout(() => { routeUpdateSent.value = false }, 5000)
    } catch (_) {
        toast.error('Could not push route update right now.')
    }
}

async function confirmUrgentInstruction() {
    const instruction = urgentInstructionMsg.value.trim()
    if (!instruction) return

    try {
        const now = await sendThreadMessage(buildUrgentInstructionMessage(instruction))
        urgentSent.value = true
        commLog.value.unshift({
            id: Date.now(),
            action: 'Urgent Instruction',
            type: 'urgent',
            contact: activeContact.value?.name,
            detail: instruction,
            time: now,
        })
        showUrgentModal.value = false
        urgentInstructionMsg.value = ''
        setTimeout(() => { urgentSent.value = false }, 5000)
    } catch (_) {
        toast.error('Could not send the urgent instruction.')
    }
}

async function sendMessage() {
    const text = newMessage.value.trim()
    if (!text || isSendingMsg.value) return

    const contact = activeContact.value
    newMessage.value = ''
    try {
        const now = await sendThreadMessage(text, { optimistic: true })
        commLog.value.unshift({ id: Date.now(), action: 'Message Sent', type: 'message', contact: contact?.name, detail: text.substring(0, 40), time: now })
    } catch (_) {
        toast.error('Could not send that message.')
    }
}
</script>
