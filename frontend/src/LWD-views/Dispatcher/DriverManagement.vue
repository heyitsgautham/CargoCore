<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Driver Management</h2>
            <div class="flex gap-2">
                <button @click="openSlipPicker('vehicleSafetyChecklist')"
                    class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">health_and_safety</span> Safety Checklist
                </button>
                <button @click="openSlipPicker('assetCheckout')"
                    class="bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">inventory_2</span> Asset Checkout
                </button>
            </div>
        </div>

        <!-- Overview Stats -->
        <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ totalDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Total Drivers</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-green-400">{{ activeDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Active Now</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-yellow-500">{{ onBreakDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">On Break</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-red-500">{{ offlineDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Maintenance/Off</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-orange-400">{{ hosWarnings }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">HOS Warning</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-cyan-400">{{ authorizedDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Authorized</div>
            </div>
        </div>

        <!-- HOS Compliance Alert -->
        <div v-if="hosWarningDriver" class="p-4 bg-orange-100 dark:bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-center gap-3">
            <span class="material-symbols-outlined text-orange-500 dark:text-orange-400 animate-pulse">warning</span>
            <div class="flex-1">
                <div class="text-sm font-bold text-orange-600 dark:text-orange-400">Hours-of-Service Compliance Alert</div>
                <div class="text-xs text-orange-700 dark:text-orange-300">{{ hosWarningDriver.name }} has logged {{ hosWarningDriver.hours }}h of {{ hosWarningDriver.maxHours }}h max continuous driving. Break required soon. System will block new assignments at limit.</div>
            </div>
            <button @click="showHOS = !showHOS" class="text-xs bg-orange-100 dark:bg-orange-500/20 hover:bg-orange-200 dark:hover:bg-orange-500/30 text-orange-700 dark:text-orange-400 px-3 py-1.5 rounded-lg font-bold transition-colors whitespace-nowrap border border-orange-300 dark:border-orange-500/30 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">{{ showHOS ? 'visibility_off' : 'visibility' }}</span>
                {{ showHOS ? 'Hide HOS' : 'View HOS' }}
            </button>
        </div>
        <HosOverview />

        <!-- Drivers List -->
        <DriversTable />

        <!-- HOS Detail -->

        <!-- Driver Chat Modal — real thread via dispatcherContacts -->
        <Teleport to="body">
        <DriverChatModal />
        </Teleport>

        <!-- Driver Profile Modal -->
        <Teleport to="body">
        <DriverProfileModal />
        </Teleport>

    <!-- Suspend Confirm Modal -->
    <Teleport to="body">
    <SuspendConfirmModal />
    </Teleport>

    <!-- Slip Picker Modal -->
    <Teleport to="body">
    <div v-if="showSlipPickerModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showSlipPickerModal = false">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-sm m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">{{ slipPickerType === 'vehicleSafetyChecklist' ? 'health_and_safety' : 'inventory_2' }}</span>
                {{ slipPickerType === 'vehicleSafetyChecklist' ? 'Safety Checklist' : 'Asset Checkout' }} — Select Driver
            </h3>
            <div class="mb-4">
                <label class="text-xs text-gray-400 mb-1 block">Driver</label>
                <select v-model="slipPickerDriver" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option v-for="d in drivers" :key="d.id" :value="d" class="bg-white dark:bg-gray-800">{{ d.name }} — {{ d.vehicle || 'No vehicle' }}</option>
                </select>
            </div>
            <div class="flex gap-2">
                <button @click="confirmSlipOpen" :disabled="!slipPickerDriver"
                    class="flex-1 bg-primary text-black font-bold py-2 rounded-lg text-sm disabled:opacity-50 hover:bg-primary-dark transition-colors">
                    Generate Slip
                </button>
                <button @click="showSlipPickerModal = false" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">Cancel</button>
            </div>
        </div>
    </div>
    </Teleport>
    </div>
</template>

<script setup>
import HosOverview from './driverManagement/HosOverview.vue'
import DriversTable from './driverManagement/DriversTable.vue'
import DriverChatModal from './driverManagement/DriverChatModal.vue'
import DriverProfileModal from './driverManagement/DriverProfileModal.vue'
import SuspendConfirmModal from './driverManagement/SuspendConfirmModal.vue'
import { driverManagementPageKey } from './driverManagement/driverManagementPageContext'
import { ref, computed, onMounted, nextTick, provide } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlipWithData, prefetchSlips } = useSlipPrinter()

const store = useDispatcherStore()
onMounted(() => {
    store.initialize().catch(() => {})
    // Pre-fetch slip HTML so opens are synchronous (bypasses popup blocker)
    prefetchSlips(['vehicleSafetyChecklist', 'assetCheckout'])
})

const driverSearch = ref('')
const statusFilter = ref('')
const authFilter = ref('')
const showHOS = ref(false)
const showDriverChat = ref(false)
const showDriverProfile = ref(false)
const chatTargetDriver = ref(null)
const chatThreadId = ref(null)
const chatLoading = ref(false)
const profileTargetDriver = ref(null)
const driverChatMsg = ref('')
const driverChatMessages = ref([])
const moreMenuDriver = ref(null)
const showSlipPickerModal = ref(false)
const slipPickerType = ref('')
const slipPickerDriver = ref(null)
const suspendConfirmDriver = ref(null)
const showSuspendConfirm = ref(false)
const chatMsgEl = ref(null)

const drivers = computed(() => store.dispatcherDrivers)

const ACTIVE_STATUSES = ['active', 'on route', 'on_route']
const BREAK_STATUSES  = ['idle', 'on break', 'on_break']

const totalDrivers    = computed(() => drivers.value.length)
const activeDrivers   = computed(() => drivers.value.filter(d => ACTIVE_STATUSES.includes((d.status || '').toLowerCase())).length)
const onBreakDrivers  = computed(() => drivers.value.filter(d => BREAK_STATUSES.includes((d.status || '').toLowerCase())).length)
const offlineDrivers  = computed(() => drivers.value.filter(d => {
    const s = (d.status || '').toLowerCase()
    return !ACTIVE_STATUSES.includes(s) && !BREAK_STATUSES.includes(s)
}).length)
const hosWarnings     = computed(() => drivers.value.filter(d => d.breakDue).length)
const authorizedDrivers = computed(() => drivers.value.filter(d => d.authorized && !d.suspended).length)
const hosWarningDriver  = computed(() => drivers.value.find(d => d.breakDue) || null)

const filteredDrivers = computed(() => {
    return drivers.value.filter(d => {
        if (driverSearch.value) {
            const q = driverSearch.value.toLowerCase()
            if (!d.name.toLowerCase().includes(q) && !(d.phone || '').includes(q) && !(d.vehicle || '').toLowerCase().includes(q)) return false
        }
        if (statusFilter.value === 'HOS') return d.breakDue
        if (statusFilter.value === 'On Route' && d.statusColor !== 'bg-green-500') return false
        if (statusFilter.value === 'Offline' && d.statusColor !== 'bg-gray-500') return false
        if (authFilter.value === 'authorized' && !d.authorized) return false
        if (authFilter.value === 'suspended' && !d.suspended) return false
        if (authFilter.value === 'expired' && d.licenseValid) return false
        return true
    })
})

// ── Real chat via dispatcherContacts (same as ServiceMoves contactCrew) ──────
async function chatDriver(driver) {
    chatTargetDriver.value = driver
    chatThreadId.value = null
    chatLoading.value = true
    driverChatMsg.value = ''
    driverChatMessages.value = []
    showDriverChat.value = true

    // Look up the contact by driver id or name
    const contact = store.dispatcherContacts.find(c => c.id === String(driver.id))
        || store.dispatcherContacts.find(c => c.name === driver.name)

    if (contact?.threadId) {
        chatThreadId.value = String(contact.threadId)
        driverChatMessages.value = (contact.messages || []).map(m => ({
            id: m.id || Date.now(),
            from: m.from || m.sender || 'driver',
            text: m.text || '',
            time: m.time || '',
        }))
    } else if (contact) {
        // No thread yet — create one
        const thread = await store.createChatForContact(contact.name, contact.phone)
        if (thread?.id) chatThreadId.value = String(thread.id)
    }

    chatLoading.value = false
    await nextTick()
    scrollChatToBottom()
}

async function sendDriverChatMsg() {
    const text = driverChatMsg.value.trim()
    if (!text) return
    driverChatMsg.value = ''

    if (chatThreadId.value) {
        const updated = await store.sendDispatchMessage(chatThreadId.value, text)
        if (updated) {
            driverChatMessages.value = (updated.messages || []).map(m => ({
                id: m.id || Date.now(),
                from: m.from || m.sender || 'driver',
                text: m.text || '',
                time: m.time || '',
            }))
            await nextTick()
            scrollChatToBottom()
            return
        }
    }
    // Fallback: show locally if thread not yet established
    driverChatMessages.value.push({ id: Date.now(), from: 'dispatch', text, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) })
    await nextTick()
    scrollChatToBottom()
}

function scrollChatToBottom() {
    if (chatMsgEl.value) chatMsgEl.value.scrollTop = chatMsgEl.value.scrollHeight
}

// ── Suspend / Unsuspend ───────────────────────────────────────────────────────
function promptSuspend(driver) {
    suspendConfirmDriver.value = driver
    showSuspendConfirm.value = true
    moreMenuDriver.value = null
}

async function confirmSuspend() {
    if (!suspendConfirmDriver.value) return
    await store.toggleDriverSuspend(suspendConfirmDriver.value.id)
    showSuspendConfirm.value = false
    suspendConfirmDriver.value = null
}

// ── View Profile ──────────────────────────────────────────────────────────────
function viewDriverProfile(driver) {
    profileTargetDriver.value = driver
    showDriverProfile.value = true
    moreMenuDriver.value = null
}

function toggleMoreMenu(driver) { moreMenuDriver.value = moreMenuDriver.value === driver.id ? null : driver.id }

function getHOSBarClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'bg-red-500'
    if (pct >= 75) return 'bg-orange-500'
    return 'bg-green-500'
}

function getHOSTextClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'text-red-400'
    if (pct >= 75) return 'text-orange-400'
    return 'text-gray-400'
}

