<template>
  <div class="relative">
    <!-- Bell Button -->
    <button
      class="w-9 h-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white relative outline-none focus:ring-2 focus:ring-primary/50"
      @click="toggle"
    >
      <span class="material-symbols-outlined text-[20px]" :class="{ 'text-primary': unreadCount > 0 }">notifications</span>
      <transition name="badge">
        <span
          v-if="badgeCount > 0"
          class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 border-2 border-white dark:border-gray-900 text-white text-[9px] font-black flex items-center justify-center leading-none animate-pulse"
        >{{ badgeCount > 99 ? '99+' : badgeCount }}</span>
      </transition>
    </button>

    <!-- Panel -->
    <transition name="slide-down">
      <div
        v-if="isOpen"
        class="absolute right-0 top-full mt-2 w-[360px] bg-white dark:bg-[#0f1117] border border-gray-200 dark:border-white/10 rounded-2xl shadow-2xl z-50 overflow-hidden flex flex-col"
        style="max-height: 520px"
      >
        <!-- Header -->
        <div class="px-4 py-3 border-b border-gray-100 dark:border-white/8 flex items-center justify-between bg-gray-50/80 dark:bg-white/3">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[18px] text-primary">notifications_active</span>
            <h3 class="text-sm font-bold text-gray-900 dark:text-white">Notifications</h3>
            <span
              v-if="unreadCount > 0"
              class="px-1.5 py-0.5 bg-red-500/10 text-red-500 dark:text-red-400 text-[10px] font-bold rounded-full"
            >{{ unreadCount }} new</span>
          </div>
          <div v-if="notifications.length > 0" class="flex items-center gap-1">
            <button
              class="p-1.5 rounded-lg text-gray-400 hover:text-primary hover:bg-primary/10 transition-all"
              title="Mark all as read"
              @click="$emit('mark-all-read')"
            >
              <span class="material-symbols-outlined text-[16px]">done_all</span>
            </button>
            <button
              class="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Clear all"
              @click="$emit('clear-all')"
            >
              <span class="material-symbols-outlined text-[16px]">delete_sweep</span>
            </button>
          </div>
        </div>

        <!-- List -->
        <div class="overflow-y-auto flex-1 divide-y divide-gray-100 dark:divide-white/5">
          <!-- Empty state -->
          <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center py-12 px-4 gap-3">
            <div class="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center">
              <span class="material-symbols-outlined text-[28px] text-gray-400 dark:text-gray-600">notifications_off</span>
            </div>
            <p class="text-sm font-medium text-gray-500 dark:text-gray-500">All caught up!</p>
            <p class="text-xs text-gray-400 dark:text-gray-600 text-center">No notifications right now.</p>
          </div>

          <!-- Unread section -->
          <template v-if="unreadNotifs.length > 0">
            <div class="px-4 py-1.5 bg-gray-50/60 dark:bg-white/2">
              <span class="text-[10px] font-bold uppercase tracking-widest text-gray-400">Unread</span>
            </div>
            <div
              v-for="notif in unreadNotifs"
              :key="notif.id"
              class="group flex gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-white/3 transition-colors cursor-pointer relative"
              :class="getLeftBorder(notif.type)"
              @click="handleMarkRead(notif)"
            >
              <!-- Icon -->
              <div class="mt-0.5 shrink-0">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center" :class="getIconBg(notif.type)">
                  <span class="material-symbols-outlined text-[16px]" :class="getIconColor(notif.type)">{{ getTypeIcon(notif.type) }}</span>
                </div>
              </div>
              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <h4 class="text-sm font-semibold text-gray-900 dark:text-white leading-snug line-clamp-1">{{ notif.title }}</h4>
                  <span class="text-[10px] text-gray-400 shrink-0 mt-0.5">{{ formatTime(notif.time) }}</span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2 leading-relaxed">{{ notif.message }}</p>
                <!-- In-progress indicator -->
                <div v-if="notif.inProgress" class="mt-1.5 flex items-center gap-1.5">
                  <div class="flex gap-0.5">
                    <span class="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay:0ms" />
                    <span class="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay:150ms" />
                    <span class="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay:300ms" />
                  </div>
                  <span class="text-[10px] text-blue-500 font-medium">In progress</span>
                </div>
              </div>
              <!-- Unread dot -->
              <div class="absolute right-3 top-3.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
            </div>
          </template>

          <!-- Read section -->
          <template v-if="readNotifs.length > 0">
            <div class="px-4 py-1.5 bg-gray-50/60 dark:bg-white/2">
              <span class="text-[10px] font-bold uppercase tracking-widest text-gray-400">Earlier</span>
            </div>
            <div
              v-for="notif in readNotifs"
              :key="notif.id"
              class="flex gap-3 px-4 py-3 opacity-60 hover:opacity-80 transition-opacity"
            >
              <div class="mt-0.5 shrink-0">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center bg-gray-100 dark:bg-white/5">
                  <span class="material-symbols-outlined text-[16px] text-gray-400">{{ getTypeIcon(notif.type) }}</span>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 leading-snug line-clamp-1">{{ notif.title }}</h4>
                  <span class="text-[10px] text-gray-400 shrink-0 mt-0.5">{{ formatTime(notif.time) }}</span>
                </div>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">{{ notif.message }}</p>
              </div>
            </div>
          </template>
        </div>

        <!-- Footer -->
        <div v-if="notifications.length > 0" class="px-4 py-2.5 border-t border-gray-100 dark:border-white/8 bg-gray-50/80 dark:bg-white/2 flex justify-center">
          <span class="text-[11px] text-gray-400 dark:text-gray-600">{{ notifications.length }} notification{{ notifications.length !== 1 ? 's' : '' }} total</span>
        </div>
      </div>
    </transition>

    <!-- Backdrop -->
    <div v-if="isOpen" class="fixed inset-0 z-40 bg-transparent" @click="close" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  notifications: { type: Array, default: () => [] },
  unreadCount: { type: Number, default: 0 },
})

