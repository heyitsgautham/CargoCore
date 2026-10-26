<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Service Move & Time Blocking</h2>
                <p class="text-sm text-gray-400 mt-1">Manage house shifts, warehouse pickups, manual service runs, crew manifest, and time blocks</p>
            </div>
            <button @click="openNewMoveModal" class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors text-sm">
                <span class="material-symbols-outlined text-[18px]">add</span> New Service Move
            </button>
        </div>

        <ServiceMoveStats />

        <ActiveServiceMoves />

        <ScheduleConflictWarning />

        <NewServiceMoveModal />

        <MapPicker
            :isOpen="showMapPicker"
            :title="mapPickerTitle"
            :initialLat="mapPickerInitialLat"
            :initialLon="mapPickerInitialLon"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />

        <ContactCrewModal />

        <LiveTrackingModal />
    </div>
</template>

<script setup>
import ServiceMoveStats from './serviceMoves/ServiceMoveStats.vue'
import ActiveServiceMoves from './serviceMoves/ActiveServiceMoves.vue'
import ScheduleConflictWarning from './serviceMoves/ScheduleConflictWarning.vue'
import NewServiceMoveModal from './serviceMoves/NewServiceMoveModal.vue'
import ContactCrewModal from './serviceMoves/ContactCrewModal.vue'
import LiveTrackingModal from './serviceMoves/LiveTrackingModal.vue'
import {
    formatVehicleLabel,
    hasOpenAssignments,
    isDriverAssignableStatus,
    isVehicleAssignableStatus,
    mapServiceMove,
} from './serviceMoves/serviceMoveRecords'
import { serviceMovesPageKey } from './serviceMoves/serviceMovesPageContext'
import { ref, computed, reactive, onMounted, watch, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL, getStoredAccessToken } from '@/config/api'
import { useToast } from '@/composables/useToast'
import MapPicker from '@/components/MapPicker.vue'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useMoveCrewActions } from './serviceMoves/useMoveCrewActions'
import { useCreateServiceMove } from './serviceMoves/useCreateServiceMove'

const store = useDispatcherStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const toast = useToast()
onMounted(async () => {
    await store.initialize().catch(() => {})
    await fetchServiceMoves()
})

// Auth headers
function authHeaders() {
    const token = getStoredAccessToken()
    return token
        ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/json' }
}

function buildServiceMoveMeta() {
    return `SERVICE_MOVE_META::${JSON.stringify({
        title: newMove.title.trim(),
        notes: newMove.notes.trim(),
    })}`
}

function buildServiceTimeBlock() {
    const durationHours = Number(newMove.estimatedDuration || 0)
    const startText = newMove.scheduledTime || 'TBD'
    if (!durationHours) return `${startText} start`
    return `${startText} start · ${durationHours}h block`
}

function resetNewMoveForm() {
    newMove.title = ''
    newMove.type = 'House Shift'
    newMove.pickup = ''
    newMove.delivery = ''
    newMove.pickupLat = null
    newMove.pickupLng = null
    newMove.deliveryLat = null
    newMove.deliveryLng = null
    newMove.vehicleId = ''
    newMove.driverId = ''
    newMove.laborerIds = []
    newMove.scheduledDate = ''
    newMove.scheduledTime = ''
    newMove.estimatedDuration = '4'
    newMove.notes = ''
}

function primeNewMoveDefaults() {
    if (!newMove.vehicleId && vehicleOptions.value.length > 0) {
        newMove.vehicleId = vehicleOptions.value[0].id
    }
    if (!newMove.driverId && availableDrivers.value.length > 0) {
        newMove.driverId = availableDrivers.value[0].id
    }
    if (!newMove.scheduledDate) {
        newMove.scheduledDate = new Date().toISOString().split('T')[0]
    }
    if (!newMove.scheduledTime) {
        newMove.scheduledTime = '10:00'
    }
}

async function closeNewMoveModal() {
    showNewMove.value = false
    formError.value = ''
    formSuccess.value = ''

    if (route.query.createMove === '1') {
        const nextQuery = { ...route.query }
        delete nextQuery.createMove
        await router.replace({ query: nextQuery })
    }
}

async function openNewMoveModal() {
    formError.value = ''
    formSuccess.value = ''
    showNewMove.value = true
    await Promise.allSettled([
        store.fetchVehicles(),
        store.fetchDrivers(),
    ])
    primeNewMoveDefaults()
}

function resolveDriverVehicleId(driver) {
    if (!driver?.vehicle) return null
    const driverVehicleCode = String(driver.vehicle).trim().toLowerCase()
    const matchedVehicle = store.filteredVehicles.find((vehicle) =>
        String(vehicle.code || '').trim().toLowerCase() === driverVehicleCode
    )
    return matchedVehicle ? matchedVehicle.id : null
}

