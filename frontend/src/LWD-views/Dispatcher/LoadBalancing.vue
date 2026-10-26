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
                <DispatchQueueBoard />
            </div>

            <div class="space-y-4">
                <AssignmentSidePanel />
            </div>
        </div>

        <AssistantPolicy />

        <Transition enter-active-class="transition ease-out duration-300" enter-from-class="translate-y-4 opacity-0" enter-to-class="translate-y-0 opacity-100" leave-active-class="transition ease-in duration-200" leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
            <div v-if="saveToast" class="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-bold text-black shadow-lg">
                <span class="material-symbols-outlined text-[18px]">check_circle</span>
                {{ saveToast }}
            </div>
        </Transition>

    </div>
</template>

<script setup>
import DispatchQueueBoard from './smartAssignment/DispatchQueueBoard.vue'
import AssignmentSidePanel from './smartAssignment/AssignmentSidePanel.vue'
import AssistantPolicy from './smartAssignment/AssistantPolicy.vue'
import { smartAssignmentPageKey } from './smartAssignment/smartAssignmentPageContext'
import { computed, onMounted, ref, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import {
    dedupeRecurringDirectCandidates,
    driverHasOpenAssignments,
    isDirectDispatchAiCandidate,
    isDriverAssignableStatus,
    isVehicleDispatchableStatus,
    priorityWeight,
    safeTimestamp,
    vehicleHasOpenAssignments,
} from './dispatchRules'
import {
    buildRisk,
    orderHasAssignableResources,
    topDriverMatch,
    topVehicleMatch,
} from './smartAssignment/assignmentRules'

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

const availableDrivers = computed(() =>
    (store.dispatcherDrivers || []).filter((driver) => {
        return driver.authorized
            && !driver.suspended
            && !driver.maintenance
            && isDriverAssignableStatus(driver.status)
            && !driverHasOpenAssignments(driver)
    })
)

const availableVehicles = computed(() =>
    (store.filteredVehicles || []).filter((vehicle) =>
        isVehicleDispatchableStatus(vehicle.status)
        && !vehicleHasOpenAssignments(vehicle.id, store.activeOrders)
    )
)

function getDriverRecommendation(order, driverPool = availableDrivers.value) {
    return topDriverMatch(order, driverPool)
}

function getVehicleRecommendation(order, vehiclePool = availableVehicles.value) {
    return topVehicleMatch(order, vehiclePool)
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

provide(smartAssignmentPageKey, {
    aiCapabilities,
    assignRecommendedDriver,
    assigningOrderId,
    assignmentErrors,
    deferOrder,
    deferredOrders,
    dispatchQueue,
    priorityBadgeClass,
    resumeReview,
    riskBadgeClass,
    watchlist,
})
</script>
