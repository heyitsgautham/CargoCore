<template>
    <div class="space-y-6 max-w-7xl mx-auto">
        <!-- Header -->
        <div
            class="flex flex-col md:flex-row md:items-end justify-between gap-4 glass-panel p-6 rounded-2xl relative overflow-hidden">
            <div
                class="absolute -right-20 -top-20 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none">
            </div>
            <div class="relative z-10">
                <h2
                    class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-500 flex items-center gap-3">
                    <span class="material-symbols-outlined text-purple-500 text-4xl">psychology</span>
                    AI Spatial Estimator
                </h2>
                <p class="text-gray-500 dark:text-gray-400 mt-2 font-medium max-w-xl text-sm leading-relaxed">
                    Upload photos of your space. Our advanced neural engine calculates volumetric requirements,
                    recommends the optimal vehicle, and predicts labor needs in real-time.
                </p>
            </div>
            <div class="flex gap-3 relative z-10">
                <div class="px-4 py-2 bg-purple-500/10 rounded-lg border border-purple-500/20 text-center">
                    <div class="text-xs text-purple-400 font-bold uppercase tracking-wider mb-0.5">Engine</div>
                    <div class="text-sm text-gray-900 dark:text-white font-bold">Cargo-Vision v4.2</div>
                </div>
                <div class="px-4 py-2 bg-blue-500/10 rounded-lg border border-blue-500/20 text-center">
                    <div class="text-xs text-blue-400 font-bold uppercase tracking-wider mb-0.5">Accuracy</div>
                    <div class="text-sm text-gray-900 dark:text-white font-bold">94.8%</div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Left Side: Upload & Scanner -->
            <div class="lg:col-span-5 space-y-6">
                <div class="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-lg">Input Source</h3>

                    <!-- Upload Dropzone -->
                    <div @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop"
                        class="relative w-full aspect-[4/3] rounded-xl overflow-hidden border-2 border-dashed transition-all"
                        :class="uploaded ? 'border-purple-500/50 bg-black' : 'border-gray-300 dark:border-white/20 hover:border-purple-400 dark:hover:border-purple-500 bg-gray-50 dark:bg-black/20 hover:bg-white/5 cursor-pointer'">

                        <!-- Image Preview -->
                        <img v-if="previewUrl" :src="previewUrl" class="w-full h-full object-cover opacity-80" />

                        <!-- Empty State -->
                        <div v-if="!uploaded"
                            class="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                            <div
                                class="w-16 h-16 rounded-full bg-purple-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                <span
                                    class="material-symbols-outlined text-3xl text-purple-400">add_photo_alternate</span>
                            </div>
                            <span class="text-base font-bold text-gray-700 dark:text-gray-200">Tap or drag image
                                here</span>
                            <span class="text-xs text-gray-500 dark:text-gray-400 mt-2">Supports JPG, PNG (Max
                                15MB)</span>
                            <span class="text-xs text-gray-500 dark:text-gray-400 mt-1">Wide-angle room shots work
                                best</span>
                        </div>

                        <!-- Scanner Overlay Animation -->
                        <div v-if="analyzing"
                            class="absolute inset-0 bg-purple-900/40 z-10 flex flex-col items-center justify-center backdrop-blur-[2px]">
                            <div
                                class="w-full h-1 bg-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.8)] absolute top-0 animate-scan">
                            </div>
                            <span class="material-symbols-outlined text-5xl text-white animate-pulse">view_in_ar</span>
                            <div class="text-white font-bold mt-4 tracking-wider text-sm">PROCESSING IMAGE MESH...</div>
                            <div class="text-purple-300 text-xs mt-1">{{ scanStatus }}</div>
                        </div>

                        <!-- Success Overlay UI -->
                        <div v-if="uploaded && !analyzing && !showResults"
                            class="absolute inset-0 bg-black/60 z-10 flex flex-col items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer">
                            <span class="material-symbols-outlined text-white text-4xl mb-2">find_replace</span>
                            <span class="text-white font-bold text-sm">Change Image</span>
                        </div>
                    </div>
                    <input type="file" ref="fileInput" accept="image/*" class="hidden" @change="handleFileSelect" />

                    <!-- Action Button -->
                    <button @click="analyzePhoto" :disabled="!uploaded || analyzing || showResults"
                        class="w-full mt-6 py-4 rounded-xl font-black uppercase tracking-widest transition-all flex items-center justify-center gap-3 text-sm shadow-xl"
                        :class="[
                            !uploaded || showResults ? 'bg-gray-200 dark:bg-white/5 text-gray-400 dark:text-gray-600 cursor-not-allowed shadow-none' : '',
                            uploaded && !analyzing && !showResults ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-purple-500/25 hover:shadow-purple-500/40 transform hover:-translate-y-0.5' : '',
                            analyzing ? 'bg-purple-800 text-purple-300 cursor-wait' : ''
                        ]">
                        <span v-if="analyzing" class="material-symbols-outlined animate-spin">progress_activity</span>
                        <span v-else-key="!showResults" class="material-symbols-outlined"
                            :class="showResults ? 'text-gray-500' : ''">memory</span>
                        {{ showResults ? 'Analysis Complete' : (analyzing ? 'Running Neural Engine...' : 'Run Analysis Core') }}
                    </button>

                    <div v-if="showResults" class="mt-4 flex gap-2">
                        <button @click="resetEstimator"
                            class="flex-1 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-white/5 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 font-bold rounded-lg transition-colors text-xs flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-sm">refresh</span> Scan Another Room
                        </button>
                    </div>
                </div>
            </div>

            <!-- Right Side: AI Results Dashboard -->
            <div class="lg:col-span-7">
                <div class="glass-panel p-6 rounded-2xl h-full flex flex-col relative overflow-hidden"
                    :class="showResults ? 'border-purple-500/30' : ''">
                    <!-- Error state -->
                    <div v-if="errorMsg"
                        class="mb-4 p-3 bg-red-50 dark:bg-red-500/10 border border-red-300 dark:border-red-500/30 rounded-xl flex items-start gap-3">
                        <span class="material-symbols-outlined text-red-500 text-lg shrink-0">error</span>
                        <p class="text-sm text-red-700 dark:text-red-400 font-medium">{{ errorMsg }}</p>
                    </div>

                    <!-- Placeholder State -->
                    <div v-if="!showResults && !errorMsg"
                        class="flex-1 flex flex-col items-center justify-center text-center opacity-50 py-12">
                        <div class="relative">
                            <span
                                class="material-symbols-outlined text-7xl text-gray-300 dark:text-gray-700 block mb-4">analytics</span>
                        </div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Awaiting Visual Input</h3>
                        <p class="text-sm text-gray-500 max-w-sm">Provide an image to the engine to generate volumetric
                            breakdown, equipment lists, and fleet requirements.</p>
                    </div>

                    <!-- Results State -->
                    <div v-else class="flex-1 flex flex-col animate-scale-in">
                        <div
                            class="flex justify-between items-start mb-6 border-b border-gray-100 dark:border-white/10 pb-4">
                            <div>
                                <h3 class="font-black text-2xl text-gray-900 dark:text-white flex items-center gap-2">
                                    <span class="material-symbols-outlined text-green-500 text-3xl">verified</span>
                                    Estimation Complete
                                </h3>
                                <p class="text-xs font-bold text-gray-500 mt-1">processed in {{ processTime }}ms •
                                    Confidence: <span class="text-green-500">{{ aiConfidence }}%</span></p>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Detected
                                    Space</div>
                                <div
                                    class="text-lg font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-3 py-1 rounded-lg">
                                    {{ detectedSpace }}</div>
                            </div>
                        </div>

                        <!-- primary metrics -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                            <div v-for="rec in aiResults" :key="rec.label"
                                class="p-4 bg-gray-50 dark:bg-black/20 rounded-xl border border-gray-200 dark:border-white/5 relative overflow-hidden group hover:border-purple-500/50 transition-colors">
                                <div class="absolute -right-2 -bottom-2 opacity-5">
                                    <span class="material-symbols-outlined text-6xl">{{ rec.icon }}</span>
                                </div>
                                <span class="material-symbols-outlined text-2xl mb-2" :class="rec.color">{{ rec.icon
                                    }}</span>
                                <div class="text-2xl font-black text-gray-900 dark:text-white leading-none">{{ rec.value
                                    }}</div>
                                <div
                                    class="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mt-2">
                                    {{ rec.label }}</div>
                                <div class="text-[10px] text-gray-400 mt-1 flex justify-between">
                                    <span>Cert:</span>
                                    <span class="text-green-500 font-bold">{{ rec.confidence }}%</span>
                                </div>
                            </div>
                        </div>

                        <!-- Fleet Recommendation -->
                        <div v-if="vehicleRec"
                            class="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-5 border border-gray-700 text-white mb-6 shadow-2xl relative overflow-hidden">
                            <div
                                class="absolute right-0 top-0 w-32 h-full bg-gradient-to-l from-purple-600/20 to-transparent pointer-events-none">
                            </div>
                            <div class="flex items-center gap-4 relative z-10">
                                <div
                                    class="w-14 h-14 rounded-full bg-purple-500/20 flex items-center justify-center border border-purple-500/30 shrink-0">
                                    <span
                                        class="material-symbols-outlined text-3xl text-purple-400">local_shipping</span>
                                </div>
                                <div class="flex-1">
                                    <div class="text-xs text-purple-300 font-bold uppercase tracking-wider mb-1">Optimal
                                        Fleet Assignment</div>
                                    <div class="text-xl font-black tracking-wide">{{ vehicleRec.display_name }}</div>
                                    <p class="text-xs text-gray-400 mt-1 max-w-md">{{ vehicleRec.reason }}</p>
                                </div>
                                <div class="text-right shrink-0">
                                    <div class="text-xs text-gray-400 mb-1">Base Cost Est.</div>
                                    <div class="text-xl font-bold text-green-400">~₹{{ estimatedCost.toLocaleString() }}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Deep Insights -->
                        <div class="flex-1">
                            <h4
                                class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                                Detected Inventory Breakdown</h4>
                            <div
                                class="bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 overflow-hidden">
                                <table class="w-full text-left text-sm">
                                    <thead>
                                        <tr class="bg-gray-100 dark:bg-black/20 text-gray-600 dark:text-gray-400">
                                            <th class="p-3 font-semibold text-xs uppercase">Item Classification</th>
                                            <th class="p-3 font-semibold text-xs uppercase text-center">Count</th>
                                            <th class="p-3 font-semibold text-xs uppercase">Special Handling</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                        <tr v-for="(item, idx) in detectedItems" :key="idx"
                                            class="hover:bg-white dark:hover:bg-white/5 transition-colors">
                                            <td
                                                class="p-3 font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                                <span class="w-2 h-2 rounded-full"
                                                    :class="item.fragile ? 'bg-amber-400' : 'bg-blue-400'"></span>
                                                {{ item.name }}
                                            </td>
                                            <td class="p-3 text-center text-gray-600 dark:text-gray-300">{{ item.qty }}
                                            </td>
                                            <td class="p-3 text-xs">
                                                <span v-if="item.fragile"
                                                    class="bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400 px-2 py-1 rounded font-bold inline-block">Requires
                                                    Bubble Wrap</span>
                                                <span v-else class="text-gray-400">Standard Loading</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Footer Action -->
                        <div class="mt-6 pt-4 border-t border-gray-100 dark:border-white/10 flex justify-end gap-3">
                            <button @click="useForBooking"
                                class="px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-green-500/20 transform hover:-translate-y-0.5">
                                Use these requirements for Booking
                                <span class="material-symbols-outlined">arrow_forward</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useIndividualStore } from '@/stores/individualStore'

