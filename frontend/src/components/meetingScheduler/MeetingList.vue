<template>

    <div v-if="isLoadingMeetings" class="py-12 text-center">
        <span class="material-symbols-outlined text-4xl animate-spin mb-3" :style="{ color: isDark ? '#475569' : '#94a3b8' }">progress_activity</span>
        <p class="text-sm" :style="{ color: isDark ? '#475569' : '#94a3b8' }">Loading meetings...</p>
    </div>

    <div v-else-if="meetingError" class="py-10 px-5 text-center space-y-3">
        <span class="material-symbols-outlined text-4xl" style="color:#ef4444">error_outline</span>
        <p class="text-sm" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">{{ meetingError }}</p>
        <button @click="loadMeetings" class="text-xs font-semibold px-4 py-1.5 rounded-lg" style="background:rgba(99,102,241,0.1);color:#6366f1">Retry</button>
    </div>

    <div v-else-if="meetings.length === 0" class="py-14 px-5 text-center">
        <div class="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center" :style="{ background: isDark ? 'rgba(99,102,241,0.1)' : '#f0f0ff' }">
            <span class="material-symbols-outlined text-3xl" style="color:#6366f1">event_note</span>
        </div>
        <p class="font-semibold text-sm mb-1" :style="{ color: isDark ? '#e2e8f0' : '#1e293b' }">No meetings scheduled</p>
        <p class="text-xs mb-4" :style="{ color: isDark ? '#475569' : '#94a3b8' }">Schedule your first meeting to get started</p>
        <button @click.stop="startCreating" class="text-xs font-semibold px-4 py-2 rounded-lg text-white" style="background:linear-gradient(135deg,#6366f1,#8b5cf6)">
            + Schedule Meeting
        </button>
    </div>

    <div v-else class="p-3 space-y-2">
        <div v-for="meeting in sortedMeetings" :key="meeting.id"
            class="group rounded-xl p-4 cursor-pointer select-none transition-all border"
            :style="{ background: isDark ? '#1e2235' : '#f8faff', borderColor: isDark ? 'rgba(255,255,255,0.06)' : '#e8edf5' }"
            @click.stop="handleMeetingClick($event, meeting)" :title="meetingCardTitle(meeting)">

            <!-- Live pulse + topic row -->
            <div class="flex items-start justify-between gap-2 mb-2">
                <div class="flex items-center gap-2 min-w-0">
                    <span v-if="isMeetingLive(meeting)" class="flex h-2 w-2 shrink-0 relative">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <h4 class="font-semibold text-sm truncate" :style="{ color: isDark ? '#f1f5f9' : '#0f172a' }">{{ meeting.topic }}</h4>
                </div>
                <span class="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full" :style="{ background: isDark ? 'rgba(255,255,255,0.08)' : '#e8edf5', color: isDark ? '#94a3b8' : '#64748b' }">
                    {{ formatDate(meeting.date) }}
                </span>
            </div>

            <!-- Meta row -->
            <div class="flex items-center gap-2 mb-3">
                <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1"
                    :class="getPlatformConfig(getMeetingPlatform(meeting)).badgeClass">
                    <span class="w-1.5 h-1.5 rounded-full inline-block shrink-0" :class="getPlatformConfig(getMeetingPlatform(meeting)).dotClass"></span>
                    {{ getPlatformConfig(getMeetingPlatform(meeting)).label }}
                </span>
                <span class="text-[11px] flex items-center gap-1" :style="{ color: isDark ? '#64748b' : '#94a3b8' }">
                    <span class="material-symbols-outlined text-[12px]">schedule</span>
                    {{ meeting.startTime }} – {{ meeting.endTime }}
                </span>
            </div>

            <p v-if="meeting.description" class="text-xs mb-3 line-clamp-1" :style="{ color: isDark ? '#64748b' : '#94a3b8' }">{{ meeting.description }}</p>

            <!-- Footer: avatars + actions -->
            <div class="flex items-center justify-between">
                <div class="flex -space-x-1.5">
                    <div v-for="uid in meeting.participants.slice(0, 4)" :key="uid"
                        class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold ring-2 ring-white dark:ring-[#1e2235]"
                        :style="{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: 'white' }"
                        :title="getUserName(uid)">{{ getUserInitials(uid) }}</div>
                    <div v-if="meeting.participants.length > 4"
                        class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold ring-2 ring-white dark:ring-[#1e2235]"
                        :style="{ background: isDark ? '#2d3348' : '#e8edf5', color: isDark ? '#94a3b8' : '#64748b' }">
                        +{{ meeting.participants.length - 4 }}
                    </div>
                </div>
                <div class="flex items-center gap-1.5">
                    <button v-if="canManageMeeting(meeting)" @click.stop="deleteMeeting(meeting.id)"
                        class="w-7 h-7 flex items-center justify-center rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                        :style="{ color: '#ef4444', background: isDark ? 'rgba(239,68,68,0.1)' : '#fef2f2' }">
                        <span class="material-symbols-outlined text-[15px]">delete</span>
                    </button>
                    <button @click.stop="joinMeeting(meeting)"
                        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white transition-all"
                        style="background: linear-gradient(135deg,#6366f1,#8b5cf6); box-shadow: 0 2px 8px rgba(99,102,241,0.35)">
                        <span class="material-symbols-outlined text-[13px]">videocam</span>
                        Join
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { formatDate, getMeetingPlatform, getPlatformConfig, isMeetingLive } from './meetingFormat'
import { meetingSchedulerKey } from './meetingSchedulerContext'

const {
    canManageMeeting,
    deleteMeeting,
    getUserInitials,
    getUserName,
    handleMeetingClick,
    isDark,
    isLoadingMeetings,
    joinMeeting,
    loadMeetings,
    meetingCardTitle,
    meetingError,
    meetings,
    sortedMeetings,
    startCreating,
} = inject(meetingSchedulerKey)
</script>
