<template>
    <div class="relative" ref="popoverRef">
        <!-- Trigger Button -->
        <button @click="togglePopover"
            class="relative w-9 h-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            :class="{ 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white': isOpen }">
            <span class="material-symbols-outlined text-[20px]">calendar_add_on</span>
            <span v-if="upcomingMeetingsCount > 0"
                class="absolute top-0 right-0 w-4 h-4 bg-primary text-white text-[10px] font-bold flex items-center justify-center rounded-full border-2 border-surface-light dark:border-background-dark">
                {{ upcomingMeetingsCount }}
            </span>
        </button>

        <!-- Popover -->
        <div v-show="isOpen"
            class="absolute right-0 mt-3 w-[420px] rounded-2xl z-50 transition-all duration-200 origin-top-right"
            :class="isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none'"
            style="background:#ffffff; box-shadow:0 20px 60px rgba(0,0,0,0.18), 0 4px 16px rgba(0,0,0,0.10);"
            :style="{ background: isDark ? '#13161f' : '#ffffff', boxShadow: '0 20px 60px rgba(0,0,0,0.25), 0 4px 16px rgba(0,0,0,0.15)' }">

            <MeetingPopoverHeader />

            <!-- VIEW MODE -->
            <div v-if="!isCreating && !isEditing" class="max-h-[480px] overflow-y-auto no-scrollbar">
                <MeetingList />
            </div>

            <!-- CREATE / EDIT FORM -->
            <div v-else class="max-h-[520px] overflow-y-auto no-scrollbar">
                <MeetingForm />
            </div>
        </div>
    </div>
</template>

<script setup>
import MeetingPopoverHeader from './meetingScheduler/MeetingPopoverHeader.vue'
import MeetingList from './meetingScheduler/MeetingList.vue'
import MeetingForm from './meetingScheduler/MeetingForm.vue'
import { meetingSchedulerKey } from './meetingScheduler/meetingSchedulerContext'
import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authenticatedJsonRequest } from '@/config/api'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import {
    detectPlatform,
    generateJitsiUrl,
    getMeetingPlatform,
    normalizeId,
    normalizeMeeting,
    normalizeMeetingUrl,
    titleCase,
    todayDate,
} from './meetingScheduler/meetingFormat'

const store = useLogisticStore()
const dispatchStore = useDispatcherStore()

const isDark = computed(() => document.documentElement.classList.contains('dark'))
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

const meetings = ref([])

const defaultForm = {
    topic: '',
    link: '',
    meetingType: 'jitsi',
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
    const linkOk = form.value.meetingType === 'jitsi' || Boolean(form.value.link.trim())
    return Boolean(
        form.value.topic.trim() &&
        linkOk &&
        form.value.date &&
        form.value.startTime &&
        form.value.endTime &&
        form.value.endTime > form.value.startTime &&
        form.value.participants.length > 0
    )
})

const linkPlaceholder = computed(() => {
    const map = {
        jitsi: 'Room auto-created — no link needed',
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

    const resolvedLink = form.value.meetingType === 'jitsi'
        ? generateJitsiUrl(form.value.topic)
        : normalizeMeetingUrl(form.value.link)

    const payload = {
        topic: form.value.topic.trim(),
        description: form.value.description.trim(),
        meeting_type: form.value.meetingType,
        link: resolvedLink,
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

provide(meetingSchedulerKey, {
    canManageMeeting,
    cancelEdit,
    deleteMeeting,
    filteredUsers,
    filters,
    form,
    getHubName,
    getUserInitials,
    getUserName,
    handleMeetingClick,
    isCreating,
    isDark,
    isEditing,
    isLoadingMeetings,
    isSaving,
    isValid,
    joinMeeting,
    linkPlaceholder,
    loadMeetings,
    meetingCardTitle,
    meetingError,
    meetings,
    roleOptions,
    saveMeeting,
    selectedParticipantCount,
    sortedMeetings,
    startCreating,
    store,
})
</script>
