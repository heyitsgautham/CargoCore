<template>
    <aside
        class="w-64 h-screen bg-surface-light dark:bg-card-darker border-r border-gray-200 dark:border-white/5 flex flex-col fixed left-0 top-0 z-50">
        <!-- Logo area -->
        <div class="h-16 flex items-center px-6 border-b border-gray-200 dark:border-white/5 gap-3">
            <img src="@/assets/cargo-core-logo.png" alt="Cargo-Core Logo" class="h-8 w-auto" />
            <div class="text-xl font-bold text-primary tracking-wide">Cargo-Core</div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto py-4 no-scrollbar">
            <ul class="space-y-1 px-3">
                <li v-for="item in menuItems" :key="item.name">
                    <router-link :to="item.route"
                        class="flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group"
                        :class="[
                            $route.path === item.route
                                ? 'bg-primary/10 text-primary'
                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'
                        ]">
                        <span class="material-symbols-outlined mr-3 text-[20px]"
                            :class="$route.path === item.route ? 'text-primary' : 'text-gray-500 group-hover:text-gray-900 dark:group-hover:text-white'">
                            {{ item.icon }}
                        </span>
                        <span class="text-sm font-medium">{{ item.label }}</span>
                        <span v-if="item.badge"
                            class="ml-auto bg-amber-500 text-black font-bold text-[10px] px-1.5 py-0.5 rounded-full">
                            {{ item.badge }}
                        </span>
                        <span v-if="item.alert"
                            class="ml-auto bg-red-500 text-white font-bold text-[10px] px-1.5 py-0.5 rounded-full animate-pulse">
                            {{ item.alert }}
                        </span>
                    </router-link>
                </li>
            </ul>

            <!-- Zone Status -->
            <div class="mt-8 px-4">
                <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Dispatch Metrics</div>
                <div class="grid grid-cols-2 gap-2">
                    <div v-for="zone in zones" :key="zone.id"
                        class="bg-gray-100 dark:bg-white/5 rounded p-2 text-center border border-gray-200 dark:border-white/5 transition-colors cursor-pointer"
                        :class="[
                            zone.status === 'Alert' ? 'hover:border-amber-500/50' :
                                zone.status === 'Full' ? 'hover:border-red-500/50' : 'hover:border-primary/50'
                        ]">
                        <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">{{ zone.name }}</div>
                        <div class="font-bold mt-1" :class="[
                            zone.status === 'Alert' ? 'text-amber-500 dark:text-yellow-400' :
                                zone.status === 'Full' ? 'text-red-500 dark:text-red-400' : 'text-primary'
                        ]">{{ zone.value }}</div>
                    </div>
                </div>
            </div>
        </nav>

        <!-- User Profile -->
        <div class="p-4 border-t border-gray-200 dark:border-white/5 relative" @mouseenter="isUserMenuOpen = true"
            @mouseleave="isUserMenuOpen = false">

            <!-- Context Menu -->
            <transition enter-active-class="transition duration-200 ease-out"
                enter-from-class="transform scale-95 opacity-0 translate-y-2"
                enter-to-class="transform scale-100 opacity-100 translate-y-0"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="transform scale-100 opacity-100 translate-y-0"
                leave-to-class="transform scale-95 opacity-0 translate-y-2">
                <div v-if="isUserMenuOpen"
                    class="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-card-darker rounded-xl shadow-xl border border-gray-200 dark:border-white/10 overflow-hidden z-50">
                    <div class="py-1">
                        <!-- Profile Option -->
                        <button @click="showProfileModal = true"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3">
                            <span class="material-symbols-outlined text-[20px]">person</span>
                            Profile
                        </button>

                        <!-- ID Card Option -->
                        <button @click="showIdCardModal = true"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3">
                            <span class="material-symbols-outlined text-[20px]">badge</span>
                            ID Card
                        </button>

                        <!-- Appearance Toggle -->
                        <div class="w-full px-4 py-2.5 flex items-center gap-3">
                            <span
                                class="material-symbols-outlined text-[20px] text-primary transition-all duration-300">
                                {{ isDark ? 'dark_mode' : 'light_mode' }}
                            </span>
                            <span class="text-sm text-gray-700 dark:text-gray-200 flex-1">Appearance</span>
                            <ThemeToggle />
                        </div>

                        <div class="border-t border-gray-200 dark:border-white/5 my-1"></div>

                        <!-- Logout Option -->
                        <button @click="showLogoutConfirm = true"
                            class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3">
                            <span class="material-symbols-outlined text-[20px]">logout</span>
                            Logout
                        </button>
                    </div>
                </div>
            </transition>

            <div
                class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors relative z-10">
                <div
                    class="w-9 h-9 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center ring-1 ring-black/5 dark:ring-white/10">
                    <span class="font-bold text-xs text-gray-700 dark:text-white">{{ userInitials }}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ userName }}</div>
                    <div class="text-xs text-gray-500 truncate">{{ userRole }}</div>
                </div>
                <span class="material-symbols-outlined text-gray-400">more_vert</span>
            </div>
        </div>
    </aside>

    <!-- Profile Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showProfileModal" @close="showProfileModal = false">
            <template #title>User Profile</template>
            <div class="space-y-6">
                <div class="flex items-center gap-4">
                    <div
                        class="w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center text-2xl font-bold text-primary border-2 border-primary/20">
                        {{ userInitials }}
                    </div>
                    <div>
                        <h4 class="text-xl font-bold text-gray-900 dark:text-white">{{ userName }}</h4>
                        <p class="text-gray-500">{{ userRole }}</p>
                        <div class="mt-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full inline-block">
                            Active
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Email Address</div>
                        <div class="font-medium text-sm">{{ userEmail }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Employee ID</div>
                        <div class="font-medium text-sm">{{ userEmployeeId }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Department</div>
                        <div class="font-medium text-sm">Dispatch Operations</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Last Login</div>
                        <div class="font-medium text-sm">{{ userLastLogin }}</div>
                    </div>
                </div>
            </div>
            <template #footer>
                <div class="flex justify-end gap-3">
                    <button @click="showProfileModal = false"
                        class="px-4 py-2 text-gray-600 hover:text-gray-900">Close</button>
                </div>
            </template>
        </BaseModal>
    </Teleport>

    <!-- ID Card Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showIdCardModal" @close="showIdCardModal = false">
            <template #title>Employee ID Card</template>
            <div class="flex justify-center w-full">
                <IdCard :employee="employeeData" />
            </div>
            <template #footer>
                <button @click="showIdCardModal = false"
                    class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
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
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import IdCard from '@/components/IdCard.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { buildIdCardProfile } from '@/utils/idCardProfile'

// State for User Menu and Modals
const isUserMenuOpen = ref(false)
const showProfileModal = ref(false)
const showIdCardModal = ref(false)
const showLogoutConfirm = ref(false)
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
})

