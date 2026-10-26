<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Loading Dock Management</h2>

        <!-- Dwell Time Overview -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Avg. Dwell Time</div>
                <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ avgDwell }} min</div>
                <div class="text-xs text-gray-500 mt-1">Across occupied docks</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Trucks Loaded Today</div>
                <div class="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">{{ trucksLoaded }}</div>
                <div class="text-xs text-gray-500 mt-1">Target: {{ Math.max(docks.length * 2, 12) }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-yellow-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Loading Delays</div>
                <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
                    {{ docks.filter(d => d.dwellMinutes > 45).length }}
                </div>
                <div class="text-xs text-gray-500 mt-1">Docks over 45 min dwell</div>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading dock status...</div>
        </div>

        <!-- Error / Empty State -->
        <div v-else-if="fetchError || docks.length === 0" class="glass-panel p-10 rounded-xl text-center">
            <span class="material-symbols-outlined text-4xl text-gray-400 dark:text-gray-500">dock</span>
            <div class="mt-3 text-lg font-semibold text-gray-700 dark:text-gray-300">
                {{ fetchError || 'No loading docks found' }}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Docks are created by the Logistics Manager from the fleet management panel.
            </div>
        </div>

        <div v-else>
            <DockCards />

            <!-- Outbound Orders Queue (replacing static incoming trucks) -->
            <OutboundQueue />
        </div>

        <!-- Assign Truck Modal -->
        <Teleport to="body">
            <AssignTruckModal />
        </Teleport>

        <!-- Settings Modal -->
        <Teleport to="body">
            <DockSettingsModal />
        </Teleport>

        <!-- Verify & Release Modal -->
        <Teleport to="body">
            <VerifyReleaseModal />
        </Teleport>

        <!-- Outbound Order Detail Modal -->
        <Teleport to="body">
            <OutboundDetailModal />
        </Teleport>

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import DockCards from './loadingDock/DockCards.vue'
import OutboundQueue from './loadingDock/OutboundQueue.vue'
import AssignTruckModal from './loadingDock/AssignTruckModal.vue'
import DockSettingsModal from './loadingDock/DockSettingsModal.vue'
import VerifyReleaseModal from './loadingDock/VerifyReleaseModal.vue'
import OutboundDetailModal from './loadingDock/OutboundDetailModal.vue'
import { loadingDockPageKey } from './loadingDock/loadingDockPageContext'
import { API_BASE_URL } from '@/config/api'
import { ref, computed, reactive, onMounted, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { getEffectiveWarehouseSubstatus, patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlip } = useSlipPrinter()

const authStore = useAuthStore()

const showVerifyModal = ref(false)
const showAssignModal = ref(false)
const showSettingsModal = ref(false)
const showTruckDetail = ref(false)
const verifyDock = ref(null)
const assignDock = ref(null)
const settingsDock = ref(null)
const selectedOutbound = ref(null)
const toastMsg = ref('')
const loading = ref(false)
const trucksLoaded = ref(0)

const assignForm = reactive({ truck: '', carrier: 'UPS Freight', orderId: '' })
const settingsForm = reactive({ status: 'Free' })

// Dynamic docks generated from warehouse capacity info
const docks = ref([])
const outboundOrders = ref([])
const fleetVehicles = ref([])
const fetchError = ref('')

const verifyChecklist = ref([
    { label: 'All items scanned and loaded', checked: false },
    { label: 'Labor physically present on truck', checked: false },
    { label: 'Packing utensils loaded', checked: false },
    { label: 'Manifest document attached', checked: false },
    { label: 'Driver has confirmed receipt', checked: false },
    { label: 'Weight verification passed', checked: false },
])

const allChecked = computed(() => verifyChecklist.value.every(item => item.checked))

const availableVehicles = computed(() => {
    const assignedVehicleIds = new Set(
        docks.value
            .filter(d => d.status === 'Occupied' && d.vehicleId && d.rawId !== assignDock.value?.rawId)
            .map(d => String(d.vehicleId))
    )
    return fleetVehicles.value.filter(v => (v.status === 'Active' || v.status === 'Available') && !assignedVehicleIds.has(String(v.id)))
})

const availableOrders = computed(() => {
    const assignedOrderIds = new Set(
        docks.value
            .filter(d => d.status === 'Occupied' && d.assignedOrderId && d.id !== assignDock.value?.id)
            .map(d => d.assignedOrderId)
    )
    return outboundOrders.value.filter(o => !assignedOrderIds.has(o.id))
})

const avgDwell = computed(() => {
    const occupied = docks.value.filter(d => d.status === 'Occupied')
    if (!occupied.length) return 0
    return Math.round(occupied.reduce((s, d) => s + d.dwellMinutes, 0) / occupied.length)
})

function showToast(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

function formatTime(dateString) {
    if (!dateString) return '--'
    try {
        return new Date(dateString).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    } catch { return '--' }
}

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
}


function getEfficiency(dwell) {
    if (dwell <= 20) return 'Excellent'
    if (dwell <= 35) return 'Good'
    if (dwell <= 45) return 'Normal'
    return 'Delayed'
}

// Fetch dock and outbound data from API
async function fetchDockData() {
    loading.value = true
    const warehouseId = getWarehouseId()

    fetchError.value = ''
    try {
        if (!warehouseId) {
            fetchError.value = 'No warehouse linked to your account.'
            return
        }

        // Fetch loading docks from new API + packed orders in parallel
        const [docksRes, packedRes] = await Promise.allSettled([
            fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/loading-docks`, {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }),
            fetch(`${API_BASE_URL}/api/v1/orders?page=1&page_size=30`, {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            })
        ])

        // Process docks from API
        if (docksRes.status === 'fulfilled' && docksRes.value.ok) {
            const data = await docksRes.value.json()
            docks.value = (data.items || []).map(dock => ({
                id: dock.dock_number,
                rawId: dock.id,
                status: dock.status === 'OCCUPIED' ? 'Occupied' : dock.status === 'MAINTENANCE' ? 'Maintenance' : 'Free',
                truck: dock.assigned_vehicle_code,
                vehicleId: dock.assigned_vehicle_id,
                carrier: dock.assigned_carrier,
                progress: dock.status === 'OCCUPIED' ? Math.min(90, Math.floor((dock.dwell_minutes / 60) * 100)) : 0,
                statusClass: dock.status === 'OCCUPIED' ? 'bg-yellow-500' : dock.status === 'MAINTENANCE' ? 'bg-red-500' : 'bg-green-500',
                badgeClass: dock.status === 'OCCUPIED' ? 'bg-yellow-500' : dock.status === 'MAINTENANCE' ? 'bg-red-500 text-white' : 'bg-green-500',
                arrivedAt: formatTime(dock.arrived_at),
                loadingSince: formatTime(dock.loading_started_at),
                dwellMinutes: dock.dwell_minutes || 0,
                efficiency: getEfficiency(dock.dwell_minutes || 0),
                assignedOrderId: dock.assigned_order_id,
                assignedOrderTracking: dock.assigned_order_tracking
            }))
        } else {
            fetchError.value = 'Failed to load docks from server.'
            docks.value = []
        }

        // Get outbound orders (PACKED or QC_PASSED)
        if (packedRes.status === 'fulfilled' && packedRes.value.ok) {
            const data = await packedRes.value.json()
            const items = (data.items || []).filter(order =>
                order.status !== 'CANCELLED' &&
                ['QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK'].includes(getEffectiveWarehouseSubstatus(order, warehouseId))
            )
            outboundOrders.value = items.map(order => ({
                id: order.id,
                tracking: order.tracking_code,
                type: order.order_type || 'Standard',
                items: order.items?.length || order.item_count || 0,
                status: getEffectiveWarehouseSubstatus(order, warehouseId) || order.status,
                eta: formatTime(order.scheduled_at) || 'ASAP'
            }))
        }

        // Count loaded trucks
        trucksLoaded.value = docks.value.filter(d => d.status === 'Free' && d.releasedAt).length

    } catch (error) {
        console.error('Error fetching dock data:', error)
        fetchError.value = 'Could not connect to server.'
        docks.value = []
    } finally {
        loading.value = false
    }
}


function openVerifyModal(dock) {
    verifyDock.value = dock
    verifyChecklist.value.forEach(item => item.checked = false)
    showVerifyModal.value = true
}

async function completeDock() {
    const warehouseId = getWarehouseId()
    if (!warehouseId || !verifyDock.value) {
        showToast('Error: Missing warehouse')
        return
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/loading-docks/${verifyDock.value.rawId}/release`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                items_scanned: verifyChecklist.value[0].checked,
                labor_present: verifyChecklist.value[1].checked,
                packing_loaded: verifyChecklist.value[2].checked,
                manifest_attached: verifyChecklist.value[3].checked,
                driver_confirmed: verifyChecklist.value[4].checked,
                weight_verified: verifyChecklist.value[5].checked
            })
        })

        if (response.ok) {
            if (verifyDock.value.assignedOrderId) {
                patchWarehouseOrderUiState(warehouseId, verifyDock.value.assignedOrderId, {
                    accepted: true,
                    warehouse_substatus: 'DISPATCHED',
                })
            }
            trucksLoaded.value++
            showVerifyModal.value = false
            showToast(`Dock ${verifyDock.value?.id} — Truck released!`)
            await Promise.all([fetchDockData(), fetchFleetVehicles()])
        } else {
            const errData = await response.json().catch(() => ({}))
            showToast(`Failed to release dock: ${errData.detail || response.statusText}`)
        }
    } catch (error) {
        console.error('Error releasing dock:', error)
        showToast('Error releasing dock')
    }
}

