<template>
    <aside
        class="w-64 h-screen bg-surface-light dark:bg-card-darker border-r border-gray-200 dark:border-white/5 flex flex-col fixed left-0 top-0 z-50 transition-transform duration-300 transform md:translate-x-0"
        :class="isOpen ? 'translate-x-0' : '-translate-x-full'">

        <!-- Logo area -->
        <div class="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-white/5">
            <div class="flex items-center gap-3">
                <img src="@/assets/cargo-core-logo.png" alt="Cargo-Core Logo" class="h-8 w-auto" />
                <div class="text-xl font-bold text-gray-900 dark:text-white tracking-wide">Cargo-Core <span
                        class="text-purple-500">AI</span></div>
            </div>
            <!-- Mobile Close Button -->
            <button @click="$emit('close')"
                class="md:hidden text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto py-4 no-scrollbar">
            <ul class="space-y-1 px-3">
                <li v-for="item in menuItems" :key="item.name">
                    <router-link :to="item.route"
                        class="flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group relative"
                        :class="[
                            $route.path === item.route
                                ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'
                        ]">
                        <!-- Active Indicator -->
                        <div v-if="$route.path === item.route"
                            class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-purple-500 rounded-r-full"></div>

                        <span class="material-symbols-outlined mr-3 text-[20px]"
                            :class="$route.path === item.route ? 'text-purple-500' : 'text-gray-500 group-hover:text-gray-900 dark:group-hover:text-white'">
                            {{ item.icon }}
                        </span>
                        <span class="text-sm font-medium">{{ item.label }}</span>
                        <span v-if="item.badge"
                            class="ml-auto bg-red-500 text-white font-bold text-[10px] px-1.5 py-0.5 rounded-full">
                            {{ item.badge }}
                        </span>
                    </router-link>
                </li>
            </ul>

            <!-- AI Status -->
            <div class="mt-6 px-4">
                <div
                    class="p-4 rounded-xl bg-gradient-to-br from-purple-600/10 to-blue-600/10 dark:from-purple-600/20 dark:to-blue-600/20 border border-purple-200/50 dark:border-white/5">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="relative flex h-2 w-2">
                            <span
                                class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        <span class="text-xs font-bold text-gray-900 dark:text-white">AI Engine Online</span>
                    </div>
                    <p class="text-[10px] text-gray-500 dark:text-gray-400">Processing live streams &amp; support
                        tickets.</p>
                    <div class="mt-3 grid grid-cols-2 gap-2">
                        <div v-for="m in aiMetrics" :key="m.id"
                            class="bg-white/60 dark:bg-white/5 rounded p-2 text-center border border-gray-200 dark:border-white/5">
                            <div class="text-[10px] text-gray-500 dark:text-gray-400 font-medium">{{ m.name }}</div>
                            <div class="font-bold text-xs mt-0.5" :class="m.color">{{ m.value }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>

        <!-- AI Admin Profile with Context Menu -->
        <div class="p-4 border-t border-gray-200 dark:border-white/5 relative" @mouseenter="isMenuOpen = true"
            @mouseleave="isMenuOpen = false">

            <!-- Context Menu -->
            <transition enter-active-class="transition duration-200 ease-out"
                enter-from-class="transform scale-95 opacity-0 translate-y-2"
                enter-to-class="transform scale-100 opacity-100 translate-y-0"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="transform scale-100 opacity-100 translate-y-0"
                leave-to-class="transform scale-95 opacity-0 translate-y-2">
                <div v-if="isMenuOpen"
                    class="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-card-dark rounded-xl shadow-xl border border-gray-200 dark:border-white/10 overflow-hidden z-50">
                    <div class="py-1">

                        <!-- Profile -->
                        <button @click="showProfileModal = true"
                            class="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3 transition-colors">
                            <span class="material-symbols-outlined text-[20px] text-purple-500">person</span>
                            Profile
                        </button>

                        <!-- ID Card -->
                        <button @click="showIdCardModal = true"
                            class="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3 transition-colors">
                            <span class="material-symbols-outlined text-[20px] text-purple-500">badge</span>
                            System ID Card
                        </button>

                        <!-- Appearance Toggle -->
                        <div class="w-full px-4 py-2.5 flex items-center gap-3">
                            <span
                                class="material-symbols-outlined text-[20px] text-purple-500 transition-all duration-300">
                                {{ isDark ? 'dark_mode' : 'light_mode' }}
                            </span>
                            <span class="text-sm text-gray-700 dark:text-gray-200 flex-1">Appearance</span>
                            <ThemeToggle />
                        </div>

                        <div class="border-t border-gray-200 dark:border-white/5 my-1"></div>

                        <!-- Logout -->
                        <button @click="showLogoutConfirm = true"
                            class="w-full text-left px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors">
                            <span class="material-symbols-outlined text-[20px]">logout</span>
                            Logout
                        </button>
                    </div>
                </div>
            </transition>

            <div
                class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors relative z-10">
                <div
                    class="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center ring-1 ring-purple-500/30 text-white text-xs font-bold shrink-0">
                    {{ userInitials }}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ authStore.userName || 'User' }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-500 truncate">{{ authStore.userRoleLabel }}</div>
                </div>
                <span class="material-symbols-outlined text-gray-500 dark:text-gray-400">more_vert</span>
            </div>
        </div>
    </aside>

    <!-- Profile Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showProfileModal" @close="showProfileModal = false">
            <template #title>My Profile</template>
            <div class="space-y-6">
                <div class="flex items-center gap-4">
                    <div
                        class="w-20 h-20 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20 text-white text-3xl font-bold">
                        {{ userInitials }}
                    </div>
                    <div>
                        <h4 class="text-xl font-bold text-gray-900 dark:text-white">{{ authStore.userName }}</h4>
                        <p class="text-gray-500">{{ authStore.userRoleLabel }}</p>
                        <div
                            class="mt-2 text-xs bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            Online
                        </div>
                    </div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">User ID</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white font-mono">{{ authStore.user?.id || '—' }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">Email Address</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white break-all">{{ authStore.userEmail || '—' }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">Role</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ authStore.userRoleLabel }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">Phone</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ authStore.user?.phone || '—' }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">Member Since</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ memberSince }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xs text-gray-500 mb-1">Open Escalations</div>
                        <div class="font-bold text-sm text-red-600 dark:text-red-400">{{ aiSupportStore.dashboard?.stats?.open_escalations ?? 0 }}</div>
                    </div>
                </div>
            </div>
            <template #footer>
                <button @click="showProfileModal = false"
                    class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Close</button>
            </template>
        </BaseModal>
    </Teleport>

    <!-- ID Card Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showIdCardModal" @close="showIdCardModal = false">
            <template #title>System ID Card</template>
            <div class="flex justify-center w-full">
                <IdCard :employee="aiCardData" />
            </div>
            <template #footer>
                <button @click="showIdCardModal = false"
                    class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                    Close
                </button>
            </template>
        </BaseModal>
    </Teleport>

    <!-- Logout Confirmation Modal -->
    <Teleport to="body">
        <div v-if="showLogoutConfirm"
            class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            @click.self="showLogoutConfirm = false">
            <div
                class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden border border-gray-100 dark:border-white/10 p-6">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-12 h-12 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center">
                        <span class="material-symbols-outlined text-red-500 text-2xl">logout</span>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Confirm Logout</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Are you sure you want to sign out?</p>
                    </div>
                </div>
                <div class="flex gap-3">
                    <button @click="showLogoutConfirm = false"
                        class="flex-1 py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors">
                        Cancel
                    </button>
                    <button @click="handleLogout"
                        class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl transition-colors">
                        Logout
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import BaseModal from '@/components/BaseModal.vue'
import IdCard from '@/components/IdCard.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/authStore'
import { useAiSupportStore } from '@/stores/aiSupportStore'

defineProps({
    isOpen: Boolean
})
defineEmits(['close'])

const router = useRouter()
const authStore = useAuthStore()
const aiSupportStore = useAiSupportStore()

// Menu & Modal State
const isMenuOpen = ref(false)
const showProfileModal = ref(false)
const showIdCardModal = ref(false)
const showLogoutConfirm = ref(false)

// Dark mode tracking for dynamic icon
const isDark = ref(true)
let themeObserver = null

onMounted(() => {
    isDark.value = document.documentElement.classList.contains('dark')
    themeObserver = new MutationObserver(() => {
        isDark.value = document.documentElement.classList.contains('dark')
    })
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
    })
    aiSupportStore.loadDashboard().catch(() => {})
    aiSupportStore.loadSessions().catch(() => {})
})

