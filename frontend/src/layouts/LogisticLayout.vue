<template>
    <div
        class="logistic-theme min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white font-display antialiased overflow-x-hidden relative"
        :class="{ 'lm-critical-state': criticalEmptyFunds }"
    >
        <!-- ═══════════════════════════════════════════════════════════
             CRITICAL FINANCIAL EMERGENCY OVERLAY
             Fires only when both revenue AND capital are drained to 0.
             pointer-events-none so it never blocks any UI interaction.
        ════════════════════════════════════════════════════════════════ -->
        <Transition name="critical-overlay">
            <div v-if="criticalEmptyFunds" class="critical-overlay" aria-hidden="true">

                <!-- Edge glow border (all 4 sides) -->
                <div class="critical-edge critical-edge--top"></div>
                <div class="critical-edge critical-edge--bottom"></div>
                <div class="critical-edge critical-edge--left"></div>
                <div class="critical-edge critical-edge--right"></div>

                <!-- Corner brackets (HUD / Command-Center style) -->
                <div class="critical-corner critical-corner--tl">
                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                        <path d="M2 18V2H18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="critical-corner critical-corner--tr">
                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                        <path d="M34 18V2H18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="critical-corner critical-corner--bl">
                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                        <path d="M2 18V34H18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="critical-corner critical-corner--br">
                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                        <path d="M34 18V34H18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                </div>

                <!-- Subtle red vignette (does NOT obscure content) -->
                <div class="critical-vignette"></div>

                <!-- Floating status pill — top-center -->
                <div class="critical-pill">
                    <span class="critical-pill__dot"></span>
                    <span class="material-symbols-outlined" style="font-size:14px;line-height:1">emergency</span>
                    <span class="critical-pill__text">FINANCIAL LOCKDOWN &nbsp;·&nbsp; Revenue &amp; Capital Drained</span>
                    <span class="critical-pill__sep">|</span>
                    <span class="critical-pill__action" @click.stop="goToFinances">Fund Now ↗</span>
                </div>

            </div>
        </Transition>

        <!-- Sidebar -->
        <LogisticSidebar />

        <!-- Main Content Area -->
        <main class="ml-64 min-h-screen flex flex-col transition-all duration-300 overflow-x-hidden">
            <!-- Top Bar with Warehouse Switcher -->
            <header
                class="h-16 px-8 flex items-center justify-between border-b border-gray-200 dark:border-white/5 bg-surface-light/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-40">
                <div class="flex items-center gap-4">
                    <!-- Warehouse Switcher (Hidden on Global Pages) -->
                    <div v-if="!isGlobalPage" class="relative group">
                        <button @click="store.openModal('warehouse-select')"
                            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors border border-gray-200 dark:border-white/5">
                            <span
                                class="material-symbols-outlined text-gray-500 dark:text-gray-400 text-[18px]">public</span>
                            <span class="text-sm font-medium text-gray-700 dark:text-white">{{ store.activeWarehouseName
                                }}</span>
                            <span class="material-symbols-outlined text-gray-500 text-[18px]">arrow_drop_down</span>
                        </button>
                    </div>

                    <!-- Static Header for Global Pages -->
                    <div v-else
                        class="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-primary/10 border border-primary/20 dark:bg-primary/20 dark:border-primary/30 shadow-sm cursor-default">
                        <span class="material-symbols-outlined text-primary text-[18px]">
                            {{ globalPageIcon }}
                        </span>
                        <span class="text-sm font-bold text-primary dark:text-blue-400 tracking-wide uppercase">
                            {{ globalPageTitle }}
                        </span>
                    </div>

                    <!-- Breadcrumbs or Page Title could go here -->
                    <h1 class="text-lg font-semibold text-white/80 hidden">Dashboard</h1>
                </div>

                <div class="flex items-center gap-4">
                    <div class="hidden sm:block">
                        <HeaderWeather hub-id="1" />
                    </div>

                    <!-- Search Bar Moved to Dashboard -->

                    <!-- Notifications -->
                    <NotificationPopover :notifications="store.notifications"
                        :unread-count="store.unreadNotificationsCount" @open="store.fetchNotifications()"
                        @mark-read="store.markNotificationRead"
                        @mark-all-read="store.markAllNotificationsRead" @clear-all="store.clearNotifications" />

                    <!-- Meeting Scheduler -->
                    <HeaderMeetingScheduler />

                    <!-- To-Do List -->
                    <HeaderTodo />

                </div>
            </header>

            <!-- Page Content -->
            <div class="flex-1 p-8 overflow-y-auto overflow-x-hidden">
                <div v-if="store.error"
                    class="mb-6 rounded-2xl border border-amber-300/60 bg-amber-50 px-4 py-3 text-sm text-amber-900 shadow-sm dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
                    <div class="flex items-start justify-between gap-4">
                        <div>
                            <div class="font-semibold">Unable to load logistics data</div>
                            <div class="mt-1 text-amber-800/90 dark:text-amber-100/90">{{ store.error }}</div>
                        </div>
                        <button
                            class="shrink-0 rounded-lg border border-amber-400/60 px-3 py-1.5 font-medium transition-colors hover:bg-amber-100 dark:border-amber-400/30 dark:hover:bg-amber-500/10"
                            @click="store.initialize(true).catch((err) => console.error('Failed to reload logistics data', err))">
                            Retry
                        </button>
                    </div>
                </div>
                <RouterView />
            </div>

            <!-- Global Modals for Logistic Layout -->
            <WarehouseSelectorModal :is-open="store.activeModal === 'warehouse-select'" :hubs="store.hubs"
                :active-id="store.activeWarehouse" @close="store.closeModal()" @select="store.setWarehouse" />
        </main>
    </div>
