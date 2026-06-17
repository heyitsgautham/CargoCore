<template>
    <div class="space-y-6">

        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Contact Form Submissions</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">All messages submitted via the public Contact page</p>
            </div>
            <div class="flex items-center gap-2">
                <!-- Search -->
                <div class="relative">
                    <input v-model="search" type="text" placeholder="Search submissions..."
                        class="w-52 bg-white dark:bg-[#1a1a2e] border border-gray-200 dark:border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors" />
                    <span class="material-symbols-outlined absolute left-2.5 top-2 text-gray-400 text-[18px]">search</span>
                </div>
                <!-- Filter by status -->
                <select v-model="filterStatus" class="cf-select" :style="selectStyle">
                    <option value="">All Status</option>
                    <option value="new">New</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                </select>
                <!-- Filter by priority -->
                <select v-model="filterPriority" class="cf-select" :style="selectStyle">
                    <option value="">All Priority</option>
                    <option value="urgent">Urgent</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
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
                    <div class="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">{{ stat.label }}</div>
                </div>
            </div>
        </div>

        <div v-if="contactStore.loading" class="rounded-xl border border-gray-100 dark:border-white/5 bg-white dark:bg-card-darker p-6 text-sm text-gray-500 dark:text-gray-400">
            Loading contact submissions...
        </div>

        <div v-else-if="contactStore.error" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ contactStore.error }}
        </div>

        <!-- Table -->
        <div v-else class="bg-white dark:bg-card-darker rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/2">
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Submitter</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Subject</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Category</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Priority</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                            <th class="text-left px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Submitted</th>
                            <th class="text-right px-5 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="filtered.length === 0">
                            <td colspan="8" class="text-center py-16 text-gray-400 dark:text-gray-600">
                                <span class="material-symbols-outlined text-4xl mb-2 block">inbox</span>
                                No submissions found
                            </td>
                        </tr>
                        <tr v-for="row in filtered" :key="row.id"
                            class="border-b border-gray-50 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/[0.06] transition-colors cursor-pointer"
                            @click="openDetail(row)">
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ row.reference_code }}</span>
                            </td>
                            <td class="px-5 py-3.5">
                                <div class="font-medium text-gray-900 dark:text-white text-sm">{{ row.name }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-500">{{ row.email }}</div>
                            </td>
                            <td class="px-5 py-3.5 hidden md:table-cell">
                                <span class="text-gray-700 dark:text-gray-300 text-sm truncate max-w-[200px] block">{{ row.subject }}</span>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell">
                                <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="categoryStyle(row.category)">
                                    {{ categoryLabel(row.category) }}
                                </span>
                            </td>
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide" :class="priorityStyle(row.priority)">
                                    {{ row.priority }}
                                </span>
                            </td>
                            <td class="px-5 py-3.5">
                                <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="statusStyle(row.status)">
                                    {{ statusLabel(row.status) }}
                                </span>
                            </td>
                            <td class="px-5 py-3.5 hidden lg:table-cell text-xs text-gray-500 dark:text-gray-500">
                                {{ formatTime(row.created_at) }}
                            </td>
                            <td class="px-5 py-3.5 text-right" @click.stop>
                                <div class="flex items-center justify-end gap-1">
                                    <button @click="openDetail(row)" title="View"
                                        class="p-1.5 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-500/10 text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
                                        <span class="material-symbols-outlined text-[18px]">open_in_new</span>
                                    </button>
                                    <button @click="removeRow(row.id)" title="Delete"
                                        class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-500/10 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors">
                                        <span class="material-symbols-outlined text-[18px]">delete</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Detail Drawer / Modal -->
        <Teleport to="body">
            <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0" enter-to-class="opacity-100"
                leave-active-class="transition-all duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0">
                <div v-if="selected" class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-end"
                    @click.self="selected = null">
                    <Transition enter-active-class="transition-all duration-300" enter-from-class="translate-x-full opacity-0" enter-to-class="translate-x-0 opacity-100">
                        <div v-if="selected"
                            class="w-full max-w-xl h-full bg-white dark:bg-gray-900 shadow-2xl overflow-y-auto flex flex-col">

                            <!-- Drawer Header -->
                            <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-white/10 px-6 py-4 flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ selected.reference_code }}</span>
                                    <h3 class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ selected.subject }}</h3>
                                </div>
                                <button @click="selected = null" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 transition-colors">
                                    <span class="material-symbols-outlined">close</span>
                                </button>
                            </div>

                            <!-- Drawer Body -->
                            <div class="flex-1 p-6 space-y-6">

                                <!-- Badges -->
                                <div class="flex flex-wrap gap-2">
                                    <span class="text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wide" :class="priorityStyle(selected.priority)">{{ selected.priority }}</span>
                                    <span class="text-xs font-bold px-2.5 py-1 rounded-full" :class="statusStyle(selected.status)">{{ statusLabel(selected.status) }}</span>
                                    <span class="text-xs font-medium px-2.5 py-1 rounded-full" :class="categoryStyle(selected.category)">{{ categoryLabel(selected.category) }}</span>
                                </div>

                                <!-- Contact Info -->
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Name</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ selected.name }}</div>
                                    </div>
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Email</div>
                                        <a :href="'mailto:' + selected.email" class="text-sm font-semibold text-purple-600 dark:text-purple-400 hover:underline truncate block">{{ selected.email }}</a>
                                    </div>
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5" v-if="selected.phone">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Phone</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ selected.phone }}</div>
                                    </div>
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Submitted</div>
                                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatFull(selected.created_at) }}</div>
                                    </div>
                                </div>

                                <!-- Message -->
                                <div>
                                    <div class="text-xs font-bold text-gray-500 uppercase mb-2">Message</div>
                                    <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ selected.message }}</div>
                                </div>

                                <!-- CS Actions -->
                                <div class="space-y-4 border-t border-gray-100 dark:border-white/10 pt-6">
                                    <div class="text-xs font-bold text-gray-500 uppercase">CS Actions</div>

                                    <!-- Status -->
                                    <div>
                                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Update Status</label>
                                        <div class="flex gap-2 flex-wrap">
                                            <button v-for="s in statusOptions" :key="s.value"
                                                @click="updateField('status', s.value)"
                                                class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-all"
                                                :class="selected.status === s.value ? s.activeClass : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-white/20'">
                                                {{ s.label }}
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Priority -->
                                    <div>
                                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Change Priority</label>
                                        <div class="flex gap-2 flex-wrap">
                                            <button v-for="p in priorityOptions" :key="p.value"
                                                @click="updateField('priority', p.value)"
                                                class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-all"
                                                :class="selected.priority === p.value ? p.activeClass : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-white/20'">
                                                {{ p.label }}
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Internal Notes -->
                                    <div>
                                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Internal Notes</label>
                                        <textarea v-model="notes" rows="3" placeholder="Add internal CS notes..."
                                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                                        <button @click="updateField('notes', notes)"
                                            class="mt-2 px-4 py-2 bg-gray-800 dark:bg-white/10 hover:bg-gray-900 dark:hover:bg-white/20 text-white font-bold rounded-lg text-xs transition-colors">
                                            Save Notes
                                        </button>
                                    </div>

                                    <!-- Reply -->
                                    <div>
                                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Reply By Email</label>
                                        <textarea
                                            v-model="replyMessage"
                                            rows="5"
                                            placeholder="Write the reply that should be emailed to this customer..."
                                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"
                                        ></textarea>
                                        <div class="mt-2 flex items-center justify-between gap-3">
                                            <p class="text-[11px] text-gray-500 dark:text-gray-400">
                                                Sends from the existing Cargo Core support mailbox and marks this submission as resolved.
                                            </p>
                                            <button
                                                @click="sendReply"
                                                :disabled="replying || !replyMessage.trim()"
                                                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 disabled:cursor-not-allowed text-white font-bold rounded-lg text-xs transition-colors whitespace-nowrap"
                                            >
                                                {{ replying ? 'Sending...' : 'Send Reply' }}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Drawer Footer -->
                            <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-white/10 px-6 py-4 flex justify-between">
                                <button @click="removeSelected"
                                    class="px-4 py-2 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 font-bold rounded-lg text-sm transition-colors flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[16px]">delete</span> Delete
                                </button>
                                <button @click="selected = null"
                                    class="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg text-sm transition-colors">
                                    Done
                                </button>
                            </div>
                        </div>
                    </Transition>
                </div>
            </Transition>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useContactStore } from '@/stores/contactStore'

