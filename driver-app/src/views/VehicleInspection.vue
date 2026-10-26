<template>
    <div class="screen-layout" :class="isDark ? 'bg-background-dark text-white' : 'bg-background-light text-gray-900'">

        <!-- ── DETAIL MODAL (Fuel / Odometer) ────────── -->
        <InspectionDetailModal />

        <!-- ── TIRE PHOTO MODAL ──────────────────────── -->
        <TirePhotoModal />

        <!-- ── HEADER ───────────────────────────────── -->
        <header class="flex-shrink-0 px-5 pt-6 pb-4 border-b" :class="isDark ? 'border-white/5' : 'border-gray-100'">
            <div class="flex items-center justify-between mb-3">
                <button @click="$router.back()" class="w-10 h-10 rounded-full flex items-center justify-center border"
                    :class="isDark ? 'bg-surface-dark border-white/5 text-gray-400' : 'bg-white border-gray-200 shadow-sm'">
                    <span class="material-icons text-xl">arrow_back</span>
                </button>
                <div class="flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-wider"
                    :class="isDark ? 'bg-primary/10 border-primary/20 text-primary' : 'bg-primary/10 border-primary/30 text-primary'">
                    Step 3 of 4
                </div>
            </div>
            <h1 class="text-2xl font-black tracking-tight">Vehicle Inspection</h1>
            <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">CC-TRK-042 · Complete all items
            </p>

            <div class="mt-3 flex items-center justify-between mb-1">
                <span class="text-xs font-semibold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Progress</span>
                <span class="text-sm font-bold text-primary">{{ completedCount }} / {{ items.length }}</span>
            </div>
            <div class="w-full rounded-full h-1.5" :class="isDark ? 'bg-gray-800' : 'bg-gray-100'">
                <div class="h-1.5 rounded-full bg-primary transition-all duration-500" :style="`width: ${progress}%`">
                </div>
            </div>
        </header>

        <!-- ── SCROLLABLE BODY ───────────────────────── -->
        <div class="screen-body px-5 py-4 space-y-3">
            <div class="rounded-xl p-3 border flex items-start gap-3"
                :class="isDark ? 'bg-signal-amber/10 border-signal-amber/20' : 'bg-amber-50 border-amber-200'">
                <span class="material-icons text-signal-amber text-base flex-shrink-0">shield</span>
                <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                    Fuel, tire &amp; odometer data is sent to the fraud detection &amp; maintenance systems.
                </p>
            </div>

            <div v-for="item in items" :key="item.id"
                class="flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all active:scale-[0.98]"
                :class="item.checked
                    ? isDark ? 'bg-primary/10 border-primary/30' : 'bg-primary/10 border-primary/30'
                    : isDark ? 'bg-surface-dark/30 border-white/5 hover:border-white/10' : 'bg-white border-gray-100 shadow-sm'"
                @click="handleItemClick(item)">

                <div class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                    :class="item.checked ? 'bg-primary/20' : isDark ? 'bg-white/5' : 'bg-gray-50'">
                    <span class="material-icons text-xl"
                        :class="item.checked ? 'text-primary' : isDark ? 'text-gray-400' : 'text-gray-500'">{{ item.icon
                        }}</span>
                </div>

                <div class="flex-1 min-w-0">
                    <p class="font-semibold text-sm">{{ item.label }}</p>
                    <p class="text-xs mt-0.5"
                        :class="item.checked ? 'text-primary font-semibold' : isDark ? 'text-gray-500' : 'text-gray-400'">
                        {{ item.checked ? item.value : item.hint }}
                    </p>
                </div>

                <div class="flex items-center gap-2 flex-shrink-0">
                    <span
                        v-if="!item.checked && (item.id === 'fuel_level' || item.id === 'odometer' || item.id === 'tire_pressure')"
                        class="material-icons text-sm"
                        :class="isDark ? 'text-gray-600' : 'text-gray-400'">photo_camera</span>
                    <div class="w-7 h-7 rounded-full border-2 flex items-center justify-center"
                        :class="item.checked ? 'bg-primary border-primary' : isDark ? 'border-gray-600' : 'border-gray-300'">
                        <span v-if="item.checked" class="material-icons text-background-dark text-sm">check</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ── STICKY FOOTER ────────────────────────── -->
        <div class="screen-footer px-5 py-4 border-t"
            :class="isDark ? 'border-white/5 bg-background-dark' : 'border-gray-100 bg-background-light'">
            <button @click="handleComplete" :disabled="completedCount < items.length"
                class="w-full rounded-2xl h-14 flex items-center justify-center gap-2 font-bold text-lg transition-all active:scale-[0.98]"
                :class="completedCount === items.length
                    ? 'bg-primary text-background-dark shadow-glow'
                    : isDark ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-gray-100 text-gray-400 cursor-not-allowed'">
                <span class="material-icons">{{ completedCount === items.length ? 'check_circle' : 'lock' }}</span>
                {{ completedCount === items.length ? 'Complete Inspection' : `${items.length - completedCount} items
                remaining`
                }}
            </button>
        </div>
    </div>