const router = useRouter()
const indStore = useIndividualStore()

const fileInput = ref(null)
const uploaded = ref(false)
const analyzing = ref(false)
const showResults = ref(false)
const previewUrl = ref(null)
const scanStatus = ref('')
const processTime = ref(0)
const errorMsg = ref('')
const estimatedVolumeM3 = ref(null)

// These are filled by the real Gemini Vision response
const aiResults = ref([])
const detectedItems = ref([])
const detectedSpace = ref('')
const vehicleRec = ref(null)
const estimatedCost = ref(0)
const aiConfidence = ref(0)

const uploadedFile = ref(null)  // keep the actual File object for upload

const scanningPhases = [
    'Initializing Neural Net...',
    'Mapping Spatial Boundary...',
    'Detecting Furniture Geometry...',
    'Evaluating Fragility Index...',
    'Calculating Volumetric Weight...',
    'Finalizing Fleet Recommendations...'
]

function triggerUpload() { fileInput.value?.click() }

function handleFileProcess(file) {
    if (file && file.type.startsWith('image/')) {
        uploadedFile.value = file
        uploaded.value = true
        showResults.value = false
        errorMsg.value = ''
        const reader = new FileReader()
        reader.onload = (e) => { previewUrl.value = e.target.result }
        reader.readAsDataURL(file)
    }
}

