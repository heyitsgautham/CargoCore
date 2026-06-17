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
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Dock Status Cards -->
                <div v-for="dock in docks" :key="dock.id" class="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div class="absolute inset-x-0 bottom-0 h-1" :class="dock.statusClass"></div>
                    <div class="flex justify-between items-start mb-4">
                        <div class="text-xl font-bold text-gray-900 dark:text-white">Dock {{ dock.id }}</div>
                        <span class="px-2 py-1 rounded text-[10px] uppercase font-bold text-black"
                            :class="dock.badgeClass">{{ dock.status }}</span>
                    </div>

                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Truck:</span>
                            <span class="text-gray-900 dark:text-white font-mono">{{ dock.truck || '--' }}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Progress:</span>
                            <span class="text-gray-900 dark:text-white font-bold">{{ dock.progress }}%</span>
                        </div>
                    </div>

                    <!-- Dwell Time Tracking -->
                    <div v-if="dock.status === 'Occupied'"
                        class="mb-4 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-[10px] text-gray-600 dark:text-gray-400 uppercase font-bold mb-2">Dwell Time</div>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <div class="text-gray-500">Arrived</div>
                                <div class="text-gray-900 dark:text-white font-mono">{{ dock.arrivedAt }}</div>
                            </div>
                            <div>
                                <div class="text-gray-500">Loading Since</div>
                                <div class="text-gray-900 dark:text-white font-mono">{{ dock.loadingSince }}</div>
                            </div>
                            <div>
                                <div class="text-gray-500">Elapsed</div>
                                <div class="font-mono font-bold"
                                    :class="dock.dwellMinutes > 45 ? 'text-red-600 dark:text-red-400' : dock.dwellMinutes > 30 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'">
                                    {{ dock.dwellMinutes }} min</div>
                            </div>
                            <div>
                                <div class="text-gray-500">Efficiency</div>
                                <div class="text-primary font-bold">{{ dock.efficiency }}</div>
                            </div>
                        </div>
                    </div>

                    <div v-if="dock.status === 'Occupied'"
                        class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden mb-4">
                        <div class="bg-blue-500 h-full animate-pulse" :style="`width: ${dock.progress}%`"></div>
                    </div>

                    <div class="flex gap-2">
                        <button v-if="dock.status === 'Occupied'" @click="openVerifyModal(dock)"
                            class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-2 rounded text-xs font-bold transition-colors">
                            Verify & Release
                        </button>
                        <button v-if="dock.status === 'Free'" @click="openAssignModal(dock)"
                            class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white py-2 rounded text-xs font-bold transition-colors">Assign
                            Truck</button>
                        <button v-if="dock.status === 'Maintenance'" @click="clearMaintenance(dock)"
                            class="flex-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-600 dark:text-blue-400 py-2 rounded text-xs font-bold transition-colors">Clear
                            Maintenance</button>
                        <button @click="openSettingsModal(dock)"
                            class="px-3 py-2 bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 rounded text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"><span
                                class="material-symbols-outlined text-sm">settings</span></button>
                    </div>
                </div>
            </div>

            <!-- Outbound Orders Queue (replacing static incoming trucks) -->
            <div class="glass-panel rounded-xl overflow-hidden p-6">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Ready for Dispatch — Outbound Queue</h3>
                <div v-if="outboundOrders.length === 0" class="text-center text-gray-500 py-6">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">local_shipping</span>
                    <p class="text-sm">No orders ready for dispatch yet</p>
                </div>
                <div v-else class="space-y-3">
                    <div v-for="order in outboundOrders" :key="order.id"
                        class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-4">
                            <div
                                class="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-gray-900 dark:text-white font-bold text-xs flex-col">
                                <span>{{ order.eta }}</span>
                                <span class="text-[8px] text-gray-600 dark:text-gray-400">DUE</span>
                            </div>
                            <div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ order.tracking }}</div>
                                <div class="text-xs text-gray-600 dark:text-gray-400">{{ order.type }} • {{ order.items
                                    }} items</div>
                                <div class="text-[10px] mt-0.5">
                                    <span class="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-600 dark:text-blue-400">{{
                                        order.status }}</span>
                                </div>
                            </div>
                        </div>
                        <button @click="selectedOutbound = order; showTruckDetail = true"
                            class="text-primary hover:underline text-xs">Details</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Assign Truck Modal -->
        <Teleport to="body">
            <div v-if="showAssignModal && assignDock"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showAssignModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Assign Truck to Dock {{
                            assignDock.id }}</h3>
                        <button @click="showAssignModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Vehicle</label>
                            <select v-if="fleetVehicles.length" v-model="assignForm.truck"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option value="">— Select vehicle —</option>
                                <option v-for="v in availableVehicles" :key="v.id" :value="v.id"
                                    class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                                    {{ v.code }}{{ v.license_plate ? ' · ' + v.license_plate : '' }} — {{ v.type }}{{ v.status !== 'Active' ? ' (' + v.status + ')' : '' }}
                                </option>
                            </select>
                            <input v-else type="text" v-model="assignForm.truck" placeholder="TRK-XXXX"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 font-mono" />
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Dispatch Order</label>
                            <select v-model="assignForm.orderId"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option value="" disabled>— Select Order (required) —</option>
                                <option v-for="order in availableOrders" :key="order.id" :value="order.id">
                                    {{ order.tracking }} - {{ order.status }}
                                </option>
                            </select>
                        </div>
                        <button @click="confirmAssign" :disabled="!assignForm.truck || !assignForm.orderId"
                            class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50">Assign
                            to Dock</button>
                        <button @click="openSlip('assetCheckout')"
                            class="w-full flex items-center justify-center gap-2 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-bold transition-colors">
                            <span class="material-symbols-outlined text-[16px]">inventory_2</span>
                            Print Asset Checkout Slip
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Settings Modal -->
        <Teleport to="body">
            <div v-if="showSettingsModal && settingsDock"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showSettingsModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock {{ settingsDock.id }} Settings
                        </h3>
                        <button @click="showSettingsModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Dock Status</label>
                            <select v-model="settingsForm.status"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Free</option>
                                <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Maintenance</option>
                            </select>
                        </div>
                        <div
                            class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-xs text-gray-600 dark:text-gray-400">
                            <div>Current Status: <span class="text-gray-900 dark:text-white font-bold">{{
                                    settingsDock.status }}</span></div>
                            <div>Truck: <span class="text-gray-900 dark:text-white">{{ settingsDock.truck || 'None'
                                    }}</span></div>
                        </div>
                        <button @click="saveSettings"
                            class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Save
                            Settings</button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Verify & Release Modal -->
        <Teleport to="body">
            <div v-if="showVerifyModal && verifyDock"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showVerifyModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock {{ verifyDock.id }} —
                            Pre-Departure Verification</h3>
                        <button @click="showVerifyModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-bold mb-2">Manifest Check
                        </div>
                        <div class="space-y-2">
                            <div v-for="item in verifyChecklist" :key="item.label"
                                class="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors"
                                :class="item.checked ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 hover:border-white/20'"
                                @click="item.checked = !item.checked">
                                <span class="material-symbols-outlined text-[18px]"
                                    :class="item.checked ? 'text-green-600 dark:text-green-400' : 'text-gray-600'">
                                    {{ item.checked ? 'check_circle' : 'radio_button_unchecked' }}
                                </span>
                                <span class="text-sm"
                                    :class="item.checked ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'">{{
                                        item.label
                                    }}</span>
                            </div>
                        </div>
                        <div
                            class="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-2">
                            <span class="material-symbols-outlined text-[16px]">warning</span>
                            Driver must confirm receipt before departure
                        </div>
                        <div class="flex gap-3">
                            <button @click="completeDock" :disabled="!allChecked"
                                class="flex-1 py-3 rounded-lg font-bold transition-colors"
                                :class="allChecked ? 'bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'">
                                <span
                                    class="material-symbols-outlined text-[18px] align-middle mr-1">check_circle</span>
                                Confirm & Release Truck
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Outbound Order Detail Modal -->
        <Teleport to="body">
            <div v-if="showTruckDetail && selectedOutbound"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showTruckDetail = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Order Details</h3>
                        <button @click="showTruckDetail = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-3">
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Tracking</div>
                                <div class="text-gray-900 dark:text-white font-bold font-mono">{{ selectedOutbound.tracking }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Type</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.type }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Items</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.items }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Status</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.status }}</div>
                            </div>
                        </div>
                        <button @click="showTruckDetail = false"
                            class="w-full bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm transition-colors">Close</button>
                    </div>
                </div>
            </div>
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
import { ref, computed, reactive, onMounted } from 'vue'
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
            fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/operations/loading-docks`, {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }),
            fetch('http://localhost:8000/api/v1/orders?page=1&page_size=30', {
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
        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/operations/loading-docks/${verifyDock.value.rawId}/release`, {
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
        const response = await fetch(`http://localhost:8000/api/v1/warehouses/${warehouseId}/operations/loading-docks/${assignDock.value.rawId}/assign`, {
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
                `http://localhost:8000/api/v1/warehouses/${warehouseId}/operations/loading-docks/${dockRawId}/maintenance?is_maintenance=${isMaintenance}`,
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
                `http://localhost:8000/api/v1/warehouses/${warehouseId}/operations/loading-docks/${dock.rawId}/maintenance?is_maintenance=false`,
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
        const res = await fetch('http://localhost:8000/api/v1/logistics/vehicles', {
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
</script>
