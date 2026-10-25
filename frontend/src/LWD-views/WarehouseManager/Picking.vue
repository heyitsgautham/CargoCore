<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Picking & Packing</h2>
            <div class="flex flex-wrap gap-2">
                <div
                    class="px-4 py-2 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white text-sm">
                    Active Pickers: <span class="text-green-600 dark:text-green-400 font-bold">{{ activePickers }}</span>
                </div>
                <div v-if="autoRefreshEnabled"
                    class="px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-600 dark:text-green-400 text-xs flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    Live {{ autoRefreshCountdown }}s
                </div>
                <button @click="toggleAutoRefresh"
                    class="px-3 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1"
                    :class="autoRefreshEnabled ? 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400' : 'bg-primary/20 text-primary'">
                    <span class="material-symbols-outlined text-[14px]">{{ autoRefreshEnabled ? 'pause' : 'play_arrow' }}</span>
                    {{ autoRefreshEnabled ? 'Pause' : 'Auto' }}
                </button>
                <button @click="openMasterPickList"
                    class="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[18px]">checklist</span>
                    Pick List
                </button>
                <button @click="refreshData"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[18px]">refresh</span>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Search & Filter Bar -->
        <PickingFilterBar v-model:search="searchQuery" v-model:priority="priorityFilter" :status-filters="statusFilters"
            :active-status-filters="activeStatusFilters" :has-active-filters="hasActiveFilters"
            @toggle-status="toggleStatusFilter" @clear="clearFilters" />

        <!-- Undo Toast -->
        <PickingUndoToast :undo-action="undoAction" @undo="performUndo" @dismiss="dismissUndo" />

        <!-- Prerequisite Warnings -->
        <PrerequisiteWarnings :warnings="prerequisiteWarnings" />

        <!-- Order Fulfillment Pipeline -->
        <PickingPipeline :pipeline-steps="pipelineSteps" :pipeline-loading="pipelineLoading" />

        <!-- Dispatcher-Assigned Direct Transport Notifications -->
        <DispatcherNotices :orders="dispatcherAssignedOrders" @dismiss="dismissDispatcherOrder" />

        <!-- Active Pick Waves - Clean Tab Layout -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <!-- Header with Status Tabs -->
            <div class="border-b border-gray-100 dark:border-white/5">
                <div class="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Active Pick Waves</h3>
                    <div class="text-xs text-gray-500">
                        {{ filteredWaves.length }} orders
                        <span v-if="hasActiveFilters" class="text-primary">(filtered)</span>
                    </div>
                </div>

                <!-- Status Tabs -->
                <PickWaveTabs v-model="selectedStatusTab" :total-count="waves.length" :waves-by-status="wavesByStatus" />
            </div>

            <!-- Loading -->
            <div v-if="loading" class="p-8 text-center">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                <div class="mt-2 text-xs text-gray-500">Loading pick waves...</div>
            </div>

            <!-- Orders Grid -->
            <div v-else class="p-4">
                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    <PickWaveCard v-for="wave in filteredWavesByTab" :key="wave.id" :wave="wave"
                        :start-blocked="isStartPickingBlocked(wave)" :action-pending="isWaveActionPending(wave)"
                        @open="openPickList" @assign-labourers="openAssignLabourers" @action="handleWaveAction"
                        @undo="undoWaveStatus" />
                </div>

                <!-- Empty State -->
                <div v-if="filteredWavesByTab.length === 0" class="text-center py-12 text-gray-500">
                    <span class="material-symbols-outlined text-5xl mb-3 opacity-30">inventory_2</span>
                    <p class="font-medium">No orders in this category</p>
                    <p class="text-xs mt-1 text-gray-400">Orders will appear here when they match this status</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

            <!-- Packing Station View + Quality Check -->
            <div class="space-y-6">
                <PackingStationsPanel :stations="stations" :show-station-monitor="showStationMonitor" :monitored-station="monitoredStation" @monitor="monitorStation" />

                <!-- Quality Check Panel -->
                <QualityCheckPanel :quality-checks="qualityChecks" :check-fields="checkFields" @toggle-check="toggleCheck" @dispatch="triggerDispatch" />
            </div>
        </div>

        <!-- Dispatch Toast -->
        <div v-if="dispatchToast"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl shadow-green-500/30 flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div>
                <div class="font-bold">{{ dispatchToast }}</div>
                <div class="text-xs opacity-80">Notification sent to Dispatcher</div>
            </div>
        </div>
        <div v-if="actionToast"
            class="fixed bottom-6 left-6 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce max-w-md"
            :class="actionToast.startsWith('⚠') ? 'bg-amber-500/95 shadow-amber-500/30' : 'bg-blue-500/90 shadow-blue-500/30'">
            <span class="material-symbols-outlined shrink-0">{{ actionToast.startsWith('⚠') ? 'warning' : 'inventory' }}</span>
            <div class="font-bold text-sm leading-tight">{{ actionToast }}</div>
        </div>

        <!-- Pick List Modal -->
        <PickListModal :show="showPickListModal" :wave="selectedWave" :items="pickListItems" :loading="pickListLoading"
            :action-disabled="pickListActionDisabled" @close="showPickListModal = false" @scan-item="requestItemScan"
            @pick-item="toggleItemPicked" @print="printPickList" @complete="completePickList" />

        <!-- Multi-Labourer Assignment Modal (for orders requiring multiple labourers) -->
        <AssignLabourersModal :show="showMultiLabourerModal" :wave="multiLabourerWave" :loading="labourersLoading"
            :assigning="assigningPicker" :available="availableLabourersForMulti" :selected="selectedLabourers"
            @close="showMultiLabourerModal = false" @toggle="toggleLabourerSelection" @assign="assignMultipleLabourers" />

        <!-- Packing Station Live Monitor Modal -->
        <StationMonitorModal :show-station-monitor="showStationMonitor" :monitored-station="monitoredStation" @close="closeStationMonitor" @refresh="refreshStationData" />
    </div>
