<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">AI Recovery Tickets</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Operational action items generated from AI support analytics insights
                </p>
            </div>
            <button
                @click="load(true)"
                class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg text-sm font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/10 transition-colors shadow-sm"
            >
                <span class="material-symbols-outlined text-[18px]" :class="loading ? 'animate-spin' : ''">refresh</span>
                Refresh
            </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-16 text-gray-400 text-sm">Loading recovery tickets...</div>

        <!-- Error -->
        <div v-else-if="loadError" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ loadError }}
        </div>

        <!-- Empty -->
        <div v-else-if="tickets.length === 0" class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-black/20 p-12 text-center shadow-sm">
            <span class="material-symbols-outlined text-4xl text-gray-300 dark:text-gray-600 mb-3 block">healing</span>
            <p class="text-gray-500 dark:text-gray-400 font-medium">No recovery tickets at the moment.</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Tickets appear here when the Support Manager acts on AI analytics insights.</p>
        </div>

        <!-- Ticket Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
                v-for="ticket in tickets"
                :key="ticket.id"
                class="bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col gap-3 cursor-pointer"
                :class="ticket.status === 'resolved' ? 'opacity-60 hover:opacity-80' : 'hover:border-blue-300 dark:hover:border-blue-500/40'"
                @click="openDetail(ticket)"
            >
                <!-- Header row -->
                <div class="flex justify-between items-start gap-2">
                    <div class="flex flex-wrap items-center gap-2">
                        <span class="text-xs font-mono font-bold px-2 py-0.5 rounded"
                            :class="ticket.status === 'resolved' ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'">
                            {{ ticket.reference_code }}
                        </span>
                        <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border" :class="priorityClass(ticket.priority)">
                            {{ ticket.priority }}
                        </span>
                    </div>
                    <span class="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider shrink-0"
                        :class="ticket.status === 'resolved' ? 'text-green-600 dark:text-green-400' : ticket.status === 'in_progress' ? 'text-yellow-600 dark:text-yellow-400' : 'text-blue-600 dark:text-blue-400'">
                        <span class="w-1.5 h-1.5 rounded-full"
                            :class="ticket.status === 'resolved' ? 'bg-green-500' : ticket.status === 'in_progress' ? 'bg-yellow-500 animate-pulse' : 'bg-blue-500'">
                        </span>
                        {{ statusLabel(ticket.status) }}
                    </span>
                </div>

                <!-- Title & description -->
                <div>
                    <h4 class="font-bold text-gray-900 dark:text-white text-sm leading-snug mb-1"
                        :class="ticket.status === 'resolved' ? 'line-through decoration-gray-400' : ''">
                        {{ ticket.title }}
                    </h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">{{ ticket.description }}</p>
                </div>

                <!-- Footer -->
                <div class="border-t border-gray-100 dark:border-white/5 pt-3 flex items-center justify-between text-xs text-gray-400">
                    <span class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-[12px]">schedule</span>
                        {{ formatTime(ticket.created_at) }}
                    </span>
                    <span v-if="ticket.status !== 'resolved'" class="flex items-center gap-1 text-blue-500 dark:text-blue-400 font-bold">
                        Take Action
                        <span class="material-symbols-outlined text-[12px]">arrow_forward</span>
                    </span>
                    <span v-else class="flex items-center gap-1 text-green-600 dark:text-green-400 font-bold">
                        <span class="material-symbols-outlined text-[12px]">check_circle</span>
                        Resolved
                    </span>
                </div>
            </div>
        </div>

        <!-- Ticket Detail Modal -->
        <Teleport to="body">
            <div
                v-if="showModal && selectedTicket"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
                @click.self="showModal = false"
            >
                <div class="relative w-full max-w-lg rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
                    style="background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%); border: 1px solid rgba(255,255,255,0.08);">

                    <!-- Glow accent top bar -->
                    <div class="h-1 w-full shrink-0" :class="selectedTicket.status === 'resolved' ? 'bg-gradient-to-r from-green-500 to-emerald-400' : selectedTicket.priority === 'urgent' ? 'bg-gradient-to-r from-red-500 to-orange-400' : 'bg-gradient-to-r from-blue-500 to-cyan-400'"></div>

                    <!-- Header -->
                    <div class="px-6 pt-5 pb-4 flex items-start justify-between gap-4 shrink-0">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2.5">
                                <span class="text-[11px] font-mono font-bold px-2.5 py-1 rounded-lg bg-white/10 text-white/80 tracking-widest">
                                    {{ selectedTicket.reference_code }}
                                </span>
                                <span class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border" :class="priorityBadge(selectedTicket.priority)">
                                    {{ selectedTicket.priority }} Priority
                                </span>
                            </div>
                            <h3 class="text-xl font-bold text-white leading-snug">{{ selectedTicket.title }}</h3>
                            <p class="text-xs text-slate-400 mt-1.5 flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[13px] text-purple-400">auto_awesome</span>
                                AI Analytics · {{ formatFull(selectedTicket.created_at) }}
                            </p>
                        </div>
                        <button @click="showModal = false" class="text-slate-500 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors shrink-0 mt-0.5">
                            <span class="material-symbols-outlined text-[18px]">close</span>
                        </button>
                    </div>

                    <!-- Status strip -->
                    <div class="mx-6 mb-4 flex items-center gap-2 px-4 py-2.5 rounded-xl shrink-0"
                        :class="selectedTicket.status === 'resolved' ? 'bg-green-500/10 border border-green-500/20' : selectedTicket.status === 'in_progress' ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-blue-500/10 border border-blue-500/20'">
                        <span class="w-2 h-2 rounded-full shrink-0"
                            :class="selectedTicket.status === 'resolved' ? 'bg-green-400' : selectedTicket.status === 'in_progress' ? 'bg-yellow-400 animate-pulse' : 'bg-blue-400'">
                        </span>
                        <span class="text-xs font-bold"
                            :class="selectedTicket.status === 'resolved' ? 'text-green-400' : selectedTicket.status === 'in_progress' ? 'text-yellow-400' : 'text-blue-400'">
                            {{ statusLabel(selectedTicket.status) }}
                        </span>
                        <span class="ml-auto text-[10px] text-slate-500">
                            {{ selectedTicket.status === 'resolved' ? 'Closed' : 'Action required by Logistics' }}
                        </span>
                    </div>

                    <!-- Body -->
                    <div class="px-6 pb-5 overflow-y-auto flex-1 space-y-4">

                        <!-- AI Finding -->
                        <div class="rounded-xl p-4" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-[14px] text-purple-400">insights</span>
                                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">What AI Detected</span>
                            </div>
                            <p class="text-sm text-slate-300 leading-relaxed">{{ selectedTicket.description }}</p>
                        </div>

                        <!-- AI Action Steps -->
                        <div v-if="selectedTicket.lm_action_steps && selectedTicket.lm_action_steps.length" class="rounded-xl p-4" style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2);">
                            <div class="flex items-center gap-2 mb-3">
                                <span class="material-symbols-outlined text-[14px] text-blue-400">task_alt</span>
                                <span class="text-[10px] font-bold uppercase tracking-wider text-blue-400">AI-Recommended Actions for You</span>
                            </div>
                            <ul class="space-y-2">
                                <li
                                    v-for="(step, i) in selectedTicket.lm_action_steps"
                                    :key="i"
                                    class="flex items-start gap-2.5 text-sm text-slate-300"
                                >
                                    <span class="shrink-0 w-5 h-5 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-400 text-[10px] font-bold flex items-center justify-center mt-0.5">{{ i + 1 }}</span>
                                    {{ step }}
                                </li>
                            </ul>
                        </div>

                        <!-- Resolved state -->
                        <div v-if="selectedTicket.status === 'resolved'" class="flex items-center gap-3 px-4 py-3 rounded-xl bg-green-500/10 border border-green-500/20">
                            <span class="material-symbols-outlined text-green-400 text-[20px]">check_circle</span>
                            <span class="text-sm text-green-400 font-semibold">You have resolved this issue.</span>
                        </div>
                    </div>

                    <!-- Modal Error -->
                    <div v-if="modalError" class="mx-6 mb-0 px-4 py-2.5 rounded-xl text-xs text-red-400 font-medium" style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2);">
                        {{ modalError }}
                    </div>

                    <!-- Footer -->
                    <div class="px-6 py-4 flex items-center justify-end gap-3 shrink-0" style="border-top: 1px solid rgba(255,255,255,0.06);">
                        <button
                            @click="showModal = false"
                            class="px-5 py-2.5 rounded-xl text-sm font-bold text-slate-300 hover:text-white transition-colors"
                            style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);"
                        >
                            Close
                        </button>
                        <button
                            v-if="selectedTicket.status === 'new'"
                            @click="changeStatus('in_progress')"
                            :disabled="updating"
                            class="px-5 py-2.5 rounded-xl text-sm font-bold text-white flex items-center gap-2 transition-all disabled:opacity-50"
                            style="background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 4px 14px rgba(245,158,11,0.3);"
                        >
                            <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                            {{ updating ? 'Saving…' : 'Start Working' }}
                        </button>
                        <button
                            v-if="selectedTicket.status !== 'resolved'"
                            @click="changeStatus('resolved')"
                            :disabled="updating"
                            class="px-5 py-2.5 rounded-xl text-sm font-bold text-white flex items-center gap-2 transition-all disabled:opacity-50"
                            style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 14px rgba(16,185,129,0.3);"
                        >
                            <span class="material-symbols-outlined text-[16px]">check_circle</span>
                            {{ updating ? 'Saving…' : 'Mark Resolved' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchTickets, updateTicket } from '@/utils/aiApi'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const tickets = ref([])
const loading = ref(false)
const loadError = ref('')
const modalError = ref('')
const openCount = ref(0)
const showModal = ref(false)
const selectedTicket = ref(null)
const updating = ref(false)

async function load(force = false) {
    if (loading.value && !force) return
    loading.value = true
    loadError.value = ''
    try {
        const response = await fetchTickets()
        const all = response.tickets || []
        tickets.value = all.filter(t => t.customer_name === 'AI Support Analytics')
        openCount.value = tickets.value.filter(t => t.status !== 'resolved').length
    } catch (err) {
        loadError.value = err.message || 'Failed to load recovery tickets'
    } finally {
        loading.value = false
    }
}

function openDetail(ticket) {
    selectedTicket.value = { ...ticket }
    modalError.value = ''
    showModal.value = true
}

async function changeStatus(newStatus) {
    if (!selectedTicket.value || updating.value) return
    updating.value = true
    modalError.value = ''
    try {
        const updated = await updateTicket(selectedTicket.value.id, { status: newStatus })
        const idx = tickets.value.findIndex(t => t.id === updated.id)
        if (idx !== -1) tickets.value.splice(idx, 1, updated)
        selectedTicket.value = { ...updated }
        if (newStatus === 'resolved') {
            toast.success('Ticket marked as resolved')
            showModal.value = false
            openCount.value = Math.max(0, openCount.value - 1)
        } else {
            toast.success('Status updated to In Progress')
        }
    } catch (err) {
        console.error('updateTicket failed:', err)
        modalError.value = err.message || 'Failed to update ticket'
    } finally {
        updating.value = false
    }
}


function statusLabel(status) {
    if (status === 'new') return 'New'
    if (status === 'in_progress') return 'In Progress'
    if (status === 'resolved') return 'Resolved'
    return status
}

function priorityBadge(priority) {
    const p = (priority || '').toLowerCase()
    if (p === 'urgent') return 'border-red-500/50 text-red-400 bg-red-500/10'
    if (p === 'high') return 'border-orange-500/50 text-orange-400 bg-orange-500/10'
    if (p === 'medium') return 'border-yellow-500/50 text-yellow-400 bg-yellow-500/10'
    return 'border-slate-500/50 text-slate-400 bg-slate-500/10'
}

function priorityClass(priority) {
    if (!priority) return 'border-gray-300 text-gray-500'
    const p = priority.toLowerCase()
    if (p === 'urgent') return 'border-red-400 text-red-600 dark:border-red-400/60 dark:text-red-400 bg-red-50 dark:bg-red-500/10'
    if (p === 'high') return 'border-orange-400 text-orange-600 dark:border-orange-400/60 dark:text-orange-400 bg-orange-50 dark:bg-orange-500/10'
    if (p === 'medium') return 'border-yellow-400 text-yellow-600 dark:border-yellow-400/60 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-500/10'
    return 'border-gray-300 text-gray-500 dark:border-gray-600 dark:text-gray-400'
}

function formatTime(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatFull(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleString(undefined, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
</script>
