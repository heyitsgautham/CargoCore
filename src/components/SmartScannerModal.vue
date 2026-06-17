<template>
    <Teleport to="body">
        <div v-if="isOpen" class="fixed inset-0 z-[120] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
            @click.self="emit('close')">
            <div class="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-950/95 shadow-2xl overflow-hidden">
                <div class="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-slate-900/90">
                    <div>
                        <h3 class="text-lg font-bold text-white">Smart Scanner</h3>
                        <p class="text-xs text-gray-400">Scan a barcode or capture a quick proof image.</p>
                    </div>
                    <button @click="emit('close')" class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="p-5 space-y-5">
                    <div class="grid grid-cols-2 gap-2 rounded-xl bg-slate-900/80 p-1 border border-white/10">
                        <button @click="activeTab = 'scan'" class="rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
                            :class="activeTab === 'scan' ? 'bg-primary text-white' : 'text-gray-300 hover:bg-white/5'">
                            Scan
                        </button>
                        <button @click="activeTab = 'camera'" class="rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
                            :class="activeTab === 'camera' ? 'bg-primary text-white' : 'text-gray-300 hover:bg-white/5'">
                            Camera
                        </button>
                    </div>

                    <template v-if="activeTab === 'scan'">
                        <div class="rounded-2xl border border-dashed border-primary/40 bg-primary/5 p-6 text-center">
                            <span class="material-symbols-outlined text-primary text-[40px]">qr_code_scanner</span>
                            <p class="mt-3 text-sm text-gray-300">Paste or type the barcode to simulate a scan.</p>
                        </div>
                        <input v-model="scanValue" type="text" placeholder="e.g. ASN-0092"
                            class="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-primary/50">
                        <button @click="submitScan" class="w-full rounded-xl bg-primary py-3 font-semibold text-white hover:bg-primary/90 transition-colors">
                            Submit Scan
                        </button>
                    </template>

                    <template v-else>
                        <div class="overflow-hidden rounded-2xl border border-emerald-400/20 bg-black/70">
                            <div v-if="cameraError" class="p-6 text-center">
                                <span class="material-symbols-outlined text-emerald-400 text-[40px]">videocam_off</span>
                                <p class="mt-3 text-sm text-gray-300">{{ cameraError }}</p>
                                <p class="mt-2 text-xs text-gray-500">You can still use your device camera fallback below.</p>
                            </div>
                            <div v-else class="relative aspect-[4/3] bg-black">
                                <video
                                    ref="videoRef"
                                    autoplay
                                    playsinline
                                    muted
                                    class="h-full w-full object-cover"
                                />
                                <div v-if="isCameraStarting" class="absolute inset-0 flex items-center justify-center bg-black/60 text-sm text-gray-300">
                                    Starting camera...
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <button @click="submitCamera" class="w-full rounded-xl bg-emerald-500 py-3 font-semibold text-white hover:bg-emerald-400 transition-colors">
                                Capture Image
                            </button>
                            <label class="w-full rounded-xl border border-white/10 bg-slate-900 py-3 text-center font-semibold text-gray-200 hover:bg-white/5 transition-colors cursor-pointer">
                                Use Device Camera
                                <input ref="fileInputRef" type="file" accept="image/*" capture="environment" class="hidden" @change="handleFileChange">
                            </label>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
    isOpen: {
        type: Boolean,
        default: false,
    },
    defaultTab: {
        type: String,
        default: 'scan',
    },
})

const emit = defineEmits(['close', 'scan', 'camera'])

const activeTab = ref(props.defaultTab)
const scanValue = ref('')
const videoRef = ref(null)
const fileInputRef = ref(null)
const cameraError = ref('')
const isCameraStarting = ref(false)
const mediaStream = ref(null)

watch(
    () => props.isOpen,
    async (open) => {
        if (!open) {
            stopCamera()
            return
        }
        activeTab.value = props.defaultTab || 'scan'
        scanValue.value = ''
        cameraError.value = ''
        if (activeTab.value === 'camera') {
            await startCamera()
        }
    },
)

watch(
    () => props.defaultTab,
    (value) => {
        activeTab.value = value || 'scan'
    },
)

watch(activeTab, async (value) => {
    if (value === 'camera' && props.isOpen) {
        await startCamera()
        return
    }
    stopCamera()
})

async function startCamera() {
    if (!props.isOpen || activeTab.value !== 'camera') return
    if (!navigator?.mediaDevices?.getUserMedia) {
        cameraError.value = 'Live camera access is not available in this browser.'
        return
    }

    stopCamera()
    isCameraStarting.value = true
    cameraError.value = ''
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' },
            },
            audio: false,
        })
        mediaStream.value = stream
        await nextTick()
        if (videoRef.value) {
            videoRef.value.srcObject = stream
            await videoRef.value.play().catch(() => {})
        }
    } catch (error) {
        cameraError.value = 'Camera permission was denied. Use the device camera fallback instead.'
    } finally {
        isCameraStarting.value = false
    }
}

function stopCamera() {
    if (!mediaStream.value) return
    mediaStream.value.getTracks().forEach((track) => track.stop())
    mediaStream.value = null
    if (videoRef.value) {
        videoRef.value.srcObject = null
    }
}

const submitScan = () => {
    emit('scan', scanValue.value.trim() || `SCAN-${Date.now()}`)
    emit('close')
}

const submitCamera = () => {
    const video = videoRef.value
    if (!video || !video.videoWidth || !video.videoHeight) {
        cameraError.value = 'Camera is not ready yet. Please wait a moment and try again.'
        return
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const context = canvas.getContext('2d')
    if (!context) {
        cameraError.value = 'Unable to capture from camera right now.'
        return
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    emit('camera', canvas.toDataURL('image/jpeg', 0.92))
    emit('close')
}

function handleFileChange(event) {
    const [file] = Array.from(event.target?.files || [])
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
        emit('camera', typeof reader.result === 'string' ? reader.result : '')
        emit('close')
    }
    reader.readAsDataURL(file)

    if (fileInputRef.value) {
        fileInputRef.value.value = ''
    }
}

onBeforeUnmount(() => {
    stopCamera()
})
</script>