function openAssignModal(dock) {
    assignDock.value = dock
    assignForm.truck = ''
    assignForm.carrier = 'UPS Freight'
    assignForm.orderId = ''
    showAssignModal.value = true
}

async function confirmAssign() {
    const warehouseId = getWarehouseId()
    if (!warehouseId || !assignDock.value) {
        showToast('Error: Missing warehouse')
        return
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/loading-docks/${assignDock.value.rawId}/assign`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_id: assignForm.truck,
                carrier: assignForm.carrier || 'Internal Fleet',
                order_id: assignForm.orderId || null
            })
        })

        if (response.ok) {
            if (assignForm.orderId) {
                patchWarehouseOrderUiState(warehouseId, assignForm.orderId, {
                    accepted: true,
                    warehouse_substatus: 'ON_DOCK',
                })
            }
            showAssignModal.value = false
            showToast(`${assignForm.truck} assigned to Dock ${assignDock.value?.id}`)
            await Promise.all([fetchDockData(), fetchFleetVehicles()])
        } else {
            const errData = await response.json().catch(() => ({}))
            const msg = Array.isArray(errData.detail)
                ? errData.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
                : (errData.detail || response.statusText)
            showToast(`Failed to assign truck: ${msg}`)
        }
    } catch (error) {
        console.error('Error assigning truck:', error)
        showToast('Error assigning truck')
    }
}

function openSettingsModal(dock) {
    settingsDock.value = dock
    settingsForm.status = dock.status === 'Occupied' ? 'Free' : dock.status
    showSettingsModal.value = true
}

async function saveSettings() {
    if (!settingsDock.value || settingsDock.value.status === 'Occupied') {
        showSettingsModal.value = false
        return
    }
    const warehouseId = getWarehouseId()
    const dockRawId = settingsDock.value.rawId
    if (warehouseId && dockRawId) {
        const isMaintenance = settingsForm.status === 'Maintenance'
        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/loading-docks/${dockRawId}/maintenance?is_maintenance=${isMaintenance}`,
                { method: 'POST', headers: { 'Authorization': `Bearer ${authStore.authToken}` } }
            )
            if (!res.ok) throw new Error('API error')
        } catch (e) {
            showToast(`Failed to save dock settings`, 'error')
            showSettingsModal.value = false
            return
        }
    }
    settingsDock.value.status = settingsForm.status
    settingsDock.value.statusClass = settingsForm.status === 'Maintenance' ? 'bg-red-500' : 'bg-green-500'
    settingsDock.value.badgeClass = settingsForm.status === 'Maintenance' ? 'bg-red-500 text-white' : 'bg-green-500'
    showSettingsModal.value = false
    showToast(`Dock ${settingsDock.value?.id} settings updated`)
}

