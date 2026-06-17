<template>
    <div class="relative" ref="popoverRef">
        <!-- Trigger Button -->
        <button @click="togglePopover"
            class="relative w-9 h-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            :class="{ 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white': isOpen }">
            <span class="material-symbols-outlined text-[20px]">calendar_add_on</span>
            <!-- Active Meetings Badge -->
            <span v-if="upcomingMeetingsCount > 0"
                class="absolute top-0 right-0 w-4 h-4 bg-primary text-white text-[10px] font-bold flex items-center justify-center rounded-full border-2 border-surface-light dark:border-background-dark">
                {{ upcomingMeetingsCount }}
            </span>
        </button>

        <!-- Popover -->
        <div v-show="isOpen"
            class="absolute right-0 mt-2 w-96 bg-white dark:bg-card-darker rounded-2xl shadow-xl border border-gray-200 dark:border-white/10 overflow-hidden z-50 transform origin-top-right transition-all duration-200"
            :class="isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none'">

            <!-- Header -->
            <div
                class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">video_call</span>
                    Meetings
                </h3>
                <div class="flex items-center gap-2">
                    <button v-if="!isCreating && !isEditing" @click.stop="startCreating"
                        class="text-xs font-semibold px-2 py-1 rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
                        + Schedule
                    </button>
                    <button v-else @click.stop="cancelEdit"
                        class="text-xs font-semibold px-2 py-1 rounded-md bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 hover:bg-red-100 transition-colors">
                        Cancel
                    </button>
                </div>
            </div>

            <!-- VIEW MODE: List of Meetings -->
            <div v-if="!isCreating && !isEditing" class="max-h-[500px] overflow-y-auto no-scrollbar">
                <div v-if="isLoadingMeetings" class="p-8 text-center text-gray-500 dark:text-gray-400">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50 animate-pulse">progress_activity</span>
                    <p class="text-sm">Loading meetings...</p>
                </div>

                <div v-else-if="meetingError" class="p-6 text-center text-gray-500 dark:text-gray-400 space-y-3">
                    <span class="material-symbols-outlined text-4xl mb-1 opacity-60">error</span>
                    <p class="text-sm">{{ meetingError }}</p>
                    <button @click="loadMeetings"
                        class="text-xs font-semibold px-3 py-1.5 rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
                        Retry
                    </button>
                </div>

                <div v-else-if="meetings.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">event_busy</span>
                    <p class="text-sm">No scheduled meetings.</p>
                </div>

                <div v-else class="divide-y divide-gray-100 dark:divide-white/5">
                    <div v-for="meeting in sortedMeetings" :key="meeting.id"
                        class="p-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group relative cursor-pointer select-none"
                        @click.stop="handleMeetingClick($event, meeting)" :title="meetingCardTitle(meeting)">

                        <div class="flex justify-between items-start mb-1">
                            <h4 class="font-semibold text-sm text-gray-900 dark:text-white flex items-center gap-2">
                                {{ meeting.topic }}
                                <span v-if="isMeetingLive(meeting)" class="flex h-2 w-2 relative">
                                    <span
                                        class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                            </h4>
                            <span
                                class="text-[10px] font-medium px-2 py-0.5 rounded-md bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 shrink-0 ml-1">
                                {{ formatDate(meeting.date) }}
                            </span>
                        </div>

                        <!-- Platform badge -->
                        <div class="flex items-center gap-1.5 mb-2">
                            <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1"
                                :class="getPlatformConfig(getMeetingPlatform(meeting)).badgeClass">
                                <span class="w-1.5 h-1.5 rounded-full inline-block shrink-0"
                                    :class="getPlatformConfig(getMeetingPlatform(meeting)).dotClass"></span>
                                {{ getPlatformConfig(getMeetingPlatform(meeting)).label }}
                            </span>
                            <span class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                <span class="material-symbols-outlined text-[12px]">schedule</span>
                                {{ meeting.startTime }} - {{ meeting.endTime }}
                            </span>
                        </div>

                        <p class="text-xs text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
                            {{ meeting.description }}
                        </p>

                        <div class="flex items-center justify-between mt-2">
                            <div class="flex -space-x-2 items-center p-1">
                                <div v-for="uid in meeting.participants.slice(0, 3)" :key="uid"
                                    class="flex h-6 w-6 rounded-full ring-2 ring-white dark:ring-gray-800 bg-gray-200 items-center justify-center text-[8px] font-bold text-gray-600 hover:z-10 hover:-translate-x-1 hover:-translate-y-1 hover:scale-110 transition-transform duration-200 cursor-pointer shadow-sm hover:shadow-md"
                                    :title="getUserName(uid)">
                                    {{ getUserInitials(uid) }}
                                </div>
                                <div v-if="meeting.participants.length > 3"
                                    class="flex h-6 w-6 rounded-full ring-2 ring-white dark:ring-gray-800 bg-gray-100 items-center justify-center text-[8px] font-bold text-gray-500 hover:z-10 hover:-translate-x-1 hover:-translate-y-1 hover:scale-110 transition-transform duration-200 cursor-pointer shadow-sm hover:shadow-md">
                                    +{{ meeting.participants.length - 3 }}
                                </div>
                            </div>

                            <div class="flex items-center gap-2">
                                <button v-if="canManageMeeting(meeting)" @click.stop="deleteMeeting(meeting.id)"
                                    class="px-2 py-1 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                                    title="Delete Meeting">
                                    <span class="material-symbols-outlined text-[18px]">delete</span>
                                </button>
                                <button @click.stop="joinMeeting(meeting)"
                                    class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm"
                                    :class="getPlatformConfig(getMeetingPlatform(meeting)).joinClass">
                                    <span class="material-symbols-outlined text-[14px]">videocam</span>
                                    Join
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- EDIT/CREATE MODE: Form -->
            <div v-else class="p-4 max-h-[500px] overflow-y-auto no-scrollbar space-y-4 bg-gray-50/30 dark:bg-white/5">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                    {{ isEditing ? 'Edit Meeting' : 'New Meeting' }}
                </h4>

                <div v-if="meetingError"
                    class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                    {{ meetingError }}
                </div>

                <!-- 1. Meeting Details -->
                <div class="space-y-3">
                    <div>
                        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Topic</label>
                        <input v-model="form.topic" type="text" placeholder="e.g. Weekly Sync"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                    </div>

                    <!-- Platform Selector -->
                    <div>
                        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Platform</label>
                        <div class="flex gap-2">
                            <button v-for="p in platformOptions" :key="p.id"
                                type="button"
                                @click="form.meetingType = p.id"
                                class="flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 border-2 transition-all"
                                :class="form.meetingType === p.id
                                    ? p.activeClass
                                    : 'border-gray-200 dark:border-white/10 text-gray-400 dark:text-gray-500 bg-transparent hover:border-gray-300 dark:hover:border-white/20'">
                                <span class="w-2 h-2 rounded-full inline-block shrink-0" :class="p.dotColor"></span>
                                {{ p.label }}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Meeting Link</label>
                        <input v-model="form.link" type="text" :placeholder="linkPlaceholder"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-blue-500 dark:text-blue-400 focus:outline-none focus:border-primary/50 transition-colors">
                        <p v-if="form.link && getMeetingPlatform(form)" class="text-[10px] mt-1 flex items-center gap-1"
                            :class="getPlatformConfig(getMeetingPlatform(form)).badgeClass.split(' ')[2]">
                            <span class="w-1.5 h-1.5 rounded-full inline-block"
                                :class="getPlatformConfig(getMeetingPlatform(form)).dotClass"></span>
                            Detected: {{ getPlatformConfig(getMeetingPlatform(form)).label }}
                        </p>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
                        <input v-model="form.date" type="date"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                    </div>

                    <div class="flex gap-2">
                        <div class="flex-1">
                            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Start Time</label>
                            <input v-model="form.startTime" type="time"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                        </div>
                        <div class="flex-1">
                            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">End Time</label>
                            <input v-model="form.endTime" type="time"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                        <textarea v-model="form.description" rows="2" placeholder="Agenda or notes..."
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors resize-none"></textarea>
                    </div>
                </div>

                <!-- 2. Select Participants -->
                <div class="space-y-3 pt-2 border-t border-gray-100 dark:border-white/5">
                    <h4
                        class="text-xs font-bold text-gray-500 uppercase tracking-wider flex justify-between items-center">
                        Participants
                        <span
                            class="text-[10px] font-normal normal-case bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">
                            {{ selectedParticipantCount }} selected
                        </span>
                    </h4>

                    <p class="text-[10px] text-gray-500 dark:text-gray-400">
                        You are included automatically. Add other roles from the list below.
                    </p>

                    <!-- Filters -->
                    <div class="flex gap-2">
                        <select v-model="filters.hub"
                            class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50">
                            <option value="">All Hubs</option>
                            <option v-for="hub in store.hubs" :key="hub.id" :value="hub.id">{{ hub.name }}</option>
                        </select>

                        <select v-model="filters.role"
                            class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50">
                            <option value="">All Roles</option>
                            <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
                        </select>
                    </div>

                    <!-- User List -->
                    <div
                        class="max-h-40 overflow-y-auto border border-gray-200 dark:border-white/10 rounded-lg bg-gray-50/50 dark:bg-black/20 divide-y divide-gray-100 dark:divide-white/5">
                        <div v-if="filteredUsers.length === 0" class="p-3 text-center text-xs text-gray-500">
                            No users found matching filters.
                        </div>
                        <label v-for="user in filteredUsers" :key="user.id"
                            class="flex items-center gap-3 p-2 hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors">
                            <input type="checkbox" :value="user.id" v-model="form.participants"
                                class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary">
                            <div class="flex-1 min-w-0">
                                <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ user.name }}</div>
                                <div class="text-[10px] text-gray-500 flex items-center gap-2">
                                    <span>{{ user.role }}</span>
                                    <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600"></span>
                                    <span>{{ getHubName(user.hubId) }}</span>
                                </div>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- Footer ACTIONS -->
                <div class="pt-4 border-t border-gray-100 dark:border-white/5 flex justify-end gap-2">
                    <button @click="saveMeeting"
                        class="w-full px-4 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        :disabled="!isValid || isSaving">
                        {{ isSaving ? (isEditing ? 'Updating...' : 'Scheduling...') : (isEditing ? 'Update Schedule' : 'Schedule Meeting') }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authenticatedJsonRequest } from '@/config/api'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'

