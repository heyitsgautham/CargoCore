<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-red-500">report</span>
            Damage Report
        </h2>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Report Form -->
            <div class="glass-panel p-4 sm:p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-5">Report Damage</h3>
                <div class="space-y-5">

                    <!-- Order -->
                    <div>
                        <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Select Order</label>
                        <select v-model="form.orderId"
                            class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-red-500/50 focus:border-red-500 outline-none">
                            <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Choose an order...</option>
                            <option v-for="o in availableOrders" :key="o.id" :value="o.backendId" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                                {{ o.id }} — {{ o.cargoType }}
                            </option>
                        </select>
                        <p v-if="availableOrders.length === 0" class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                            All delivered orders already have a damage ticket or were already reviewed.
                        </p>
                    </div>

                    <!-- Description -->
                    <div>
                        <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Describe the Damage</label>
                        <textarea v-model="form.description" rows="3"
                            placeholder="Describe what was damaged, when you noticed it, and the extent..."
                            class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500/50 focus:border-red-500 outline-none resize-none"></textarea>
                    </div>

                    <!-- Photo Upload -->
                    <div>
                        <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Upload Photos / Videos</label>
                        <div @click="$refs.photoInput?.click()"
                            class="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer hover:border-red-400 dark:hover:border-red-500 hover:bg-gray-50 dark:hover:bg-white/5 transition-all text-gray-400">
                            <span class="material-symbols-outlined text-3xl mb-2">add_photo_alternate</span>
                            <span class="text-sm font-bold">Click to upload damage photos</span>
                            <span class="text-xs mt-1">{{ photos.length > 0 ? photos.length + ' file(s) selected' : 'Before / After photos recommended' }}</span>
                        </div>
                        <input type="file" ref="photoInput" accept="image/*,video/*" multiple class="hidden" @change="handlePhotos" />
                        <!-- Previews -->
                        <div v-if="photos.length > 0" class="flex gap-2 flex-wrap mt-2">
                            <div v-for="(p, i) in photos" :key="i"
                                class="relative w-14 h-14 rounded-lg overflow-hidden border border-gray-200 dark:border-white/10 bg-gray-100 dark:bg-white/5 flex items-center justify-center">
                                <img v-if="p.preview" :src="p.preview" class="w-full h-full object-cover" />
                                <span v-else class="material-symbols-outlined text-xl text-gray-400">movie</span>
                                <button @click.stop="photos.splice(i, 1)"
                                    class="absolute top-0.5 right-0.5 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                                    <span class="material-symbols-outlined text-white text-[10px]">close</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Preferred Resolution Type -->
                    <div>
                        <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Preferred Resolution Type</label>
                        <div class="space-y-2">

                            <!-- Option 1: Photo Review Only -->
                            <button type="button"
                                @click="form.resolutionType = 'photo_review'"
                                class="w-full text-left p-4 rounded-xl border-2 transition-all"
                                :class="form.resolutionType === 'photo_review'
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10'
                                    : 'border-gray-200 dark:border-white/10 hover:border-blue-300 dark:hover:border-blue-500/40'">
                                <div class="flex items-start gap-3">
                                    <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 shrink-0"
                                        :class="form.resolutionType === 'photo_review' ? 'border-blue-500' : 'border-gray-300 dark:border-white/30'">
                                        <div v-if="form.resolutionType === 'photo_review'" class="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                                    </div>
                                    <div>
                                        <div class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                                            <span class="material-symbols-outlined text-blue-500 text-[16px]">photo_camera</span>
                                            Photo Review Only
                                        </div>
                                        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Faster resolution based on submitted photos. No pickup arranged.</div>
                                    </div>
                                </div>
                            </button>

                            <!-- Option 2: Pickup Inspection -->
                            <button type="button"
                                @click="form.resolutionType = 'pickup_inspection'"
                                class="w-full text-left p-4 rounded-xl border-2 transition-all"
                                :class="form.resolutionType === 'pickup_inspection'
                                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-500/10'
                                    : 'border-gray-200 dark:border-white/10 hover:border-purple-300 dark:hover:border-purple-500/40'">
                                <div class="flex items-start gap-3">
                                    <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 shrink-0"
                                        :class="form.resolutionType === 'pickup_inspection' ? 'border-purple-500' : 'border-gray-300 dark:border-white/30'">
                                        <div v-if="form.resolutionType === 'pickup_inspection'" class="w-2.5 h-2.5 rounded-full bg-purple-500"></div>
                                    </div>
                                    <div>
                                        <div class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                                            <span class="material-symbols-outlined text-purple-500 text-[16px]">local_shipping</span>
                                            Request Parcel Pickup for Physical Inspection
                                        </div>
                                        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">A driver collects your parcel for physical inspection at the warehouse.</div>
                                    </div>
                                </div>
                            </button>
                        </div>
                    </div>

                    <!-- Flow 1 note -->
                    <div v-if="form.resolutionType === 'photo_review'"
                        class="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-xl text-xs text-blue-700 dark:text-blue-300">
                        <span class="material-symbols-outlined text-[16px] mt-0.5 shrink-0">info</span>
                        <span>Your claim will be reviewed based on the photos and details you provide. <strong>No parcel pickup will be arranged</strong> in this option.</span>
                    </div>

                    <!-- Flow 2 warning + checkbox -->
                    <template v-if="form.resolutionType === 'pickup_inspection'">
                        <div class="p-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl text-xs text-amber-700 dark:text-amber-300 space-y-1">
                            <div class="font-bold flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[16px]">warning</span>
                                Important — Please Read
                            </div>
                            <p>Physical inspection <strong>does not guarantee a refund</strong>. If the claim is found invalid after inspection, pickup or transport charges may apply.</p>
                        </div>
                        <label class="flex items-start gap-3 cursor-pointer select-none">
                            <input type="checkbox" v-model="form.pickupAcknowledged"
                                class="mt-0.5 w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 cursor-pointer shrink-0" />
                            <span class="text-xs text-gray-700 dark:text-gray-300">
                                I understand that physical inspection does not guarantee refund and pickup or transport charges may apply if the claim is rejected.
                            </span>
                        </label>
                    </template>

                    <!-- Submit -->
                    <button @click="submitReport" :disabled="!canSubmit || submitting"
                        class="w-full py-3 font-bold rounded-xl transition-colors text-sm"
                        :class="canSubmit && !submitting
                            ? 'bg-red-600 hover:bg-red-700 text-white'
                            : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                        {{ submitting ? 'Submitting...' : 'Submit Damage Report' }}
                    </button>
                </div>
            </div>

            <!-- Report History -->
            <div class="space-y-4">
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Report History</h3>
                    <div v-if="store.damageReports.length === 0" class="text-center py-8 text-gray-400 dark:text-gray-500">
                        <span class="material-symbols-outlined text-4xl block mb-2">verified</span>
                        <p class="text-sm">No damage reports. All is well!</p>
                    </div>
                    <div v-else class="space-y-3">
                        <div v-for="report in store.damageReports" :key="report.id"
                            class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/5">
                            <div class="flex items-center justify-between mb-2 gap-2 flex-wrap">
                                <span class="font-mono font-bold text-red-600 dark:text-red-400 text-sm">{{ report.id }}</span>
                                <div class="flex items-center gap-1.5 flex-wrap">
                                    <!-- Flow badge -->
                                    <span v-if="report.flow_type === 'photo_review'"
                                        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400">
                                        <span class="material-symbols-outlined text-[10px]">photo_camera</span> Photo Review
                                    </span>
                                    <span v-else-if="report.flow_type === 'pickup_inspection'"
                                        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400">
                                        <span class="material-symbols-outlined text-[10px]">local_shipping</span> Pickup
                                    </span>
                                    <!-- Status -->
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase" :class="getStatusClass(report.status)">
                                        {{ report.status || 'Reported' }}
                                    </span>
                                </div>
                            </div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">Order: {{ report.orderId }}</div>
                            <div class="text-sm text-gray-700 dark:text-gray-300 mt-1 line-clamp-2">{{ report.description }}</div>

                            <!-- Resolution details -->
                            <div v-if="report.condition && report.condition !== 'Reported'" class="mt-2 flex flex-wrap gap-2">
                                <span class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300">
                                    <span class="material-symbols-outlined text-[12px]">inventory_2</span>
                                    Condition: {{ report.condition }}
                                </span>
                                <span v-if="report.refundAmount && report.refundAmount > 0"
                                    class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400">
                                    <span class="material-symbols-outlined text-[12px]">currency_rupee</span>
                                    Refund: ₹{{ report.refundAmount.toLocaleString() }}
                                </span>
                                <span v-else-if="report.status === 'Rejected'"
                                    class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400">
                                    <span class="material-symbols-outlined text-[12px]">cancel</span>
                                    No Refund Issued
                                </span>
                            </div>

                            <!-- QR Code -->
                            <div class="mt-3 p-2 bg-white dark:bg-black/20 rounded border border-gray-200 dark:border-white/10 flex items-center gap-3">
                                <div class="w-12 h-12 bg-gray-100 dark:bg-white/10 rounded flex items-center justify-center">
                                    <span class="material-symbols-outlined text-2xl text-gray-500">qr_code_2</span>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-500 font-medium">Reverse Logistics QR</div>
                                    <div class="text-xs font-mono text-gray-700 dark:text-gray-300">{{ report.qrCode }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Status timelines -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl space-y-4">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm">Report Status Flow</h3>

                    <!-- Flow 1 -->
                    <div>
                        <div class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[12px]">photo_camera</span> Photo Review Only
                        </div>
                        <div class="flex items-center gap-1 flex-wrap text-[10px]">
                            <span v-for="(s, i) in flow1Statuses" :key="s" class="flex items-center gap-1">
                                <span class="px-2 py-1 rounded-full font-bold" :class="flow1Class(s)">{{ s }}</span>
                                <span v-if="i < flow1Statuses.length - 1" class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-xs">arrow_forward</span>
                            </span>
                        </div>
                    </div>

                    <!-- Flow 2 -->
                    <div>
                        <div class="text-[10px] font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[12px]">local_shipping</span> Pickup Inspection
                        </div>
                        <div class="flex items-center gap-1 flex-wrap text-[10px]">
                            <span v-for="(s, i) in flow2Statuses" :key="s" class="flex items-center gap-1">
                                <span class="px-2 py-1 rounded-full font-bold" :class="flow2Class(s)">{{ s }}</span>
                                <span v-if="i < flow2Statuses.length - 1" class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-xs">arrow_forward</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl bg-red-600 text-white border border-red-500 max-w-sm">
                    <span class="material-symbols-outlined">check_circle</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'

const store = useIndividualStore()

const form = reactive({
    orderId: '',
    description: '',
    resolutionType: '',
    pickupAcknowledged: false,
})
const photos = ref([])
const submitting = ref(false)

const availableOrders = computed(() => {
    const blockedOrderIds = new Set((store.damageReports || []).map(r => String(r.orderId || '')))
    return (store.deliveredOrders || []).filter(o => !blockedOrderIds.has(String(o.backendId || '')))
})

const canSubmit = computed(() => {
    if (!form.orderId || !form.description || !form.resolutionType) return false
    if (availableOrders.value.length === 0) return false
    if (form.resolutionType === 'pickup_inspection' && !form.pickupAcknowledged) return false
    return true
})

function handlePhotos(e) {
    const files = Array.from(e.target.files).map(f => ({
        file: f,
        preview: f.type.startsWith('image/') ? URL.createObjectURL(f) : null
    }))
    photos.value = [...photos.value, ...files]
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(file)
    })
}

