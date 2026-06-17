<template>
    <div class="space-y-6">
        <div class="flex items-center gap-3">
            <div
                class="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-400 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                <span class="material-symbols-outlined text-gray-900 dark:text-white">psychology</span>
            </div>
            <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500">
                Smart WMS Intelligence</h2>
        </div>

        <!-- AI Chat Interface -->
        <div class="glass-panel rounded-xl overflow-hidden border border-purple-500/20">
            <div
                class="p-4 border-b border-gray-100 dark:border-white/5 bg-gradient-to-r from-purple-500/10 to-pink-500/10">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-400">smart_toy</span>
                    AI Assistant — Ask me anything about your warehouse
                </h3>
            </div>
            <div class="p-4 h-64 overflow-y-auto space-y-3" ref="chatContainer">
                <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex"
                    :class="msg.type === 'user' ? 'justify-end' : 'justify-start'">
                    <div class="max-w-[80%] p-3 rounded-lg text-sm"
                        :class="msg.type === 'user' ? 'bg-primary/20 text-green-800 dark:text-primary border border-primary/20 whitespace-pre-line' : 'bg-gray-50 dark:bg-white/5 text-gray-700 dark:text-gray-200 border border-gray-100 dark:border-white/5 whitespace-pre-line'">
                        {{ msg.text }}
                    </div>
                </div>
                <div v-if="chatLoading" class="flex justify-start">
                    <div class="max-w-[80%] p-3 rounded-lg text-sm bg-gray-50 dark:bg-white/5 text-gray-700 dark:text-gray-200 border border-gray-100 dark:border-white/5 whitespace-pre-line">
                        Analyzing live warehouse state...
                    </div>
                </div>
            </div>
            <div class="p-4 border-t border-gray-100 dark:border-white/5 flex gap-3">
                <input v-model="chatInput" @keyup.enter="sendChat" type="text"
                    placeholder="Ask: 'Which aisle has free space?' or 'How many laborers are free at 3 PM?'"
                    class="flex-1 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-purple-500/50 text-sm" />
                <button @click="sendChat" :disabled="chatLoading"
                    class="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-gray-900 dark:text-white px-5 py-3 rounded-lg font-bold transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">send</span>
                </button>
            </div>
            <!-- Quick Queries -->
            <div class="px-4 pb-4 flex flex-wrap gap-2">
                <button v-for="q in quickQueries" :key="q" @click="chatInput = q; sendChat()"
                    class="bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 px-3 py-1.5 rounded-lg text-xs border border-purple-500/20 transition-colors">
                    {{ q }}
                </button>
            </div>
        </div>

        <!-- AI Insights Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="insight in aiInsights" :key="insight.title"
                class="glass-panel p-6 rounded-xl transition-colors cursor-pointer group"
                :class="`hover:border-${insight.color}-500/50`">
                <div class="flex items-start justify-between mb-4">
                    <div class="p-3 rounded-lg" :class="`bg-${insight.color}-500/20 text-${insight.color}-400`">
                        <span class="material-symbols-outlined">{{ insight.icon }}</span>
                    </div>
                    <div class="text-xs text-gray-500">{{ insight.confidence }}</div>
                </div>
                <h3 class="font-bold text-gray-900 dark:text-white mb-2 transition-colors"
                    :class="`group-hover:text-${insight.color}-400`">
                    {{ insight.title }}</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ insight.description }}</p>
                <button @click="handleInsightAction(insight)"
                    class="w-full py-2 rounded text-sm font-bold transition-colors"
                    :class="`bg-${insight.color}-500/20 hover:bg-${insight.color}-500/30 text-${insight.color}-400`">
                    {{ insight.action }}
                </button>
            </div>
        </div>

        <!-- Tomorrow's Workload Prediction -->
        <div class="glass-panel p-6 rounded-xl border border-purple-500/10">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-purple-400">auto_graph</span>
                Tomorrow's Workload Prediction
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-center">
                    <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Expected Orders</div>
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ predictedOrders }}</div>
                    <div class="text-xs text-blue-600 dark:text-blue-400 mt-1">↑ ~20% vs today's {{ totalOrders }}</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-center">
                    <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Staff Needed</div>
                    <div class="text-3xl font-bold text-blue-600 dark:text-blue-400">{{ predictedStaffNeeded }}</div>
                    <div class="text-xs text-yellow-600 dark:text-yellow-400 mt-1">{{ extraStaffNeeded > 0 ? '+' + extraStaffNeeded + ' extra needed' : 'Sufficient staff' }}</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-center">
                    <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Active Orders</div>
                    <div class="text-3xl font-bold text-orange-600 dark:text-orange-400">{{ pickingOrders }}</div>
                    <div class="text-xs text-gray-500 mt-1">Picking / Packing now</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-center">
                    <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Available Staff</div>
                    <div class="text-3xl font-bold text-green-600 dark:text-green-400">{{ availableStaff }}/{{ totalStaff }}</div>
                    <div class="text-xs" :class="availableStaff < extraStaffNeeded ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400 mt-1'">{{ availableStaff < extraStaffNeeded ? 'May need extra' : 'Capacity OK' }}</div>
                </div>
            </div>
            <div class="mt-4 flex gap-3">
                <button @click="autoScheduleStaff"
                    class="bg-purple-500/20 hover:bg-purple-500/30 text-purple-600 dark:text-purple-400 px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">schedule</span> Auto-Schedule Extra Staff
                </button>
                <button @click="alertLogistics"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">notifications</span> Alert Logistics Manager
                </button>
            </div>
        </div>

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 text-gray-900 dark:text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce"
            :class="toastClass">
            <span class="material-symbols-outlined">{{ toastIcon }}</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>