const store = useLogisticStore()
const dispatchStore = useDispatcherStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const isOpen = ref(false)
const popoverRef = ref(null)

const isCreating = ref(false)
const isEditing = ref(false)
const isSaving = ref(false)
const isLoadingMeetings = ref(false)
const isLoadingParticipants = ref(false)
const meetingError = ref('')
const editId = ref(null)
const participantOptions = ref([])

const detectPlatform = (url) => {
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

const platformOptions = [
    {
        id: 'gmeet',
        label: 'Google Meet',
        dotColor: 'bg-green-500',
        activeClass: 'border-green-500 bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400'
    },
    {
        id: 'zoom',
        label: 'Zoom',
        dotColor: 'bg-blue-500',
        activeClass: 'border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400'
    },
    {
        id: 'other',
        label: 'Other',
        dotColor: 'bg-gray-400',
        activeClass: 'border-gray-400 bg-gray-50 dark:bg-white/10 text-gray-700 dark:text-gray-300'
    }
]

const getPlatformConfig = (type) => {
    const configs = {
        gmeet: {
            label: 'Google Meet',
            badgeClass: 'bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-400',
            dotClass: 'bg-green-500',
            joinClass: 'bg-green-600 hover:bg-green-700 text-white'
        },
        zoom: {
            label: 'Zoom',
            badgeClass: 'bg-blue-100 dark:bg-blue-500/15 text-blue-700 dark:text-blue-400',
            dotClass: 'bg-blue-500',
            joinClass: 'bg-blue-600 hover:bg-blue-700 text-white'
        },
        other: {
            label: 'Meeting',
            badgeClass: 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300',
            dotClass: 'bg-gray-400',
            joinClass: 'bg-primary hover:bg-primary/90 text-white'
        }
    }
    return configs[type] || configs.other
}

const getMeetingPlatform = (meeting) => meeting.meetingType || detectPlatform(meeting.link)

const todayDate = () => new Date().toISOString().split('T')[0]
const normalizeId = (value) => value == null ? '' : String(value)
const titleCase = (value) => String(value || 'User')
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())