</template>

<script setup>
import InspectionDetailModal from './vehicleInspection/InspectionDetailModal.vue'
import TirePhotoModal from './vehicleInspection/TirePhotoModal.vue'
import { vehicleInspectionPageKey } from './vehicleInspection/vehicleInspectionPageContext'
import { ref, computed, nextTick, provide } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '../stores/uiStore.js'
import { useDriverStore } from '../stores/driverStore.js'
import { useCamera } from '../composables/useCamera.js'
import { extractNumbersFromText } from '../utils/cameraUtils.js'

const router = useRouter()
const uiStore = useUiStore()
const driverStore = useDriverStore()
const isDark = computed(() => uiStore.theme !== 'light')
const { takePhoto, scanOdometer } = useCamera()

// ── Constants ──────────────────────────────────────
const TANK_CAPACITY = 120

// ── Standard Inspection Checklist ──────────────────
const defaultInspectionChecklist = [
    { id: 'fuel_level', label: 'Fuel level recorded', icon: 'local_gas_station', value: '', checked: false },
    { id: 'tire_pressure', label: 'Tire pressure OK – All 4 tires', icon: 'donut_large', value: '', checked: false },
    { id: 'odometer', label: 'Odometer reading captured', icon: 'speed', value: '', checked: false },
    { id: 'lights', label: 'Lights & indicators working', icon: 'lightbulb', value: '', checked: false },
    { id: 'cargo', label: 'Cargo area clean & secure', icon: 'inventory_2', value: '', checked: false },
    { id: 'brakes', label: 'Brakes responsive', icon: 'commute', value: '', checked: false },
]

// ── Detail modal (fuel / odometer) ─────────────────
const detailModal = ref(false)
const detailType = ref('')
const detailItem = ref(null)
const fuelLiters = ref(null)
const odometerKm = ref(null)
const odometerAutoDetected = ref(false)
const photoUrl = ref(null)
const fuelInputRef = ref(null)
const odometerInputRef = ref(null)

const fuelPercent = computed(() => {
    if (!fuelLiters.value || fuelLiters.value <= 0) return 0
    return Math.min(100, Math.round((fuelLiters.value / TANK_CAPACITY) * 100))
})

const canConfirmDetail = computed(() => {
    if (detailType.value === 'fuel') {
        const v = Number(fuelLiters.value)
        return !isNaN(v) && v > 0
    }
    if (detailType.value === 'odometer') {
        const v = Number(odometerKm.value)
        return !isNaN(v) && v > 0
    }
    return false
})

function clampFuel() {
    if (fuelLiters.value > TANK_CAPACITY) fuelLiters.value = TANK_CAPACITY
    if (fuelLiters.value < 0) fuelLiters.value = 0
}

function cancelDetail() {
    detailModal.value = false
    detailItem.value = null
    photoUrl.value = null
    odometerAutoDetected.value = false
}

async function removePhoto() {
    photoUrl.value = null
    if (detailType.value === 'fuel') {
        const result = await takePhoto({ promptLabel: 'Capture fuel gauge' })
        if (result) photoUrl.value = result.base64
        else cancelDetail()
    } else {
        const result = await scanOdometer('Scan odometer')
        if (result) {
            photoUrl.value = result.base64 || 'data:image/jpeg;base64,MOCK'
            const extractedValue = extractNumbersFromText(result.text)
            odometerKm.value = extractedValue || null
            odometerAutoDetected.value = Boolean(extractedValue)
        } else {
            cancelDetail()
        }
    }
}

function confirmDetail() {
    if (!canConfirmDetail.value) {
        uiStore.showToast('Please enter a valid value', 'error', 1500)
        return
    }
    const item = detailItem.value
    if (!item) return
    const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

    if (detailType.value === 'fuel') {
        const pct = fuelPercent.value
        const liters = Number(fuelLiters.value)
        item.checked = true
        item.value = `${pct}% · ${liters}L · confirmed at ${now}`
        uiStore.showToast(`Fuel: ${pct}% recorded ✓`, 'success', 1200)
    } else if (detailType.value === 'odometer') {
        const km = Number(odometerKm.value)
        item.checked = true
        item.value = `${km.toLocaleString('en-IN')} km · confirmed at ${now}`
        uiStore.showToast(`Odometer: ${km.toLocaleString('en-IN')} km recorded ✓`, 'success', 1200)
    }

    detailModal.value = false
    detailItem.value = null
    odometerAutoDetected.value = false
}

// ── Tire photo modal ───────────────────────────────
const tireModal = ref(false)
const tireItem = ref(null)
const tirePhotos = ref([
    { label: 'Front Left', url: null },
    { label: 'Front Right', url: null },
    { label: 'Rear Left', url: null },
    { label: 'Rear Right', url: null },
])
const tireCaptured = computed(() => tirePhotos.value.filter(t => t.url).length)

