<template>
    <!-- Tab Content: Live Locations -->
    <div v-if="activeTab === 'Live Locations'" class="flex flex-col gap-4">

        <!-- Driver List -->
        <div class="glass-panel rounded-xl p-5 border border-gray-200 dark:border-white/5">
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Active Driver Locations</h3>
                <span class="text-xs text-gray-500">{{ wsConnected ? 'Live via WebSocket' : 'Polling every 30s' }}</span>
            </div>
            <div v-if="liveDrivers.length === 0" class="text-center py-8 text-gray-400 text-sm">
                <span class="material-symbols-outlined block text-3xl mb-2">signal_disconnected</span>
                No live GPS data. Drivers need to start a shift on the driver app.
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div v-for="d in liveDrivers" :key="d.driver_id"
                    class="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-transparent hover:border-primary/30 transition-colors cursor-pointer"
                    @click="selectedFleetDriver = d">
                    <div class="w-9 h-9 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                        <span class="material-symbols-outlined text-green-500 text-[18px]">local_shipping</span>
                    </div>
                    <div class="min-w-0 flex-1">
                        <p class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ d.driver_name }}</p>
                        <p class="text-[10px] text-gray-500">{{ d.vehicle_code || 'No vehicle' }}</p>
                        <p class="text-[10px] text-primary truncate">
                            {{ liveDriverLocation(d) }}
                        </p>
                    </div>
                    <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase flex-shrink-0"
                        :class="d.status === 'in-transit' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400' : 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400'">
                        {{ d.status }}
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    activeTab,
    liveDriverLocation,
    liveDrivers,
    selectedFleetDriver,
    wsConnected,
} = inject(fleetPageKey)
</script>