const normalizeMeeting = (meeting) => {
    if (!meeting || typeof meeting !== 'object') return null

    const explicitType = String(meeting.meetingType || meeting.meeting_type || '').toLowerCase()
    const meetingType = ['gmeet', 'zoom', 'other'].includes(explicitType)
        ? explicitType
        : detectPlatform(meeting.link)

    return {
        id: normalizeId(meeting.id),
        topic: String(meeting.topic || '').trim(),
        description: String(meeting.description || '').trim(),
        meetingType,
        link: normalizeMeetingUrl(meeting.link),
        date: String(meeting.date || ''),
        startTime: String(meeting.startTime || meeting.start_time || ''),
        endTime: String(meeting.endTime || meeting.end_time || ''),
        participants: Array.isArray(meeting.participants)
            ? meeting.participants.map(normalizeId).filter(Boolean)
            : [],
        createdById: normalizeId(meeting.createdById || meeting.created_by_id),
        warehouseId: normalizeId(meeting.warehouseId || meeting.warehouse_id),
        createdAt: String(meeting.createdAt || meeting.created_at || ''),
        updatedAt: String(meeting.updatedAt || meeting.updated_at || '')
    }
}

const meetings = ref([])

const defaultForm = {
    topic: '',
    link: '',
    meetingType: 'other',
    date: '',
    startTime: '',
    endTime: '',
    description: '',
    participants: []
}