onUnmounted(() => {
    if (themeObserver) themeObserver.disconnect()
})

// User Data
const userName = computed(() => authStore.currentUser?.name || 'Dispatcher')
const userRole = computed(() => authStore.userRoleLabel || 'Dispatcher')
const userEmail = computed(() => authStore.currentUser?.email || 'support@cargocore.local')
const userCreatedAt = computed(() => authStore.currentUser?.created_at || authStore.currentUser?.createdAt || null)
const userEmployeeId = computed(() => {
    const rawId = authStore.currentUser?.id
    if (!rawId) return 'DP-USER'
    return `DP-${String(rawId).replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 8)}`
})
const userJoinDate = computed(() => {
    if (!userCreatedAt.value) return 'Active account'
    const parsed = new Date(userCreatedAt.value)
    if (Number.isNaN(parsed.getTime())) return 'Active account'
    return parsed.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
})
const userLastLogin = computed(() => authStore.isAuthenticated ? 'Active session' : 'Offline')
const userInitials = computed(() => {
    return userName.value
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2)
})

const employeeData = computed(() => buildIdCardProfile({
    user: authStore.currentUser,
    role: authStore.currentUser?.role || 'DISPATCHER',
    roleLabel: userRole.value,
    department: 'Dispatch Operations',
    address: authStore.currentUser?.address || 'CargoCore Dispatch Network',
    phone: authStore.currentUser?.phone || 'Managed by admin directory',
    email: userEmail.value,
    joinDate: userJoinDate.value,
}))

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = async () => {
    showLogoutConfirm.value = false
    const loginPath = authStore.logout()
    router.replace(loginPath)
}

const menuItems = [
    { label: 'Dispatch Board', icon: 'dashboard_customize', route: '/dispatcher/dashboard' },
    { label: 'Pending Queue', icon: 'pending_actions', route: '/dispatcher/pending-queue' },
    { label: 'Order Clustering', icon: 'hub', route: '/dispatcher/clustering' },
    { label: 'Route Optimization', icon: 'alt_route', route: '/dispatcher/optimization' },
    { label: 'Smart Assignment', icon: 'person_add', route: '/dispatcher/load-balancing' },
    { label: 'Driver Management', icon: 'badge', route: '/dispatcher/drivers' },
    { label: 'Manifest Center', icon: 'inventory_2', route: '/dispatcher/manifest' },
    { label: 'Service Moves', icon: 'local_shipping', route: '/dispatcher/service-moves' },
    { label: 'Order Status', icon: 'package_2', route: '/dispatcher/order-status' },
    { label: 'Crisis Management', icon: 'emergency_home', route: '/dispatcher/crisis' },
    { label: 'Communication Hub', icon: 'forum', route: '/dispatcher/communication' },
    { label: 'Performance Metrics', icon: 'monitoring', route: '/dispatcher/performance' },
    { label: 'Smart Dispatcher', icon: 'psychology', route: '/dispatcher/ai-assistant' },
]

const zones = computed(() => {
    const currentRoute = router.currentRoute.value.path.split('/').pop() || 'dashboard'
    return [
        {
            id: 'dispatcher-role',
            name: 'Role',
            value: authStore.userRoleLabel || 'Dispatcher',
            status: 'Normal'
        },
        {
            id: 'dispatcher-auth',
            name: 'Access',
            value: authStore.isAuthenticated ? 'Live' : 'Idle',
            status: authStore.isAuthenticated ? 'Normal' : 'Alert'
        },
        {
            id: 'dispatcher-user',
            name: 'Account',
            value: userEmployeeId.value,
            status: 'Normal'
        },
        {
            id: 'dispatcher-route',
            name: 'Route',
            value: currentRoute.replace(/-/g, ' ').slice(0, 10),
            status: currentRoute === 'crisis' ? 'Alert' : 'Normal'
        },
    ]
})
</script>
