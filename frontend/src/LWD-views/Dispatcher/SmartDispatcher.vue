<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div
                    class="w-10 h-10 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center shadow-lg shadow-green-500/30">
                    <span class="material-symbols-outlined text-black">health_and_safety</span>
                </div>
                <h2
                    class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-500">
                    Smart Dispatch Assistant</h2>
            </div>
            <div class="flex items-center gap-3">
                <button @click="showChat = !showChat"
                    :class="showChat ? 'bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-800 dark:text-white border-gray-300 dark:border-white/20' : 'bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20'"
                    class="border py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-bold">
                    <span class="material-symbols-outlined text-[18px]">smart_toy</span>
                    {{ showChat ? 'Hide' : 'AI' }} Chat
                </button>
                <div class="flex items-center gap-2 text-xs text-gray-400">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> AI Engine Active
                </div>
            </div>
        </div>

        <!-- Natural Language Command Input -->
        <CommandBar />

        <div class="grid gap-6" :class="showChat ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1 lg:grid-cols-2'">
            <!-- AI Recommendations -->
            <RecommendationsPanel />

            <!-- Dispatch Forecast + Controls -->
            <ForecastControls />

            <!-- AI Chat Interface -->
            <DispatchChatPanel />
        </div>

        <!-- AI Delay Prediction Panel -->
        <DelayPredictions />
    </div>
</template>

<script setup>
import CommandBar from './smartDispatcher/CommandBar.vue'
import RecommendationsPanel from './smartDispatcher/RecommendationsPanel.vue'
import ForecastControls from './smartDispatcher/ForecastControls.vue'
import DispatchChatPanel from './smartDispatcher/DispatchChatPanel.vue'
import DelayPredictions from './smartDispatcher/DelayPredictions.vue'
import { smartDispatcherPageKey } from './smartDispatcher/smartDispatcherPageContext'
import { escapeHtml } from '@/utils/html'
import { ref, computed, nextTick, onMounted, provide } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from 'chart.js'
import { useDispatcherStore } from '@/stores/dispatcherStore'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const store = useDispatcherStore()
onMounted(() => store.initialize().catch(() => {}))

const nlCommand = ref('')
const nlResponse = ref('')
const nlProcessing = ref(false)
const peakReallocation = ref(true)
const shiftExtension = ref(false)
const vipLock = ref(true)
const peakToast = ref('')
const showChat = ref(false)
const chatInput = ref('')
const chatTyping = ref(false)
const chatContainer = ref(null)

const quickCommands = [
    'Show ready orders with assigned vehicles',
    'Suggest best driver for released orders',
    'Show free drivers near Warehouse 3',
    'Flag orders with no driver available',
    'Prioritize urgent released orders',
    'Explain why this driver was suggested',
    'Predict dispatch delay for ready orders',
    'Find the next backup driver'
]

const chatChips = ['Best driver?', 'Ready orders?', 'No driver available?', 'Why this driver?']



function normalizeCommand(value) {
    return String(value || '').trim().toLowerCase()
}

function getWarehouseByNumber(number) {
    const normalized = String(number)
    return (store.hubs || []).find((hub) => {
        const idMatch = String(hub.id || '') === normalized
        const codeMatch = String(hub.hubCode || '').match(/\d+/)?.[0] === normalized
        const nameMatch = String(hub.name || '').match(/\d+/)?.[0] === normalized
        return idMatch || codeMatch || nameMatch
    }) || null
}

