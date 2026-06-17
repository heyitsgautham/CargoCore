<template>
    <div class="space-y-6">

        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Reverse Logistics & Returns</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Customer intake and damage report status
                    tracking</p>
            </div>
            <div class="flex items-center gap-2">
                <div class="relative">
                    <input v-model="search" type="text" placeholder="Search reports..."
                        class="w-52 bg-white dark:bg-[#1a1a2e] border border-gray-200 dark:border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors" />
                    <span class="material-symbols-outlined absolute left-2.5 top-2 text-gray-400 text-[18px]">search</span>
                </div>
                <button @click="openRaiseCase"
                    class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg flex items-center gap-2 transition-colors text-sm">
                    <span class="material-symbols-outlined text-sm">add</span>
                    <span class="hidden sm:inline">Raise Case</span>
                </button>
            </div>
        </div>

        <!-- Stats Strip -->
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-4">
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
        <div class="flex gap-1 bg-white dark:bg-black/20 p-1 rounded-lg border border-gray-200 dark:border-white/10 w-fit flex-wrap">
            <button v-for="tab in filterTabs" :key="tab.id" @click="activeTab = tab.id"
                class="px-3 py-1.5 rounded-md text-xs font-bold transition-all"
                :class="activeTab === tab.id ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'">
                {{ tab.label }}
            </button>
        </div>

        <!-- Loading / Error -->
        <div v-if="store.loading"
            class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-card-darker p-6 text-sm text-gray-500 dark:text-gray-400">
            Loading damage reports...
        </div>
        <div v-else-if="store.error"
            class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ store.error }}
        </div>

        <!-- Table -->
        <div v-else class="bg-white dark:bg-card-darker rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/2">
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ref</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Order</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Flow</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Sentiment</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden xl:table-cell">Created</th>
                            <th class="text-right px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="filtered.length === 0">
                            <td colspan="8" class="text-center py-16 text-gray-400 dark:text-gray-600">
                                <span class="material-symbols-outlined text-4xl mb-2 block">inbox</span>
                                No damage reports found
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
                                <div class="text-xs text-gray-500 dark:text-gray-500">{{ row.customer_email }}</div>
                            </td>
                            <td class="px-5 py-3.5 hidden md:table-cell">
                                <span v-if="row.order_tracking_code" class="font-mono text-xs text-blue-600 dark:text-blue-400">{{ row.order_tracking_code }}</span>
                                <span v-else class="text-gray-400 text-xs">—</span>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell">
                                <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="flowStyle(row.flow_type)">{{ flowLabel(row.flow_type) }}</span>
                            </td>
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="statusStyle(row.status)">{{ row.status }}</span>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell">
                                <span v-if="row.sentiment" class="text-xs font-medium px-2 py-0.5 rounded-full" :class="sentimentStyle(row.sentiment)">{{ row.sentiment }}</span>
                                <span v-else class="text-gray-400 text-xs">—</span>
                            </td>
                            <td class="px-5 py-3.5 hidden xl:table-cell text-xs text-gray-500 dark:text-gray-500">{{ formatTime(row.created_at) }}</td>
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

        <!-- ── Case Detail Drawer ─────────────────────────────────────────── -->
        <Teleport to="body">
            <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0"
                enter-to-class="opacity-100" leave-active-class="transition-all duration-200"
                leave-from-class="opacity-100" leave-to-class="opacity-0">
                <div v-if="selected"
                    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-end"
                    @click.self="selected = null">
                    <div class="w-full max-w-2xl h-full bg-white dark:bg-gray-900 shadow-2xl overflow-y-auto flex flex-col">

                        <!-- Drawer Header -->
                        <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-white/10 px-6 py-4 flex items-center justify-between z-10">
                            <div>
                                <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ selected.reference_code }}</span>
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white mt-1 truncate max-w-[24rem]">{{ selected.description }}</h3>
                            </div>
                            <button @click="selected = null"
                                class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 transition-colors">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <!-- Drawer Body: two-column layout -->
                        <div class="flex-1 p-6 flex gap-6">

                            <!-- Left: main content -->
                            <div class="flex-1 space-y-6 min-w-0">

                                <!-- Badges -->
                                <div class="flex flex-wrap gap-2">
                                    <span class="text-xs font-bold px-2.5 py-1 rounded-full" :class="statusStyle(selected.status)">{{ selected.status }}</span>
                                    <span class="text-xs font-medium px-2.5 py-1 rounded-full" :class="flowStyle(selected.flow_type)">{{ flowLabel(selected.flow_type) }}</span>
                                    <span v-if="selected.sentiment" class="text-xs font-medium px-2.5 py-1 rounded-full" :class="sentimentStyle(selected.sentiment)">{{ selected.sentiment }}</span>
                                </div>

                                <!-- Info Grid -->
                                <div class="grid grid-cols-2 gap-3">
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Customer</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ selected.customer_name }}</div>
                                        <div class="text-xs text-gray-500">{{ selected.customer_email }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Order</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white font-mono">{{ selected.order_tracking_code || '—' }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Filed</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatFull(selected.created_at) }}</div>
                                    </div>
                                    <div v-if="selected.session_id" class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">AI Session</div>
                                        <a class="text-xs text-purple-500 hover:underline truncate block" href="#">View Conversation</a>
                                    </div>
                                </div>

                                <!-- Description -->
                                <div>
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Description</div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ selected.description }}</div>
                                </div>

                                <!-- Photos -->
                                <div v-if="selected.photos && selected.photos.length > 0">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Customer Photos</div>
                                    <div class="grid grid-cols-3 gap-2">
                                        <div v-for="(photo, idx) in selected.photos" :key="idx"
                                            class="aspect-square bg-gray-100 dark:bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                                            @click="zoomPhoto(photo)">
                                            <img :src="photo" class="w-full h-full object-cover" :alt="'Photo ' + (idx + 1)" loading="lazy" />
                                        </div>
                                    </div>
                                </div>
                                <div v-else-if="selected.photos !== undefined">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Customer Photos</div>
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-xs text-gray-400 text-center">No photos submitted</div>
                                </div>

                                <!-- Internal Notes -->
                                <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Internal Support Notes</div>
                                    <textarea v-model="notesValue" rows="3" placeholder="Add internal notes (visible to WM and LM)..."
                                        class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                                    <button @click="saveNotes"
                                        :disabled="savingNotes"
                                        class="mt-2 px-4 py-2 bg-gray-800 dark:bg-white/10 hover:bg-gray-900 dark:hover:bg-white/20 text-white font-bold rounded-lg text-xs transition-colors disabled:opacity-50">
                                        {{ savingNotes ? 'Saving…' : 'Save Notes' }}
                                    </button>
                                </div>

                                <!-- Customer Communication Panel -->
                                <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Message to Customer</div>
                                    <!-- Sent message thread -->
                                    <div v-if="selected.support_messages && selected.support_messages.length > 0"
                                        class="mb-3 space-y-2 max-h-40 overflow-y-auto">
                                        <div v-for="(msg, idx) in selected.support_messages" :key="idx"
                                            class="p-2.5 bg-purple-50 dark:bg-purple-500/10 rounded-lg border border-purple-100 dark:border-purple-500/20">
                                            <div class="text-xs font-semibold text-purple-700 dark:text-purple-400 mb-0.5">{{ msg.sent_by }}</div>
                                            <div class="text-sm text-gray-800 dark:text-gray-200">{{ msg.text }}</div>
                                            <div class="text-[10px] text-gray-400 mt-1">{{ formatFull(msg.sent_at) }}</div>
                                        </div>
                                    </div>
                                    <textarea v-model="customerMessage" rows="2" placeholder="Type a message to send to the customer..."
                                        class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                                    <div v-if="sendMessageError" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ sendMessageError }}</div>
                                    <button @click="sendCustomerMessage"
                                        :disabled="sendingMessage || !customerMessage.trim()"
                                        class="mt-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold rounded-lg text-xs transition-colors flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[14px]">send</span>
                                        {{ sendingMessage ? 'Sending...' : 'Send' }}
                                    </button>
                                </div>
                            </div>

                            <!-- Right: Customer History Sidebar -->
                            <div class="w-44 flex-shrink-0 space-y-3">
                                <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer History</div>
                                <div v-if="loadingHistory" class="text-xs text-gray-400">Loading…</div>
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

        <!-- ── Photo Zoom Modal ───────────────────────────────────────────── -->
        <Teleport to="body">
            <div v-if="zoomedPhoto"
                class="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4"
                @click="zoomedPhoto = null">
                <img :src="zoomedPhoto" class="max-h-[90vh] max-w-full rounded-xl shadow-2xl object-contain" />
            </div>
        </Teleport>

        <!-- ── Raise Case Modal ───────────────────────────────────────────── -->
        <Teleport to="body">
            <Transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 scale-95"
                enter-to-class="opacity-100 scale-100">
                <div v-if="showRaiseModal"
                    class="fixed inset-0 z-[150] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
                    @click.self="showRaiseModal = false">
                    <div class="w-full max-w-lg bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
                        <div class="px-6 py-4 border-b border-gray-100 dark:border-white/10 flex items-center justify-between">
                            <h3 class="text-base font-bold text-gray-900 dark:text-white">Raise Case on Customer's Behalf</h3>
                            <button @click="showRaiseModal = false" class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500">
                                <span class="material-symbols-outlined text-[18px]">close</span>
                            </button>
                        </div>
                        <div class="p-6 space-y-4">
                            <!-- Duplicate Warning -->
                            <div v-if="duplicateWarning"
                                class="p-3 bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/20 rounded-xl text-xs text-yellow-800 dark:text-yellow-300 flex items-start gap-2">
                                <span class="material-symbols-outlined text-[16px] flex-shrink-0 mt-0.5">warning</span>
                                <span>A damage report already exists for this order: <strong>{{ duplicateWarning.reference_code }}</strong> ({{ duplicateWarning.status }}). Are you sure you want to create another?</span>
                            </div>

                            <div>
                                <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Customer ID</label>
                                <input v-model="raiseForm.customer_id" type="text" placeholder="UUID of the customer..."
                                    class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Order ID <span class="text-gray-400 font-normal">(optional)</span></label>
                                <input v-model="raiseForm.order_id" type="text" placeholder="UUID of the order..."
                                    @blur="checkDuplicate"
                                    class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Flow Type</label>
                                <select v-model="raiseForm.flow_type" class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition">
                                    <option value="photo_review">Photo Review</option>
                                    <option value="pickup_inspection">Pickup Inspection</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Description</label>
                                <textarea v-model="raiseForm.description" rows="3" placeholder="Describe the damage or issue..."
                                    class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                            </div>
                            <div v-if="raiseError" class="text-sm text-red-600 dark:text-red-400">{{ raiseError }}</div>
                        </div>
                        <div class="px-6 py-4 border-t border-gray-100 dark:border-white/10 flex justify-end gap-2">
                            <button @click="showRaiseModal = false"
                                class="px-4 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                                Cancel
                            </button>
                            <button @click="submitRaiseCase" :disabled="raisingCase"
                                class="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg text-sm transition-colors disabled:opacity-50">
                                {{ raisingCase ? 'Creating…' : 'Create Report' }}
                            </button>
                        </div>
                    </div>
                </div>
            </Transition>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useReverseLogisticsStore } from '@/stores/reverseLogisticsStore'