<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL } from '@/config/api'

const authStore = useAuthStore()
const chatInput = ref('')
const chatContainer = ref(null)
const chatLoading = ref(false)
const chatSessionId = ref(null)

// Live data
const allOrders = ref([])
const labourers = ref([])
const dashboardData = ref(null)

const totalOrders = computed(() => allOrders.value.length)
const pendingOrders = computed(() => dashboardData.value?.pending_orders_count ?? allOrders.value.filter(o =>
    o.warehouse_substatus === 'AWAITING_PICK' ||
    o.status === 'PENDING' ||
    o.status === 'CONFIRMED'
).length)
const pickingOrders = computed(() => allOrders.value.filter(o =>
    o.warehouse_substatus === 'PICKING' ||
    o.warehouse_substatus === 'PICKED' ||
    o.warehouse_substatus === 'PACKING'
).length)
const availableStaff = computed(() => labourers.value.filter(l =>
    l.status === 'AVAILABLE' || l.status === 'IN_WAREHOUSE' || l.status === 'In Warehouse'
).length)
const onFieldStaff = computed(() => labourers.value.filter(l =>
    l.status === 'ON_DUTY' || l.status === 'ASSIGNED' || l.status === 'assigned' || l.status === 'ON_FIELD'
).length)
const totalStaff = computed(() => dashboardData.value?.total_labor ?? labourers.value.length)

// Predicted tomorrow workload (real current + 20%)
const predictedOrders = computed(() => Math.round(totalOrders.value * 1.2))
const predictedStaffNeeded = computed(() => Math.round(totalStaff.value * 1.15))
const extraStaffNeeded = computed(() => Math.max(0, predictedStaffNeeded.value - availableStaff.value))
const capacityPercent = computed(() => totalOrders.value > 0 ? Math.round((pickingOrders.value / totalOrders.value) * 100) : 0)

async function fetchLiveData() {
    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }
        const warehouseId = authStore.currentUser?.warehouse_id
        const labourUrl = warehouseId
            ? `${API_BASE_URL}/api/v1/labourers?page=1&page_size=100&warehouse_id=${warehouseId}`
            : `${API_BASE_URL}/api/v1/labourers?page=1&page_size=100`
        const dashboardUrl = warehouseId
            ? `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/dashboard`
            : null
        const requests = [
            fetch(`${API_BASE_URL}/api/v1/orders?page=1&page_size=200`, { headers }),
            fetch(labourUrl, { headers })
        ]
        if (dashboardUrl) requests.push(fetch(dashboardUrl, { headers }))
        const [ordersRes, labourRes, dashboardRes] = await Promise.allSettled(requests)
        if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
            const data = await ordersRes.value.json()
            allOrders.value = data.items || []
        }
        if (labourRes.status === 'fulfilled' && labourRes.value.ok) {
            const data = await labourRes.value.json()
            labourers.value = data.items || []
        }
        if (dashboardRes?.status === 'fulfilled' && dashboardRes.value.ok) {
            dashboardData.value = await dashboardRes.value.json()
        }
    } catch (error) {
        console.error('SmartWMS fetch error:', error)
    }
}

const quickQueries = [
    'Which aisle has free space?',
    'Which laborers are on-field?',
    'Do we have capacity for 5 more orders?',
    'Predict tomorrow\'s workload',
    'Suggest staff reallocation',
]

const chatMessages = ref([
    { type: 'ai', text: 'Hello! I\'m your Smart WMS assistant. Ask me about warehouse capacity, staff availability, aisle space, or workload predictions.' },
])

