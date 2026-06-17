<template>
    <div
        class="warehouse-theme min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white font-display antialiased flex">

        <!-- Mobile Overlay -->
        <div v-if="sidebarOpen" class="fixed inset-0 bg-black/50 z-40 lg:hidden" @click="sidebarOpen = false"></div>

        <!-- Sidebar -->
        <div :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
            class="fixed inset-y-0 left-0 z-50 transition-transform duration-300">
            <WarehouseSidebar />
        </div>

        <!-- Main Content Area -->
        <main
            class="flex-1 lg:ml-64 min-h-screen flex flex-col transition-all duration-300 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 dark:from-teal-900/10 via-surface-light dark:via-background-dark to-surface-light dark:to-background-dark">

            <!-- Top Bar -->
            <header
                class="h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between border-b border-gray-200 dark:border-white/5 bg-surface-light/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-40">
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Toggle -->
                    <button @click="sidebarOpen = !sidebarOpen"
                        class="lg:hidden p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">menu</span>
                    </button>
                    <div>
                        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">{{ warehouseTitle }}</h1>
                        <div class="text-xs text-gray-400 flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                            {{ warehouseSubtitle }}
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-2 sm:gap-6">
                    <!-- Quick Metrics in Header (hidden on mobile) -->
                    <div class="hidden md:flex gap-4 border-r border-gray-200 dark:border-white/10 pr-6">
                        <div class="text-right">
                            <div class="text-[10px] text-gray-500 uppercase">Capacity</div>
                            <div class="text-sm font-bold text-teal-500 dark:text-teal-400">{{ warehouseCapacityLabel }}</div>
                        </div>
                        <div class="text-right">
                            <div class="text-[10px] text-gray-500 uppercase">Pending</div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ warehousePendingLabel }}</div>
                        </div>
                    </div>

                    <div class="flex items-center gap-1 sm:gap-3">
                        <div class="hidden sm:block">
                            <HeaderWeather hub-id="1" />
                        </div>

                        <!-- Notifications -->
                        <NotificationPopover :notifications="store.notifications"
                            :unread-count="store.unreadNotificationsCount" @open="store.fetchNotifications()"
                            @mark-read="store.markNotificationRead"
                            @mark-all-read="store.markAllNotificationsRead" @clear-all="store.clearNotifications" />

                        <!-- Meeting Scheduler -->
                        <div class="hidden sm:block">
                            <HeaderMeetingScheduler />
                        </div>

                        <!-- To-Do List -->
                        <div class="hidden sm:block">
                            <HeaderTodo />
                        </div>

                    </div>
                </div>
            </header>

            <!-- Page Content -->
            <div class="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto overflow-x-hidden">
                <div v-if="!warehouseContextReady" class="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400">
                    Loading warehouse context...
                </div>
                <RouterView v-else />
            </div>
        </main>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import WarehouseSidebar from '../LWD-components/WarehouseSidebar.vue'
import HeaderWeather from '@/components/HeaderWeather.vue'
import HeaderTodo from '@/components/HeaderTodo.vue'
import HeaderMeetingScheduler from '@/components/HeaderMeetingScheduler.vue'
import NotificationPopover from '@/components/NotificationPopover.vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { RouterView, useRouter } from 'vue-router'
import { authenticatedJsonRequest } from '@/config/api'

const store = useLogisticStore()
const authStore = useAuthStore()
const router = useRouter()
const sidebarOpen = ref(false)
const warehouseContextReady = ref(false)
const warehouseHeaderStats = ref({
    pendingCount: null,
    capacityPercent: null,
})

const warehouseTitle = computed(() => {
    return authStore.currentWarehouse?.name || authStore.currentUser?.warehouse_name || 'Assigned Warehouse'
})

const warehouseId = computed(() => authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null)

const warehouseSubtitle = computed(() => {
    const warehouse = authStore.currentWarehouse
    if (warehouse?.address) return warehouse.address
    if (authStore.currentUser?.warehouse_id) return 'Operational warehouse linked to your account'
    return 'No warehouse linked to this account'
})

const warehouseCapacityLabel = computed(() => {
    const value = warehouseHeaderStats.value.capacityPercent
    return Number.isFinite(value) ? `${value}%` : '--'
})

const warehousePendingLabel = computed(() => {
    const value = warehouseHeaderStats.value.pendingCount
    return Number.isFinite(value) ? new Intl.NumberFormat('en-IN').format(value) : '--'
})


async function fetchWarehouseHeaderStats() {
    if (!warehouseId.value) {
        warehouseHeaderStats.value = { pendingCount: null, capacityPercent: null }
        return
    }

    try {
        const [dashboard, kpis] = await Promise.all([
            authenticatedJsonRequest(`api/v1/warehouses/${warehouseId.value}/dashboard`).catch(() => null),
            authenticatedJsonRequest(`api/v1/warehouses/${warehouseId.value}/kpis`).catch(() => null),
        ])

        const capacityLimit = Number(authStore.currentWarehouse?.capacity_limit ?? 0)
        const orderCount = Number(kpis?.order_count ?? 0)
        const pendingCount = Number(dashboard?.pending_orders_count ?? 0)

        warehouseHeaderStats.value = {
            pendingCount,
            capacityPercent: capacityLimit > 0
                ? Math.max(0, Math.min(100, Math.round((orderCount / capacityLimit) * 100)))
                : null,
        }
    } catch (error) {
        console.error('Error loading warehouse header stats:', error)
        warehouseHeaderStats.value = { pendingCount: null, capacityPercent: null }
    }
}

function refreshWarehouseHeaderStats() {
    fetchWarehouseHeaderStats().catch(() => {})
}

onMounted(async () => {
    document.body.classList.add('warehouse-theme-portal')
    await authStore.ensureWarehouseContext()
    warehouseContextReady.value = true
    await fetchWarehouseHeaderStats()
    store.fetchNotifications().catch(() => {})
    window.addEventListener('warehouse-orders-updated', refreshWarehouseHeaderStats)
})

onBeforeUnmount(() => {
    document.body.classList.remove('warehouse-theme-portal')
})

onUnmounted(() => {
    window.removeEventListener('warehouse-orders-updated', refreshWarehouseHeaderStats)
})

watch(warehouseId, (nextId, prevId) => {
    if (nextId === prevId) return
    refreshWarehouseHeaderStats()
})
</script>

<style>
:is(.warehouse-theme, body.warehouse-theme-portal) {
    --primary: #1ce783;
    --primary-dark: #17c06d;
}
</style>
