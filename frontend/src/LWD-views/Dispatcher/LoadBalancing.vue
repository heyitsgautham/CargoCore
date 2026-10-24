<template>
    <div class="space-y-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Smart Driver Assignment</h2>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    AI helps the dispatcher assign ready orders. For normal warehouse flow it suggests the best driver
                    for the locked vehicle, and for direct recurring/vendor non-packing moves it also recommends a vehicle.
                </p>
            </div>
            <div class="flex gap-2">
                <button @click="refreshPanel" :disabled="refreshing"
                    class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-bold text-blue-700 transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-300 dark:hover:bg-blue-500/20">
                    <span v-if="refreshing" class="material-symbols-outlined text-[18px] align-middle animate-spin">progress_activity</span>
                    <span v-else class="material-symbols-outlined text-[18px] align-middle">refresh</span>
                    {{ refreshing ? 'Refreshing...' : 'Refresh Readiness' }}
                </button>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-4 md:grid-cols-5">
            <div class="glass-panel rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ readyOrdersCount }}</div>
                <div class="mt-1 text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400">Ready Orders</div>
            </div>
            <div class="glass-panel rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ vehicleAssignedCount }}</div>
                <div class="mt-1 text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400">Vehicle Ready</div>
            </div>
            <div class="glass-panel rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ availableDrivers.length }}</div>
                <div class="mt-1 text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400">Drivers Free</div>
            </div>
            <div class="glass-panel rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ coverageScore }}%</div>
                <div class="mt-1 text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400">AI Coverage</div>
            </div>
            <div class="glass-panel rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ atRiskCount }}</div>
                <div class="mt-1 text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400">Needs Attention</div>
            </div>
        </div>

        <div v-if="readyOrdersCount > 0" class="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/20 dark:bg-amber-500/10">
            <span class="material-symbols-outlined text-amber-600 dark:text-amber-400">info</span>
            <div>
                <div class="text-sm font-bold text-amber-800 dark:text-amber-300">Dispatcher flow aligned to one order, one driver</div>
                <div class="text-xs text-amber-700 dark:text-amber-200">
                    This section checks ready orders that still need a driver. Direct recurring/vendor non-packing moves
                    are included even when the dispatcher still needs to choose the vehicle.
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div class="xl:col-span-2">
                <div class="glass-panel rounded-xl p-5">
                    <div class="mb-4 flex items-center justify-between">
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">Dispatch Readiness Queue</h3>
                            <p class="text-xs text-gray-500 dark:text-gray-400">Ready orders waiting for dispatcher AI review, including direct-dispatch recurring/vendor jobs.</p>
                        </div>
                        <div class="rounded-full bg-gray-100 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:bg-white/5 dark:text-gray-300">
                            {{ dispatchQueue.length }} items
                        </div>
                    </div>

                    <div v-if="dispatchQueue.length === 0" class="rounded-xl border border-dashed border-green-200 bg-green-50 p-8 text-center dark:border-green-500/20 dark:bg-green-500/10">
                        <span class="material-symbols-outlined mb-2 block text-[32px] text-green-600 dark:text-green-400">check_circle</span>
                        <div class="text-sm font-bold text-green-800 dark:text-green-300">No ready orders are waiting for AI assignment review</div>
                        <div class="mt-1 text-xs text-green-700 dark:text-green-200">Released warehouse jobs and direct recurring/vendor non-packing jobs will appear here when they are ready.</div>
                    </div>

                    <div v-else class="overflow-x-auto">
                        <table class="w-full min-w-[920px] text-left text-sm">
                            <thead class="bg-gray-50 text-[10px] uppercase tracking-wider text-gray-500 dark:bg-white/5 dark:text-gray-400">
                                <tr>
                                    <th class="p-3">Order</th>
                                    <th class="p-3">Warehouse Flow</th>
                                    <th class="p-3">Vehicle</th>
                                    <th class="p-3">AI Driver Match</th>
                                    <th class="p-3">Risk</th>
                                    <th class="p-3">Why AI Chose This</th>
                                    <th class="p-3">Action</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                                <tr v-for="item in dispatchQueue" :key="item.id" class="transition-colors hover:bg-gray-50 dark:hover:bg-white/5">
                                    <td class="p-3 align-top">
                                        <div class="font-bold text-gray-900 dark:text-white">{{ item.trackingCode || item.id }}</div>
                                        <div class="mt-1 flex items-center gap-2">
                                            <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="priorityBadgeClass(item.priority)">
                                                {{ item.priority || 'NORMAL' }}
                                            </span>
                                            <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ item.type || 'Standard Move' }}</span>
                                        </div>
                                        <div class="mt-2 text-[11px] text-gray-500 dark:text-gray-400">
                                            <div>Customer: <span class="text-gray-700 dark:text-gray-200">{{ item.customerName || 'Pending confirmation' }}</span></div>
                                            <div>Deadline: <span class="text-gray-700 dark:text-gray-200">{{ formatDeadline(item.deadline) }}</span></div>
                                        </div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <div class="text-xs font-medium text-gray-900 dark:text-white">{{ item.warehouse || 'Warehouse' }}</div>
                                        <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                                            <div>{{ isDirectDispatchAiCandidate(item) && !item.readyForDispatch ? 'Flow: Accepted by WM, dispatcher can plan now' : orderAllowsDirectVehicleSelection(item) ? 'Flow: Direct dispatcher vehicle selection' : 'Dock: Released by Warehouse Manager' }}</div>
                                            <div>Pickup: {{ Number(item.packingAmount || 0) > 0 ? 'Packing items ready' : 'Non-packing pickup ready' }}</div>
                                            <div>Destination: {{ item.deliveryAddr || 'Customer destination pending' }}</div>
                                        </div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <div class="text-xs font-bold" :class="item.vehicleId ? 'text-blue-700 dark:text-blue-300' : (item.recommendedVehicle ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-600 dark:text-red-400')">
                                            {{ item.vehicleId ? item.vehicle : item.recommendedVehicle?.label || 'No vehicle available' }}
                                        </div>
                                        <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                                            <div>{{ item.vehicleId ? 'Vehicle locked by warehouse' : orderAllowsDirectVehicleSelection(item) ? 'AI recommended for dispatcher selection' : 'Vehicle must be locked before dispatch' }}</div>
                                            <div>Vehicle type: {{ item.vehicleType || item.recommendedVehicle?.type || 'General cargo' }}</div>
                                            <div>Order weight: {{ item.weight || 0 }} kg</div>
                                        </div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <div v-if="item.recommendedDriver" class="space-y-1">
                                            <div class="font-bold text-gray-900 dark:text-white">{{ item.recommendedDriver.name }}</div>
                                            <div class="text-[11px] text-gray-500 dark:text-gray-400">
                                                <div>Status: {{ item.recommendedDriver.status }}</div>
                                                <div>Shift used: {{ item.recommendedDriver.hours }}h</div>
                                                <div>Load: {{ item.recommendedDriver.load }}%</div>
                                            </div>
                                        </div>
                                        <div v-else class="rounded-lg border border-red-200 bg-red-50 p-2 text-[11px] text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                                            No driver currently available
                                        </div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="riskBadgeClass(item.risk.level)">
                                            {{ item.risk.level }}
                                        </span>
                                        <div class="mt-2 text-[11px] text-gray-500 dark:text-gray-400">{{ item.risk.text }}</div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <div class="text-[11px] leading-5 text-gray-600 dark:text-gray-300">
                                            {{ item.recommendationReason }}
                                        </div>
                                    </td>
                                    <td class="p-3 align-top">
                                        <div v-if="deferredOrders.has(item.id)" class="flex flex-col gap-2">
                                            <div class="rounded-lg border border-gray-200 bg-gray-50 p-2 text-[11px] font-bold text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
                                                Deferred for later review
                                            </div>
                                            <button @click="resumeReview(item.id)"
                                                class="rounded-lg border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-primary/20">
                                                Resume Review
                                            </button>
                                        </div>
                                        <div v-else class="flex flex-col gap-2">
                                            <button @click="assignRecommendedDriver(item)"
                                                :disabled="!orderHasAssignableResources(item) || assigningOrderId === item.id"
                                                class="rounded-lg border border-primary/30 bg-primary/15 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-primary/25 disabled:cursor-not-allowed disabled:opacity-50">
                                                <span v-if="assigningOrderId === item.id">Assigning...</span>
                                                <span v-else-if="item.recommendedDriver && item.vehicleId">Assign {{ item.recommendedDriver.name }}</span>
                                                <span v-else-if="item.recommendedDriver && item.recommendedVehicle">Assign {{ item.recommendedDriver.name }} + {{ item.recommendedVehicle.label }}</span>
                                                <span v-else>No Resources Available</span>
                                            </button>
                                            <button @click="deferOrder(item.id)"
                                                class="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 transition-colors hover:bg-gray-50 dark:border-white/10 dark:bg-white/5 dark:text-gray-200 dark:hover:bg-white/10">
                                                Review Later
                                            </button>
                                            <div v-if="assignmentErrors[item.id]" class="text-[10px] font-bold text-red-600 dark:text-red-400">
                                                {{ assignmentErrors[item.id] }}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="space-y-4">
                <div class="glass-panel rounded-xl p-5">
                    <h3 class="mb-4 font-bold text-gray-900 dark:text-white">What AI Handles Here</h3>
                    <div class="space-y-3">
                        <div v-for="capability in aiCapabilities" :key="capability.title" class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-white/5 dark:bg-white/5">
                            <div class="flex items-start gap-3">
                                <span class="material-symbols-outlined text-primary">{{ capability.icon }}</span>
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ capability.title }}</div>
                                    <div class="mt-1 text-[11px] leading-5 text-gray-500 dark:text-gray-400">{{ capability.description }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="glass-panel rounded-xl p-5">
                    <h3 class="mb-4 font-bold text-gray-900 dark:text-white">Dispatch Watchlist</h3>
                    <div v-if="watchlist.length === 0" class="text-[11px] text-gray-500 dark:text-gray-400">
                        No driver-assignment risks are open right now.
                    </div>
                    <div v-else class="space-y-3">
                        <div v-for="item in watchlist" :key="item.id" class="rounded-xl border p-3"
                            :class="item.risk.level === 'High' ? 'border-red-200 bg-red-50 dark:border-red-500/20 dark:bg-red-500/10' : 'border-yellow-200 bg-yellow-50 dark:border-yellow-500/20 dark:bg-yellow-500/10'">
                            <div class="flex items-start justify-between gap-2">
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.trackingCode || item.id }}</div>
                                    <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">{{ item.risk.text }}</div>
                                </div>
                                <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="riskBadgeClass(item.risk.level)">
                                    {{ item.risk.level }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="glass-panel rounded-xl p-5">
                    <h3 class="mb-4 font-bold text-gray-900 dark:text-white">Gemini Dispatch Mode</h3>
                    <div class="space-y-3 text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                        <div class="rounded-xl border border-blue-200 bg-blue-50 p-3 dark:border-blue-500/20 dark:bg-blue-500/10">
                            <div class="font-bold text-blue-800 dark:text-blue-300">Rule engine stays in control</div>
                            <div class="mt-1">One driver gets one order. Standard warehouse jobs keep the warehouse vehicle lock, while direct recurring/vendor non-packing jobs let dispatcher confirm the AI vehicle suggestion.</div>
                        </div>
                        <div class="rounded-xl border border-primary/20 bg-primary/10 p-3">
                            <div class="font-bold text-gray-900 dark:text-white">Gemini assists with reasoning</div>
                            <div class="mt-1">Best driver suggestion, delay prediction, no-driver alerts, reassignment suggestions, and plain-language explanations.</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass-panel rounded-xl p-6">
            <h3 class="mb-4 font-bold text-gray-900 dark:text-white">AI Dispatch Assistant Policy</h3>
            <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                    <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">Rules</div>
                    <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                        Order must be accepted and ready. Standard warehouse flow requires a released vehicle lock. Direct recurring/vendor non-packing flow allows dispatcher vehicle selection with AI support.
                    </div>
                </div>
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                    <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">AI Support</div>
                    <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                        AI recommends the best available driver, predicts dispatch delay, flags missing resources, and explains why the recommendation fits the job.
                    </div>
                </div>
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                    <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">Dispatcher Decision</div>
                    <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                        Dispatcher reviews the AI suggestion, confirms the one-to-one assignment, and hands off the trip to the driver for pickup, transit, and unloading.
                    </div>
                </div>
            </div>
        </div>

        <Transition enter-active-class="transition ease-out duration-300" enter-from-class="translate-y-4 opacity-0" enter-to-class="translate-y-0 opacity-100" leave-active-class="transition ease-in duration-200" leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
            <div v-if="saveToast" class="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-bold text-black shadow-lg">
                <span class="material-symbols-outlined text-[18px]">check_circle</span>
                {{ saveToast }}
            </div>
        </Transition>

    </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'

const store = useDispatcherStore()

onMounted(() => {
    store.initialize().catch(() => {})
    hydrateUiState()
})

const refreshing = ref(false)
const saveToast = ref('')
const deferredOrders = ref(new Set())
const assigningOrderId = ref(null)
const assignmentErrors = ref({})

const UI_STATE_KEY = 'cc_dispatcher_smart_assignment_state'

function persistUiState() {
    if (typeof window === 'undefined') return
    const snapshot = {
        deferredOrders: [...deferredOrders.value],
    }
    localStorage.setItem(UI_STATE_KEY, JSON.stringify(snapshot))
}

function hydrateUiState() {
    if (typeof window === 'undefined') return
    try {
        const raw = localStorage.getItem(UI_STATE_KEY)
        if (!raw) return
        const parsed = JSON.parse(raw)
        deferredOrders.value = new Set(parsed.deferredOrders || [])
    } catch (_) {
        localStorage.removeItem(UI_STATE_KEY)
    }
}

const aiCapabilities = [
    {
        icon: 'person_search',
        title: 'Best Driver Suggestion',
        description: 'Ranks the best free driver for released warehouse jobs and direct recurring/vendor non-packing jobs.',
    },
    {
        icon: 'schedule',
        title: 'Dispatch Delay Prediction',
        description: 'Warns the dispatcher when a ready order may miss its planned release or delivery window.',
    },
    {
        icon: 'warning',
        title: 'Exception Alerts',
        description: 'Flags cases like no driver available, no direct-dispatch vehicle free, shift nearly over, or route risk rising.',
    },
    {
        icon: 'swap_horiz',
        title: 'Reassignment Recommendation',
        description: 'If the first driver is unavailable or delayed, AI suggests the next best driver and preserves the right vehicle path for the job.',
    },
    {
        icon: 'help',
        title: 'Why This Driver?',
        description: 'Explains the recommendation in simple language so the dispatcher can trust and review the assignment quickly.',
    },
]

const allOrders = computed(() => {
    const unique = new Map()
    ;[...(store.pendingOrders || []), ...(store.activeOrders || [])].forEach((order) => {
        if (order?.id) unique.set(String(order.id), order)
    })
    return [...unique.values()]
})

function normalizeDriverAvailabilityStatus(status) {
    return String(status || '')
        .trim()
        .toLowerCase()
        .replace(/[_\s]+/g, '-')
}

function isDriverAssignableStatus(status) {
    const normalized = normalizeDriverAvailabilityStatus(status)
    return ['active', 'idle', 'available', 'on-duty', 'online', 'on-route', 'standby', 'stand-by', 'on-break'].includes(normalized)
}

function hasOpenAssignments(driver) {
    return (driver.activeOrders || []).some((order) => {
        const status = String(order?.status || '').toUpperCase()
        return !['DELIVERED', 'COMPLETED', 'CANCELLED', 'CLOSED'].includes(status)
    })
}

const availableDrivers = computed(() =>
    (store.dispatcherDrivers || []).filter((driver) => {
        return driver.authorized
            && !driver.suspended
            && !driver.maintenance
            && isDriverAssignableStatus(driver.status)
            && !hasOpenAssignments(driver)
    })
)

function priorityWeight(priority) {
    const normalized = String(priority || '').toUpperCase()
    if (normalized === 'CRITICAL' || normalized === 'URGENT') return 4
    if (normalized === 'VIP') return 3
    if (normalized === 'HIGH') return 2
    if (normalized === 'MEDIUM') return 1
    return 0
}

function safeTimestamp(value) {
    if (!value || value === '—') return Number.MAX_SAFE_INTEGER
    const ts = new Date(value).getTime()
    return Number.isNaN(ts) ? Number.MAX_SAFE_INTEGER : ts
}

function formatDeadline(value) {
    if (!value || value === '—') return 'Not scheduled'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return String(value)
    return parsed.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    })
}