const form = ref({ ...defaultForm })

const filters = ref({
    hub: '',
    role: ''
})

const currentUserId = computed(() => normalizeId(authStore.currentUser?.id))

const legacyAvailableUsers = computed(() => {
    const registry = new Map()

    const upsertUser = (user) => {
        const id = normalizeId(user?.id)
        const name = String(user?.name || '').trim()
        if (!id || !name) return

        registry.set(id, {
            id,
            name,
            role: String(user.role || 'User').trim() || 'User',
            hubId: user.hubId ? normalizeId(user.hubId) : '',
        })
    }

    store.users.forEach((user) => {
        upsertUser({
            id: user.id,
            name: user.name || user.email,
            role: user.role || 'User',
            hubId: user.hubId,
        })
    })

    store.drivers.forEach((driver) => {
        upsertUser({
            id: driver.id,
            name: driver.name,
            role: 'Driver',
            hubId: driver.hubId,
        })
    })

    dispatchStore.dispatcherContacts.forEach((contact) => {
        upsertUser({
            id: contact.id,
            name: contact.name,
            role: titleCase(contact.role || contact.type || 'User'),
            hubId: authStore.currentUser?.warehouse_id,
        })
    })

    if (authStore.currentUser) {
        upsertUser({
            id: authStore.currentUser.id,
            name: authStore.currentUser.name || authStore.userEmail,
            role: titleCase(authStore.currentUser.role || authStore.userRole || 'User'),
            hubId: authStore.currentUser.warehouse_id,
        })
    }

    return [...registry.values()].sort((a, b) => a.name.localeCompare(b.name))
})

const availableUsers = computed(() => {
    if (participantOptions.value.length > 0) {
        return participantOptions.value
    }
    return legacyAvailableUsers.value
})

