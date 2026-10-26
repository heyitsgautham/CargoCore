<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Recurring Shipments</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Automate your regular shipping schedules</p>
            </div>
            <button @click="openCreateModal"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px]">add</span> Create Schedule
            </button>
        </div>

        <!-- Summary Chips -->
        <div class="flex flex-wrap gap-3">
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-500 text-[18px]">schedule</span>
                <span class="text-sm font-bold text-gray-900 dark:text-white">{{ store.recurringRules.length }}</span>
                <span class="text-xs text-gray-500">Total</span>
            </div>
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-green-500 text-[18px]">toggle_on</span>
                <span class="text-sm font-bold text-green-500">{{ activeCount }}</span>
                <span class="text-xs text-gray-500">Active</span>
            </div>
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-gray-400 text-[18px]">toggle_off</span>
                <span class="text-sm font-bold text-gray-400">{{ store.recurringRules.length - activeCount }}</span>
                <span class="text-xs text-gray-500">Paused</span>
            </div>
        </div>

        <!-- Loading skeleton -->
        <div v-if="store.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="i in 3" :key="i" class="glass-panel p-5 rounded-xl animate-pulse">
                <div class="flex justify-between mb-4">
                    <div class="h-5 w-20 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="flex gap-1">
                        <div class="h-7 w-7 bg-gray-200 dark:bg-white/10 rounded-lg"></div>
                        <div class="h-7 w-7 bg-gray-200 dark:bg-white/10 rounded-lg"></div>
                    </div>
                </div>
                <div class="h-5 w-3/4 bg-gray-200 dark:bg-white/10 rounded mb-2"></div>
                <div class="h-4 w-full bg-gray-200 dark:bg-white/10 rounded mb-4"></div>
                <div class="space-y-2 mb-4">
                    <div class="h-4 w-2/3 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-4 w-1/2 bg-gray-200 dark:bg-white/10 rounded"></div>
                </div>
                <div class="flex justify-between pt-3 border-t border-gray-100 dark:border-white/5">
                    <div class="h-4 w-24 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-5 w-9 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                </div>
            </div>
        </div>

        <!-- Rules Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <RuleCardsGrid />
        </div>

        <!-- Create / Edit Modal -->
        <Teleport to="body">
            <RuleFormModal />
        </Teleport>

        <!-- Delete Confirmation Modal -->
        <Teleport to="body">
            <DeleteRuleModal />
        </Teleport>

        <Teleport to="body">
            <MapPicker
                v-if="showDestinationMapPicker"
                :isOpen="showDestinationMapPicker"
                title="Select Recurring Destination on Map"
                :initial-lat="destinationMapInitialLat"
                :initial-lon="destinationMapInitialLon"
                @close="showDestinationMapPicker = false"
                @select="handleDestinationSelect"
            />
        </Teleport>
    </div>
</template>

<script setup>
import RuleCardsGrid from './recurring/RuleCardsGrid.vue'
import RuleFormModal from './recurring/RuleFormModal.vue'
import DeleteRuleModal from './recurring/DeleteRuleModal.vue'
import { recurringPageKey } from './recurring/recurringPageContext'
import { localDateISO } from '@/utils/date'
import { computed, defineAsyncComponent, ref, watch, provide } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'

const store = useVendorStore()
const MapPicker = defineAsyncComponent(() => import('@/components/MapPicker.vue'))

// Modal state
const showFormModal = ref(false)
const showDeleteModal = ref(false)
const editingRule = ref(null)
const deletingRule = ref(null)
const showDestinationMapPicker = ref(false)
const destinationMapInitialLat = ref(12.9716)
const destinationMapInitialLon = ref(77.5946)

// Cost estimate state
const costEstimate = ref(null)
const costEstimateLoading = ref(false)
let costEstimateDebounce = null

// Loading/error state
const isSubmitting = ref(false)
const isDeleting = ref(false)
const togglingId = ref(null)
const submitError = ref('')
const deleteError = ref('')
const formErrors = ref({})