function hoursUntil(value) {
    if (!value || value === '—') return null
    const parsed = new Date(value).getTime()
    if (Number.isNaN(parsed)) return null
    return (parsed - Date.now()) / 3_600_000
}

function orderAllowsDirectVehicleSelection(order) {
    const type = String(order?.type || '').toUpperCase()
    return type === 'PARCEL_PICKUP' || type === 'SERVICE_MOVE' || type === 'VENDOR'
}

function recurringRuleId(order) {
    const notes = String(order?.deliveryNotes || '')
    const match = notes.match(/RECURRING_RULE:([^|\n]+)/i)
    return match?.[1] || null
}

function isDirectDispatchAiCandidate(order) {
    const substatus = String(order?.warehouseSubstatus || '').toUpperCase()
    return orderAllowsDirectVehicleSelection(order)
        && !order?.driverId
        && Number(order?.packingAmount || 0) === 0
        && ['AWAITING_INBOUND', 'AWAITING_PICK', 'QC_PASSED', 'READY_FOR_DISPATCH', 'DISPATCHED'].includes(substatus)
}

function dedupeRecurringDirectCandidates(orders) {
    const byRule = new Map()
    const passthrough = []

    for (const order of orders) {
        if (!isDirectDispatchAiCandidate(order)) {
            passthrough.push(order)
            continue
        }

        const ruleId = recurringRuleId(order)
        if (!ruleId) {
            passthrough.push(order)
            continue
        }

        const existing = byRule.get(ruleId)
        const orderTs = safeTimestamp(order.deadline || order.createdAt)
        const existingTs = existing ? safeTimestamp(existing.deadline || existing.createdAt) : Number.MAX_SAFE_INTEGER
        if (!existing || orderTs < existingTs) {
            byRule.set(ruleId, order)
        }
    }

    return [...passthrough, ...byRule.values()]
}