import { sendSupportMessage } from '@/utils/aiApi'

const store = useReverseLogisticsStore()

onMounted(async () => {
    try { await store.load() } catch { /* error shown in template */ }
})

// ── Tabs & Filters ────────────────────────────────────────────────────────────
const search = ref('')
const activeTab = ref('all')

const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'photo_review', label: 'Photo Review' },
    { id: 'pickup_inspection', label: 'Pickup Inspection' },
    { id: 'reported', label: 'Reported' },
    { id: 'under_review', label: 'Under Review' },
]

const filtered = computed(() => {
    let list = store.reports
    if (activeTab.value === 'photo_review') list = list.filter((r) => r.flow_type === 'photo_review')
    else if (activeTab.value === 'pickup_inspection') list = list.filter((r) => r.flow_type === 'pickup_inspection')
    else if (activeTab.value === 'reported') list = list.filter((r) => r.status === 'reported')
    else if (activeTab.value === 'under_review') list = list.filter((r) => ['under_review', 'Under Review'].includes(r.status))

    const q = search.value.toLowerCase()
    if (q) {
        list = list.filter((r) =>
            (r.reference_code || '').toLowerCase().includes(q) ||
            (r.customer_name || '').toLowerCase().includes(q) ||
            (r.customer_email || '').toLowerCase().includes(q) ||
            (r.order_tracking_code || '').toLowerCase().includes(q),
        )
    }
    return list
})