function executeLocalQuickCommand(command) {
    const normalized = normalizeCommand(command)
    const drivers = store.dispatcherDrivers || []
    const activeOrders = store.activeOrders || []

    if (normalized === 'show idle drivers near warehouse 3') {
        const hub = getWarehouseByNumber(3)
        const idleDrivers = drivers
            .filter((driver) => driver.statusColor === 'bg-green-500' && (driver.load || 0) < 30)
            .sort((a, b) => {
                const aNear = String(a.hubId || '') === String(hub?.id || '')
                const bNear = String(b.hubId || '') === String(hub?.id || '')
                if (aNear !== bNear) return aNear ? -1 : 1
                return (a.load || 0) - (b.load || 0)
            })
            .slice(0, 5)

        return {
            text: idleDrivers.length
                ? `<b>Executed:</b> idle-driver scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>${idleDrivers.map((driver) => `${escapeHtml(driver.name)} (${driver.load}% load)`).join(', ')}.`
                : `<b>Executed:</b> idle-driver scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>No low-load active drivers found right now.`,
        }
    }

    if (normalized === 'prioritize vip orders for next 2 hours') {
        vipLock.value = true
        peakToast.value = 'VIP priority lock ON — Smart Dispatcher reserved priority handling'
        setTimeout(() => { peakToast.value = '' }, 3000)
        const vipOrders = activeOrders.filter((order) => String(order.priority || '').toUpperCase() === 'VIP')
        return {
            text: `<b>Executed:</b> VIP priority lock enabled for the next 2 hours.<br>Current VIP orders in scope: <b>${vipOrders.length}</b>.`
        }
    }

    if (normalized === 'find closest vehicle to warehouse 4') {
        const hub = getWarehouseByNumber(4)
        const nearbyDrivers = drivers
            .filter((driver) => String(driver.hubId || '') === String(hub?.id || ''))
            .sort((a, b) => (a.load || 0) - (b.load || 0))
        const best = nearbyDrivers[0]

        return {
            text: best
                ? `<b>Executed:</b> closest-vehicle scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>Best available match: <b>${escapeHtml(best.vehicle || 'Unassigned vehicle')}</b> with driver <b>${escapeHtml(best.name)}</b> at <b>${best.load}%</b> load.`
                : `<b>Executed:</b> closest-vehicle scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>No active driver-linked vehicle found for that warehouse right now.`,
        }
    }

    if (normalized === 'balance load across all active drivers') {
        const overloaded = drivers.filter((driver) => (driver.load || 0) > 85)
        const underused = drivers.filter((driver) => driver.statusColor === 'bg-green-500' && (driver.load || 0) < 30)
        return {
            text: `<b>Analysis ready:</b> load balance review completed.<br>Overloaded drivers: <b>${overloaded.length}</b>. Underused active drivers: <b>${underused.length}</b>.<br>No automatic reassignment is wired from this panel yet.`,
        }
    }

    if (normalized === 'assign all downtown parcels to smallest van') {
        const pendingCount = (store.pendingOrders || []).length
        return {
            text: `<b>Analysis ready:</b> found <b>${pendingCount}</b> pending order(s) to review for downtown assignment.<br>This panel does not yet auto-assign orders from the quick chip itself.`,
        }
    }

    if (normalized === 're-route zone b around highway closure') {
        return {
            text: `<b>Analysis ready:</b> reroute request captured for <b>Zone B</b>.<br>No direct reroute executor is connected from this quick chip yet; use Route Optimization to apply route changes.`,
        }
    }

    if (normalized === 'delay route 7 due to weather alerts') {
        return {
            text: `<b>Analysis ready:</b> weather-delay scenario prepared for <b>Route 7</b>.<br>This quick chip does not currently write an actual route-delay update into operations data.`,
        }
    }

    if (normalized === 'simulate 20% traffic increase in downtown') {
        return {
            text: `<b>Analysis ready:</b> simulated downtown traffic increase request received.<br>This panel currently shows advisory output only and does not run a live traffic simulation.`,
        }
    }

    return null
}

async function executeNLCommand() {
    if (!nlCommand.value.trim() || nlProcessing.value) return
    nlProcessing.value = true
    nlResponse.value = ''
    try {
        const localResult = executeLocalQuickCommand(nlCommand.value)
        if (localResult) {
            nlResponse.value = localResult.text
            return
        }
        const result = await store.askAi(nlCommand.value)
        nlResponse.value = result?.text || `Could not get an AI response for "${nlCommand.value}". Please try again.`
    } catch (_) {
        nlResponse.value = `AI engine unavailable. Please try again.`
    } finally {
        nlProcessing.value = false
    }
}