const upcomingMeetingsCount = computed(() => meetings.value.length)
const roleOptions = computed(() => [...new Set(availableUsers.value.map((user) => user.role).filter(Boolean))])
const selectedParticipantCount = computed(() => form.value.participants.filter((id) => id !== currentUserId.value).length)

const sortedMeetings = computed(() => {
    return [...meetings.value].sort((a, b) => {
        const dateA = new Date(`${a.date}T${a.startTime}`)
        const dateB = new Date(`${b.date}T${b.startTime}`)
        return dateA - dateB
    })
})

const filteredUsers = computed(() => {
    return availableUsers.value.filter((user) => {
        if (user.id === currentUserId.value) return false
        const matchHub = filters.value.hub ? user.hubId === filters.value.hub : true
        const matchRole = filters.value.role ? user.role === filters.value.role : true
        return matchHub && matchRole
    })
})

const isValid = computed(() => {
    return Boolean(
        form.value.topic.trim() &&
        form.value.link.trim() &&
        form.value.date &&
        form.value.startTime &&
        form.value.endTime &&
        form.value.endTime > form.value.startTime &&
        form.value.participants.length > 0
    )
})

const linkPlaceholder = computed(() => {
    const map = {
        gmeet: 'Paste Google Meet URL',
        zoom: 'Paste Zoom meeting URL',
        other: 'Paste meeting URL'
    }
    return map[form.value.meetingType] || map.other
})

const canManageMeeting = (meeting) => normalizeId(meeting?.createdById) === currentUserId.value
const meetingCardTitle = (meeting) => canManageMeeting(meeting) ? 'Triple click to edit' : 'Scheduled meeting'

watch(() => form.value.link, (newLink) => {
    form.value.meetingType = detectPlatform(newLink)
})

watch(isOpen, (open) => {
    if (open) {
        loadMeetings()
    }
})

const upsertMeeting = (meeting) => {
    const normalized = normalizeMeeting(meeting)
    if (!normalized) return

    const index = meetings.value.findIndex((item) => item.id === normalized.id)
    if (index === -1) {
        meetings.value.push(normalized)
        return
    }

    meetings.value[index] = normalized
}

const loadMeetings = async () => {
    isLoadingMeetings.value = true
    meetingError.value = ''

    try {
        const data = await authenticatedJsonRequest('api/v1/logistics/meetings')
        meetings.value = Array.isArray(data)
            ? data.map(normalizeMeeting).filter(Boolean)
            : []
    } catch (error) {
        meetingError.value = error instanceof Error ? error.message : 'Unable to load meetings.'
        meetings.value = []
    } finally {
        isLoadingMeetings.value = false
    }
}

const loadParticipantOptions = async () => {
    isLoadingParticipants.value = true

    try {
        const data = await authenticatedJsonRequest('api/v1/logistics/meeting-participants')
        participantOptions.value = Array.isArray(data)
            ? data.map((user) => ({
                id: normalizeId(user.id),
                name: String(user.name || '').trim(),
                role: String(user.role || 'User').trim() || 'User',
                hubId: normalizeId(user.hub_id),
            })).filter((user) => user.id && user.name)
            : []
    } catch {
        participantOptions.value = []
    } finally {
        isLoadingParticipants.value = false
    }
}

const togglePopover = () => {
    isOpen.value = !isOpen.value
    if (!isOpen.value) cancelEdit()
}

const startCreating = () => {
    isCreating.value = true
    isEditing.value = false
    editId.value = null
    form.value = {
        ...defaultForm,
        date: todayDate(),
        participants: currentUserId.value ? [currentUserId.value] : []
    }
}

const cancelEdit = () => {
    isCreating.value = false
    isEditing.value = false
    editId.value = null
    form.value = { ...defaultForm }
}

const editMeeting = (meeting) => {
    if (!canManageMeeting(meeting)) return

    isCreating.value = false
    isEditing.value = true
    editId.value = meeting.id
    form.value = {
        topic: meeting.topic,
        link: meeting.link,
        meetingType: meeting.meetingType,
        date: meeting.date,
        startTime: meeting.startTime,
        endTime: meeting.endTime,
        description: meeting.description,
        participants: [...meeting.participants]
    }
}