const contactStore = useContactStore()
const toast = useToast()

// Dark mode detection — drives inline color-scheme on native <select>
const isDark = ref(document.documentElement.classList.contains('dark'))
let _observer = null
onMounted(async () => {
    _observer = new MutationObserver(() => {
        isDark.value = document.documentElement.classList.contains('dark')
    })
    _observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    try {
        await contactStore.load()
    } catch {
        // store.error is rendered in the template
    }
})
onUnmounted(() => { if (_observer) _observer.disconnect() })

const selectStyle = computed(() =>
    isDark.value
        ? { colorScheme: 'dark', backgroundColor: '#1e1e2e', color: '#e2e8f0', borderColor: 'rgba(255,255,255,0.1)' }
        : { colorScheme: 'light', backgroundColor: '#fff', color: '#374151', borderColor: '#e5e7eb' }
)

// Filters
const search = ref('')
const filterStatus = ref('')
const filterPriority = ref('')

// Selected row for drawer
const selected = ref(null)
const notes = ref('')
const replyMessage = ref('')
const replying = ref(false)

const openDetail = (row) => {
    selected.value = { ...row }
    notes.value = row.notes || ''
    replyMessage.value = ''
}

const updateField = async (field, value) => {
    if (!selected.value) return
    try {
        const updated = await contactStore.update(selected.value.id, { [field]: value })
        selected.value = { ...updated }
        if (field === 'notes') notes.value = value
    } catch (error) {
        toast.error(error.message || 'Failed to update submission')
    }
}