</template>

<script setup>
import StationMonitorModal from './picking/StationMonitorModal.vue'
import PickingPipeline from './picking/PickingPipeline.vue'
import PackingStationsPanel from './picking/PackingStationsPanel.vue'
import QualityCheckPanel from './picking/QualityCheckPanel.vue'
import PickingFilterBar from './picking/PickingFilterBar.vue'
import PickingUndoToast from './picking/PickingUndoToast.vue'
import DispatcherNotices from './picking/DispatcherNotices.vue'
import PickWaveTabs from './picking/PickWaveTabs.vue'
import PickWaveCard from './picking/PickWaveCard.vue'
import PickListModal from './picking/PickListModal.vue'
import AssignLabourersModal from './picking/AssignLabourersModal.vue'
import PrerequisiteWarnings from './picking/PrerequisiteWarnings.vue'
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { isHouseShift } from './picking/pickingFormat'
import {
    buildOrderAssignments,
    buildPickWaves,
    buildQualityChecks,
    classifyPickingOrders,
    filterWaves,
    groupWavesByStatus,
    pipelineCounts,
    prerequisiteWarnings as listPrerequisiteWarnings,
    toDispatcherNotice,
    wavesForTab,
} from './picking/pickingBoard'
import * as api from './picking/pickingApi'
import { usePickingUndo } from './picking/usePickingUndo'
import { usePickList } from './picking/usePickList'
import { useLabourerAssignment } from './picking/useLabourerAssignment'
import { useQualityDispatch } from './picking/useQualityDispatch'
import { useWaveActions } from './picking/useWaveActions'

const { openSlipWithData } = useSlipPrinter()

const authStore = useAuthStore()
const openScanner = inject('openScanner', null)
const lastGlobalScan = inject('lastGlobalScan', ref(null))
const dispatchToast = ref('')
const actionToast = ref('')
const loading = ref(false)
const pipelineLoading = ref(false)
// Prerequisite checks — null = not yet checked, 0 = empty/missing, >0 = ok
const inventoryCount = ref(null)
const floorPlanConfigured = ref(null) // null=checking, false=not set up, true=ok
const labourers = ref([])

// Search & Filter state
const searchQuery = ref('')
const activeStatusFilters = ref([])
const priorityFilter = ref('')
const statusFilters = [
    { label: 'Awaiting', value: 'AWAITING_PICK' },
    { label: 'Picking', value: 'PICKING' },
    { label: 'Picked', value: 'PICKED' },
    { label: 'Packing', value: 'PACKING' },
]

const {
    enabled: autoRefreshEnabled,
    countdown: autoRefreshCountdown,
    start: startAutoRefresh,
    stop: stopAutoRefresh,
    toggle: toggleAutoRefresh,
} = useAutoRefresh(() => fetchPickingData(), { seconds: 30, isBusy: () => loading.value })

