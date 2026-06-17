<template>
    <div ref="roomRef" class="fixed inset-0 flex flex-col bg-surface-light dark:bg-background-dark p-6 z-[100]">
        <!-- Header -->
        <div class="mb-4 flex justify-between items-center">
            <div>
                <div class="flex items-center gap-2 mb-0.5">
                    <!-- Platform pill in header -->
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1"
                        :class="platformConfig.pillClass">
                        <span class="w-1.5 h-1.5 rounded-full inline-block" :class="platformConfig.dotClass"></span>
                        {{ platformConfig.name }}
                    </span>
                </div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ meetingTitle || 'Live Meeting' }}</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400">Connected to secure meeting room</p>
            </div>
            <div class="flex items-center gap-3">
                <button @click="toggleFullscreen"
                    class="px-3 py-2 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-gray-300 rounded-lg transition-colors flex items-center gap-2 text-sm">
                    <span class="material-symbols-outlined text-[18px]">{{ isFullscreen ? 'fullscreen_exit' : 'fullscreen' }}</span>
                    {{ isFullscreen ? 'Exit Fullscreen' : 'Fullscreen' }}
                </button>
                <button @click="showLeaveModal = true"
                    class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">call_end</span>
                    Leave Room
                </button>
            </div>
        </div>

        <!-- Meeting Container -->
        <div class="flex-1 bg-black rounded-2xl overflow-hidden shadow-2xl relative border border-gray-200 dark:border-white/10">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-white">
                <div class="flex flex-col items-center gap-2">
                    <span class="material-symbols-outlined animate-spin text-4xl">sync</span>
                    <span>Connecting...</span>
                </div>
            </div>

            <div v-if="meetingUrl" class="flex flex-col items-center justify-center w-full h-full bg-gray-900 text-white p-8 text-center">

                <!-- Platform Logo Area -->
                <div class="mb-6">
                    <!-- Google Meet -->
                    <div v-if="meetingType === 'gmeet'"
                        class="w-20 h-20 rounded-2xl mx-auto flex items-center justify-center shadow-2xl"
                        style="background: linear-gradient(135deg, #00897B 0%, #1565C0 100%)">
                        <svg viewBox="0 0 48 48" class="w-11 h-11" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M29 10H10C9.4 10 9 10.4 9 11V37L15 31H29C29.6 31 30 30.6 30 30V11C30 10.4 29.6 10 29 10Z" fill="white" fill-opacity="0.9"/>
                            <path d="M39 16L33 21V27L39 32C39.6 32 40 31.6 40 31V17C40 16.4 39.6 16 39 16Z" fill="white" fill-opacity="0.7"/>
                        </svg>
                    </div>

                    <!-- Zoom -->
                    <div v-else-if="meetingType === 'zoom'"
                        class="w-20 h-20 rounded-2xl mx-auto flex items-center justify-center shadow-2xl bg-blue-600">
                        <svg viewBox="0 0 48 48" class="w-11 h-11" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="8" y="14" width="22" height="20" rx="3" fill="white" fill-opacity="0.9"/>
                            <path d="M30 20L40 14V34L30 28V20Z" fill="white" fill-opacity="0.7"/>
                        </svg>
                    </div>

                    <!-- Other -->
                    <div v-else
                        class="w-20 h-20 rounded-2xl mx-auto flex items-center justify-center shadow-2xl bg-primary/20 animate-pulse">
                        <span class="material-symbols-outlined text-5xl text-primary">videocam</span>
                    </div>
                </div>

                <!-- Platform label -->
                <span class="text-xs font-bold px-3 py-1 rounded-full mb-4"
                    :class="platformConfig.pillClass">
                    {{ platformConfig.name }}
                </span>

                <h2 class="text-3xl font-bold mb-2">Ready to Join?</h2>
                <p class="text-gray-400 max-w-md mb-8">{{ platformConfig.description }}</p>

                <!-- Action Buttons — Zoom: two options -->
                <template v-if="meetingType === 'zoom'">
                    <div class="flex flex-col gap-3 w-full max-w-xs">
                        <!-- Open in Zoom App (deeplink) -->
                        <a v-if="zoomDeeplink" :href="zoomDeeplink"
                            class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-[20px]">launch</span>
                            Open in Zoom App
                        </a>
                        <!-- Join in Browser (fallback) -->
                        <a :href="meetingUrl" target="_blank" rel="noopener noreferrer"
                            class="px-8 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 border border-white/20">
                            <span class="material-symbols-outlined text-[20px]">open_in_new</span>
                            Join in Browser
                        </a>
                        <p class="text-xs text-gray-500 mt-1">
                            App not installed? Use "Join in Browser" instead.
                        </p>
                    </div>
                </template>

                <!-- Action Button — Google Meet -->
                <template v-else-if="meetingType === 'gmeet'">
                    <a :href="meetingUrl" target="_blank" rel="noopener noreferrer"
                        class="px-8 py-3 text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg flex items-center gap-2"
                        style="background: linear-gradient(135deg, #00897B 0%, #1565C0 100%)">
                        <span>Open Google Meet</span>
                        <span class="material-symbols-outlined text-[20px]">open_in_new</span>
                    </a>
                </template>

                <!-- Action Button — Other -->
                <template v-else>
                    <a :href="meetingUrl" target="_blank" rel="noopener noreferrer"
                        class="px-8 py-3 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg flex items-center gap-2">
                        <span>Launch Meeting</span>
                        <span class="material-symbols-outlined text-[20px]">open_in_new</span>
                    </a>
                </template>

                <!-- Meeting link display -->
                <div class="mt-8 text-sm text-gray-500">
                    <p>Meeting Link:</p>
                    <code class="bg-black/30 px-3 py-1.5 rounded-lg mt-1 block text-xs break-all max-w-md">{{ meetingUrl }}</code>
                </div>
            </div>

            <div v-else class="flex items-center justify-center h-full text-white">
                <div class="text-center">
                    <span class="material-symbols-outlined text-6xl text-gray-600 mb-4">link_off</span>
                    <h3 class="text-xl font-bold">No Meeting Link Provided</h3>
                    <p class="text-gray-500">Please verify the meeting URL.</p>
                </div>
            </div>
        </div>

        <!-- Leave Room Confirmation Modal -->
        <Teleport to="body">
            <div v-if="showLeaveModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[200] flex items-center justify-center p-4"
                @click.self="showLeaveModal = false">
                <div
                    class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-sm border border-gray-200 dark:border-white/10 overflow-hidden">
                    <div class="p-6 text-center">
                        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
                            <span class="material-symbols-outlined text-4xl text-red-500">meeting_room</span>
                        </div>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Leave this Room?</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Before leaving, make sure you have
                            exited the meeting. You will be redirected back to your dashboard.</p>

                        <!-- Verification Checkbox -->
                        <label
                            class="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors mb-6"
                            :class="hasExitedMeeting ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10'"
                            @click="hasExitedMeeting = !hasExitedMeeting">
                            <span class="material-symbols-outlined text-[20px]"
                                :class="hasExitedMeeting ? 'text-green-500' : 'text-gray-400'">
                                {{ hasExitedMeeting ? 'check_circle' : 'radio_button_unchecked' }}
                            </span>
                            <span class="text-sm font-medium"
                                :class="hasExitedMeeting ? 'text-green-700 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'">
                                I confirm I have exited the meeting
                            </span>
                        </label>

                        <div class="flex gap-3">
                            <button @click="showLeaveModal = false; hasExitedMeeting = false"
                                class="flex-1 py-3 rounded-lg text-sm font-bold bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition-colors">
                                Stay in Room
                            </button>
                            <button @click="leaveRoom" :disabled="!hasExitedMeeting"
                                class="flex-1 py-3 rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-2"
                                :class="hasExitedMeeting ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'">
                                <span class="material-symbols-outlined text-[18px]">logout</span>
                                Leave Room
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const roomRef = ref(null)
const meetingUrl = ref('')
const meetingTitle = ref('')
const loading = ref(false)
const showLeaveModal = ref(false)
const hasExitedMeeting = ref(false)
const isFullscreen = ref(false)