const handleMeetingClick = (event, meeting) => {
    if (event.detail === 3 && canManageMeeting(meeting)) {
        editMeeting(meeting)
        event.stopPropagation()
    }
}

const saveMeeting = async () => {
    if (!isValid.value) return

    isSaving.value = true
    meetingError.value = ''

    const payload = {
        topic: form.value.topic.trim(),
        description: form.value.description.trim(),
        meeting_type: form.value.meetingType,
        link: normalizeMeetingUrl(form.value.link),
        date: form.value.date,
        start_time: form.value.startTime,
        end_time: form.value.endTime,
        participants: form.value.participants,
    }

    try {
        const response = isEditing.value
            ? await authenticatedJsonRequest(`api/v1/logistics/meetings/${editId.value}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            })
            : await authenticatedJsonRequest('api/v1/logistics/meetings', {
                method: 'POST',
                body: JSON.stringify(payload),
            })

        upsertMeeting(response)
        cancelEdit()
    } catch (error) {
        meetingError.value = error instanceof Error ? error.message : 'Unable to save meeting.'
    } finally {
        isSaving.value = false
    }
}

const deleteMeeting = async (id) => {
    const meeting = meetings.value.find((item) => item.id === normalizeId(id))
    if (!meeting || !canManageMeeting(meeting)) return

    meetingError.value = ''

    try {
        await authenticatedJsonRequest(`api/v1/logistics/meetings/${id}`, {
            method: 'DELETE',
        })
        meetings.value = meetings.value.filter((item) => item.id !== normalizeId(id))
    } catch (error) {
        meetingError.value = error instanceof Error ? error.message : 'Unable to delete meeting.'
    }
}

const getRoutePrefix = (path) => {
    if (path.startsWith('/warehouse')) return '/warehouse'
    if (path.startsWith('/dispatcher')) return '/dispatcher'
    return '/logistic'
}

const joinMeeting = (meeting) => {
    const prefix = getRoutePrefix(route.path)
    const normalizedUrl = normalizeMeetingUrl(meeting.link)
    router.push({
        path: `${prefix}/meeting-room`,
        query: {
            url: normalizedUrl,
            title: meeting.topic,
            type: getMeetingPlatform(meeting)
        }
    })
    isOpen.value = false
}

const getHubName = (hubId) => {
    const hub = store.hubs?.find((item) => item.id === hubId)
    return hub ? hub.name : hubId
}

const getUserName = (id) => availableUsers.value.find((user) => user.id === normalizeId(id))?.name || 'Unknown'

const getUserInitials = (id) => {
    const name = getUserName(id)
    return name
        .split(' ')
        .map((part) => part[0])
        .filter(Boolean)
        .join('')
        .substring(0, 2)
        .toUpperCase() || '?'
}

const formatDate = (dateStr) => {
    const dateValue = new Date(dateStr)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (dateValue.toDateString() === today.toDateString()) return 'Today'
    if (dateValue.toDateString() === tomorrow.toDateString()) return 'Tomorrow'

    return dateValue.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const isMeetingLive = (meeting) => {
    const now = new Date()
    const start = new Date(`${meeting.date}T${meeting.startTime}`)
    const end = new Date(`${meeting.date}T${meeting.endTime}`)
    return now >= new Date(start.getTime() - 10 * 60000) && now <= end
}

const handleClickOutside = (event) => {
    if (popoverRef.value && !popoverRef.value.contains(event.target)) {
        isOpen.value = false
    }
}

onMounted(() => {
    document.addEventListener('click', handleClickOutside)

    if (!store.initialized && authStore.userRole !== 'DISPATCHER') {
        store.initialize().catch(() => {})
    }

    if (authStore.userRole === 'DISPATCHER' && dispatchStore.dispatcherContacts.length === 0) {
        dispatchStore.initialize().catch(() => {})
    }

    loadMeetings()
    loadParticipantOptions()
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})
</script>