function normalizeVehicleAvailabilityStatus(status) {
    return String(status || '')
        .trim()
        .toLowerCase()
        .replace(/[_\s]+/g, '-')
}

function isVehicleDispatchableStatus(status) {
    const normalized = normalizeVehicleAvailabilityStatus(status)
    return ['active', 'idle', 'available', 'standby', 'ready'].includes(normalized)
}

function hasVehicleOpenAssignments(vehicleId) {
    if (!vehicleId) return false
    return (store.activeOrders || []).some((order) => {
        const status = String(order?.status || '').toUpperCase()
        return String(order?.vehicleId || '') === String(vehicleId)
            && ['ASSIGNED', 'IN_TRANSIT'].includes(status)
    })
}

const availableVehicles = computed(() =>
    (store.filteredVehicles || []).filter((vehicle) =>
        isVehicleDispatchableStatus(vehicle.status)
        && !hasVehicleOpenAssignments(vehicle.id)
    )
)

function scoreDriver(driver, order) {
    let score = 40
    const orderWarehouseId = order.warehouseId ? String(order.warehouseId) : ''
    const driverHubId = driver.hubId ? String(driver.hubId) : ''
    const locationText = `${driver.location || ''} ${driver.currentJob || ''}`.toLowerCase()
    const warehouseText = `${order.warehouse || ''} ${order.hub || ''}`.toLowerCase().trim()

    if (orderWarehouseId && driverHubId && orderWarehouseId === driverHubId) score += 30
    if (warehouseText && locationText && locationText.includes(warehouseText.split(/\s+/)[0])) score += 12
    if ((driver.load || 0) === 0) score += 14
    else score += Math.max(0, 12 - Math.round((driver.load || 0) / 8))

    if ((driver.hours || 0) < 3) score += 10
    else if ((driver.hours || 0) < 6) score += 6
    else score -= 4

    if (driver.breakDue) score -= 18
    score += Math.min(12, Math.round((driver.efficiency || 0) / 8))

    if (priorityWeight(order.priority) >= 3) score += 4

    return score
}