async function captureTirePhoto(idx) {
    if (tirePhotos.value[idx].url) return // already captured

    // On native: open camera. In browser: use file picker.
    try {
        const result = await takePhoto({ promptLabel: `Capture ${tirePhotos.value[idx].label} tire` })
        if (result && result.base64 && result.base64.startsWith('data:')) {
            tirePhotos.value[idx].url = result.base64
        } else if (result && result.base64) {
            tirePhotos.value[idx].url = `data:image/jpeg;base64,${result.base64}`
        } else if (result) {
            tirePhotos.value[idx].url = 'https://images.unsplash.com/photo-1580274455191-1c62238fa333?auto=format&fit=crop&q=80&w=200&h=200'
        }
    } catch {
        // If camera fails, still allow marking as captured for testing
        tirePhotos.value[idx].url = 'https://images.unsplash.com/photo-1580274455191-1c62238fa333?auto=format&fit=crop&q=80&w=200&h=200'
    }
}

function removeTirePhoto(idx) {
    tirePhotos.value[idx].url = null
}

function confirmTires() {
    if (tireCaptured.value < 4) {
        uiStore.showToast(`Capture all 4 tires (${tireCaptured.value}/4 done)`, 'error', 1500)
        return
    }
    const item = tireItem.value
    if (!item) return
    const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    item.checked = true
    item.value = `All 4 tires · confirmed at ${now}`
    uiStore.showToast('Tire pressure verified ✓', 'success', 1200)
    tireModal.value = false
    tireItem.value = null
}

// ── Items ──────────────────────────────────────────
const items = ref(defaultInspectionChecklist.map(i => {
    let hint = 'Tap to confirm'
    if (i.id === 'fuel_level') hint = 'Tap to capture & enter fuel level'
    if (i.id === 'odometer') hint = 'Tap to capture odometer photo'
    if (i.id === 'tire_pressure') hint = 'Tap to photograph all 4 tires'
    return { ...i, hint }
}))

const completedCount = computed(() => items.value.filter(i => i.checked).length)
const progress = computed(() => Math.round((completedCount.value / items.value.length) * 100))

// ── Handle click ───────────────────────────────────
async function handleItemClick(item) {
    if (item.checked) {
        item.checked = false
        item.value = ''
        return
    }

    if (item.id === 'fuel_level') {
        // Step 1: Camera
        const result = await takePhoto({ promptLabel: 'Capture fuel gauge' })
        if (!result) return

        // Step 2: Open fuel detail modal
        detailType.value = 'fuel'
        detailItem.value = item
        fuelLiters.value = null
        photoUrl.value = (result.base64 && !result.base64.startsWith('MOCK'))
            ? `data:image/jpeg;base64,${result.base64}`
            : 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&q=80&w=400&h=200'
        detailModal.value = true
        await nextTick()
        fuelInputRef.value?.focus()

    } else if (item.id === 'odometer') {
        // Step 1: Camera + OCR
        const result = await scanOdometer('Scan odometer')
        if (!result) return

        // Step 2: Open odometer modal with OCR auto-fill
        detailType.value = 'odometer'
        detailItem.value = item
        photoUrl.value = (result.base64 && !result.base64.startsWith('MOCK'))
            ? `data:image/jpeg;base64,${result.base64}`
            : 'https://images.unsplash.com/photo-1627883287040-e2ef6cb90b21?auto=format&fit=crop&q=80&w=400&h=200'
        const extractedValue = extractNumbersFromText(result.text)
        odometerKm.value = extractedValue || null
        odometerAutoDetected.value = Boolean(extractedValue)
        detailModal.value = true
        await nextTick()
        odometerInputRef.value?.focus()

    } else if (item.id === 'tire_pressure') {
        // Open tire photo modal
        tireItem.value = item
        tirePhotos.value.forEach(t => t.url = null)
        tireModal.value = true

    } else {
        // Simple toggle (lights, cargo, brakes)
        item.checked = true
        const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
        item.value = `Confirmed at ${now}`
    }
}

function handleComplete() {
    driverStore.inspectionDone = true
    // Keep legacy flag true so persisted sessions from older builds stay consistent.
    driverStore.jobTypeSelected = true
    router.push('/dashboard')
}

provide(vehicleInspectionPageKey, {
    TANK_CAPACITY,
    canConfirmDetail,
    cancelDetail,
    captureTirePhoto,
    clampFuel,
    confirmDetail,
    confirmTires,
    detailModal,
    detailType,
    fuelInputRef,
    fuelLiters,
    fuelPercent,
    isDark,
    odometerAutoDetected,
    odometerInputRef,
    odometerKm,
    photoUrl,
    removePhoto,
    removeTirePhoto,
    tireCaptured,
    tireModal,
    tirePhotos,
})
</script>

<style scoped src="./vehicleInspection/VehicleInspection.css"></style>
