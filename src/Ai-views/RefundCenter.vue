<template>
    <div class="space-y-6">

        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Refund Center</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Track refund cases and flag urgent
                    situations</p>
            </div>
            <div class="relative">
                <input v-model="search" type="text" placeholder="Search refund cases..."
                    class="w-52 bg-white dark:bg-[#1a1a2e] border border-gray-200 dark:border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors" />
                <span class="material-symbols-outlined absolute left-2.5 top-2 text-gray-400 text-[18px]">search</span>
            </div>
        </div>

        <!-- Stats Strip -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div v-for="stat in statCards" :key="stat.label"
                class="bg-white dark:bg-card-darker rounded-xl border border-gray-100 dark:border-white/5 p-4 flex items-center gap-3 shadow-sm">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" :class="stat.bg">
                    <span class="material-symbols-outlined text-[20px]" :class="stat.iconColor">{{ stat.icon }}</span>
                </div>
                <div>
                    <div class="text-2xl font-black text-gray-900 dark:text-white">{{ stat.value }}</div>
                    <div class="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">{{
                        stat.label }}</div>
                </div>
            </div>
        </div>

        <!-- Filter Tabs -->
        <div
            class="flex gap-1 bg-white dark:bg-black/20 p-1 rounded-lg border border-gray-200 dark:border-white/10 w-fit flex-wrap">
            <button v-for="tab in filterTabs" :key="tab.id" @click="activeTab = tab.id"
                class="px-3 py-1.5 rounded-md text-xs font-bold transition-all"
                :class="activeTab === tab.id ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'">
                {{ tab.label }}
            </button>
        </div>

        <!-- Loading / Error -->
        <div v-if="store.loading"
            class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-card-darker p-6 text-sm text-gray-500 dark:text-gray-400">
            Loading refund cases...
        </div>
        <div v-else-if="store.error"
            class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ store.error }}
        </div>

        <!-- Table -->
        <div v-else
            class="bg-white dark:bg-card-darker rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/2">
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ref</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Original</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Refund</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Flags</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Sentiment</th>
                            <th class="text-right px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="filtered.length === 0">
                            <td colspan="8" class="text-center py-16 text-gray-400 dark:text-gray-600">
                                <span class="material-symbols-outlined text-4xl mb-2 block">currency_exchange</span>
                                No refund cases found
                            </td>
                        </tr>
                        <tr v-for="row in filtered" :key="row.id"
                            class="border-b border-gray-50 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/[0.06] transition-colors cursor-pointer"
                            @click="openDetail(row)">
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ row.reference_code }}</span>
                            </td>
                            <td class="px-5 py-3.5">
                                <div class="font-medium text-gray-900 dark:text-white text-sm">{{ row.customer_name }}</div>
                            </td>
                            <td class="px-5 py-3.5 hidden md:table-cell text-sm text-gray-700 dark:text-gray-300">₹{{ formatAmount(row.original_price) }}</td>
                            <td class="px-5 py-3.5 text-sm font-semibold text-green-700 dark:text-green-400">₹{{ formatAmount(row.refund_amount) }}</td>
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="statusStyle(row.status)">{{ row.status }}</span>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell">
                                <div class="flex flex-wrap gap-1">
                                    <span v-if="row.is_urgent"
                                        class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400">
                                        Urgent
                                    </span>
                                    <span v-if="isChargebackRisk(row)"
                                        class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400">
                                        Chargeback
                                    </span>
                                </div>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell">
                                <span v-if="row.sentiment" class="text-xs font-medium px-2 py-0.5 rounded-full" :class="sentimentStyle(row.sentiment)">{{ row.sentiment }}</span>
                                <span v-else class="text-gray-400 text-xs">&#8212;</span>
                            </td>
                            <td class="px-5 py-3.5 text-right" @click.stop>
                                <button @click="openDetail(row)" title="View"
                                    class="p-1.5 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-500/10 text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
                                    <span class="material-symbols-outlined text-[18px]">open_in_new</span>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Case Detail Drawer -->
        <Teleport to="body">
            <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0"
                enter-to-class="opacity-100">
                <div v-if="selected"
                    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-end"
                    @click.self="selected = null">
                    <div class="w-full max-w-2xl h-full bg-white dark:bg-gray-900 shadow-2xl overflow-y-auto flex flex-col">

                        <!-- Header -->
                        <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-white/10 px-6 py-4 flex items-center justify-between z-10">
                            <div>
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ selected.reference_code }}</span>
                                    <span v-if="selected.is_urgent" class="text-xs font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400">Urgent</span>
                                    <span v-if="isChargebackRisk(selected)" class="text-xs font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400">Chargeback Risk</span>
                                </div>
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ selected.customer_name }}</h3>
                            </div>
                            <button @click="selected = null"
                                class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 transition-colors">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <!-- Body: two-column -->
                        <div class="flex-1 p-6 flex gap-6">

                            <!-- Left -->
                            <div class="flex-1 space-y-6 min-w-0">

                                <!-- Info Grid -->
                                <div class="grid grid-cols-2 gap-3">
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Status</div>
                                        <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="statusStyle(selected.status)">{{ selected.status }}</span>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Flow</div>
                                        <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="flowStyle(selected.flow_type)">{{ flowLabel(selected.flow_type) }}</span>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Original Price</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">₹{{ formatAmount(selected.original_price) }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Refund Amount</div>
                                        <div class="text-sm font-semibold text-green-700 dark:text-green-400">₹{{ formatAmount(selected.refund_amount) }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Filed</div>
                                        <div class="text-xs font-semibold text-gray-900 dark:text-white">{{ formatFull(selected.created_at) }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Updated</div>
                                        <div class="text-xs font-semibold text-gray-900 dark:text-white">{{ formatFull(selected.updated_at) }}</div>
                                    </div>
                                </div>

                                <!-- Refund Timeline -->
                                <div>
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-3">Refund Timeline</div>
                                    <div class="relative">
                                        <div class="absolute left-3.5 top-0 h-full w-0.5 bg-gray-200 dark:bg-white/10"></div>
                                        <div v-for="(step, idx) in timelineSteps" :key="idx" class="relative flex items-start gap-3 mb-4">
                                            <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 z-10 border-2"
                                                :class="step.done ? 'bg-purple-600 border-purple-600' : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-white/20'">
                                                <span class="material-symbols-outlined text-[14px]" :class="step.done ? 'text-white' : 'text-gray-400'">{{ step.icon }}</span>
                                            </div>
                                            <div class="pt-0.5">
                                                <div class="text-sm font-semibold" :class="step.done ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-600'">{{ step.label }}</div>
                                                <div class="text-xs text-gray-500">{{ step.desc }}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Urgency Flag -->
                                <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-3">Urgency Flag</div>
                                    <div class="flex items-center gap-3 mb-3">
                                        <button @click="toggleUrgent"
                                            class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-all"
                                            :class="urgentDraft ? 'border-red-400 bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400' : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-gray-300'">
                                            {{ urgentDraft ? 'Marked Urgent' : 'Mark as Urgent' }}
                                        </button>
                                        <button v-if="urgentDraft" @click="toggleUrgent"
                                            class="px-3 py-1.5 rounded-lg text-xs font-bold border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-gray-300 transition-all">
                                            Clear
                                        </button>
                                    </div>
                                    <textarea v-if="urgentDraft" v-model="urgentReason" rows="2"
                                        placeholder="Reason (e.g. customer threatened chargeback)..."
                                        class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500 transition resize-none mb-2"></textarea>
                                    <button @click="saveUrgent" :disabled="savingUrgent"
                                        class="px-4 py-2 bg-gray-800 dark:bg-white/10 hover:bg-gray-900 dark:hover:bg-white/20 text-white font-bold rounded-lg text-xs transition-colors disabled:opacity-50">
                                        {{ savingUrgent ? 'Saving...' : 'Save Flag' }}
                                    </button>
                                </div>

                                <!-- Support Notes (read-only from damage_report side) -->
                                <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Support Notes</div>
                                    <div v-if="selected.support_notes" class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ selected.support_notes }}</div>
                                    <div v-else class="text-xs text-gray-400">No support notes on this case.</div>
                                </div>
                            </div>

                            <!-- Right: Customer History Sidebar -->
                            <div class="w-44 flex-shrink-0 space-y-3">
                                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer History</div>
                                <div v-if="loadingHistory" class="text-xs text-gray-400">Loading...</div>
                                <template v-else-if="customerHistory">
                                    <div v-for="item in customerHistoryCards" :key="item.label"
                                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-center">
                                        <div class="text-xl font-black" :class="item.color">{{ item.value }}</div>
                                        <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 leading-tight">{{ item.label }}</div>
                                    </div>
                                    <div v-if="customerHistory.last_sentiment"
                                        class="p-3 rounded-xl border text-center text-xs font-bold"
                                        :class="sentimentStyle(customerHistory.last_sentiment)">
                                        {{ customerHistory.last_sentiment }}
                                    </div>
                                </template>
                                <div v-else class="text-xs text-gray-400">N/A</div>
                            </div>
                        </div>
                    </div>
                </div>
            </Transition>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRefundStore } from '@/stores/refundStore'