</template>

<script setup>
import LogisticSidebar from '../LWD-components/LogisticSidebar.vue'
import WarehouseSelectorModal from '@/LWD-components/WarehouseSelectorModal.vue'
import HeaderWeather from '@/components/HeaderWeather.vue'
import NotificationPopover from '@/components/NotificationPopover.vue'
import HeaderTodo from '@/components/HeaderTodo.vue'
import HeaderMeetingScheduler from '@/components/HeaderMeetingScheduler.vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { computed, onBeforeUnmount, onMounted } from 'vue'

const store = useLogisticStore()
const route = useRoute()
const router = useRouter()

// Critical lockdown: both revenue AND capital are fully drained.
// Guard on store.initialized so this NEVER fires during the loading
// flash (all values are 0 by default before bootstrap data arrives).
const criticalEmptyFunds = computed(() => {
    if (!store.initialized || store.isLoading) return false
    const s = store.activeFinanceSummary
    return (s.total_revenue ?? 1) <= 0 && (s.capital_invested ?? 1) <= 0
})

function goToFinances() {
    router.push('/logistic/reports').then(() => {
        // Brief delay so Reports.vue mounts, then switch to financials tab
        // (Reports.vue reads activeTab from its own local ref, so we use
        //  a CustomEvent the page can listen to)
        setTimeout(() => document.dispatchEvent(new CustomEvent('lm:goto-tab', { detail: 'financials' })), 150)
    })
}
let notificationPoll = null

onMounted(() => {
    store.initialize().catch((err) => {
        console.error('Failed to initialize logistic data', err)
    })
    store.fetchNotifications().catch(() => {})
    notificationPoll = window.setInterval(() => {
        store.fetchNotifications().catch(() => {})
    }, 30000)
    document.body.classList.add('logistic-theme-portal')
})

onBeforeUnmount(() => {
    if (notificationPoll) window.clearInterval(notificationPoll)
    document.body.classList.remove('logistic-theme-portal')
})

const isGlobalPage = computed(() => {
    return route.path.includes('/logistic/warehouses') ||
        route.path.includes('/logistic/ai') ||
        route.path.includes('/logistic/comparative-viewers') ||
        route.path.includes('/logistic/rate-governance')
})

const globalPageIcon = computed(() => {
    if (route.path.includes('ai')) return 'smart_toy'
    if (route.path.includes('comparative')) return 'compare_arrows'
    if (route.path.includes('rate-governance')) return 'account_balance'
    return 'domain'
})

const globalPageTitle = computed(() => {
    if (route.path.includes('ai')) return 'Corporate AI Assistant'
    if (route.path.includes('comparative')) return 'Comparative Viewers'
    if (route.path.includes('rate-governance')) return 'Global Rate Governance'
    return 'Global Network Overview'
})
</script>

<style src="./styles/LogisticLayout.css"></style>