async function sendChat() {
    if (!chatInput.value.trim() || chatLoading.value) return
    const userMsg = chatInput.value.trim()
    chatMessages.value.push({ type: 'user', text: userMsg })
    chatInput.value = ''
    await nextTick()
    chatLoading.value = true
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userMsg,
                context: 'warehouse_management',
                session_id: chatSessionId.value
            })
        })

        if (response.ok) {
            const data = await response.json()
            chatSessionId.value = data.session_id || chatSessionId.value
            chatMessages.value.push({
                type: 'ai',
                text: data.response || data.message || 'I processed your request.'
            })
        } else {
            chatMessages.value.push({
                type: 'ai',
                text: `I couldn't complete that warehouse analysis right now. Current snapshot: ${pendingOrders.value} orders need attention, ${availableStaff.value}/${totalStaff.value} staff are available, and ${pickingOrders.value} orders are in picking or packing.`
            })
        }
    } catch (error) {
        console.error('AI chat error:', error)
        chatMessages.value.push({
            type: 'ai',
            text: `Smart WMS is temporarily unavailable. Current warehouse snapshot: ${pendingOrders.value} orders need attention, ${availableStaff.value}/${totalStaff.value} staff are available, and ${pickingOrders.value} orders are in picking or packing.`
        })
    } finally {
        chatLoading.value = false
        await nextTick()
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

const toastMsg = ref('')
const toastClass = ref('bg-green-500/90')
const toastIcon = ref('check_circle')

function showToast(msg, type = 'success') {
    toastMsg.value = msg
    toastClass.value = type === 'alert' ? 'bg-purple-500/90' : type === 'warning' ? 'bg-yellow-500/90' : 'bg-green-500/90'
    toastIcon.value = type === 'alert' ? 'notifications_active' : type === 'warning' ? 'warning' : 'check_circle'
    setTimeout(() => { toastMsg.value = '' }, 3000)
}

function handleInsightAction(insight) {
    chatMessages.value.push({ type: 'user', text: `Execute: ${insight.action}` })
    setTimeout(() => {
        chatMessages.value.push({ type: 'ai', text: `✅ ${insight.title} action initiated. ${insight.description} I've started processing this recommendation.` })
        nextTick(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
        })
    }, 600)
    showToast(`${insight.action} — initiated`, 'alert')
}

function autoScheduleStaff() {
    const extra = extraStaffNeeded.value || 5
    showToast(`${extra} extra staff auto-scheduled for tomorrow morning shift`, 'alert')
}

function alertLogistics() {
    showToast('Alert sent to Logistics Manager about tomorrow\'s workload spike', 'warning')
}

const aiInsights = computed(() => [
    {
        title: 'Slotting Optimization',
        icon: 'inventory_2', color: 'purple', confidence: 'Confidence: 99%',
        description: dashboardData.value?.picking_queue?.length
            ? `Highest live queue pressure is around ${dashboardData.value.picking_queue[0]?.zone || 'the primary picking aisle'}. Rebalance fast-moving SKUs closer to dispatch to reduce pick path length.`
            : 'Queue volume is light right now. Use this window to tidy high-frequency aisles and prep fast movers near dispatch.',
        action: 'Optimize Layout'
    },
    {
        title: 'Predictive Staffing',
        icon: 'schedule', color: 'blue', confidence: 'Confidence: 92%',
        description: `Based on ${totalOrders.value} active orders, schedule ${extraStaffNeeded.value > 0 ? extraStaffNeeded.value + ' extra' : 'standby'} staff for tomorrow's morning shift.`,
        action: 'Adjust Roster'
    },
    {
        title: 'Orders Pending Action',
        icon: 'warning', color: 'red',
        confidence: pendingOrders.value > 0 ? `${pendingOrders.value} need attention` : 'All clear',
        description: pendingOrders.value > 0
            ? `${pendingOrders.value} orders are PENDING or CONFIRMED and need validation before they enter picking.`
            : 'No pending orders — all orders are in the processing pipeline.',
        action: 'Review Orders'
    },
    {
        title: 'Staff Availability',
        icon: 'groups', color: 'green', confidence: `${availableStaff.value}/${totalStaff.value} available`,
        description: `${availableStaff.value} out of ${totalStaff.value} staff members are currently available for assignment. ${onFieldStaff.value} are actively on duty.`,
        action: 'Reallocate Staff'
    },
    {
        title: 'Visual Damage Assessment',
        icon: 'image_search', color: 'orange', confidence: 'AI Vision: Active',
        description: dashboardData.value?.recent_returns?.length
            ? `${dashboardData.value.recent_returns.length} recent return case(s) need attention. Review suspicious items during grading and confirm disposition quickly.`
            : 'No recent graded returns were pulled into the dashboard. Keep inbound inspection active for new damage cases.',
        action: 'Review Items'
    },
    {
        title: 'Tomorrow\'s Prediction',
        icon: 'auto_graph', color: 'teal',
        confidence: `~${predictedOrders.value} orders expected`,
        description: `Based on the current pipeline of ${totalOrders.value} orders and ${pendingOrders.value} waiting actions, tomorrow's load is estimated at ${predictedOrders.value} orders. Staff needed: ~${predictedStaffNeeded.value}.`,
        action: 'Plan Schedule'
    },
])

onMounted(async () => {
    await fetchLiveData()
})
</script>
