<template>
    <!-- Tab Content: Active Drivers -->
    <div v-if="activeTab === 'Active Drivers'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <!-- Driver Scorecard -->
        <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Driver Roster & Performance</h3>
            <div class="space-y-4 overflow-y-auto pr-2 flex-grow custom-scrollbar">
                <div v-for="driver in searchedDrivers" :key="driver.id"
                    class="flex items-center gap-4 p-3 rounded-lg border transition-colors shadow-sm"
                    :class="driver.dispatcherSuspended
                        ? 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/20'
                        : 'bg-gray-50 dark:bg-white/5 border-transparent'">
                    <!-- Avatar with suspended ring -->
                    <div class="relative shrink-0">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm"
                            :class="driver.dispatcherSuspended ? 'bg-red-700 opacity-60' : driver.avatarColor">
                            {{ driver.name.charAt(0) }}
                        </div>
                        <span v-if="driver.dispatcherSuspended"
                            class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-red-500 border-2 border-white dark:border-gray-900 flex items-center justify-center"
                            title="Suspended by Dispatcher">
                            <span class="material-symbols-outlined text-white" style="font-size:8px">block</span>
                        </span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-center gap-2">
                            <span class="font-bold text-sm truncate"
                                :class="driver.dispatcherSuspended ? 'text-red-700 dark:text-red-400' : 'text-gray-900 dark:text-white'">
                                {{ driver.name }}
                            </span>
                            <div class="flex items-center gap-1.5 shrink-0">
                                <!-- Dispatcher suspended badge -->
                                <span v-if="driver.dispatcherSuspended"
                                    class="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400 border border-red-300 dark:border-red-500/30 flex items-center gap-1">
                                    <span class="material-symbols-outlined" style="font-size:10px">block</span>
                                    Suspended
                                </span>
                                <!-- Normal status badge -->
                                <span v-else class="text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wider"
                                    :class="String(driver.status || '').toLowerCase() === 'active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400'">
                                    {{ driver.status }}
                                </span>
                            </div>
                        </div>
                        <div class="text-xs mt-0.5 flex items-center gap-2 flex-wrap"
                            :class="driver.dispatcherSuspended ? 'text-red-400/70 dark:text-red-400/50' : 'text-gray-500 dark:text-gray-400'">
                            <span v-if="driver.dispatcherSuspended" class="font-semibold text-red-500 dark:text-red-400/80">Blocked from dispatch</span>
                            <template v-else>
                                <span class="font-medium text-green-600 dark:text-green-400">{{ driver.efficiency }}% eff.</span>
                                <span v-if="driver.rating" class="text-yellow-500">★ {{ Number(driver.rating).toFixed(1) }}</span>
                                <span class="text-gray-300 dark:text-gray-600">•</span>
                                <span class="font-medium text-primary truncate">{{ store.hubs.find(h => h.id === driver.hubId)?.name || 'Main Hub' }}</span>
                                <span class="text-gray-300 dark:text-gray-600">•</span>
                                <span class="truncate">{{ driver.currentJob || 'Standby' }}</span>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Top Driver Stats -->
        <TopDriversLeaderboard :searched-top-drivers="searchedTopDrivers" />
    </div>
</template>

<script setup>
import { inject } from 'vue'
import TopDriversLeaderboard from './TopDriversLeaderboard.vue'
import { fleetPageKey } from './fleetPageContext'

const { activeTab, searchedDrivers, searchedTopDrivers, store } = inject(fleetPageKey)
</script>