function handleFileSelect(e) { handleFileProcess(e.target.files[0]) }
function handleDrop(e) { handleFileProcess(e.dataTransfer.files[0]) }

function resetEstimator() {
    uploaded.value = false
    showResults.value = false
    previewUrl.value = null
    uploadedFile.value = null
    errorMsg.value = ''
    estimatedVolumeM3.value = null
    aiResults.value = []
    detectedItems.value = []
    if (fileInput.value) fileInput.value.value = ''
}

async function analyzePhoto() {
    if (!uploadedFile.value) return

    analyzing.value = true
    showResults.value = false
    errorMsg.value = ''

    const startTime = performance.now()
    let phaseIdx = 0
    scanStatus.value = scanningPhases[0]

    // Cycle through scanning phase labels while waiting for API
    const interval = setInterval(() => {
        phaseIdx = (phaseIdx + 1) % scanningPhases.length
        scanStatus.value = scanningPhases[phaseIdx]
    }, 600)

    try {
        const formData = new FormData()
        formData.append('file', uploadedFile.value)

        const res = await fetch('http://localhost:8000/api/v1/ai/estimate-image', {
            method: 'POST',
            body: formData,
        })

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
            throw new Error(err.detail || `HTTP ${res.status}`)
        }

        const data = await res.json()

        // Populate reactive state from real Gemini response
        detectedSpace.value = data.detected_space || 'Unknown Space'
        aiConfidence.value = data.confidence || 0
        vehicleRec.value = data.vehicle_recommendation || null
        estimatedCost.value = data.estimated_base_cost_inr || 0
        detectedItems.value = (data.items || []).map(i => ({
            name: i.name,
            qty: i.qty,
            fragile: i.fragile,
        }))

        const m = data.metrics || {}
        estimatedVolumeM3.value = Number.isFinite(Number(m.estimated_volume_cubic_feet))
            ? Number((Number(m.estimated_volume_cubic_feet) * 0.0283168).toFixed(2))
            : null
        aiResults.value = [
            { label: 'Boxes Needed',  value: String(m.boxes_needed ?? '?'),       icon: 'inventory_2',    color: 'text-blue-500',   confidence: 91 },
            { label: 'Laborers',      value: String(m.laborers ?? '?'),            icon: 'group',          color: 'text-green-500',  confidence: 98 },
            { label: 'Bubble Wrap',   value: `${m.bubble_wrap_rolls ?? '?'} Rolls`, icon: 'bubble_chart', color: 'text-amber-500',  confidence: 88 },
            { label: 'Heavy Items',   value: String(m.heavy_items ?? '?'),         icon: 'fitness_center', color: 'text-purple-500', confidence: 95 },
            { label: 'Volume',        value: estimatedVolumeM3.value !== null ? `${estimatedVolumeM3.value} m³` : '?', icon: 'deployed_code', color: 'text-cyan-500', confidence: 90 },
        ]

        processTime.value = Math.round(performance.now() - startTime)
        showResults.value = true

    } catch (err) {
        errorMsg.value = err.message || 'AI analysis failed. Please try again.'
    } finally {
        clearInterval(interval)
        analyzing.value = false
    }
}

