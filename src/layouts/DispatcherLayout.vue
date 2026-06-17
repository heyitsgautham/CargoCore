<template>
    <div
        class="dispatcher-theme min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white font-display antialiased flex">

        <!-- Mobile Overlay -->
        <div v-if="sidebarOpen" class="fixed inset-0 bg-black/50 z-40 lg:hidden" @click="sidebarOpen = false"></div>

        <!-- Sidebar -->
        <div :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
            class="fixed inset-y-0 left-0 z-50 transition-transform duration-300">
            <DispatcherSidebar />
        </div>

        <!-- Main Content Area -->
        <main
            class="flex-1 lg:ml-64 min-h-screen flex flex-col transition-all duration-300 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/5 dark:from-primary/5 via-surface-light dark:via-background-dark to-surface-light dark:to-background-dark">

            <!-- Top Bar -->
            <header
                class="h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between border-b border-gray-200 dark:border-white/5 bg-surface-light/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-40">
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Toggle -->
                    <button @click="sidebarOpen = !sidebarOpen"
                        class="lg:hidden p-2 rounded-lg bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">menu</span>
                    </button>
                    <div>
                        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary text-[20px]">campaign</span>
                            Dispatch Console
                        </h1>
                        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            {{ hubLabel }}
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-2 sm:gap-6">
                    <!-- Quick Metrics in Header (hidden on mobile) -->
                    <div class="hidden md:flex gap-4 border-r border-gray-200 dark:border-white/10 pr-6">
                        <div class="text-right">
                            <div class="text-[10px] text-gray-500 uppercase">Active</div>
                            <div class="text-sm font-bold text-green-500 dark:text-green-400">{{ store.dashboardStats.activeDeliveries || 0 }}</div>
                        </div>
                        <div class="text-right">
                            <div class="text-[10px] text-gray-500 uppercase">Pending</div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ dispatchStore.pendingOrders.length }}</div>
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

                        <div class="hidden sm:block h-6 w-px bg-gray-200 dark:bg-white/10 mx-2"></div>

                        <!-- New Service Button -->
                        <button @click="openNewServiceMove"
                            class="hidden sm:flex h-10 rounded-lg items-center justify-center gap-2 bg-primary text-black hover:bg-primary/90 transition-colors shadow-md px-4 text-xs font-bold">
                            <span class="material-symbols-outlined text-[16px]">add</span>
                            New Service
                        </button>
                    </div>
                </div>
            </header>

            <!-- Page Content - Responsive Padding -->
            <div class="flex-1 relative" :class="route.meta.fullWidth ? 'overflow-hidden p-0' : 'overflow-y-auto p-4 sm:p-6 lg:p-8'">
                <RouterView />
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import DispatcherSidebar from '../LWD-components/DispatcherSidebar.vue'
import HeaderWeather from '@/components/HeaderWeather.vue'
import HeaderTodo from '@/components/HeaderTodo.vue'
import HeaderMeetingScheduler from '@/components/HeaderMeetingScheduler.vue'
import NotificationPopover from '@/components/NotificationPopover.vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'

const store = useLogisticStore()
const dispatchStore = useDispatcherStore()
const authStore = useAuthStore()
const router = useRouter()
let notificationPoll = null

onMounted(() => {
    document.body.classList.add('dispatcher-theme-portal')
    store.fetchNotifications().catch(() => {})
    notificationPoll = window.setInterval(() => {
        store.fetchNotifications().catch(() => {})
    }, 30000)
})

onBeforeUnmount(() => {
    if (notificationPoll) window.clearInterval(notificationPoll)
    document.body.classList.remove('dispatcher-theme-portal')
})

// Resolve hub name from user profile → hubs list
const dispatcherHub = computed(() => {
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!warehouseId) return null
    return store.hubs.find(h => h.id === String(warehouseId)) || null
})
const hubLabel = computed(() => dispatcherHub.value?.name || 'All Hubs')
const route = useRoute()
const sidebarOpen = ref(false)

function openNewServiceMove() {
    router.push({
        name: 'DispatcherServiceMoves',
        query: {
            ...route.query,
            createMove: '1',
        },
    })
}
</script>

<style>
:is(.dispatcher-theme, body.dispatcher-theme-portal) {
    --primary: #1ce783;
    --primary-dark: #17c06d;
}
</style>