const availableDrivers = computed(() => {
    return store.dispatcherDrivers
        .filter((driver) =>
            isDriverAssignableStatus(driver.status) &&
            !driver.suspended &&
            !hasOpenAssignments(driver)
        )
        .map((driver) => ({
            ...driver,
            assignedVehicleId: resolveDriverVehicleId(driver),
        }))
})

const vehicleOptions = computed(() => {
    const selectedDriver = availableDrivers.value.find((driver) => driver.id === newMove.driverId)
    const selectedDriverVehicleId = selectedDriver?.assignedVehicleId || null

    return store.filteredVehicles
        .filter((vehicle) =>
            isVehicleAssignableStatus(vehicle.status) ||
            (selectedDriverVehicleId && vehicle.id === selectedDriverVehicleId)
        )
        .map(v => ({
            id: v.id,
            label: formatVehicleLabel(v),
            code: v.code || '',
            type: v.type || '',
            seatCapacity: v.seatCapacity ?? null,
        }))
})
// Alias used in template
const realVehicleOptions = vehicleOptions

const completedToday = ref(0)
const showNewMove = ref(false)
const showCrewChat = ref(false)
const crewChatMove = ref(null)
const crewMsg = ref('')
const crewMessages = ref([])
const moveMenu = ref(null)
const loading = ref(false)
const formError = ref('')
const formSuccess = ref('')
const showTrackingModal = ref(false)
const trackingMove = ref(null)
const trackedDriver = ref(null)
const trackingLoading = ref(false)
const crewThreadId = ref(null)
const showMapPicker = ref(false)
const mapPickerType = ref('pickup')
const selectedVehicleOption = computed(() =>
    vehicleOptions.value.find(vehicle => vehicle.id === newMove.vehicleId) || null
)
const assignedHub = computed(() => {
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!warehouseId) return null
    return store.hubs.find((hub) => String(hub.id) === String(warehouseId)) || null
})
const mapPickerTitle = computed(() =>
    mapPickerType.value === 'pickup' ? 'Select Pickup Location' : 'Select Delivery Location'
)
const mapPickerInitialLat = computed(() => {
    if (mapPickerType.value === 'pickup' && newMove.pickupLat !== null) return Number(newMove.pickupLat)
    if (mapPickerType.value === 'delivery' && newMove.deliveryLat !== null) return Number(newMove.deliveryLat)
    return Number(assignedHub.value?.lat ?? 12.9716)
})
const mapPickerInitialLon = computed(() => {
    if (mapPickerType.value === 'pickup' && newMove.pickupLng !== null) return Number(newMove.pickupLng)
    if (mapPickerType.value === 'delivery' && newMove.deliveryLng !== null) return Number(newMove.deliveryLng)
    return Number(assignedHub.value?.lng ?? 77.5946)
})

const driverMapIcon = computed(() =>
    L.divIcon({
        html: `<div style="
            width:40px;height:40px;
            background:#111827;
            border:2.5px solid #22c55e;
            border-radius:50%;
            box-shadow:0 3px 10px rgba(0,0,0,0.5);
            display:flex;align-items:center;justify-content:center;
            font-size:20px;
        ">🚚</div>`,
        className: '',
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        tooltipAnchor: [0, -24],
    })
)

const newMove = reactive({
    title: '',
    type: 'House Shift',
    pickup: '',
    delivery: '',
    pickupLat: null,
    pickupLng: null,
    deliveryLat: null,
    deliveryLng: null,
    vehicleId: '',
    driverId: '',
    laborerIds: [],
    scheduledDate: '',
    scheduledTime: '',
    estimatedDuration: '4',
    notes: ''
})

const serviceMoves = ref([])

const totalCrewCount = computed(() => serviceMoves.value.reduce((sum, m) => sum + m.crew.length, 0))
const blockedHours = computed(() => serviceMoves.value.reduce((sum, m) => sum + parseInt(m.duration), 0))
const vehiclesReserved = computed(() => serviceMoves.value.length)

watch(showNewMove, (isOpen) => {
    if (isOpen) {
        formError.value = ''
        formSuccess.value = ''
        primeNewMoveDefaults()
    }
})

watch(() => route.query.createMove, (value) => {
    if (value === '1') {
        openNewMoveModal()
        return
    }

    if (showNewMove.value) {
        showNewMove.value = false
        formError.value = ''
        formSuccess.value = ''
    }
}, { immediate: true })

watch(() => newMove.driverId, (driverId) => {
    if (!driverId) return
    const selectedDriver = availableDrivers.value.find((driver) => driver.id === driverId)
    if (selectedDriver?.assignedVehicleId) {
        newMove.vehicleId = selectedDriver.assignedVehicleId
    }
})