function scoreVehicle(vehicle, order) {
    let score = 30
    const vehicleType = String(vehicle?.type || '').trim().toLowerCase()
    const orderVehicleType = String(order?.vehicleType || '').trim().toLowerCase()

    if (vehicleType && orderVehicleType && vehicleType === orderVehicleType) score += 35
    else if (!orderVehicleType) score += 10

    const orderWeightTons = Number(order?.weight || 0) / 1000
    const capacityTons = Number(vehicle?.cargoCapacityTons || 0)
    if (capacityTons > 0 && orderWeightTons > 0) {
        if (capacityTons >= orderWeightTons) score += 18
        else score -= 25
    }

    if (priorityWeight(order.priority) >= 3) score += 6
    return score
}

function buildDriverReasons(driver, order) {
    const reasons = []
    if (order.warehouseId && driver.hubId && String(order.warehouseId) === String(driver.hubId)) {
        reasons.push('same warehouse coverage')
    }
    if ((driver.activeOrders?.length || 0) === 0) {
        reasons.push('no active order assigned')
    }
    if ((driver.hours || 0) < 4) {
        reasons.push('healthy shift time remaining')
    }
    if ((driver.efficiency || 0) >= 70) {
        reasons.push('strong recent dispatch efficiency')
    }
    if (reasons.length === 0) reasons.push('best available dispatcher match')
    return reasons.slice(0, 3)
}