// ── Stats Strip ───────────────────────────────────────────────────────────────
const statCards = computed(() => [
    { label: 'Total', value: store.reports.length, icon: 'assignment', bg: 'bg-gray-100 dark:bg-white/5', iconColor: 'text-gray-600 dark:text-gray-400' },
    { label: 'Reported', value: store.reportedCount, icon: 'pending_actions', bg: 'bg-orange-100 dark:bg-orange-500/10', iconColor: 'text-orange-600 dark:text-orange-400' },
    { label: 'Photo Review', value: store.photoReviewCount, icon: 'photo_camera', bg: 'bg-blue-100 dark:bg-blue-500/10', iconColor: 'text-blue-600 dark:text-blue-400' },
    { label: 'Pickup Inspect.', value: store.pickupInspectionCount, icon: 'local_shipping', bg: 'bg-purple-100 dark:bg-purple-500/10', iconColor: 'text-purple-600 dark:text-purple-400' },
    { label: 'Under Review', value: store.underReviewCount, icon: 'rate_review', bg: 'bg-teal-100 dark:bg-teal-500/10', iconColor: 'text-teal-600 dark:text-teal-400' },
])

// ── Detail Drawer ─────────────────────────────────────────────────────────────
const selected = ref(null)
const notesValue = ref('')
const savingNotes = ref(false)
const customerMessage = ref('')
const sendingMessage = ref(false)
const sendMessageError = ref('')
const customerHistory = ref(null)
const loadingHistory = ref(false)
const zoomedPhoto = ref(null)