function togglePeak(type) {
    if (type === 'reallocation') { peakReallocation.value = !peakReallocation.value; peakToast.value = peakReallocation.value ? 'Ready-order prioritization enabled for released jobs' : 'Ready-order prioritization disabled' }
    else if (type === 'shift') { shiftExtension.value = !shiftExtension.value; peakToast.value = shiftExtension.value ? 'Driver availability escalation activated' : 'Driver availability escalation disabled' }
    else if (type === 'vip') { vipLock.value = !vipLock.value; peakToast.value = vipLock.value ? 'Critical order priority lock enabled' : 'Critical order priority lock removed' }
    setTimeout(() => { peakToast.value = '' }, 3000)
}

const appliedSuggestions = ref(new Set())
const ignoredSuggestions = ref(new Set())

function applySuggestion(suggestion, actionLabel) {
    if (actionLabel === 'Ignore') {
        ignoredSuggestions.value.add(suggestion.id)
        return
    }
    appliedSuggestions.value.add(suggestion.id)
}

// Chart.js Demand Prediction — derived from real order data bucketed by scheduled delivery hour
const hourlyVolumes = computed(() => {
    const buckets = Array(24).fill(0)
    const allOrders = [...(store.pendingOrders || []), ...(store.activeOrders || [])]
    allOrders.forEach(o => {
        const dateStr = o.deadline || o.eta || o.lastUpdated
        if (dateStr && dateStr !== '—') {
            const h = new Date(dateStr).getHours()
            if (!isNaN(h)) buckets[h]++
        }
    })
    // If no timestamp data, use order counts spread across hours as a flat baseline
    if (!buckets.some(v => v > 0)) {
        const basePerHour = Math.ceil((store.pendingOrders?.length || 0) / 6)
        if (basePerHour > 0) return Array.from({ length: 24 }, (_, i) => (i >= new Date().getHours() && i < new Date().getHours() + 6 ? basePerHour : 0))
    }
    return buckets
})

const demandChartData = computed(() => {
    const currentHour = new Date().getHours()
    const vols = hourlyVolumes.value
    const next6h = Array.from({ length: 6 }, (_, i) => vols[(currentHour + i) % 24] || 0)
    const maxVal = Math.max(...next6h, 1)
    return {
        labels: ['Now', '+1h', '+2h', '+3h', '+4h', '+5h'],
        datasets: [{
            label: 'Predicted Orders',
            data: next6h,
            backgroundColor: next6h.map(v => v === maxVal && v > 0 ? 'rgba(239,68,68,0.75)' : 'rgba(59,130,246,0.5)'),
            borderColor: 'rgba(59,130,246,0.8)',
            borderWidth: 1,
            borderRadius: 6,
        }]
    }
})

const demandPeakHint = computed(() => {
    const currentHour = new Date().getHours()
    const vols = hourlyVolumes.value
    const next6h = Array.from({ length: 6 }, (_, i) => ({ offset: i, vol: vols[(currentHour + i) % 24] || 0 }))
    if (!next6h.some(v => v.vol > 0)) return null
    const peak = next6h.reduce((a, b) => a.vol > b.vol ? a : b)
    if (peak.vol === 0) return null
    const peakHour = (currentHour + peak.offset) % 24
    return `Peak expected at ${String(peakHour).padStart(2, '0')}:00 — ${peak.vol} order(s) predicted.`
})

const demandChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#111', titleColor: '#fff', bodyColor: '#ccc', padding: 10 } },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#6b7280', font: { size: 10 } } },
        y: { grid: { color: 'rgba(156,163,175,0.2)' }, ticks: { color: '#6b7280', font: { size: 10 } }, beginAtZero: true }
    }
}

// Chat
const chatMessages = ref([
    { id: 1, sender: 'ai', text: 'Hello! I\'m your AI Dispatch Agent. Ask me about released orders, best driver suggestions, no-driver exceptions, or dispatch delay risks.' }
])