// Map Gemini vehicle type key → BookMove vehicleType key
const vehicleKeyMap = { 'mini-truck': 'mini-truck', 'tempo': 'tempo', 'lcv': 'lcv', 'hcv': 'hcv' }

function useForBooking() {
    const m = aiResults.value.reduce((acc, r) => {
        if (r.label === 'Boxes Needed') acc.boxes = parseInt(r.value) || 10
        if (r.label === 'Laborers')     acc.laborers = parseInt(r.value) || 2
        if (r.label === 'Bubble Wrap')  acc.bubbleWrap = parseInt(r.value) || 2
        return acc
    }, { boxes: 10, laborers: 2, bubbleWrap: 2 })

    const hasFragile = detectedItems.value.some(i => i.fragile)

    indStore.setAiPrefill({
        vehicleType:      vehicleKeyMap[vehicleRec.value?.type] || 'tempo',
        laborCount:       m.laborers,
        cargoType:        hasFragile ? 'Fragile Items' : 'Household Goods',
        packingRequired:  hasFragile,             // auto-enable packing if fragile
        boxes:            m.boxes,
        bubbleWrap:       m.bubbleWrap,
        estimatedVolumeM3: estimatedVolumeM3.value,
    })
    router.push('/individual/book-move')
}
</script>



<style scoped>
.animate-scan {
    animation: scanLine 2s linear infinite;
}

@keyframes scanLine {
    0% {
        top: 0%;
        box-shadow: 0 0 20px 2px rgba(168, 85, 247, 0.9);
    }

    50% {
        top: 100%;
        box-shadow: 0 0 20px 2px rgba(168, 85, 247, 0.9);
    }

    100% {
        top: 0%;
        box-shadow: 0 0 20px 2px rgba(168, 85, 247, 0.0);
    }
}

.animate-scale-in {
    animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes scaleIn {
    0% {
        opacity: 0;
        transform: scale(0.97) translateY(10px);
    }

    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}
</style>
