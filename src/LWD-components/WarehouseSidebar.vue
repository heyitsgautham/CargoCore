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
                        class="flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group" :class="[
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
                    </router-link>
                </li>
            </ul>

            <!-- Floor Map Preview (Mini) -->
            <div class="mt-8 px-4" :class="{ 'mt-2': $route.path.includes('/warehouse/comparative-viewers') }">
                <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">
                    {{ $route.path.includes('/warehouse/comparative-viewers') ? 'Drag Zone' : 'Zone Status' }}
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div v-for="zone in availableZones" :key="zone.id"
                        :draggable="$route.path.includes('/warehouse/comparative-viewers')"
                        @dragstart="onDragStart($event, zone)"
                        class="bg-gray-100 dark:bg-white/5 rounded p-2 text-center border border-gray-200 dark:border-white/5 transition-colors group"
                        :class="[
                            $route.path.includes('/warehouse/comparative-viewers') ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
                            zone.status === 'Alert' ? 'hover:border-amber-500/50' :
                                zone.status === 'Full' ? 'hover:border-red-500/50' : 'hover:border-primary/50'
                        ]">
                        <div
                            class="text-xs text-gray-500 dark:text-gray-400 font-medium group-hover:text-gray-900 dark:group-hover:text-white flex items-center justify-center gap-1">
                            <span v-if="$route.path.includes('/warehouse/comparative-viewers')"
                                class="material-symbols-outlined text-[14px] text-gray-400 group-hover:text-primary transition-colors">drag_indicator</span>
                            {{ zone.name }}
                        </div>
                        <div class="font-bold flex items-center justify-center gap-1 mt-1" :class="[
                            zone.status === 'Alert' ? 'text-amber-500 dark:text-yellow-400' :
                                zone.status === 'Full' ? 'text-red-500 dark:text-red-400' : 'text-primary'
                        ]">
                            <div v-if="zone.color" class="w-2 h-2 rounded-full"
                                :style="{ backgroundColor: zone.color }"></div>
                            {{ zone.value }}
                        </div>
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
                        <div class="font-medium text-sm">Warehouse Operations</div>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import IdCard from '@/components/IdCard.vue'
import { useWarehouseFloorStore } from '@/stores/warehouseFloorStore'
import { useLogisticStore } from '@/stores/logisticStore'
import { getEffectiveWarehouseSubstatus, isWarehouseOrderAccepted } from '@/utils/warehouseOrderState'
import { buildIdCardProfile } from '@/utils/idCardProfile'
import ThemeToggle from '@/components/ThemeToggle.vue'

const store = useWarehouseFloorStore()
const logisticStore = useLogisticStore()

// State for User Menu and Modals
const isUserMenuOpen = ref(false)
const showProfileModal = ref(false)
const showIdCardModal = ref(false)
const showLogoutConfirm = ref(false)
const isDark = ref(true)
let themeObserver = null

