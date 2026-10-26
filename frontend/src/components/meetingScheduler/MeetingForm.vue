<template>
    <div class="p-5 space-y-4">

        <div v-if="meetingError" class="rounded-xl px-4 py-3 text-xs font-medium flex items-center gap-2" style="background:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2)">
            <span class="material-symbols-outlined text-[15px]">error</span>
            {{ meetingError }}
        </div>

        <!-- Topic -->
        <div>
            <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Meeting Topic</label>
            <input v-model="form.topic" type="text" placeholder="e.g. Weekly Sync"
                class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none transition-all"
                :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: isDark ? '#f1f5f9' : '#0f172a' }">
        </div>

        <!-- Platform -->
        <div>
            <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Platform</label>
            <div class="grid grid-cols-2 gap-2">
                <button v-for="p in platformOptions" :key="p.id"
                    type="button" @click="form.meetingType = p.id"
                    class="py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all border-2"
                    :class="form.meetingType === p.id ? p.activeClass : 'border-transparent'"
                    :style="form.meetingType !== p.id ? { background: isDark ? '#1e2235' : '#f1f5f9', color: isDark ? '#64748b' : '#94a3b8' } : {}">
                    <span class="w-2 h-2 rounded-full shrink-0" :class="p.dotColor"></span>
                    {{ p.label }}
                </button>
            </div>
        </div>

        <!-- Jitsi info / link input -->
        <div v-if="form.meetingType === 'jitsi'" class="flex items-start gap-3 rounded-xl px-4 py-3" style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.2)">
            <span class="material-symbols-outlined text-[18px] mt-0.5 shrink-0" style="color:#8b5cf6">auto_awesome</span>
            <p class="text-xs leading-relaxed" style="color:#8b5cf6">
                A private video room is <strong>auto-generated and runs inside the app</strong> — no link needed.
            </p>
        </div>
        <div v-else>
            <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Meeting Link</label>
            <input v-model="form.link" type="text" :placeholder="linkPlaceholder"
                class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none transition-all"
                :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: '#6366f1' }">
            <p v-if="form.link && getMeetingPlatform(form)" class="text-[10px] mt-1.5 flex items-center gap-1.5" :class="getPlatformConfig(getMeetingPlatform(form)).badgeClass.split(' ')[2]">
                <span class="w-1.5 h-1.5 rounded-full" :class="getPlatformConfig(getMeetingPlatform(form)).dotClass"></span>
                Detected: {{ getPlatformConfig(getMeetingPlatform(form)).label }}
            </p>
        </div>

        <!-- Date + Time row -->
        <div class="grid grid-cols-3 gap-2">
            <div class="col-span-3">
                <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Date</label>
                <input v-model="form.date" type="date"
                    class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none transition-all"
                    :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: isDark ? '#f1f5f9' : '#0f172a' }">
            </div>
            <div>
                <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Start</label>
                <input v-model="form.startTime" type="time"
                    class="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none transition-all"
                    :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: isDark ? '#f1f5f9' : '#0f172a' }">
            </div>
            <div class="col-span-2">
                <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">End</label>
                <input v-model="form.endTime" type="time"
                    class="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none transition-all"
                    :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: isDark ? '#f1f5f9' : '#0f172a' }">
            </div>
        </div>

        <!-- Description -->
        <div>
            <label class="block text-xs font-semibold mb-1.5" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Description <span class="font-normal opacity-60">(optional)</span></label>
            <textarea v-model="form.description" rows="2" placeholder="Agenda or notes..."
                class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none transition-all resize-none"
                :style="{ background: isDark ? '#1e2235' : '#f8faff', border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0', color: isDark ? '#f1f5f9' : '#0f172a' }"></textarea>
        </div>

        <!-- Participants -->
        <div class="rounded-xl overflow-hidden" :style="{ border: isDark ? '1px solid rgba(255,255,255,0.07)' : '1px solid #e2e8f0' }">
            <div class="px-4 py-3 flex items-center justify-between" :style="{ background: isDark ? '#1a1e2e' : '#f8faff' }">
                <span class="text-xs font-semibold" :style="{ color: isDark ? '#94a3b8' : '#64748b' }">Participants</span>
                <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full" style="background:rgba(99,102,241,0.12);color:#6366f1">
                    {{ selectedParticipantCount }} added
                </span>
            </div>
            <div class="px-4 py-2 flex gap-2" :style="{ borderTop: isDark ? '1px solid rgba(255,255,255,0.05)' : '1px solid #f1f5f9' }">
                <select v-model="filters.hub" class="flex-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none"
                    :style="{ background: isDark ? '#1e2235' : '#f1f5f9', color: isDark ? '#94a3b8' : '#64748b', border: 'none' }">
                    <option value="">All Hubs</option>
                    <option v-for="hub in store.hubs" :key="hub.id" :value="hub.id">{{ hub.name }}</option>
                </select>
                <select v-model="filters.role" class="flex-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none"
                    :style="{ background: isDark ? '#1e2235' : '#f1f5f9', color: isDark ? '#94a3b8' : '#64748b', border: 'none' }">
                    <option value="">All Roles</option>
                    <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
                </select>
            </div>
            <div class="max-h-36 overflow-y-auto divide-y" :style="{ borderTop: isDark ? '1px solid rgba(255,255,255,0.05)' : '1px solid #f1f5f9', divideColor: isDark ? 'rgba(255,255,255,0.04)' : '#f1f5f9' }">
                <div v-if="filteredUsers.length === 0" class="p-4 text-center text-xs" :style="{ color: isDark ? '#475569' : '#94a3b8' }">No users found.</div>
                <label v-for="user in filteredUsers" :key="user.id"
                    class="flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors"
                    :style="{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.04)' : '1px solid #f8faff' }"
                    :class="isDark ? 'hover:bg-white/5' : 'hover:bg-indigo-50/50'">
                    <input type="checkbox" :value="user.id" v-model="form.participants"
                        class="w-4 h-4 rounded accent-indigo-500">
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium truncate" :style="{ color: isDark ? '#e2e8f0' : '#1e293b' }">{{ user.name }}</div>
                        <div class="text-[10px] flex items-center gap-1.5" :style="{ color: isDark ? '#475569' : '#94a3b8' }">
                            <span>{{ user.role }}</span>
                            <span class="w-1 h-1 rounded-full" :style="{ background: isDark ? '#334155' : '#cbd5e1' }"></span>
                            <span>{{ getHubName(user.hubId) }}</span>
                        </div>
                    </div>
                </label>
            </div>
        </div>
    </div>

    <!-- Sticky footer -->
    <div class="px-5 pb-5">
        <button @click="saveMeeting"
            class="w-full py-3 rounded-xl text-sm font-bold text-white transition-all"
            :style="isValid && !isSaving ? 'background:linear-gradient(135deg,#6366f1,#8b5cf6);box-shadow:0 4px 14px rgba(99,102,241,0.4)' : 'background:#94a3b8;cursor:not-allowed'"
            :disabled="!isValid || isSaving">
            <span class="flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-[16px]">{{ isSaving ? 'hourglass_top' : (isEditing ? 'edit_calendar' : 'event_available') }}</span>
                {{ isSaving ? (isEditing ? 'Updating...' : 'Scheduling...') : (isEditing ? 'Update Schedule' : 'Schedule Meeting') }}
            </span>
        </button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { getMeetingPlatform, getPlatformConfig, platformOptions } from './meetingFormat'
import { meetingSchedulerKey } from './meetingSchedulerContext'

const {
    filteredUsers,
    filters,
    form,
    getHubName,
    isDark,
    isEditing,
    isSaving,
    isValid,
    linkPlaceholder,
    meetingError,
    roleOptions,
    saveMeeting,
    selectedParticipantCount,
    store,
} = inject(meetingSchedulerKey)
</script>