async function submitReport() {
    if (!canSubmit.value || submitting.value) return
    submitting.value = true
    const photoData = await Promise.all(
        photos.value.map(p => p.file ? fileToBase64(p.file) : null)
    ).then(arr => arr.filter(Boolean))
    const result = await store.reportDamageRemote(
        form.orderId,
        form.description,
        photoData,
        form.resolutionType
    )
    submitting.value = false
    if (!result.success) {
        showToast(result.message || 'Failed to submit damage report.')
        return
    }
    form.orderId = ''
    form.description = ''
    form.resolutionType = ''
    form.pickupAcknowledged = false
    photos.value = []
    showToast('Damage report submitted! QR code generated.')
}

const flow1Statuses = ['Reported', 'Under Review', 'Claims Reviewed', 'Approved', 'Refunded', 'Closed']
const flow2Statuses = ['Reported', 'Pickup Requested', 'Pickup Approved', 'Pickup Scheduled', 'At Warehouse', 'Physically Inspected', 'Approved', 'Refunded', 'Closed']

function flow1Class(s) {
    const m = { 'Reported': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', 'Under Review': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'Claims Reviewed': 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400', 'Approved': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', 'Refunded': 'bg-green-200 text-green-800 dark:bg-green-500/30 dark:text-green-300', 'Closed': 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400' }
    return m[s] || 'bg-gray-100 text-gray-600'
}

