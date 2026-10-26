<template>
    <!-- Right Panel: Alerts & Bottlenecks -->
    <div class="glass-panel rounded-2xl p-5 flex flex-col h-full">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center">
                <span class="material-symbols-outlined mr-2 text-yellow-500">warning</span>
                Attention Needed
            </h3>

            <!-- Search -->
            <div class="relative flex items-center">
                <input v-if="store.isSearchOpen" v-model="store.searchQuery" type="text"
                    placeholder="Search drivers, alerts..."
                    class="w-48 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-primary/50 transition-all absolute right-10 shadow-sm"
                    autofocus />
                <button @click="store.toggleSearch"
                    class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    :class="{ 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white': store.isSearchOpen }">
                    <span class="material-symbols-outlined text-[18px]">search</span>
                </button>
            </div>
        </div>

        <div class="flex-1 relative">
            <div class="absolute inset-0 overflow-y-auto pr-1 space-y-3 no-scrollbar">
                <div v-if="store.alerts.length === 0" class="text-center py-8 text-gray-500 text-sm">
                    No active alerts. Good job!
                </div>
                <!-- Alert Item -->
                <div v-for="alert in store.alerts" :key="alert.id"
                    class="p-3 rounded-lg border flex gap-3 transition-colors" :class="[
                        alert.severity === 'high' ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20' : 'bg-yellow-50 dark:bg-yellow-500/10 border-yellow-200 dark:border-yellow-500/20'
                    ]">
                    <div class="mt-1 min-w-[24px]">
                        <span class="material-symbols-outlined text-[20px]" :class="[
                            alert.severity === 'high' ? 'text-red-500' : 'text-yellow-500'
                        ]">{{ alert.icon }}</span>
                    </div>
                    <div>
                        <h4 class="text-sm font-semibold text-gray-900 dark:text-white">{{ alert.title }}</h4>
                        <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{{ alert.description }}</p>
                        <button @click="store.openModal('alert-details', alert)"
                            class="mt-2 text-xs font-medium hover:underline" :class="[
                                alert.severity === 'high' ? 'text-red-600 dark:text-red-400 hover:text-red-500 dark:hover:text-red-300' : 'text-yellow-600 dark:text-yellow-400 hover:text-yellow-500 dark:hover:text-yellow-300'
                            ]">
                            {{ alert.severity === 'high' ? 'View Details' : 'Investigate' }}
                        </button>
                    </div>
                </div>

                <!-- List of Drivers Needing Attention -->
                <div class="mt-4 pt-4 border-t border-gray-100 dark:border-white/5">
                    <h4
                        class="text-xs font-semibold text-gray-500 dark:text-gray-500 uppercase tracking-wider mb-2">
                        Drivers Needing
                        Support</h4>
                    <div v-if="driversNeedingSupport.length" class="space-y-2">
                        <div v-for="driver in driversNeedingSupport" :key="driver.id"
                            @click="store.openModal('driver-profile', driver)"
                            class="flex items-center justify-between p-2 rounded hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer group transition-colors">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-sm"
                                    :class="driver.avatarColor">
                                    {{ driver.name.charAt(0) }}
                                </div>
                                <div>
                                    <div
                                        class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary transition-colors">
                                        {{ driver.name }}</div>
                                    <div class="text-[10px]" :class="[
                                        driver.supportTone === 'critical' ? 'text-red-500 dark:text-red-400' : 'text-yellow-500 dark:text-yellow-400'
                                    ]">{{ driver.supportStatusLabel }}</div>
                                </div>
                            </div>
                            <span
                                class="material-symbols-outlined text-gray-400 dark:text-gray-500 text-[18px]">chevron_right</span>
                        </div>
                    </div>
                    <div v-else class="rounded-xl border border-dashed border-gray-200 dark:border-white/10 px-3 py-4 text-xs text-gray-500 dark:text-gray-400">
                        No drivers currently need support.
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const { driversNeedingSupport, store } = inject(lmDashboardPageKey)
</script>