onUnmounted(() => {
    if (themeObserver) themeObserver.disconnect()
})

// User initials helper
const userInitials = computed(() => {
    return (authStore.userName || 'U')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map(p => p[0]?.toUpperCase() || '')
        .join('')
})

// Member since formatted
const memberSince = computed(() => {
    const raw = authStore.user?.created_at
    if (!raw) return '—'
    return new Date(raw).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
})

// ID Card — real user data
const aiCardData = computed(() => ({
    name: authStore.userName || 'User',
    id: authStore.user?.id ? String(authStore.user.id) : '—',
    designation: authStore.userRoleLabel,
    department: 'Cargo-Core AI Support',
    address: authStore.user?.address || 'Cargo-Core HQ',
    phone: authStore.user?.phone || '—',
    email: authStore.userEmail || '—',
    joinDate: memberSince.value,
    validUntil: '31 December 2027',
    emergencyContact: {
        name: 'IT Support',
        relation: 'System Administrator',
        phone: '+00 0000000001'
    }
}))

const handleLogout = async () => {
    showLogoutConfirm.value = false
    isMenuOpen.value = false
    await authStore.logout()
    router.push('/login')
}

// AI Live Metrics for sidebar
const aiMetrics = computed(() => {
    const stats = aiSupportStore.dashboard?.stats
    return [
        { id: 'm1', name: 'Sessions', value: String(stats?.total_sessions ?? 0), color: 'text-purple-600 dark:text-purple-400' },
        { id: 'm2', name: 'Open Forms', value: String(stats?.open_contact_forms ?? 0), color: 'text-yellow-600 dark:text-yellow-400' },
        { id: 'm3', name: 'Human', value: String(stats?.human_engaged_sessions ?? 0), color: 'text-green-600 dark:text-green-400' },
        { id: 'm4', name: 'Escalated', value: String(stats?.open_escalations ?? 0), color: 'text-red-600 dark:text-red-400' },
    ]
})

const menuItems = computed(() => [
    { label: 'Dashboard', icon: 'dashboard', route: '/ai/dashboard' },
    { label: 'Contact Forms', icon: 'contact_mail', route: '/ai/contact-forms' },
    { label: 'Live Conversations', icon: 'chat', route: '/ai/live-conversations', badge: aiSupportStore.sessions.length ? String(aiSupportStore.sessions.length) : '' },
    { label: 'Escalations', icon: 'warning', route: '/ai/escalations', badge: aiSupportStore.dashboard?.stats?.open_escalations ? String(aiSupportStore.dashboard.stats.open_escalations) : '' },
    { label: 'Tickets', icon: 'confirmation_number', route: '/ai/tickets' },
    { label: 'Reverse Logistics', icon: 'assignment_return', route: '/ai/reverse-logistics' },
    { label: 'Refund Center', icon: 'currency_exchange', route: '/ai/refund-center' },
    { label: 'AI Analytics', icon: 'analytics', route: '/ai/analytics' },
    { label: 'Knowledge Base', icon: 'menu_book', route: '/ai/knowledge-base' },
    { label: 'Legal & Rules', icon: 'gavel', route: '/ai/legal' },
    { label: 'Settings', icon: 'settings', route: '/ai/settings' },
])
</script>