const store = useRefundStore()

onMounted(async () => {
    try { await store.load() } catch { /* error shown in template */ }
})

// Tabs & Filters
const search = ref('')
const activeTab = ref('all')

const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'pending', label: 'Pending Decision' },
    { id: 'claimed', label: 'Claimed' },
    { id: 'rejected', label: 'Rejected' },
    { id: 'chargeback', label: 'Chargeback Risk' },
    { id: 'urgent', label: 'Urgent' },
]

const isChargebackRisk = (c) => c.status === 'Rejected' && c.sentiment === 'Negative'

const filtered = computed(() => {
    let list = store.cases
    if (activeTab.value === 'pending') {
        list = list.filter((c) => ['Pending', 'Under Review', 'Claims Reviewed', 'Physically Inspected'].includes(c.status))
    } else if (activeTab.value === 'claimed') {
        list = list.filter((c) => ['Claimed', 'Refunded'].includes(c.status))
    } else if (activeTab.value === 'rejected') {
        list = list.filter((c) => c.status === 'Rejected')
    } else if (activeTab.value === 'chargeback') {
        list = list.filter(isChargebackRisk)
    } else if (activeTab.value === 'urgent') {
        list = list.filter((c) => c.is_urgent)
    }
    const q = search.value.toLowerCase()
    if (q) {
        list = list.filter((c) =>
            (c.reference_code || '').toLowerCase().includes(q) ||
            (c.customer_name || '').toLowerCase().includes(q),
        )
    }
    return list
})