function buildVehicleReasons(vehicle, order) {
    const reasons = []
    const vehicleType = String(vehicle?.type || '').trim().toLowerCase()
    const orderVehicleType = String(order?.vehicleType || '').trim().toLowerCase()

    if (vehicleType && orderVehicleType && vehicleType === orderVehicleType) {
        reasons.push('matching vehicle type')
    }
    if (vehicle?.cargoCapacityTons) {
        reasons.push(`capacity ${vehicle.cargoCapacityTons}t available`)
    }
    if (reasons.length === 0) reasons.push('best available vehicle fit')
    return reasons.slice(0, 2)
}

function getDriverRecommendation(order, driverPool = availableDrivers.value) {
    if (!driverPool.length) return null
    const ranked = driverPool
        .map((driver) => ({
            driver,
            score: scoreDriver(driver, order),
            reasons: buildDriverReasons(driver, order),
        }))
        .sort((a, b) => b.score - a.score)
    return ranked[0] || null
}

function getVehicleRecommendation(order, vehiclePool = availableVehicles.value) {
    if (!orderAllowsDirectVehicleSelection(order) || order.vehicleId || !vehiclePool.length) return null
    const ranked = vehiclePool
        .map((vehicle) => ({
            vehicle,
            score: scoreVehicle(vehicle, order),
            reasons: buildVehicleReasons(vehicle, order),
        }))
        .sort((a, b) => b.score - a.score)
    return ranked[0] || null
}