// Form
const defaultForm = {
    name: '',
    description: '',
    frequency: 'Every Monday',
    hubId: '',
    hub: '',
    dropOffTime: '09:00',
    destinationAddress: '',
    destinationCity: '',
    destinationPincode: '',
    destinationLat: null,
    destinationLon: null,
    details: '',
    autoDebitEnabled: false,
    nextRun: '',
}
const form = ref({ ...defaultForm })

// Today's date for the date picker minimum
const todayISO = localDateISO()

const activeCount = computed(() => store.recurringRules.filter(r => r.active).length)
const availableHubs = computed(() => (store.warehouses || []).map((hub) => ({
    id: String(hub.id),
    name: hub.name,
    address: hub.address || '',
    lat: hub.lat ?? null,
    lng: hub.lng ?? null,
})))
const selectedHub = computed(() => availableHubs.value.find((hub) => hub.id === form.value.hubId) || null)

function parseRuleDetails(details) {
    try {
        const parsed = JSON.parse(details)
        if (parsed && typeof parsed === 'object' && parsed.cargo) {
            return {
                cargo: parsed.cargo,
                hubId: parsed.hubId || '',
                hub: parsed.hub || '',
                dropOffTime: parsed.dropOffTime || '',
                destinationAddress: parsed.destinationAddress || '',
                destinationCity: parsed.destinationCity || '',
                destinationPincode: parsed.destinationPincode || '',
                destinationLat: parsed.destinationLat ?? null,
                destinationLon: parsed.destinationLon ?? null,
                autoDebitEnabled: !!parsed.autoDebitEnabled,
            }
        }
    } catch (e) {
        // Ignore parse errors for legacy plain-text details
    }
    return {
        cargo: details || '—',
        hubId: '',
        hub: '',
        dropOffTime: '',
        destinationAddress: '',
        destinationCity: '',
        destinationPincode: '',
        destinationLat: null,
        destinationLon: null,
        autoDebitEnabled: false,
    }
}

function getRuleMeta(rule) {
    return parseRuleDetails(rule.details)
}

function inferDestinationFromRoute(route) {
    if (!route) return ''
    const parts = String(route).split('→').map((part) => part.trim()).filter(Boolean)
    return parts[parts.length - 1] || ''
}

function inferHubFromRoute(route) {
    if (!route) return ''
    const parts = String(route).split('→').map((part) => part.trim()).filter(Boolean)
    return parts[0] || ''
}

function formatRuleDestination(meta) {
    const address = meta.destinationAddress || ''
    const city = meta.destinationCity || ''
    const pincode = meta.destinationPincode || ''
    if (address && city) return `${address}, ${city}${pincode ? ` - ${pincode}` : ''}`
    if (address) return address
    if (city) return `${city}${pincode ? ` - ${pincode}` : ''}`
    return '—'
}

function buildDetailsPayload() {
    return JSON.stringify({
        hubId: form.value.hubId,
        cargo: form.value.details,
        hub: selectedHub.value?.name || form.value.hub,
        dropOffTime: form.value.dropOffTime,
        destinationAddress: form.value.destinationAddress,
        destinationCity: form.value.destinationCity,
        destinationPincode: form.value.destinationPincode,
        destinationLat: form.value.destinationLat,
        destinationLon: form.value.destinationLon,
        autoDebitEnabled: !!form.value.autoDebitEnabled,
    })
}

function buildRoutePayload() {
    const hubLabel = (selectedHub.value?.name || form.value.hub || 'Vendor Hub').trim()
    const destinationLabel = (form.value.destinationCity || form.value.destinationAddress || 'Destination').trim()
    const compactRoute = `${hubLabel} → ${destinationLabel}`
    return compactRoute.length > 240 ? `${hubLabel} → ${destinationLabel.slice(0, 180)}…` : compactRoute
}

