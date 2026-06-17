<template>
    <div
        class="min-h-screen bg-background-light dark:bg-background-dark font-display text-gray-900 dark:text-white antialiased flex relative overflow-x-hidden">

        <!-- Mobile Overlay -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false"
            class="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"></div>

        <!-- Sidebar -->
        <AISidebar :is-open="isSidebarOpen" @close="isSidebarOpen = false" />

        <!-- Main Content Area -->
        <main
            class="flex-1 min-w-0 md:ml-64 min-h-screen flex flex-col overflow-x-hidden transition-all duration-300 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-500/5 dark:from-purple-900/10 via-surface-light dark:via-background-dark to-surface-light dark:to-background-dark">

            <!-- Top Bar -->
            <header
                class="h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between border-b border-gray-200 dark:border-white/5 bg-surface-light/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-40">

                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Toggle -->
                    <button @click="isSidebarOpen = !isSidebarOpen"
                        class="md:hidden p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-white/5 dark:hover:bg-white/10 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">menu</span>
                    </button>
                    <div>
                        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">{{ pageTitle }}</h1>
                        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
                            AI-Powered Logistics Support
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-2 sm:gap-3">
                    <!-- System Status Badge -->
                    <div class="hidden md:flex items-center gap-2 border-r border-gray-200 dark:border-white/10 pr-4">
                        <div class="text-right">
                            <div class="text-[10px] text-gray-500 uppercase font-bold">System Status</div>
                            <div class="text-sm font-bold text-green-600 dark:text-green-400 flex items-center gap-1">
                                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                All Operational
                            </div>
                        </div>
                    </div>

                    <!-- AI Quick Stats -->
                    <div class="hidden lg:flex items-center gap-3 border-r border-gray-200 dark:border-white/10 pr-4">
                        <div class="text-center">
                            <div class="text-[10px] text-gray-500 uppercase font-bold">Tickets</div>
                            <div class="text-sm font-bold text-purple-600 dark:text-purple-400">{{ supportStats.totalSessions }}</div>
                        </div>
                        <div class="text-center">
                            <div class="text-[10px] text-gray-500 uppercase font-bold">Escalated</div>
                            <div class="text-sm font-bold text-red-600 dark:text-red-400">{{ supportStats.openEscalations }}</div>
                        </div>
                    </div>

                    <!-- Notifications -->
                    <NotificationPopover :notifications="store.notifications"
                        :unread-count="store.unreadNotificationsCount" @mark-read="store.markNotificationRead"
                        @mark-all-read="store.markAllNotificationsRead" @clear-all="store.clearNotifications"
                        @open="store.fetchNotifications" />

                    <!-- New Ticket Button -->
                    <router-link to="/ai/tickets"
                        class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm shadow-sm">
                        <span class="material-symbols-outlined text-[18px]">add</span>
                        <span class="hidden sm:inline">New Ticket</span>
                    </router-link>
                </div>
            </header>

            <!-- Page Content -->
            <div class="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 overflow-x-hidden">
                <RouterView />
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AISidebar from '../Ai-components/AISidebar.vue'
import NotificationPopover from '@/components/NotificationPopover.vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAiSupportStore } from '@/stores/aiSupportStore'

const store = useLogisticStore()
const aiSupportStore = useAiSupportStore()
const isSidebarOpen = ref(false)
const route = useRoute()

const pageTitles = {
    '/ai/dashboard': 'AI Dashboard',
    '/ai/contact-forms': 'Contact Form Submissions',
    '/ai/live-conversations': 'Live Conversations',
    '/ai/escalations': 'Escalation Center',
    '/ai/tickets': 'Ticket Management',
    '/ai/reverse-logistics': 'Reverse Logistics',
    '/ai/refund-center': 'Refund Center',
    '/ai/analytics': 'AI Analytics',
    '/ai/knowledge-base': 'Knowledge Base',
    '/ai/legal': 'Legal & Compliance',
    '/ai/settings': 'Settings',
}

const pageTitle = computed(() => pageTitles[route.path] || 'Internal Support Dashboard')
const supportStats = computed(() => ({
    totalSessions: aiSupportStore.dashboard?.stats?.total_sessions ?? 0,
    openEscalations: aiSupportStore.dashboard?.stats?.open_escalations ?? 0,
}))

// Close sidebar on route change
watch(route, () => {
    isSidebarOpen.value = false
})

onMounted(() => {
    aiSupportStore.loadDashboard().catch(() => {})
    store.fetchNotifications().catch(() => {})
})
</script>