// Undo state

// Pick list modal state


const selectedStatusTab = ref('ALL') // ALL, ON_HOLD, AWAITING_PICK, PICKING, PICKED, PACKING

// Station monitor state
const showStationMonitor = ref(false)
const monitoredStation = ref(null)

const checkFields = [
    { key: 'goodsCorrect', label: 'Correct goods' },
    { key: 'countCorrect', label: 'Correct count' },
    { key: 'packagingOk', label: 'Packaging verified' },
    { key: 'laborConfirmed', label: 'Labor assigned' },
    { key: 'weightOk', label: 'Weight verified' },
    { key: 'labelAttached', label: 'Shipping label attached' },
]

// Dynamic data
const waves = ref([])
const qualityChecks = ref([])
// Dispatcher-assigned direct transport orders — shown as notification banners, not picking cards
const dispatcherAssignedOrders = ref([])
const dismissedDispatcherOrders = ref(new Set())
const pipelineSteps = ref([
    { label: 'Accepted', icon: 'task_alt', active: true, count: 0 },
    { label: 'Picking', icon: 'shopping_basket', active: false, count: 0 },
    { label: 'Packing', icon: 'package_2', active: false, count: 0 },
    { label: 'Quality Check', icon: 'verified', active: false, count: 0 },
    { label: 'Ready for Dispatch', icon: 'local_shipping', active: false, count: 0 },
])

// Packing stations - fetched from API
const stations = ref([])

// Track assigned labourers per order
const orderAssignments = ref({})

const context = { token, getWarehouseId, flashAction, refresh: () => fetchPickingData() }

const { undoAction, undoHistory, saveUndoState, performUndo, dismissUndo, undoWaveStatus, clearUndoTimer } =
    usePickingUndo(context)

const {
    showPickListModal,
    selectedWave,
    pickListItems,
    pickListLoading,
    pickListActionDisabled,
    requestItemScan,
    openPickList,
    toggleItemPicked,
    printPickList,
    completePickList,
} = usePickList({ ...context, openScanner, lastGlobalScan, runWaveAction: (wave) => handleWaveAction(wave) })

const {
    labourersLoading,
    assigningPicker,
    showMultiLabourerModal,
    multiLabourerWave,
    selectedLabourers,
    availableLabourersForMulti,
    openAssignLabourers,
    toggleLabourerSelection,
    assignMultipleLabourers,
} = useLabourerAssignment({ ...context, labourers, fetchLabourers, actionToast })

const { toggleCheck, triggerDispatch } = useQualityDispatch({ ...context, dispatchToast, pipelineSteps })

const { isWaveActionPending, handleWaveAction } = useWaveActions({
    ...context,
    actionToast,
    inventoryCount,
    floorPlanConfigured,
    labourers,
    orderAssignments,
    saveUndoState,
})

const filteredWaves = computed(() => filterWaves(waves.value, {
    search: searchQuery.value,
    statuses: activeStatusFilters.value,
    priority: priorityFilter.value,
}))

const hasActiveFilters = computed(() => Boolean(searchQuery.value.trim() || activeStatusFilters.value.length > 0 || priorityFilter.value))

// Waves grouped by status for Kanban board
const wavesByStatus = computed(() => groupWavesByStatus(waves.value))

// Available labourers for multi-selection modal

// Filtered waves based on selected tab
const filteredWavesByTab = computed(() => wavesForTab(wavesByStatus.value, selectedStatusTab.value))

// Active pickers: count real labourers currently attached to picking/packing orders
const activePickers = computed(() => labourers.value.filter(labourer =>
    labourer.is_active && ['PICKING', 'PACKING'].includes(labourer.assigned_order_substatus)
).length)

const prerequisiteWarnings = computed(() => listPrerequisiteWarnings({
    hasHouseShiftOrders: waves.value.some(w => isHouseShift(w)),
    inventoryCount: inventoryCount.value,
    floorPlanConfigured: floorPlanConfigured.value,
    labourerCount: labourers.value.length,
}))

function isStartPickingBlocked(wave) {
    if (wave.status !== 'AWAITING_PICK' && wave.status !== 'CONFIRMED') return false
    if (isHouseShift(wave)) {
        return inventoryCount.value === 0 || floorPlanConfigured.value === false || labourers.value.length === 0
    }
    // Small package / parcel — no inventory, floor plan, or labour required
    return false
}


function token() {
    return authStore.authToken
}

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
}