function findHubBySavedMeta(meta, route = '') {
    const savedHubId = meta.hubId ? String(meta.hubId) : ''
    const savedHubName = meta.hub || inferHubFromRoute(route) || ''
    return availableHubs.value.find((hub) => hub.id === savedHubId)
        || availableHubs.value.find((hub) => hub.name === savedHubName)
        || null
}

function formatNextRun(val) {
    if (!val) return '—'
    // If ISO date string (YYYY-MM-DD), format nicely
    if (/^\d{4}-\d{2}-\d{2}/.test(val)) {
        return new Date(val + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    }
    return val
}

function validateForm() {
    const errs = {}
    if (!form.value.name?.trim()) errs.name = 'Schedule name is required'
    if (!form.value.hubId?.trim()) errs.hub = 'Hub is required'
    if (!form.value.dropOffTime) errs.dropOffTime = 'Drop time is required'
    if (!form.value.destinationAddress?.trim()) errs.destinationAddress = 'Destination is required'
    if (!form.value.destinationCity?.trim()) errs.destinationCity = 'Destination city is required'
    if (!form.value.destinationPincode?.trim()) errs.destinationPincode = 'Destination pincode is required'
    if (!form.value.details?.trim()) errs.details = 'Cargo details are required'
    if (!form.value.nextRun) errs.nextRun = 'Next run date is required'
    formErrors.value = errs
    return Object.keys(errs).length === 0
}

async function toggleRule(rule) {
    if (togglingId.value) return
    togglingId.value = rule.id
    try {
        await store.toggleRecurringRule(rule.id)
        showToast(rule.active ? `"${rule.name}" paused` : `"${rule.name}" activated`)
    } catch (e) {
        showToast(e?.message || 'Failed to toggle schedule', 'error')
    } finally {
        togglingId.value = null
    }
}

async function openCreateModal() {
    if (!availableHubs.value.length) {
        await store.fetchWarehouses().catch(() => {})
    }
    editingRule.value = null
    form.value = { ...defaultForm }
    formErrors.value = {}
    submitError.value = ''
    showFormModal.value = true
}

function openEditModal(rule) {
    editingRule.value = rule
    const parsedDetails = parseRuleDetails(rule.details)
    const matchedHub = findHubBySavedMeta(parsedDetails, rule.route)
    // Normalize nextRun to ISO date if possible
    let nextRun = rule.nextRun || ''
    if (nextRun && !/^\d{4}-\d{2}-\d{2}/.test(nextRun)) {
        const parsed = new Date(nextRun)
        if (!isNaN(parsed)) nextRun = localDateISO(parsed)
    }
    const destinationAddress = parsedDetails.destinationAddress || inferDestinationFromRoute(rule.route) || ''
    form.value = {
        name: rule.name,
        description: rule.description || '',
        frequency: rule.frequency,
        hubId: matchedHub?.id || '',
        hub: matchedHub?.name || parsedDetails.hub || inferHubFromRoute(rule.route) || '',
        dropOffTime: parsedDetails.dropOffTime || '09:00',
        destinationAddress,
        destinationCity: parsedDetails.destinationCity || '',
        destinationPincode: parsedDetails.destinationPincode || '',
        destinationLat: parsedDetails.destinationLat ?? null,
        destinationLon: parsedDetails.destinationLon ?? null,
        details: parsedDetails.cargo,
        autoDebitEnabled: !!parsedDetails.autoDebitEnabled,
        nextRun,
    }
    formErrors.value = {}
    submitError.value = ''
    showFormModal.value = true
}

function closeFormModal() {
    showFormModal.value = false
    submitError.value = ''
    formErrors.value = {}
}

function openDestinationMapPicker() {
    destinationMapInitialLat.value = Number(form.value.destinationLat ?? 12.9716)
    destinationMapInitialLon.value = Number(form.value.destinationLon ?? 77.5946)
    showDestinationMapPicker.value = true
}

function handleDestinationSelect(data) {
    form.value.destinationAddress = data.address
    form.value.destinationLat = data.lat
    form.value.destinationLon = data.lon
    showDestinationMapPicker.value = false
    triggerCostEstimate()
}

function triggerCostEstimate() {
    clearTimeout(costEstimateDebounce)
    const lat = form.value.destinationLat
    const lon = form.value.destinationLon
    const hubId = form.value.hubId
    const hubName = selectedHub.value?.name || form.value.hub
    if (!lat || !lon || !hubId) {
        costEstimate.value = null
        return
    }
    costEstimateDebounce = setTimeout(() => fetchCostEstimate({ hubId, hubName, lat, lon }), 300)
}

async function fetchCostEstimate({ hubId, hubName, lat, lon }) {
    costEstimateLoading.value = true
    try {
        costEstimate.value = await store.estimateRecurringCost({
            hubId,
            hubName: hubName || '',
            destinationLat: lat,
            destinationLon: lon,
            destinationAddress: form.value.destinationAddress || '',
        })
    } catch (e) {
        costEstimate.value = null
    } finally {
        costEstimateLoading.value = false
    }
}

// Re-fetch if hub changes after destination already selected
watch(() => form.value.hubId, () => {
    form.value.hub = selectedHub.value?.name || ''
    if (form.value.destinationLat && form.value.destinationLon) {
        triggerCostEstimate()
    }
})

async function submitForm() {
    if (!validateForm()) return
    isSubmitting.value = true
    submitError.value = ''
    try {
        if (editingRule.value) {
            await store.updateRecurringRule(editingRule.value.id, {
                ...form.value,
                route: buildRoutePayload(),
                details: buildDetailsPayload(),
                active: editingRule.value.active,
            })
            showToast('Schedule updated')
        } else {
            await store.addRecurringRule({
                ...form.value,
                route: buildRoutePayload(),
                details: buildDetailsPayload(),
                active: true,
            })
            showToast('Schedule created')
        }
        closeFormModal()
    } catch (e) {
        submitError.value = e?.message || 'Something went wrong. Please try again.'
    } finally {
        isSubmitting.value = false
    }
}

function confirmDelete(rule) {
    deletingRule.value = rule
    deleteError.value = ''
    showDeleteModal.value = true
}

async function executeDelete() {
    if (!deletingRule.value) return
    isDeleting.value = true
    deleteError.value = ''
    try {
        await store.deleteRecurringRule(deletingRule.value.id)
        showDeleteModal.value = false
        showToast('Schedule deleted')
        deletingRule.value = null
    } catch (e) {
        deleteError.value = e?.message || 'Failed to delete. Please try again.'
    } finally {
        isDeleting.value = false
    }
}

function formatPickupSourceLabel(source) {
    return {
        warehouse_coordinates: 'Warehouse Coordinates',
        geofence_zone: 'Geofence Zone Center',
        missing_coordinates: 'Base Fee Only',
    }[source] || 'Estimated Pickup Source'
}

function formatDistanceMethodLabel(method) {
    return {
        road_route: 'Road Route Estimate',
        road_route_fallback: 'Route Fallback Estimate',
    }[method] || 'Distance Estimate'
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    t.className = `fixed right-4 bottom-4 z-[9999] text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

provide(recurringPageKey, {
    availableHubs,
    closeFormModal,
    confirmDelete,
    costEstimate,
    costEstimateLoading,
    deleteError,
    deletingRule,
    editingRule,
    executeDelete,
    form,
    formErrors,
    formatDistanceMethodLabel,
    formatNextRun,
    formatPickupSourceLabel,
    formatRuleDestination,
    getRuleMeta,
    isDeleting,
    isSubmitting,
    openCreateModal,
    openDestinationMapPicker,
    openEditModal,
    selectedHub,
    showDeleteModal,
    showFormModal,
    store,
    submitError,
    submitForm,
    todayISO,
    toggleRule,
    togglingId,
})
</script>
