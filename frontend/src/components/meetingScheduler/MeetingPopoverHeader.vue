<template>
    <!-- Header bar with gradient accent -->
    <div class="px-5 pt-5 pb-4" :style="{ background: isDark ? '#1a1e2e' : '#f8faff', borderRadius: '16px 16px 0 0', borderBottom: isDark ? '1px solid rgba(255,255,255,0.07)' : '1px solid #e8edf5' }">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl flex items-center justify-center" style="background: linear-gradient(135deg,#6366f1,#8b5cf6)">
                    <span class="material-symbols-outlined text-white text-[18px]">video_call</span>
                </div>
                <div>
                    <h3 class="font-bold text-[15px]" :style="{ color: isDark ? '#f1f5f9' : '#0f172a' }">Meetings</h3>
                    <p class="text-[11px]" :style="{ color: isDark ? '#64748b' : '#94a3b8' }">
                        {{ meetings.length > 0 ? `${meetings.length} scheduled` : 'No meetings yet' }}
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button v-if="!isCreating && !isEditing" @click.stop="startCreating"
                    class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
                    style="background: linear-gradient(135deg,#6366f1,#8b5cf6); color: white;">
                    <span class="material-symbols-outlined text-[14px]">add</span>
                    Schedule
                </button>
                <button v-else @click.stop="cancelEdit"
                    class="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                    :style="{ background: isDark ? 'rgba(239,68,68,0.15)' : '#fef2f2', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }">
                    <span class="material-symbols-outlined text-[14px]">close</span>
                    Cancel
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { meetingSchedulerKey } from './meetingSchedulerContext'

const {
    cancelEdit,
    isCreating,
    isDark,
    isEditing,
    meetings,
    startCreating,
} = inject(meetingSchedulerKey)
</script>
