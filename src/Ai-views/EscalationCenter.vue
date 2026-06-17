<template>
    <div class="space-y-6">
        <!-- Header & Search -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-red-500 text-3xl">local_fire_department</span>
                    Escalation Center
                </h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage, de-escalate, and resolve high-priority
                    customer issues</p>
            </div>
            <div class="flex gap-2 w-full sm:w-auto">
                <div class="relative w-full sm:w-64">
                    <input v-model="searchQuery" type="text" placeholder="Search customer or Order ID..."
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-red-500 transition-colors shadow-sm">
                    <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-lg">search</span>
                </div>
            </div>
        </div>

        <!-- Metrics Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-5 rounded-xl shadow-sm border-t-4 border-t-red-500 relative overflow-hidden group">
                <div class="absolute -right-4 -top-4 w-16 h-16 bg-red-500/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Total Escalations</div>
                <div class="flex items-end gap-3">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ store.escalations.length }}</div>
                    <div class="text-xs text-red-500 mb-1 font-bold">All time</div>
                </div>
            </div>
            <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-5 rounded-xl shadow-sm border-t-4 border-t-orange-500 relative overflow-hidden group">
                <div class="absolute -right-4 -top-4 w-16 h-16 bg-orange-500/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Open</div>
                <div class="flex items-end gap-3">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ store.openCount }}</div>
                    <div class="text-xs text-orange-500 dark:text-orange-400 font-bold flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">warning</span> Needs Attention
                    </div>
                </div>
            </div>
            <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-5 rounded-xl shadow-sm border-t-4 border-t-purple-500 relative overflow-hidden group">
                <div class="absolute -right-4 -top-4 w-16 h-16 bg-purple-500/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Negative Sentiment</div>
                <div class="flex items-end gap-3">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ negativeCount }}</div>
                    <div class="text-xs text-purple-500 dark:text-purple-400 mb-1 font-bold">Frustrated Customers</div>
                </div>
            </div>
            <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-5 rounded-xl shadow-sm border-t-4 border-t-green-500 relative overflow-hidden group">
                <div class="absolute -right-4 -top-4 w-16 h-16 bg-green-500/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Resolved</div>
                <div class="flex items-end gap-3">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ store.resolvedCount }}</div>
                    <div class="text-xs text-green-500 dark:text-green-400 mb-1 font-bold flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">check_circle</span> Closed
                    </div>
                </div>
            </div>
        </div>

        <!-- Filter Bar + Table -->
        <div class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 rounded-xl overflow-hidden shadow-sm flex flex-col">
            <div v-if="!isSupportManager" class="mx-4 mt-4 rounded-lg border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 px-4 py-3 text-xs text-amber-700 dark:text-amber-300">
                Escalations are visible here for the wider support team, but only the Support Manager can resolve them.
            </div>
            <div class="p-4 bg-gray-50 dark:bg-white/5 border-b border-gray-100 dark:border-white/5 flex gap-2 overflow-x-auto no-scrollbar">
                <button v-for="f in filterTabs" :key="f.label" @click="activeFilter = f.label"
                    class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap flex items-center gap-2"
                    :class="activeFilter === f.label
                        ? 'bg-red-50 text-red-700 border border-red-200 shadow-sm dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30'
                        : 'bg-transparent text-gray-600 border border-transparent hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/10'">
                    <span class="material-symbols-outlined text-[16px]">{{ f.icon }}</span> {{ f.label }}
                </button>
            </div>

            <div v-if="store.loading" class="p-10 text-center text-gray-400 text-sm">Loading escalations...</div>
            <div v-else-if="store.error" class="p-6 text-sm text-red-600 dark:text-red-400">{{ store.error }}</div>

            <div v-else class="overflow-x-auto">
                <table class="w-full text-left text-sm min-w-[900px]">
                    <thead class="bg-gray-100/50 dark:bg-black/40 text-gray-500 dark:text-gray-400 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="p-4 pl-6 w-16">Status</th>
                            <th class="p-4">Customer</th>
                            <th class="p-4">Escalation Reason</th>
                            <th class="p-4">Sentiment</th>
                            <th class="p-4">Order</th>
                            <th class="p-4">Time Escalated</th>
                            <th class="p-4 text-right pr-6">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="esc in filtered" :key="esc.id"
                            class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                            @click="openDetail(esc)">
                            <td class="p-4 pl-6">
                                <div class="w-3 h-3 rounded-full shadow-inner mx-auto"
                                    :class="esc.status === 'OPEN' ? 'bg-red-500 animate-pulse' : 'bg-green-500'">
                                </div>
                            </td>
                            <td class="p-4">
                                <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                    <div class="w-7 h-7 rounded-sm bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center text-gray-700 dark:text-gray-300 font-bold text-xs uppercase shadow-sm">
                                        {{ initials(esc.customer_name) }}
                                    </div>
                                    <div>
                                        {{ esc.customer_name }}
                                        <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 font-normal">{{ esc.customer_email }}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="p-4">
                                <span class="px-2 py-1 rounded text-[10px] font-bold border inline-flex items-center gap-1 bg-red-50 text-red-700 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20">
                                    <span class="material-symbols-outlined text-[12px]">warning</span>
                                    {{ esc.reason.length > 60 ? esc.reason.slice(0, 60) + '…' : esc.reason }}
                                </span>
                            </td>
                            <td class="p-4">
                                <span class="text-xs font-bold" :class="sentimentColor(esc.sentiment)">
                                    {{ esc.sentiment }}
                                </span>
                            </td>
                            <td class="p-4 text-xs text-purple-600 dark:text-purple-400 font-mono font-bold">
                                {{ esc.latest_order_tracking_code || '—' }}
                            </td>
                            <td class="p-4">
                                <div class="text-sm font-bold text-gray-900 dark:text-gray-300">{{ formatTime(esc.escalated_at) }}</div>
                                <div class="text-[10px] text-gray-400 mt-0.5">{{ esc.assigned_agent_name ? `Support Manager: ${esc.assigned_agent_name}` : 'Support Manager Queue' }}</div>
                            </td>
                            <td class="p-4 pr-6 text-right">
                                <button v-if="esc.status === 'OPEN' && isSupportManager" @click.stop="openResolveModal(esc)"
                                    class="px-3 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-500/20 dark:hover:bg-red-500/30 text-red-700 dark:text-red-400 text-xs font-bold rounded-lg transition-colors border border-red-200 dark:border-red-500/30 shadow-sm">
                                    Resolve
                                </button>
                                <span v-else class="text-xs font-bold" :class="esc.status === 'OPEN' ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'">{{ esc.status === 'OPEN' ? 'Support Manager Only' : 'Resolved' }}</span>
                            </td>
                        </tr>
                        <tr v-if="filtered.length === 0">
                            <td colspan="7" class="p-12 text-center text-gray-500 dark:text-gray-400">
                                <div class="flex flex-col items-center justify-center">
                                    <span class="material-symbols-outlined text-5xl mb-3 text-gray-300 dark:text-gray-600">volunteer_activism</span>
                                    <p class="text-lg font-bold">No Escalations Found</p>
                                    <p class="text-sm mt-1">Inbox zero! Customer support is running smoothly.</p>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Detail Modal -->
        <Teleport to="body">
            <div v-if="showDetail && selectedEsc"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-6"
                @click.self="showDetail = false">
                <div class="bg-gray-50 dark:bg-gray-900 flex flex-col rounded-2xl w-full max-w-2xl shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden max-h-[90vh]">
                    <div class="px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-white/10 flex justify-between items-center shrink-0">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center text-white font-bold text-lg shadow-inner">
                                {{ initials(selectedEsc.customer_name) }}
                            </div>
                            <div>
                                <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedEsc.customer_name }}</h3>
                                <div class="flex items-center gap-3 text-sm mt-1">
                                    <span class="text-gray-500 dark:text-gray-400">{{ selectedEsc.customer_email }}</span>
                                    <span v-if="selectedEsc.latest_order_tracking_code" class="text-purple-600 dark:text-purple-400 font-mono font-bold">
                                        #{{ selectedEsc.latest_order_tracking_code }}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <button @click="showDetail = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-2 rounded-full hover:bg-gray-100 dark:hover:bg-white/10 transition">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-white dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Status</div>
                                <span class="text-sm font-bold" :class="selectedEsc.status === 'OPEN' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                                    {{ selectedEsc.status }}
                                </span>
                            </div>
                            <div class="bg-white dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Sentiment</div>
                                <span class="text-sm font-bold" :class="sentimentColor(selectedEsc.sentiment)">{{ selectedEsc.sentiment }}</span>
                            </div>
                            <div class="bg-white dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Escalated</div>
                                <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatFull(selectedEsc.escalated_at) }}</div>
                            </div>
                            <div class="bg-white dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Assigned Agent</div>
                                <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ selectedEsc.assigned_agent_name || 'Support Manager Queue' }}</div>
                            </div>
                        </div>

                        <div class="bg-white dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                            <div class="text-[10px] text-gray-500 uppercase font-bold mb-2">Escalation Reason</div>
                            <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{{ selectedEsc.reason }}</p>
                        </div>

                        <div v-if="selectedEsc.resolved_at" class="bg-green-50 dark:bg-green-500/10 rounded-xl p-4 border border-green-100 dark:border-green-500/20">
                            <div class="text-[10px] text-green-600 dark:text-green-400 uppercase font-bold mb-1">Resolved At</div>
                            <div class="text-sm text-green-700 dark:text-green-300 font-semibold">{{ formatFull(selectedEsc.resolved_at) }}</div>
                        </div>

                        <router-link :to="`/ai/live-conversations?sessionId=${selectedEsc.session_id}`"
                            class="flex items-center gap-2 text-sm font-bold text-purple-600 dark:text-purple-400 hover:underline">
                            <span class="material-symbols-outlined text-[18px]">forum</span>
                            View Full Conversation
                        </router-link>
                    </div>

                    <div class="p-6 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-white/10 flex gap-3 shrink-0">
                        <button @click="showDetail = false"
                            class="flex-1 py-3 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors">
                            Close
                        </button>
                        <button v-if="selectedEsc.status === 'OPEN' && isSupportManager" @click="openResolveModal(selectedEsc); showDetail = false"
                            class="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-colors shadow-sm flex justify-center items-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">check_circle</span> Resolve
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Resolve Modal -->
        <Teleport to="body">
            <div v-if="showResolve"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                @click.self="showResolve = false">
                <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-full text-green-600 dark:text-green-400">
                                <span class="material-symbols-outlined">gpp_good</span>
                            </div>
                            <div>
                                <h3 class="text-xl font-bold text-gray-900 dark:text-white">Resolve Escalation</h3>
                                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ resolveTarget?.customer_name }}</p>
                            </div>
                        </div>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5 text-sm text-gray-700 dark:text-gray-300">
                            <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Reason</div>
                            {{ resolveTarget?.reason }}
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Notes (optional)</label>
                            <textarea v-model="resolveNotes" rows="3"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white outline-none focus:border-green-500 transition-colors resize-none"
                                placeholder="Summary of manual intervention..."></textarea>
                        </div>
                    </div>
                    <div class="p-6 border-t border-gray-100 dark:border-white/5 flex gap-3 bg-gray-50 dark:bg-white/5">
                        <button @click="showResolve = false"
                            class="flex-1 py-2.5 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors border border-gray-200 dark:border-white/10 shadow-sm">
                            Cancel
                        </button>
                        <button @click="confirmResolve" :disabled="resolving"
                            class="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-bold rounded-xl transition-colors shadow-sm">
                            {{ resolving ? 'Resolving…' : 'Submit & Close' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useEscalationStore } from '@/stores/escalationStore'

const store = useEscalationStore()
const authStore = useAuthStore()
const searchQuery = ref('')
const activeFilter = ref('All')
const showDetail = ref(false)
const showResolve = ref(false)
const selectedEsc = ref(null)
const resolveTarget = ref(null)
const resolveNotes = ref('')
const resolving = ref(false)
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

const filterTabs = [
    { label: 'All', icon: 'list' },
    { label: 'Open', icon: 'warning' },
    { label: 'Resolved', icon: 'check_circle' },
    { label: 'Negative', icon: 'mood_bad' },
]

onMounted(() => store.load())

const negativeCount = computed(() =>
    store.escalations.filter(e => e.sentiment === 'Negative').length
)

const filtered = computed(() => {
    let result = store.escalations

    if (activeFilter.value === 'Open') result = result.filter(e => e.status === 'OPEN')
    else if (activeFilter.value === 'Resolved') result = result.filter(e => e.status === 'RESOLVED')
    else if (activeFilter.value === 'Negative') result = result.filter(e => e.sentiment === 'Negative')

    if (searchQuery.value.trim()) {
        const q = searchQuery.value.trim().toLowerCase()
        result = result.filter(e =>
            (e.customer_name || '').toLowerCase().includes(q) ||
            (e.customer_email || '').toLowerCase().includes(q) ||
            (e.reason || '').toLowerCase().includes(q) ||
            (e.latest_order_tracking_code || '').toLowerCase().includes(q)
        )
    }
    return result
})

function openDetail(esc) {
    selectedEsc.value = esc
    showDetail.value = true
}

function openResolveModal(esc) {
    resolveTarget.value = esc
    resolveNotes.value = ''
    showResolve.value = true
}

async function confirmResolve() {
    if (!isSupportManager.value) return
    if (!resolveTarget.value) return
    resolving.value = true
    try {
        await store.resolve(resolveTarget.value.id)
        showResolve.value = false
        resolveTarget.value = null
    } finally {
        resolving.value = false
    }
}

function initials(name) {
    return (name || 'C')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map(p => p[0]?.toUpperCase() || '')
        .join('')
}

function sentimentColor(s) {
    if (s === 'Negative') return 'text-red-600 dark:text-red-400'
    if (s === 'Positive') return 'text-green-600 dark:text-green-400'
    return 'text-gray-500 dark:text-gray-400'
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
</script>