// User Data
const userName = computed(() => authStore.currentUser?.name || 'Warehouse Manager')
const userRole = computed(() => authStore.userRoleLabel || 'Warehouse Manager')
const userEmail = computed(() => authStore.currentUser?.email || 'support@cargocore.local')
const userCreatedAt = computed(() => authStore.currentUser?.created_at || authStore.currentUser?.createdAt || null)
const userEmployeeId = computed(() => {
    const rawId = authStore.currentUser?.id
    if (!rawId) return 'WH-USER'
    return `WH-${String(rawId).replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 8)}`
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
    role: authStore.currentUser?.role || 'WAREHOUSE_MANAGER',
    roleLabel: userRole.value,
    department: 'Warehouse Operations',
    address: authStore.currentWarehouse?.name || authStore.currentUser?.address || 'CargoCore Warehouse Network',
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

// Live badge counts
const inboundBadge = ref(null)
// Track order IDs we've already notified about so we don't re-notify on refresh
const notifiedOrderIds = ref(new Set())

async function fetchSidebarBadges() {
    try {
        const warehouseId = authStore.currentUser?.warehouse_id
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        const [ordersRes, inboundRes] = await Promise.allSettled([
            fetch('http://localhost:8000/api/v1/orders?page=1&page_size=100', { headers }),
            fetch('http://localhost:8000/api/v1/orders?page=1&page_size=50&status_filter=CONFIRMED', { headers })
        ])

        // New Orders → push to notification bell instead of sidebar badge
        if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
            const data = await ordersRes.value.json()
            const orders = (data.items || []).filter(o =>
                warehouseId ? o.warehouse_id === warehouseId : true
            )
            const newOrders = orders.filter(o =>
                (o.status === 'DRAFT' || (
                    o.status === 'CONFIRMED' &&
                    !isWarehouseOrderAccepted(o, warehouseId) &&
                    (!getEffectiveWarehouseSubstatus(o, warehouseId) || getEffectiveWarehouseSubstatus(o, warehouseId) === 'AWAITING_PICK')
                )) && !notifiedOrderIds.value.has(o.id)
            )
            newOrders.forEach(o => {
                notifiedOrderIds.value.add(o.id)
                logisticStore.notifications.unshift({
                    id: `new-order-${o.id}`,
                    title: 'New Order Received',
                    message: `Order ${o.tracking_code} is awaiting warehouse processing.`,
                    time: 'Just now',
                    read: false,
                    type: 'order',
                })
            })
        }

        // Inbound badge = vendor orders not yet received (no warehouse_substatus set)
        if (inboundRes.status === 'fulfilled' && inboundRes.value.ok) {
            const data = await inboundRes.value.json()
            const items = (data.items || []).filter(o =>
                o.order_type === 'VENDOR' &&
                (warehouseId ? o.warehouse_id === warehouseId : true) &&
                !o.warehouse_substatus
            )
            inboundBadge.value = items.length > 0 ? String(items.length) : null
        }
    } catch (error) {
        console.warn('Sidebar badge fetch failed:', error)
    }
}

const menuItems = computed(() => [
    { label: 'Overview', icon: 'grid_view', route: '/warehouse/dashboard' },
    { label: 'New Orders', icon: 'orders', route: '/warehouse/new-orders' },
    { label: 'Inventory', icon: 'inventory', route: '/warehouse/inventory' },
    { label: 'Inbound', icon: 'input', route: '/warehouse/inbound', badge: inboundBadge.value },
    { label: 'Floor Plan', icon: 'map', route: '/warehouse/floor-plan' },
    { label: 'Picking', icon: 'shopping_basket', route: '/warehouse/picking' },
    { label: 'Packing Materials', icon: 'package_2', route: '/warehouse/packing-materials' },
    { label: 'Safety Stock', icon: 'notification_important', route: '/warehouse/safety-stock' },
    { label: 'Loading Dock', icon: 'local_shipping', route: '/warehouse/dock' },
    { label: 'Returns', icon: 'assignment_return', route: '/warehouse/returns' },
    { label: 'Labor Mgmt', icon: 'groups', route: '/warehouse/labor' },
    { label: 'Performance', icon: 'bar_chart', route: '/warehouse/performance' },
    { label: 'Smart WMS', icon: 'psychology', route: '/warehouse/ai' },
    { label: 'Comparative Viewers', icon: 'compare_arrows', route: '/warehouse/comparative-viewers' },
    { label: 'Messages', icon: 'forum', route: '/warehouse/messages' },
])

onMounted(() => {
    isDark.value = document.documentElement.classList.contains('dark')
    themeObserver = new MutationObserver(() => {
        isDark.value = document.documentElement.classList.contains('dark')
    })
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
    })

    window.addEventListener('warehouse-orders-updated', fetchSidebarBadges)
    authStore.ensureWarehouseContext().finally(() => {
        fetchSidebarBadges()
    })
})

onUnmounted(() => {
    if (themeObserver) themeObserver.disconnect()
    window.removeEventListener('warehouse-orders-updated', fetchSidebarBadges)
})

// Default zones when no floor plan groups exist
const defaultZones = [
    { id: 'zone-a', name: 'Zone A', value: '72%', status: 'Normal', color: '#3b82f6' },
    { id: 'zone-b', name: 'Zone B', value: '85%', status: 'Full', color: '#ef4444' },
    { id: 'zone-c', name: 'Zone C', value: '45%', status: 'Normal', color: '#10b981' },
    { id: 'zone-d', name: 'Zone D', value: '2 RMA', status: 'Alert', color: '#f59e0b' },
]

const zones = computed(() => {
    if (!store.groups.length) return defaultZones
    return store.groups.slice(0, 4).map((group, index) => {
        const groupSections = store.sections.filter(section => section.groupId === group.id)
        const groupRackIds = store.racks
            .filter(rack => groupSections.some(section => section.id === rack.sectionId))
            .map(rack => rack.id)
        const groupProducts = store.products.filter(product => groupRackIds.includes(product.rackId))
        const returnCount = groupProducts.filter(product => product.rma).length
        const fillRatio = groupRackIds.length
            ? Math.min(100, Math.round((groupProducts.length / (groupRackIds.length * 12)) * 100))
            : 0
        const status = returnCount > 0 ? 'Alert' : fillRatio >= 85 ? 'Full' : 'Normal'
        return {
            id: group.id,
            name: group.name.substring(0, 10),
            value: status === 'Alert' ? `${returnCount} RMA` : `${fillRatio}%`,
            status,
            color: group.color || store.presetColors[index]
        }
    })
})

const availableZones = computed(() => {
    if (store.comparedZones) {
        return zones.value.filter(z => !store.comparedZones.find(cz => cz.id === z.id))
    }
    return zones.value
})

const onDragStart = (event, zone) => {
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('zoneId', zone.id)
    event.dataTransfer.setData('text/plain', JSON.stringify(zone))
}
</script>