async function clearMaintenance(dock) {
    const warehouseId = getWarehouseId()
    if (warehouseId && dock.rawId) {
        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/loading-docks/${dock.rawId}/maintenance?is_maintenance=false`,
                { method: 'POST', headers: { 'Authorization': `Bearer ${authStore.authToken}` } }
            )
            if (!res.ok) throw new Error('API error')
        } catch (e) {
            showToast(`Failed to clear maintenance`, 'error')
            return
        }
    }
    dock.status = 'Free'
    dock.statusClass = 'bg-green-500'
    dock.badgeClass = 'bg-green-500'
    showToast(`Dock ${dock.id} — maintenance cleared`)
}

async function fetchFleetVehicles() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/logistics/vehicles`, {
            headers: { 'Authorization': `Bearer ${authStore.authToken}` }
        })
        if (res.ok) {
            const data = await res.json()
            fleetVehicles.value = Array.isArray(data) ? data : (data.items || [])
        }
    } catch (e) {
        console.warn('Could not fetch fleet vehicles', e)
    }
}

onMounted(() => {
    fetchDockData()
    fetchFleetVehicles()
})

provide(loadingDockPageKey, {
    allChecked,
    assignDock,
    assignForm,
    availableOrders,
    availableVehicles,
    clearMaintenance,
    completeDock,
    confirmAssign,
    docks,
    fleetVehicles,
    openAssignModal,
    openSettingsModal,
    openSlip,
    openVerifyModal,
    outboundOrders,
    saveSettings,
    selectedOutbound,
    settingsDock,
    settingsForm,
    showAssignModal,
    showSettingsModal,
    showTruckDetail,
    showVerifyModal,
    verifyChecklist,
    verifyDock,
})
</script>