function buildRisk(order, recommendation, vehicleRecommendation) {
    const deadlineHours = hoursUntil(order.deadline || order.eta)
    if (isDirectDispatchAiCandidate(order) && !order.readyForDispatch) {
        if (!vehicleRecommendation) {
            return {
                level: 'High',
                text: 'Accepted direct-dispatch order is waiting in dispatcher review, but no free vehicle is available yet.',
            }
        }
        if (!recommendation) {
            return {
                level: 'High',
                text: 'Accepted direct-dispatch order has a vehicle path, but no free driver is available yet.',
            }
        }
        return {
            level: 'Low',
            text: 'Accepted direct-dispatch order is ready for AI planning before warehouse release.',
        }
    }
    if (orderAllowsDirectVehicleSelection(order) && !order.vehicleId && !vehicleRecommendation) {
        return {
            level: 'High',
            text: 'Direct-dispatch order is ready, but no dispatcher-selectable vehicle is free right now.',
        }
    }
    if (!recommendation) {
        return {
            level: 'High',
            text: orderAllowsDirectVehicleSelection(order) && !order.vehicleId
                ? 'AI found a vehicle path, but no free driver is currently available for this direct-dispatch order.'
                : 'Vehicle assigned but no free driver is currently available for this released order.',
        }
    }
    if (deadlineHours !== null && deadlineHours <= 2) {
        return {
            level: 'High',
            text: 'Dispatch window is close. Confirm the driver quickly to avoid delay.',
        }
    }
    if (recommendation.driver.breakDue || (recommendation.driver.hours || 0) >= 8) {
        return {
            level: 'Medium',
            text: 'Recommended driver is nearing shift limit. Review before confirming.',
        }
    }
    if (priorityWeight(order.priority) >= 3) {
        return {
            level: 'Medium',
            text: 'Priority order. Confirm driver and release paperwork without delay.',
        }
    }
    return {
        level: 'Low',
        text: 'Ready for assignment with low operational risk.',
    }
}