const customerHistoryCards = computed(() => {
    if (!customerHistory.value) return []
    return [
        { label: 'Total Orders', value: customerHistory.value.total_orders, color: 'text-blue-600 dark:text-blue-400' },
        { label: 'Damage Reports', value: customerHistory.value.damage_reports_count, color: 'text-orange-600 dark:text-orange-400' },
        { label: 'Escalations', value: customerHistory.value.escalations_count, color: 'text-red-600 dark:text-red-400' },
    ]
})

async function openDetail(row) {
    selected.value = { ...row }
    notesValue.value = row.support_notes || ''
    customerMessage.value = ''
    customerHistory.value = null
    if (row.customer_id) {
        loadingHistory.value = true
        customerHistory.value = await store.loadCustomerHistory(row.customer_id)
        loadingHistory.value = false
    }
}

async function saveNotes() {
    if (!selected.value) return
    savingNotes.value = true
    try {
        const updated = await store.updateNotes(selected.value.id, notesValue.value)
        selected.value = { ...updated }
    } finally {
        savingNotes.value = false
    }
}

async function sendCustomerMessage() {
    const text = customerMessage.value.trim()
    if (!text || !selected.value) return
    sendingMessage.value = true
    sendMessageError.value = ''
    try {
        const updated = await sendSupportMessage(selected.value.id, text)
        selected.value = { ...updated }
        customerMessage.value = ''
        // Sync in the store list too
        const idx = store.reports.findIndex((r) => r.id === updated.id)
        if (idx !== -1) store.reports.splice(idx, 1, updated)
    } catch (err) {
        sendMessageError.value = err.message || 'Failed to send message'
    } finally {
        sendingMessage.value = false
    }
}

function zoomPhoto(url) {
    zoomedPhoto.value = url
}

// ── Raise Case Modal ──────────────────────────────────────────────────────────
const showRaiseModal = ref(false)
const raisingCase = ref(false)
const raiseError = ref('')
const duplicateWarning = ref(null)
const raiseForm = ref({ customer_id: '', order_id: '', flow_type: 'photo_review', description: '' })

function openRaiseCase() {
    raiseForm.value = { customer_id: '', order_id: '', flow_type: 'photo_review', description: '' }
    raiseError.value = ''
    duplicateWarning.value = null
    showRaiseModal.value = true
}

function checkDuplicate() {
    if (!raiseForm.value.order_id) { duplicateWarning.value = null; return }
    duplicateWarning.value = store.findDuplicate(raiseForm.value.order_id)
}

async function submitRaiseCase() {
    raiseError.value = ''
    if (!raiseForm.value.customer_id.trim()) { raiseError.value = 'Customer ID is required'; return }
    if (!raiseForm.value.description.trim()) { raiseError.value = 'Description is required'; return }
    raisingCase.value = true
    try {
        await store.createReport({
            customer_id: raiseForm.value.customer_id.trim(),
            order_id: raiseForm.value.order_id.trim() || undefined,
            flow_type: raiseForm.value.flow_type,
            description: raiseForm.value.description.trim(),
        })
        showRaiseModal.value = false
    } catch (err) {
        raiseError.value = err.message || 'Failed to create report'
    } finally {
        raisingCase.value = false
    }
}

// ── Style Helpers ─────────────────────────────────────────────────────────────
const flowStyle = (f) => ({
    photo_review: 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
    pickup_inspection: 'bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400',
}[f] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400')

const flowLabel = (f) => ({ photo_review: 'Photo Review', pickup_inspection: 'Pickup Inspection' }[f] || f || '—')

const statusStyle = (s) => {
    const map = {
        reported: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400',
        under_review: 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
        'Under Review': 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
        'Claims Reviewed': 'bg-teal-100 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400',
        closed: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
        Closed: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
    }
    return map[s] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400'
}

const sentimentStyle = (s) => ({
    Positive: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
    Negative: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
    Neutral: 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400',
}[s] || 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400')

const formatTime = (iso) => {
    if (!iso) return '—'
    const d = new Date(iso)
    const now = new Date()
    const diff = Math.floor((now - d) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

const formatFull = (iso) =>
    new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>