// --- Platform Detection ---

const detectPlatformFromUrl = (url) => {
    if (!url) return 'other'
    const lower = url.toLowerCase()
    if (lower.includes('meet.google.com')) return 'gmeet'
    if (lower.includes('zoom.us') || lower.includes('zoom.com')) return 'zoom'
    return 'other'
}

const normalizeMeetingUrl = (value) => {
    const trimmed = String(value || '').trim()
    if (!trimmed) return ''
    if (/^https?:\/\//i.test(trimmed)) return trimmed
    if (/^(meet\.google\.com|[\w-]+\.zoom\.(us|com)|zoom\.us|zoom\.com)/i.test(trimmed)) {
        return `https://${trimmed}`
    }
    return trimmed
}

const meetingType = computed(() => {
    return route.query.type || detectPlatformFromUrl(meetingUrl.value)
})

const platformConfig = computed(() => {
    const configs = {
        gmeet: {
            name: 'Google Meet',
            pillClass: 'bg-green-500/20 text-green-400',
            dotClass: 'bg-green-500',
            description: 'Your Google Meet session is ready. Click below to open it in a new window.'
        },
        zoom: {
            name: 'Zoom Meeting',
            pillClass: 'bg-blue-500/20 text-blue-400',
            dotClass: 'bg-blue-500',
            description: 'Open in the Zoom app for the best experience, or join directly in your browser.'
        },
        other: {
            name: 'Meeting',
            pillClass: 'bg-primary/20 text-primary',
            dotClass: 'bg-primary',
            description: 'This meeting is hosted on an external platform. Click below to open the secure meeting room.'
        }
    }
    return configs[meetingType.value] || configs.other
})

// Zoom deeplink: converts web URL → zoommtg:// app deeplink
const zoomDeeplink = computed(() => {
    if (meetingType.value !== 'zoom' || !meetingUrl.value) return null
    try {
        const url = new URL(meetingUrl.value)
        const pathMatch = url.pathname.match(/\/j\/(\d+)/)
        if (!pathMatch) return null
        const confNo = pathMatch[1]
        const pwd = url.searchParams.get('pwd')
        let deeplink = `zoommtg://zoom.us/join?confno=${confNo}&zc=0`
        if (pwd) deeplink += `&pwd=${pwd}`
        return deeplink
    } catch {
        return null
    }
})

// --- Fullscreen ---

function enterFullscreen() {
    const el = document.documentElement
    if (el.requestFullscreen) el.requestFullscreen()
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen()
    else if (el.msRequestFullscreen) el.msRequestFullscreen()
}

function exitFullscreen() {
    if (document.exitFullscreen) document.exitFullscreen()
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen()
    else if (document.msExitFullscreen) document.msExitFullscreen()
}

function toggleFullscreen() {
    if (document.fullscreenElement) exitFullscreen()
    else enterFullscreen()
}

function onFullscreenChange() {
    isFullscreen.value = !!document.fullscreenElement
}

function leaveRoom() {
    showLeaveModal.value = false
    hasExitedMeeting.value = false
    if (document.fullscreenElement) exitFullscreen()
    router.back()
}

onMounted(() => {
    if (route.query.url) {
        meetingUrl.value = normalizeMeetingUrl(route.query.url)
        meetingTitle.value = route.query.title || 'Meeting'
    }
    enterFullscreen()
    document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    if (document.fullscreenElement) exitFullscreen()
})
</script>