// Stats Strip
const statCards = computed(() => [
    {
        label: 'Total Refunded',
        value: '₹' + formatAmount(store.stats.total_refunded_value || 0),
        icon: 'currency_exchange',
        bg: 'bg-green-100 dark:bg-green-500/10',
        iconColor: 'text-green-600 dark:text-green-400',
    },
    {
        label: 'Pending Decision',
        value: store.stats.pending_decision || 0,
        icon: 'hourglass_empty',
        bg: 'bg-yellow-100 dark:bg-yellow-500/10',
        iconColor: 'text-yellow-600 dark:text-yellow-400',
    },
    {
        label: 'Urgent Flagged',
        value: store.urgentCount,
        icon: 'priority_high',
        bg: 'bg-red-100 dark:bg-red-500/10',
        iconColor: 'text-red-600 dark:text-red-400',
    },
    {
        label: 'Chargeback Risk',
        value: store.chargebackRiskCount,
        icon: 'credit_card_off',
        bg: 'bg-orange-100 dark:bg-orange-500/10',
        iconColor: 'text-orange-600 dark:text-orange-400',
    },
])

// Detail Drawer
const selected = ref(null)
const urgentDraft = ref(false)
const urgentReason = ref('')
const savingUrgent = ref(false)
const customerHistory = ref(null)
const loadingHistory = ref(false)