const emit = defineEmits(['mark-read', 'mark-all-read', 'clear-all', 'open'])

const isOpen = ref(false)

const unreadNotifs = computed(() => props.notifications.filter(n => !n.read))
const readNotifs = computed(() => props.notifications.filter(n => n.read))

// Persist seen notification IDs in localStorage so badge resets after user views them
const SEEN_KEY = 'cargo_notif_seen_ids'

function loadSeenIds() {
  try { return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')) } catch { return new Set() }
}
function saveSeenIds(ids) {
  try { localStorage.setItem(SEEN_KEY, JSON.stringify([...ids])) } catch {}
}

const seenIds = ref(loadSeenIds())

// Badge: unread notifications not yet seen by the user
const badgeCount = computed(() =>
  props.notifications.filter(n => !n.read && !seenIds.value.has(String(n.id))).length
)

// Guard against the backdrop's click firing on the same interaction that opens the panel
let allowClose = false

function toggle() {
  if (isOpen.value) {
    isOpen.value = false
    return
  }
  isOpen.value = true
  allowClose = false
  // Mark all current notifications as seen — clears badge, persists across refreshes
  const updated = new Set([...seenIds.value, ...props.notifications.map(n => String(n.id))])
  seenIds.value = updated
  saveSeenIds(updated)
  setTimeout(() => { allowClose = true }, 100)
  emit('open')
}
function close() {
  if (!allowClose) return
  isOpen.value = false
}

function handleMarkRead(notif) {
  if (!notif.read) emit('mark-read', notif.id)
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const diff = Date.now() - date.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
}

function getTypeIcon(type) {
  const icons = {
    alert: 'error',
    warning: 'warning',
    success: 'check_circle',
    info: 'info',
    order: 'package_2',
    payment: 'payments',
    system: 'settings',
  }
  return icons[type] ?? 'notifications'
}

function getIconBg(type) {
  const map = {
    alert: 'bg-red-50 dark:bg-red-500/10',
    warning: 'bg-yellow-50 dark:bg-yellow-500/10',
    success: 'bg-green-50 dark:bg-green-500/10',
    info: 'bg-blue-50 dark:bg-blue-500/10',
    order: 'bg-violet-50 dark:bg-violet-500/10',
    payment: 'bg-emerald-50 dark:bg-emerald-500/10',
    system: 'bg-gray-100 dark:bg-white/5',
  }
  return map[type] ?? 'bg-blue-50 dark:bg-blue-500/10'
}

function getIconColor(type) {
  const map = {
    alert: 'text-red-500',
    warning: 'text-yellow-500',
    success: 'text-green-500',
    info: 'text-blue-500',
    order: 'text-violet-500',
    payment: 'text-emerald-500',
    system: 'text-gray-500',
  }
  return map[type] ?? 'text-blue-500'
}

function getLeftBorder(type) {
  const map = {
    alert: 'border-l-2 border-l-red-500',
    warning: 'border-l-2 border-l-yellow-400',
    success: 'border-l-2 border-l-green-500',
    info: 'border-l-2 border-l-blue-500',
    order: 'border-l-2 border-l-violet-500',
    payment: 'border-l-2 border-l-emerald-500',
    system: 'border-l-2 border-l-gray-400',
  }
  return map[type] ?? 'border-l-2 border-l-blue-500'
}
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.97);
}

.badge-enter-active,
.badge-leave-active {
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.15s;
}
.badge-enter-from,
.badge-leave-to {
  transform: scale(0);
  opacity: 0;
}
</style>