function orderHasAssignableResources(item) {
    if (!item?.recommendedDriver) return false
    if (item.vehicleId) return true
    return !!item.recommendedVehicle
}

const dispatchQueue = computed(() => {
    const candidateOrders = dedupeRecurringDirectCandidates(
        allOrders.value.filter((order) => {
            const standardWarehouseCandidate = order.readyForDispatch && !!order.vehicleId && !order.driverId
            return standardWarehouseCandidate || isDirectDispatchAiCandidate(order)
        })
    ).sort((a, b) => {
        const byPriority = priorityWeight(b.priority) - priorityWeight(a.priority)
        if (byPriority !== 0) return byPriority
        return safeTimestamp(a.createdAt || a.deadline) - safeTimestamp(b.createdAt || b.deadline)
    })

    const remainingDrivers = [...availableDrivers.value]
    const remainingVehicles = [...availableVehicles.value]

    return candidateOrders.map((order) => {
        const recommendation = getDriverRecommendation(order, remainingDrivers)
        const vehicleRecommendation = getVehicleRecommendation(order, remainingVehicles)
        const risk = buildRisk(order, recommendation, vehicleRecommendation)
        const vehicleReasons = vehicleRecommendation?.reasons || []

        if (recommendation?.driver?.id) {
            const nextDriverIdx = remainingDrivers.findIndex((driver) => String(driver.id) === String(recommendation.driver.id))
            if (nextDriverIdx !== -1) remainingDrivers.splice(nextDriverIdx, 1)
        }

        if (!order.vehicleId && vehicleRecommendation?.vehicle?.id) {
            const nextVehicleIdx = remainingVehicles.findIndex((vehicle) => String(vehicle.id) === String(vehicleRecommendation.vehicle.id))
            if (nextVehicleIdx !== -1) remainingVehicles.splice(nextVehicleIdx, 1)
        }

        return {
            ...order,
            recommendedDriver: recommendation?.driver || null,
            recommendedVehicle: vehicleRecommendation
                ? {
                    id: vehicleRecommendation.vehicle.id,
                    label: vehicleRecommendation.vehicle.licensePlate || vehicleRecommendation.vehicle.code || vehicleRecommendation.vehicle.model || 'Vehicle',
                    type: vehicleRecommendation.vehicle.type || '',
                }
                : null,
            recommendationReason: recommendation
                ? [
                    recommendation.reasons.join(', '),
                    !order.vehicleId && vehicleReasons.length ? `vehicle: ${vehicleReasons.join(', ')}` : '',
                ].filter(Boolean).join(' • ')
                : 'No eligible driver is free right now. AI recommends dispatcher follow-up or reassignment review.',
            risk,
        }
    })
})