const removeSelected = async () => {
    if (!selected.value) return
    try {
        await contactStore.remove(selected.value.id)
        selected.value = null
        toast.success('Submission deleted')
    } catch (error) {
        toast.error(error.message || 'Failed to delete submission')
    }
}

const removeRow = async (id) => {
    try {
        await contactStore.remove(id)
        if (selected.value?.id === id) {
            selected.value = null
        }
        toast.success('Submission deleted')
    } catch (error) {
        toast.error(error.message || 'Failed to delete submission')
    }
}

const sendReply = async () => {
    if (!selected.value || !replyMessage.value.trim() || replying.value) return

    replying.value = true
    try {
        const updated = await contactStore.reply(selected.value.id, replyMessage.value.trim())
        selected.value = { ...updated }
        replyMessage.value = ''
        toast.success(`Reply sent to ${updated.email}`)
    } catch (error) {
        toast.error(error.message || 'Failed to send reply')
    } finally {
        replying.value = false
    }
}

// Stats
const statCards = computed(() => [
    { label: 'Total', value: contactStore.stats.total, icon: 'inbox', bg: 'bg-gray-100 dark:bg-white/5', iconColor: 'text-gray-600 dark:text-gray-400' },
    { label: 'New', value: contactStore.stats.new, icon: 'fiber_new', bg: 'bg-blue-100 dark:bg-blue-500/10', iconColor: 'text-blue-600 dark:text-blue-400' },
    { label: 'In Progress', value: contactStore.stats.inProgress, icon: 'pending', bg: 'bg-yellow-100 dark:bg-yellow-500/10', iconColor: 'text-yellow-600 dark:text-yellow-400' },
    { label: 'Resolved', value: contactStore.stats.resolved, icon: 'check_circle', bg: 'bg-green-100 dark:bg-green-500/10', iconColor: 'text-green-600 dark:text-green-400' },
    { label: 'Urgent', value: contactStore.stats.urgent, icon: 'priority_high', bg: 'bg-red-100 dark:bg-red-500/10', iconColor: 'text-red-600 dark:text-red-400' },
])

// Filtered + searched list
const filtered = computed(() => {
    return contactStore.submissions.filter(s => {
        const q = search.value.toLowerCase()
        const matchSearch = !q
            || s.name.toLowerCase().includes(q)
            || s.email.toLowerCase().includes(q)
            || s.subject.toLowerCase().includes(q)
            || s.reference_code.toLowerCase().includes(q)
        const matchStatus = !filterStatus.value || s.status === filterStatus.value
        const matchPriority = !filterPriority.value || s.priority === filterPriority.value
        return matchSearch && matchStatus && matchPriority
    })
})

// Formatters
const formatTime = (iso) => {
    const d = new Date(iso)
    const now = new Date()
    const diff = Math.floor((now - d) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}
const formatFull = (iso) => new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

// Style helpers
const priorityStyle = (p) => ({
    urgent: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400',
    medium: 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
    low: 'bg-gray-100 text-gray-600 dark:bg-white/5 dark:text-gray-400',
}[p] || '')

const statusStyle = (s) => ({
    new: 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
    in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400',
    resolved: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
}[s] || '')

const statusLabel = (s) => ({ new: 'New', in_progress: 'In Progress', resolved: 'Resolved' }[s] || s)

const categoryStyle = (c) => ({
    delivery: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400',
    billing: 'bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400',
    technical: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-400',
    damage: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
    refund: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400',
    general: 'bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-gray-400',
}[c] || 'bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-gray-400')

const categoryLabel = (c) => ({ delivery: 'Delivery', billing: 'Billing', technical: 'Technical', damage: 'Damage', refund: 'Refund', general: 'General' }[c] || c)

const statusOptions = [
    { value: 'new', label: 'New', activeClass: 'border-blue-400 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400' },
    { value: 'in_progress', label: 'In Progress', activeClass: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400' },
    { value: 'resolved', label: 'Resolved', activeClass: 'border-green-400 bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400' },
]

const priorityOptions = [
    { value: 'low', label: 'Low', activeClass: 'border-gray-400 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-gray-300' },
    { value: 'medium', label: 'Medium', activeClass: 'border-blue-400 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400' },
    { value: 'high', label: 'High', activeClass: 'border-orange-400 bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400' },
    { value: 'urgent', label: 'Urgent', activeClass: 'border-red-400 bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400' },
]
</script>

<style scoped>
.cf-select {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    outline: none;
    transition: border-color 0.15s, background-color 0.15s, color 0.15s;
    cursor: pointer;
    width: 100%;
}
.cf-select:focus { border-color: #a855f7; }
</style>
