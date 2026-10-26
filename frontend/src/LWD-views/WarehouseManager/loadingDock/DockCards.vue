<template>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Dock Status Cards -->
        <div v-for="dock in docks" :key="dock.id" class="glass-panel p-6 rounded-xl relative overflow-hidden group">
            <div class="absolute inset-x-0 bottom-0 h-1" :class="dock.statusClass"></div>
            <div class="flex justify-between items-start mb-4">
                <div class="text-xl font-bold text-gray-900 dark:text-white">Dock {{ dock.id }}</div>
                <span class="px-2 py-1 rounded text-[10px] uppercase font-bold text-black"
                    :class="dock.badgeClass">{{ dock.status }}</span>
            </div>

            <div class="space-y-2 mb-4">
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600 dark:text-gray-400">Truck:</span>
                    <span class="text-gray-900 dark:text-white font-mono">{{ dock.truck || '--' }}</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600 dark:text-gray-400">Progress:</span>
                    <span class="text-gray-900 dark:text-white font-bold">{{ dock.progress }}%</span>
                </div>
            </div>

            <!-- Dwell Time Tracking -->
            <div v-if="dock.status === 'Occupied'"
                class="mb-4 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                <div class="text-[10px] text-gray-600 dark:text-gray-400 uppercase font-bold mb-2">Dwell Time</div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div>
                        <div class="text-gray-500">Arrived</div>
                        <div class="text-gray-900 dark:text-white font-mono">{{ dock.arrivedAt }}</div>
                    </div>
                    <div>
                        <div class="text-gray-500">Loading Since</div>
                        <div class="text-gray-900 dark:text-white font-mono">{{ dock.loadingSince }}</div>
                    </div>
                    <div>
                        <div class="text-gray-500">Elapsed</div>
                        <div class="font-mono font-bold"
                            :class="dock.dwellMinutes > 45 ? 'text-red-600 dark:text-red-400' : dock.dwellMinutes > 30 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'">
                            {{ dock.dwellMinutes }} min</div>
                    </div>
                    <div>
                        <div class="text-gray-500">Efficiency</div>
                        <div class="text-primary font-bold">{{ dock.efficiency }}</div>
                    </div>
                </div>
            </div>

            <div v-if="dock.status === 'Occupied'"
                class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden mb-4">
                <div class="bg-blue-500 h-full animate-pulse" :style="`width: ${dock.progress}%`"></div>
            </div>

            <div class="flex gap-2">
                <button v-if="dock.status === 'Occupied'" @click="openVerifyModal(dock)"
                    class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-2 rounded text-xs font-bold transition-colors">
                    Verify & Release
                </button>
                <button v-if="dock.status === 'Free'" @click="openAssignModal(dock)"
                    class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white py-2 rounded text-xs font-bold transition-colors">Assign
                    Truck</button>
                <button v-if="dock.status === 'Maintenance'" @click="clearMaintenance(dock)"
                    class="flex-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-600 dark:text-blue-400 py-2 rounded text-xs font-bold transition-colors">Clear
                    Maintenance</button>
                <button @click="openSettingsModal(dock)"
                    class="px-3 py-2 bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 rounded text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"><span
                        class="material-symbols-outlined text-sm">settings</span></button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const {
    clearMaintenance,
    docks,
    openAssignModal,
    openSettingsModal,
    openVerifyModal,
} = inject(loadingDockPageKey)
</script>
