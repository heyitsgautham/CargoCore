<template>
    <div class="space-y-6 flex flex-col h-[540px] overflow-y-auto no-scrollbar pr-2">
        <div class="glass-panel p-6 rounded-xl flex-1">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Dispatch Readiness Forecast (Next 4 Hours)</h3>
            <div class="h-48">
                <Bar :data="demandChartData" :options="demandChartOptions" />
            </div>
            <div v-if="demandPeakHint" class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                {{ demandPeakHint }}
            </div>
            <div v-else class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                No demand forecast data yet. Will populate from live order volume.
            </div>
        </div>

        <!-- Dispatch Control Toggles -->
        <div class="glass-panel p-6 rounded-xl flex-[0_0_auto]">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-red-400">priority_high</span>
                Dispatch Control Toggles
            </h3>
            <div class="space-y-3">
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">Ready Order Prioritization</div>
                        <div class="text-[10px] text-gray-500">Auto-rank released orders that are waiting for driver confirmation</div>
                    </div>
                    <button @click="togglePeak('reallocation')"
                        :class="peakReallocation ? 'bg-primary' : 'bg-gray-600'"
                        class="w-10 h-5 rounded-full relative transition-colors">
                        <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                            :class="peakReallocation ? 'left-5' : 'left-0.5'"></span>
                    </button>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">Driver Availability Escalation</div>
                        <div class="text-[10px] text-gray-500">Alert operations when vehicle-linked orders have no free driver</div>
                    </div>
                    <button @click="togglePeak('shift')" :class="shiftExtension ? 'bg-primary' : 'bg-gray-600'"
                        class="w-10 h-5 rounded-full relative transition-colors">
                        <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                            :class="shiftExtension ? 'left-5' : 'left-0.5'"></span>
                    </button>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">Critical Order Priority Lock</div>
                        <div class="text-[10px] text-gray-500">Keep urgent released orders at the top of dispatcher review</div>
                    </div>
                    <button @click="togglePeak('vip')" :class="vipLock ? 'bg-primary' : 'bg-gray-600'"
                        class="w-10 h-5 rounded-full relative transition-colors">
                        <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                            :class="vipLock ? 'left-5' : 'left-0.5'"></span>
                    </button>
                </div>
                <div v-if="peakToast"
                    class="p-2 bg-primary/10 border border-primary/20 rounded text-xs text-primary text-center transition-all">
                    {{ peakToast }}
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar } from 'vue-chartjs'
import { smartDispatcherPageKey } from './smartDispatcherPageContext'

const {
    demandChartData,
    demandChartOptions,
    demandPeakHint,
    peakReallocation,
    peakToast,
    shiftExtension,
    togglePeak,
    vipLock,
} = inject(smartDispatcherPageKey)
</script>