const customerHistoryCards = computed(() => {
    if (!customerHistory.value) return []
    return [
        { label: 'Total Orders', value: customerHistory.value.total_orders, color: 'text-blue-600 dark:text-blue-400' },
        { label: 'Damage Reports', value: customerHistory.value.damage_reports_count, color: 'text-orange-600 dark:text-orange-400' },
        { label: 'Escalations', value: customerHistory.value.escalations_count, color: 'text-red-600 dark:text-red-400' },
    ]
})

const TIMELINE_STEPS = [
    { label: 'Reported', icon: 'flag', statuses: ['Pending', 'Under Review', 'Claims Reviewed', 'Pickup Requested', 'Pickup Approved', 'Pickup Scheduled', 'Collected', 'Arrived at Warehouse', 'Physically Inspected', 'Rejected', 'Claimed', 'Refunded', 'Closed'] },
    { label: 'Under Review', icon: 'rate_review', statuses: ['Under Review', 'Claims Reviewed', 'Pickup Requested', 'Pickup Approved', 'Pickup Scheduled', 'Collected', 'Arrived at Warehouse', 'Physically Inspected', 'Rejected', 'Claimed', 'Refunded', 'Closed'] },
    { label: 'Decision Made', icon: 'gavel', statuses: ['Rejected', 'Claimed', 'Refunded', 'Closed'] },
    { label: 'Refunded / Closed', icon: 'check_circle', statuses: ['Refunded', 'Closed'] },
]

const timelineSteps = computed(() => {
    const status = selected.value?.status || ''
    return TIMELINE_STEPS.map((step) => ({
        ...step,
        done: step.statuses.includes(status),
        desc: step.statuses.includes(status) ? 'Completed' : 'Pending',
    }))
})

async function openDetail(row) {
    selected.value = { ...row }
    urgentDraft.value = row.is_urgent
    urgentReason.value = row.urgent_reason || ''
    customerHistory.value = null
    if (row.customer_id) {
        loadingHistory.value = true
        customerHistory.value = await store.loadCustomerHistory(row.customer_id)
        loadingHistory.value = false
    }
}

function toggleUrgent() {
    urgentDraft.value = !urgentDraft.value
    if (!urgentDraft.value) urgentReason.value = ''
}

async function saveUrgent() {
    if (!selected.value) return
    savingUrgent.value = true
    try {
        const updated = await store.flagUrgent(selected.value.id, urgentDraft.value, urgentReason.value)
        selected.value = { ...updated }
        urgentDraft.value = updated.is_urgent
        urgentReason.value = updated.urgent_reason || ''
    } finally {
        savingUrgent.value = false
    }
}

// Style Helpers
const flowStyle = (f) => ({
    photo_review: 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
    pickup_inspection: 'bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400',
}[f] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400')

const flowLabel = (f) => ({ photo_review: 'Photo Review', pickup_inspection: 'Pickup Inspection' }[f] || f || '&#8212;')

const statusStyle = (s) => {
    const map = {
        Pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400',
        'Under Review': 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
        'Claims Reviewed': 'bg-teal-100 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400',
        Claimed: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400',
        Rejected: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
        Refunded: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
        Closed: 'bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-gray-400',
    }
    return map[s] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400'
}

const sentimentStyle = (s) => ({
    Positive: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
    Negative: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
    Neutral: 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400',
}[s] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400')

const formatAmount = (n) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })

const formatFull = (iso) =>
    new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>
