<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Support Tickets</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage and track all support requests</p>
            </div>
            <div class="flex gap-2">
                <div class="relative hidden sm:block">
                    <input v-model="searchQuery" type="text" placeholder="Search tickets..."
                        class="w-64 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-purple-500 transition-colors shadow-sm">
                    <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-lg">search</span>
                </div>
                <button @click="showNewTicketModal = true"
                    v-if="isSupportManager"
                    class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg flex items-center gap-2 transition-colors shadow-sm text-sm">
                    <span class="material-symbols-outlined text-sm">add</span> <span class="hidden sm:inline">New Ticket</span>
                </button>
            </div>
        </div>

        <!-- Loading / Error -->
        <div v-if="store.loading" class="text-center py-16 text-gray-400 text-sm">Loading tickets...</div>
        <div v-else-if="store.error" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">{{ store.error }}</div>

        <!-- Kanban Board -->
        <div v-else class="space-y-4">
            <div v-if="!isSupportManager" class="rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300">
                Tickets are visible to the wider support team, but only the Support Manager can create, update, resolve, or delete them.
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pb-4">

            <!-- New Column -->
            <div class="bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 p-4 rounded-xl flex flex-col shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                        <span class="w-2 h-2 rounded-full bg-blue-500"></span> New
                    </h3>
                    <span class="bg-white dark:bg-white/10 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full text-xs font-bold shadow-sm">{{ filteredNew.length }}</span>
                </div>
                <div class="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-300px)] custom-scrollbar pr-1">
                    <div v-if="filteredNew.length === 0" class="text-center text-gray-400 text-xs py-8">No new tickets</div>
                    <div v-for="ticket in filteredNew" :key="ticket.id"
                        class="bg-white dark:bg-black/20 p-4 rounded-xl border border-gray-200 dark:border-white/10 hover:border-blue-400 dark:hover:border-blue-500/50 cursor-pointer transition-all shadow-sm flex flex-col gap-3"
                        @click="openModal(ticket)">
                        <div class="flex justify-between items-start">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="text-xs text-blue-600 dark:text-blue-400 font-bold bg-blue-50 dark:bg-blue-500/10 px-2 py-0.5 rounded">{{ ticket.reference_code }}</span>
                                <span v-if="ticket.source !== 'manual'" class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-white/70">{{ ticket.source_label }}</span>
                            </div>
                            <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border" :class="priorityClass(ticket.priority)">{{ ticket.priority }}</span>
                        </div>
                        <div>
                            <h4 class="text-gray-900 dark:text-white font-bold text-sm mb-1 leading-snug">{{ ticket.title }}</h4>
                            <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{{ ticket.description }}</p>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-xs border-t border-gray-100 dark:border-white/5 pt-3">
                            <div>
                                <span class="text-gray-400 block mb-0.5">Source</span>
                                <span class="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[10px]">{{ ticket.source === 'vendor_portal' ? 'storefront' : categoryIcon(ticket.category) }}</span>
                                    {{ ticket.source_label }}
                                </span>
                            </div>
                            <div>
                                <span class="text-gray-400 block mb-0.5">{{ ticket.requester_type || 'Customer' }}</span>
                                <span class="text-gray-700 dark:text-gray-300 font-medium truncate">{{ ticket.customer_name || '—' }}</span>
                            </div>
                        </div>
                        <div v-if="ticket.linked_order_tracking_code || ticket.linked_vendor_ticket_code" class="text-[11px] text-gray-500 dark:text-gray-400">
                            {{ ticket.linked_order_tracking_code || ticket.linked_vendor_ticket_code }}
                        </div>
                        <div class="flex items-center justify-between mt-auto pt-2">
                            <span class="text-xs text-gray-500 dark:text-gray-500">{{ formatTime(ticket.created_at) }}</span>
                            <span v-if="ticket.assigned_agent_name" class="text-[10px] text-purple-600 dark:text-purple-400 font-bold">{{ ticket.assigned_agent_name }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- In Progress Column -->
            <div class="bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 p-4 rounded-xl flex flex-col shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                        <span class="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span> In Progress
                    </h3>
                    <span class="bg-white dark:bg-white/10 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full text-xs font-bold shadow-sm">{{ filteredInProgress.length }}</span>
                </div>
                <div class="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-300px)] custom-scrollbar pr-1">
                    <div v-if="filteredInProgress.length === 0" class="text-center text-gray-400 text-xs py-8">No in-progress tickets</div>
                    <div v-for="ticket in filteredInProgress" :key="ticket.id"
                        class="bg-white dark:bg-black/20 p-4 rounded-xl border border-gray-200 dark:border-white/10 hover:border-yellow-400 dark:hover:border-yellow-500/50 cursor-pointer transition-all shadow-sm flex flex-col gap-3"
                        @click="openModal(ticket)">
                        <div class="flex justify-between items-start">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="text-xs text-yellow-600 dark:text-yellow-400 font-bold bg-yellow-50 dark:bg-yellow-500/10 px-2 py-0.5 rounded">{{ ticket.reference_code }}</span>
                                <span v-if="ticket.source !== 'manual'" class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-white/70">{{ ticket.source_label }}</span>
                            </div>
                            <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border" :class="priorityClass(ticket.priority)">{{ ticket.priority }}</span>
                        </div>
                        <div>
                            <h4 class="text-gray-900 dark:text-white font-bold text-sm mb-1 leading-snug">{{ ticket.title }}</h4>
                            <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{{ ticket.description }}</p>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-xs border-t border-gray-100 dark:border-white/5 pt-3">
                            <div>
                                <span class="text-gray-400 block mb-0.5">Requester</span>
                                <span class="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[10px]">{{ ticket.source === 'vendor_portal' ? 'storefront' : 'person' }}</span>
                                    {{ ticket.customer_name || '—' }}
                                </span>
                            </div>
                            <div>
                                <span class="text-gray-400 block mb-0.5">Order Ref</span>
                                <span class="text-gray-700 dark:text-gray-300 font-medium truncate text-[10px]">{{ ticket.linked_order_tracking_code || ticket.linked_vendor_ticket_code || '—' }}</span>
                            </div>
                        </div>
                        <div class="flex items-center justify-between mt-auto pt-2">
                            <span class="text-xs text-gray-500 dark:text-gray-500">{{ formatTime(ticket.updated_at) }}</span>
                            <span v-if="ticket.assigned_agent_name" class="text-[10px] text-purple-600 dark:text-purple-400 font-bold">{{ ticket.assigned_agent_name }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Resolved Column -->
            <div class="bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 p-4 rounded-xl flex flex-col shadow-sm border-t-4 border-t-green-500/50">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                        <span class="w-2 h-2 rounded-full bg-green-500"></span> Resolved
                    </h3>
                    <span class="bg-white dark:bg-white/10 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full text-xs font-bold shadow-sm">{{ filteredResolved.length }}</span>
                </div>
                <div class="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-300px)] custom-scrollbar pr-1">
                    <div v-if="filteredResolved.length === 0" class="text-center text-gray-400 text-xs py-8">No resolved tickets</div>
                    <div v-for="ticket in filteredResolved" :key="ticket.id"
                        class="bg-white dark:bg-black/20 p-4 rounded-xl border border-gray-200 dark:border-white/10 hover:border-green-400 dark:hover:border-green-500/50 cursor-pointer transition-all opacity-70 hover:opacity-100 flex flex-col gap-3"
                        @click="openModal(ticket)">
                        <div class="flex justify-between items-start">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="text-xs text-green-600 dark:text-green-400 font-bold bg-green-50 dark:bg-green-500/10 px-2 py-0.5 rounded">{{ ticket.reference_code }}</span>
                                <span v-if="ticket.source !== 'manual'" class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-white/70">{{ ticket.source_label }}</span>
                            </div>
                        </div>
                        <div>
                            <h4 class="text-gray-900 dark:text-white font-bold text-sm mb-1 line-through decoration-gray-400 dark:decoration-gray-600">{{ ticket.title }}</h4>
                            <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 truncate">{{ ticket.linked_order_tracking_code || ticket.notes || categoryLabel(ticket.category) }}</p>
                        </div>
                        <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-green-500 text-sm">check_circle</span>
                                <span class="text-[10px] text-gray-500 dark:text-gray-500 font-medium uppercase tracking-wider">Resolved</span>
                            </div>
                            <span class="text-xs text-gray-400 dark:text-gray-500">{{ ticket.resolved_at ? formatTime(ticket.resolved_at) : formatTime(ticket.updated_at) }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </div>

        <!-- Ticket Detail Modal -->
        <Teleport to="body">
            <TicketDetailModal />
        </Teleport>

        <!-- New Ticket Modal -->
        <Teleport to="body">
            <NewTicketModal />
        </Teleport>
    </div>
</template>

<script setup>
import TicketDetailModal from './tickets/TicketDetailModal.vue'
import NewTicketModal from './tickets/NewTicketModal.vue'
import { ticketsPageKey } from './tickets/ticketsPageContext'
import { ref, computed, onMounted, watch, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useTicketStore } from '@/stores/ticketStore'

const store = useTicketStore()
const authStore = useAuthStore()
const showModal = ref(false)
const showNewTicketModal = ref(false)
const selectedTicket = ref(null)
const searchQuery = ref('')
const editNotes = ref('')
const replyDraft = ref('')
const creating = ref(false)
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

const newForm = ref({ title: '', description: '', priority: 'medium', category: 'general', customer_name: '' })

onMounted(() => store.load())

watch(selectedTicket, (t) => {
    if (!t) return
    editNotes.value = t.notes || ''
    replyDraft.value = ''
})

// Filtered columns
const filteredNew = computed(() => filterList(store.newTickets))
const filteredInProgress = computed(() => filterList(store.inProgressTickets))
const filteredResolved = computed(() => filterList(store.resolvedTickets))
const isWarehouseInboundSelected = computed(() => selectedTicket.value?.source === 'warehouse_inbound')
const supportReplyLocked = computed(() => selectedTicket.value?.status === 'resolved')
const statusOptionsForSelectedTicket = computed(() => (
    isWarehouseInboundSelected.value
        ? statusOptions.filter((option) => option.value !== 'resolved')
        : statusOptions
))

function filterList(list) {
    if (!searchQuery.value.trim()) return list
    const q = searchQuery.value.trim().toLowerCase()
    return list.filter(t =>
        t.title.toLowerCase().includes(q) ||
        t.reference_code.toLowerCase().includes(q) ||
        (t.customer_name || '').toLowerCase().includes(q) ||
        (t.source_label || '').toLowerCase().includes(q) ||
        (t.linked_order_tracking_code || '').toLowerCase().includes(q) ||
        (t.linked_vendor_ticket_code || '').toLowerCase().includes(q)
    )
}

function openModal(ticket) {
    selectedTicket.value = { ...ticket }
    showModal.value = true
}

async function updateStatus(status) {
    if (!isSupportManager.value) return
    if (!selectedTicket.value) return
    if (selectedTicket.value.source === 'warehouse_inbound' && status === 'resolved') return
    const updated = await store.update(selectedTicket.value.id, { status })
    selectedTicket.value = { ...updated }
    if (status === 'resolved') showModal.value = false
}

async function saveNotes() {
    if (!isSupportManager.value) return
    if (!selectedTicket.value) return
    const updated = await store.update(selectedTicket.value.id, { notes: editNotes.value })
    selectedTicket.value = { ...updated }
}

async function sendVendorReply() {
    if (!isSupportManager.value) return
    if (!selectedTicket.value || !replyDraft.value.trim()) return
    if (selectedTicket.value.status === 'resolved') return
    const updated = await store.reply(selectedTicket.value.id, replyDraft.value.trim())
    selectedTicket.value = { ...updated }
    replyDraft.value = ''
}

async function resolveWarehouseIssue(action) {
    if (!isSupportManager.value) return
    if (!selectedTicket.value) return
    const updated = await store.update(selectedTicket.value.id, {
        status: 'resolved',
        notes: editNotes.value,
        resolution_action: action,
    })
    selectedTicket.value = { ...updated }
}

async function removeTicket() {
    if (!isSupportManager.value) return
    if (!selectedTicket.value) return
    await store.remove(selectedTicket.value.id)
    showModal.value = false
}

async function submitNewTicket() {
    if (!isSupportManager.value) return
    if (!newForm.value.title) return
    creating.value = true
    try {
        await store.create({
            title: newForm.value.title,
            description: newForm.value.description || '—',
            priority: newForm.value.priority,
            category: newForm.value.category,
            customer_name: newForm.value.customer_name || null,
        })
        showNewTicketModal.value = false
        newForm.value = { title: '', description: '', priority: 'medium', category: 'general', customer_name: '' }
    } finally {
        creating.value = false
    }
}

// Style helpers
function priorityClass(p) {
    return {
        urgent: 'bg-red-50 text-red-600 dark:bg-red-500/20 dark:text-red-400 border-red-200 dark:border-red-500/30',
        high: 'bg-orange-50 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400 border-orange-200 dark:border-orange-500/30',
        medium: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/20 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/30',
        low: 'bg-blue-50 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400 border-blue-200 dark:border-blue-500/30',
    }[p] || ''
}

function categoryIcon(c) {
    return { technical: 'bug_report', billing: 'receipt_long', logistics: 'local_shipping', damage: 'gavel', account: 'lock', refund: 'payments', general: 'help', vendor_support: 'storefront' }[c] || 'help'
}

function categoryLabel(c) {
    return { technical: 'Technical', billing: 'Billing', logistics: 'Logistics', damage: 'Damage', account: 'Account', refund: 'Refund', general: 'General', vendor_support: 'Vendor Support' }[c] || c
}

function statusLabel(s) {
    return { new: 'New', in_progress: 'In Progress', resolved: 'Resolved' }[s] || s
}

function warehouseResolutionHint(action) {
    return {
        vendor_accept_move: 'Warehouse Manager can continue receiving and move the shipment into picking.',
        vendor_take_back: 'Warehouse Manager can now generate the vendor take-back for this inbound shipment.',
    }[action] || 'Warehouse flow will continue based on this support resolution.'
}

function formatTime(iso) {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

function formatFull(iso) {
    return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const statusOptions = [
    { value: 'new', label: 'New', activeClass: 'border-blue-400 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400' },
    { value: 'in_progress', label: 'In Progress', activeClass: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400' },
    { value: 'resolved', label: 'Resolved', activeClass: 'border-green-400 bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400' },
]

provide(ticketsPageKey, {
    creating,
    editNotes,
    formatFull,
    isSupportManager,
    isWarehouseInboundSelected,
    newForm,
    priorityClass,
    removeTicket,
    replyDraft,
    resolveWarehouseIssue,
    saveNotes,
    selectedTicket,
    sendVendorReply,
    showModal,
    showNewTicketModal,
    statusLabel,
    statusOptionsForSelectedTicket,
    submitNewTicket,
    supportReplyLocked,
    updateStatus,
    warehouseResolutionHint,
})
</script>