function getHOSStatus(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 100) return 'LIMIT REACHED — BLOCKED'
    if (pct >= 90) return 'CRITICAL — Near limit'
    if (pct >= 75) return 'Warning — Monitor'
    return 'Compliant'
}

function getHOSStatusClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'text-red-400 font-bold'
    if (pct >= 75) return 'text-orange-400'
    return 'text-green-400'
}

function openSlipPicker(type) {
    slipPickerType.value = type
    slipPickerDriver.value = drivers.value[0] || null
    showSlipPickerModal.value = true
}

async function confirmSlipOpen() {
    const driver = slipPickerDriver.value
    if (!driver) return

    const vehicle = store.filteredVehicles.find(v =>
        v.id === driver.vehicleId ||
        v.code === driver.vehicle ||
        v.licensePlate === driver.vehicle ||
        v.model === driver.vehicle
    ) || {
        code: driver.vehicle || '—',
        type: driver.vehicle || 'Truck',
        model: driver.vehicle || 'Standard Vehicle'
    }

    await openSlipWithData(slipPickerType.value, driver, vehicle)
    showSlipPickerModal.value = false
}

provide(driverManagementPageKey, {
    authFilter,
    chatDriver,
    chatLoading,
    chatMsgEl,
    chatTargetDriver,
    chatThreadId,
    confirmSuspend,
    driverChatMessages,
    driverChatMsg,
    driverSearch,
    drivers,
    filteredDrivers,
    getHOSBarClass,
    getHOSStatus,
    getHOSStatusClass,
    getHOSTextClass,
    moreMenuDriver,
    profileTargetDriver,
    promptSuspend,
    sendDriverChatMsg,
    showDriverChat,
    showDriverProfile,
    showHOS,
    showSuspendConfirm,
    statusFilter,
    suspendConfirmDriver,
    toggleMoreMenu,
    viewDriverProfile,
})
</script>