function flow2Class(s) {
    const m = { 'Reported': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', 'Pickup Requested': 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400', 'Pickup Approved': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'Pickup Scheduled': 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-300', 'At Warehouse': 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400', 'Physically Inspected': 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400', 'Approved': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', 'Refunded': 'bg-green-200 text-green-800 dark:bg-green-500/30 dark:text-green-300', 'Closed': 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400' }
    return m[s] || 'bg-gray-100 text-gray-600'
}

function getStatusClass(status) {
    const m = { 'Reported': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', 'Under Review': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'Claims Reviewed': 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400', 'Pickup Requested': 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400', 'Pickup Approved': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'Pickup Scheduled': 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-300', 'Collected': 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-400', 'At Warehouse': 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400', 'Physically Inspected': 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400', 'Approved': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', 'Partially Approved': 'bg-lime-100 text-lime-700 dark:bg-lime-500/20 dark:text-lime-400', 'Rejected': 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400', 'Refunded': 'bg-green-200 text-green-800 dark:bg-green-500/30 dark:text-green-300', 'Closed': 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400' }
    return m[status] || 'bg-gray-100 text-gray-600'
}

const toast = reactive({ show: false, message: '' })
function showToast(msg) { toast.show = true; toast.message = msg; setTimeout(() => { toast.show = false }, 3000) }

onMounted(async () => {
    await Promise.all([store.fetchOrders('delivered'), store.fetchDamageReports()])
})
</script>