watch([availableDrivers, vehicleOptions], () => {
    if (showNewMove.value) {
        primeNewMoveDefaults()
    }
})

// Fetch service moves from backend — fetch all active statuses separately
// (backend status_filter only accepts one value at a time)
async function fetchServiceMoves() {
    loading.value = true
    try {
        const [r1, r2, r3, r4] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=CONFIRMED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=DELIVERED&page_size=100`, { headers: authHeaders() }),
        ])
        const parse = async r => r.ok ? (await r.json()) : []
        const [d1, d2, d3, d4] = await Promise.all([parse(r1), parse(r2), parse(r3), parse(r4)])

        const assigned    = Array.isArray(d1) ? d1 : (d1.items || [])
        const inTransit   = Array.isArray(d2) ? d2 : (d2.items || [])
        const confirmed   = Array.isArray(d3) ? d3 : (d3.items || [])
        const delivered   = Array.isArray(d4) ? d4 : (d4.items || [])
        const isServiceMoveOrder = (order) => {
            const legacyTypes = ['House Shift', 'Office Shift', 'Warehouse Transfer']
            return String(order?.order_type || '').toUpperCase() === 'SERVICE_MOVE'
                || legacyTypes.includes(order?.cargo_type)
        }

        const activeMoves = [
            // All assigned orders that have a driver — regardless of type
            ...assigned.filter(o => o.assigned_driver_id),
            // All in-transit orders — they're on the road and need dispatcher visibility
            ...inTransit,
            // Only confirmed orders explicitly created as service moves
            ...confirmed.filter(isServiceMoveOrder),
        ]
        serviceMoves.value = activeMoves.map(mapServiceMoveFor)

        // Count completed today
        const today = new Date().toISOString().split('T')[0]
        completedToday.value = delivered.filter(o =>
            o.delivered_at?.startsWith(today) && isServiceMoveOrder(o)
        ).length
    } catch (err) {
        console.error('Failed to fetch service moves:', err)
    }
    loading.value = false
}

function mapServiceMoveFor(order) {
    return mapServiceMove(order, store.dispatcherDrivers, store.filteredVehicles)
}

function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}

function handleMapSelect(data) {
    if (mapPickerType.value === 'pickup') {
        newMove.pickup = data.address
        newMove.pickupLat = data.lat
        newMove.pickupLng = data.lon
    } else {
        newMove.delivery = data.address
        newMove.deliveryLat = data.lat
        newMove.deliveryLng = data.lon
    }
    showMapPicker.value = false
}

function useAssignedHub(type) {
    if (!assignedHub.value?.address) return

    const hubLat = assignedHub.value.lat !== null && assignedHub.value.lat !== undefined
        ? Number(assignedHub.value.lat)
        : null
    const hubLng = assignedHub.value.lng !== null && assignedHub.value.lng !== undefined
        ? Number(assignedHub.value.lng)
        : null

    if (type === 'pickup') {
        newMove.pickup = assignedHub.value.address
        newMove.pickupLat = hubLat
        newMove.pickupLng = hubLng
        return
    }

    newMove.delivery = assignedHub.value.address
    newMove.deliveryLat = hubLat
    newMove.deliveryLng = hubLng
}

const {
    trackMove,
    toggleMoveMenu,
    contactCrew,
    sendCrewMsg,
    cancelMove,
    completeMove,
} = useMoveCrewActions({
    authHeaders,
    completedToday,
    crewChatMove,
    crewMessages,
    crewMsg,
    crewThreadId,
    moveMenu,
    serviceMoves,
    showCrewChat,
    showTrackingModal,
    store,
    trackedDriver,
    trackingLoading,
    trackingMove,
})

const { createServiceMove } = useCreateServiceMove({
    authHeaders,
    buildServiceMoveMeta,
    buildServiceTimeBlock,
    closeNewMoveModal,
    fetchServiceMoves,
    formError,
    formSuccess,
    loading,
    newMove,
    resetNewMoveForm,
    selectedVehicleOption,
    toast,
})

provide(serviceMovesPageKey, {
    assignedHub,
    availableDrivers,
    blockedHours,
    cancelMove,
    closeNewMoveModal,
    completeMove,
    completedToday,
    contactCrew,
    createServiceMove,
    crewChatMove,
    crewMessages,
    crewMsg,
    crewThreadId,
    driverMapIcon,
    formError,
    formSuccess,
    loading,
    moveMenu,
    newMove,
    openMapPicker,
    realVehicleOptions,
    sendCrewMsg,
    serviceMoves,
    showCrewChat,
    showNewMove,
    showTrackingModal,
    toggleMoveMenu,
    totalCrewCount,
    trackMove,
    trackedDriver,
    trackingLoading,
    trackingMove,
    useAssignedHub,
    vehiclesReserved,
})
</script>