function flashAction(message, ms = 2500) {
    actionToast.value = message
    setTimeout(() => { actionToast.value = '' }, ms)
}

// ==================
// Filters
// ==================

function toggleStatusFilter(status) {
    const idx = activeStatusFilters.value.indexOf(status)
    if (idx >= 0) {
        activeStatusFilters.value.splice(idx, 1)
    } else {
        activeStatusFilters.value.push(status)
    }
}

function clearFilters() {
    searchQuery.value = ''
    activeStatusFilters.value = []
    priorityFilter.value = ''
}

// ==================
// Undo
// ==================



function dismissDispatcherOrder(rawId) {
    dismissedDispatcherOrders.value.add(rawId)
    dispatcherAssignedOrders.value = dispatcherAssignedOrders.value.filter(o => o.rawId !== rawId)
}

async function fetchLabourers(warehouseId) {
    labourers.value = warehouseId ? await api.fetchLabourerList(token(), warehouseId) : []
    orderAssignments.value = buildOrderAssignments(labourers.value)
}

// ==================
// Pick List Modal
// ==================

/** Top-level "Pick List" button — master overview of all active waves */
async function openMasterPickList() {
    await fetchPickingData()   // get fresh order items before building the slip
    await openSlipWithData('digitalPickList', { waves: waves.value })
}


// ==================
// Labourer Assignment
// ==================


// ==================
// Station Monitor
// ==================

function monitorStation(station) {
    monitoredStation.value = { ...station }
    showStationMonitor.value = true
}

function closeStationMonitor() {
    showStationMonitor.value = false
    monitoredStation.value = null
}

async function refreshStationData() {
    const warehouseId = getWarehouseId()
    if (!warehouseId || !monitoredStation.value) return

    stations.value = await api.fetchPackingStations(token(), warehouseId)
    const updated = stations.value.find(s => s.id === monitoredStation.value.id)
    if (updated) {
        monitoredStation.value = { ...updated }
    }
}

// ==================
// Data Fetching
// ==================

async function refreshData() {
    await fetchPickingData()
}

async function fetchPickingData() {
    loading.value = true
    pipelineLoading.value = true
    await authStore.ensureWarehouseContext()
    const warehouseId = getWarehouseId()

    try {
        const orders = await api.fetchOrders(token(), searchQuery.value)
        const stages = classifyPickingOrders(orders || [], warehouseId)
        if (orders) {
            dispatcherAssignedOrders.value = stages.dispatcherAssigned
                .filter(order => !dismissedDispatcherOrders.value.has(order.id))
                .map(toDispatcherNotice)
        }

        await fetchLabourers(warehouseId)
        if (warehouseId) {
            const prerequisites = await api.checkPrerequisites(token(), warehouseId)
            inventoryCount.value = prerequisites.inventoryCount
            floorPlanConfigured.value = prerequisites.floorPlanConfigured
        }
        const qcItems = await api.fetchQualityChecks(token(), warehouseId)

        waves.value = buildPickWaves(stages, {
            labourers: labourers.value,
            orderAssignments: orderAssignments.value,
            undoHistory: undoHistory.value,
        })
        pipelineCounts(stages).forEach((count, index) => {
            pipelineSteps.value[index].count = count
            pipelineSteps.value[index].active = count > 0
        })
        qualityChecks.value = buildQualityChecks(stages.packed, qcItems, orderAssignments.value)

        stations.value = warehouseId ? await api.fetchPackingStations(token(), warehouseId) : []
    } catch (error) {
        console.error('Error fetching picking data:', error)
    } finally {
        loading.value = false
        pipelineLoading.value = false
    }
}


// Debounced backend search when searchQuery changes
let searchDebounceTimer = null
watch(searchQuery, () => {
    clearTimeout(searchDebounceTimer)
    searchDebounceTimer = setTimeout(() => {
        fetchPickingData()
    }, 400)
})

onMounted(() => {
    window.addEventListener('warehouse-orders-updated', fetchPickingData)
    fetchPickingData()
    if (autoRefreshEnabled.value) {
        startAutoRefresh()
    }
})

onUnmounted(() => {
    window.removeEventListener('warehouse-orders-updated', fetchPickingData)
    stopAutoRefresh()
    clearUndoTimer()
    clearTimeout(searchDebounceTimer)
})
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
    transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
    transform: translate(-50%, 100%);
    opacity: 0;
}
</style>