let chatId = 2
async function sendChat() {
    if (!chatInput.value.trim()) return
    const userMsg = chatInput.value.trim()
    chatMessages.value.push({ id: chatId++, sender: 'user', text: userMsg })
    chatInput.value = ''
    chatTyping.value = true
    scrollChat()
    try {
        const result = await store.askAi(userMsg)
        const responseText = result?.text || 'No response from AI. Please try again.'
        chatMessages.value.push({ id: chatId++, sender: 'ai', text: responseText })
    } catch (_) {
        chatMessages.value.push({ id: chatId++, sender: 'ai', text: 'AI engine unavailable. Please try again.' })
    } finally {
        chatTyping.value = false
        scrollChat()
    }
}

function scrollChat() {
    nextTick(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    })
}

function handleChipsScroll(e) {
    if (e.deltaX !== 0) {
        e.currentTarget.scrollLeft += e.deltaX;
    } else if (e.deltaY !== 0) {
        e.currentTarget.scrollLeft += e.deltaY;
    }
}

// Suggestions generated dynamically from store data
const suggestions = computed(() => {
    const result = []
    const drivers = store.dispatcherDrivers
    const allOrders = [...(store.pendingOrders || []), ...(store.activeOrders || [])]
    const recurringRuleId = (order) => {
        const notes = String(order?.deliveryNotes || '')
        const match = notes.match(/RECURRING_RULE:([^|\n]+)/i)
        return match?.[1] || null
    }
    const isDirectDispatchAiCandidate = (order) => {
        const type = String(order?.type || '').toUpperCase()
        const substatus = String(order?.warehouseSubstatus || '').toUpperCase()
        const allowsDirectVehicleSelection = type === 'PARCEL_PICKUP' || type === 'SERVICE_MOVE' || type === 'VENDOR'
        return allowsDirectVehicleSelection
            && !order?.driverId
            && Number(order?.packingAmount || 0) === 0
            && ['AWAITING_INBOUND', 'AWAITING_PICK', 'QC_PASSED', 'READY_FOR_DISPATCH', 'DISPATCHED'].includes(substatus)
    }
    const readyOrders = (() => {
        const candidates = allOrders.filter(order => {
            const standardWarehouseCandidate = order.readyForDispatch && !order.driverId && !!order.vehicleId
            return standardWarehouseCandidate || isDirectDispatchAiCandidate(order)
        })
        const byRule = new Map()
        const deduped = []
        for (const order of candidates) {
            if (!isDirectDispatchAiCandidate(order)) {
                deduped.push(order)
                continue
            }
            const ruleId = recurringRuleId(order)
            if (!ruleId) {
                deduped.push(order)
                continue
            }
            const existing = byRule.get(ruleId)
            const orderTs = new Date(order.deadline || order.createdAt || 0).getTime() || Number.MAX_SAFE_INTEGER
            const existingTs = existing ? (new Date(existing.deadline || existing.createdAt || 0).getTime() || Number.MAX_SAFE_INTEGER) : Number.MAX_SAFE_INTEGER
            if (!existing || orderTs < existingTs) {
                byRule.set(ruleId, order)
            }
        }
        return [...deduped, ...byRule.values()]
    })()
    const freeDrivers = drivers.filter(driver =>
        driver.authorized
        && !driver.suspended
        && !driver.maintenance
        && (driver.activeOrders?.length || 0) === 0
    )

    if (readyOrders.length && freeDrivers.length) {
        const firstReady = readyOrders[0]
        const vehicleLabel = firstReady.vehicleId
            ? (firstReady.vehicle || 'assigned')
            : 'dispatcher vehicle selection'
        result.push({
            id: 'best-driver-match',
            title: 'Best Driver Suggestion Ready',
            color: 'text-primary',
            applied: false,
            message: `<strong>${firstReady.trackingCode || firstReady.id}</strong> is ready with <strong>${vehicleLabel}</strong>. <strong>${freeDrivers[0].name}</strong> is the best free driver to review first.`,
            explanation: 'The suggestion is based on driver availability, shift time remaining, and warehouse-fit signals from current dispatch data.',
            confidence: 94,
            actions: [
                { label: 'Queue Suggestion', class: 'bg-primary/30 hover:bg-primary/40 text-primary-900 dark:text-primary border border-primary/40 dark:border-primary/20' },
                { label: 'Review', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    if (readyOrders.length > freeDrivers.length) {
        result.push({
            id: 'driver-gap',
            title: 'Driver Gap Detected',
            color: 'text-orange-600 dark:text-orange-400',
            applied: false,
            message: `<strong>${readyOrders.length - freeDrivers.length}</strong> ready order(s) do not have enough free drivers available right now.`,
            explanation: 'Dispatcher attention is needed for escalation, reassignment, or release sequencing.',
            confidence: 92,
            actions: [
                { label: 'Review Gap', class: 'bg-orange-500/30 hover:bg-orange-500/40 text-orange-800 dark:text-orange-400 border border-orange-500/40 dark:border-orange-500/20' },
                { label: 'Ignore', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    const hosRisk = drivers.filter(d => d.breakDue)
    if (hosRisk.length) {
        result.push({
            id: 'hos-risk', title: 'Driver Shift Limit Risk', color: 'text-red-600 dark:text-red-400', applied: false,
            message: `<strong>${hosRisk.length}</strong> driver(s) are approaching their shift limit. New one-to-one assignments may be blocked soon.`,
            explanation: `Drivers: ${hosRisk.map(d => d.name).join(', ')}. Confirm a backup driver before assigning another released order.`,
            confidence: 95,
            actions: [
                { label: 'Review HOS', class: 'bg-red-500/30 hover:bg-red-500/40 text-red-800 dark:text-red-400 border border-red-500/40 dark:border-red-500/20' },
                { label: 'Ignore', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    return result
})

const mitigatedRoutes = ref(new Set())

const delayPredictions = computed(() => {
    const disruptions = store.disruptions || []
    const crises = store.activeCrises || []
    const items = []
    disruptions.forEach(d => {
        const sev = (d.severity || '').toLowerCase()
        const risk = sev === 'high' || sev === 'critical' ? 'High' : sev === 'medium' ? 'Medium' : 'Low'
        const baseProbability = risk === 'High' ? 78 : risk === 'Medium' ? 45 : 15
        const key = d.route || d.location || d.name || String(d.id)
        const mitigated = mitigatedRoutes.value.has(key)
        items.push({
            key,
            route: d.route || d.location || d.name || 'Affected Route',
            risk: mitigated ? (risk === 'High' ? 'Medium' : 'Low') : risk,
            probability: mitigated ? Math.max(5, baseProbability - 30) : baseProbability,
            reason: d.description || d.type || 'Disruption reported in this area',
            delay: risk === 'High' ? '30–45 min' : risk === 'Medium' ? '10–20 min' : '0–5 min',
            mitigated,
        })
    })
    crises.forEach(c => {
        const key = c.route || c.location || c.title || String(c.id)
        const mitigated = mitigatedRoutes.value.has(key)
        items.push({
            key,
            route: c.route || c.location || c.title || 'Crisis Route',
            risk: mitigated ? 'Medium' : 'High',
            probability: mitigated ? 55 : 85,
            reason: c.description || c.type || 'Active crisis — immediate attention needed',
            delay: mitigated ? '15–25 min' : '45+ min',
            mitigated,
        })
    })
    return items
})

function mitigateDelay(pred) {
    mitigatedRoutes.value = new Set([...mitigatedRoutes.value, pred.key])
}

provide(smartDispatcherPageKey, {
    appliedSuggestions,
    applySuggestion,
    chatChips,
    chatContainer,
    chatInput,
    chatMessages,
    chatTyping,
    delayPredictions,
    demandChartData,
    demandChartOptions,
    demandPeakHint,
    executeNLCommand,
    handleChipsScroll,
    ignoredSuggestions,
    mitigateDelay,
    nlCommand,
    nlProcessing,
    nlResponse,
    peakReallocation,
    peakToast,
    quickCommands,
    sendChat,
    shiftExtension,
    showChat,
    suggestions,
    togglePeak,
    vipLock,
})
</script>