const readyOrdersCount = computed(() => dispatchQueue.value.length)
const vehicleAssignedCount = computed(() => dispatchQueue.value.filter((item) => item.vehicleId || item.recommendedVehicle).length)
const atRiskCount = computed(() => dispatchQueue.value.filter((item) => item.risk.level !== 'Low').length)
const coverageScore = computed(() => {
    if (!dispatchQueue.value.length) return 100
    const matched = dispatchQueue.value.filter((item) => orderHasAssignableResources(item)).length
    return Math.round((matched / dispatchQueue.value.length) * 100)
})
const watchlist = computed(() => dispatchQueue.value.filter((item) => item.risk.level !== 'Low').slice(0, 4))

function riskBadgeClass(level) {
    if (level === 'High') return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300'
    if (level === 'Medium') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300'
    return 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300'
}

function priorityBadgeClass(priority) {
    const normalized = String(priority || '').toUpperCase()
    if (normalized === 'CRITICAL' || normalized === 'URGENT') return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300'
    if (normalized === 'VIP') return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300'
    if (normalized === 'HIGH') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300'
    return 'bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-300'
}

async function refreshPanel() {
    refreshing.value = true
    try {
        await Promise.all([
            store.fetchOrders(),
            store.fetchActiveOrders(),
            store.fetchDrivers(),
            store.fetchVehicles(),
        ])
        saveToast.value = 'Dispatcher readiness refreshed.'
    } finally {
        refreshing.value = false
        setTimeout(() => { saveToast.value = '' }, 2500)
    }
}

async function assignRecommendedDriver(item) {
    if (!item?.recommendedDriver || assigningOrderId.value === item.id) return

    assigningOrderId.value = item.id
    assignmentErrors.value = {
        ...assignmentErrors.value,
        [item.id]: '',
    }

    try {
        const resolvedVehicleId = item.vehicleId || item.recommendedVehicle?.id || null
        if (!resolvedVehicleId) {
            assignmentErrors.value = {
                ...assignmentErrors.value,
                [item.id]: 'No available vehicle found for this direct-dispatch order.',
            }
            return
        }

        const ok = await store.assignOrder(item.id, item.recommendedDriver.id, resolvedVehicleId)
        if (!ok) {
            assignmentErrors.value = {
                ...assignmentErrors.value,
                [item.id]: 'Failed to assign driver. Please try again.',
            }
            return
        }

        if (deferredOrders.value.has(item.id)) {
            const nextDeferred = new Set(deferredOrders.value)
            nextDeferred.delete(item.id)
            deferredOrders.value = nextDeferred
            persistUiState()
        }

        const vehicleLabel = item.vehicleId ? item.vehicle : item.recommendedVehicle?.label
        saveToast.value = `${item.recommendedDriver.name}${vehicleLabel ? ` + ${vehicleLabel}` : ''} assigned to ${item.trackingCode || item.id}.`
        setTimeout(() => { saveToast.value = '' }, 3000)
    } finally {
        assigningOrderId.value = null
    }
}

function deferOrder(orderId) {
    const nextDeferred = new Set(deferredOrders.value)
    nextDeferred.add(orderId)
    deferredOrders.value = nextDeferred
    persistUiState()
}

function resumeReview(orderId) {
    const nextDeferred = new Set(deferredOrders.value)
    nextDeferred.delete(orderId)
    deferredOrders.value = nextDeferred
    persistUiState()
}
</script>
