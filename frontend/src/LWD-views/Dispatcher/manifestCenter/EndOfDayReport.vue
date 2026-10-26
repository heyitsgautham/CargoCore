<template>
    <!-- End of Day Report -->
    <Transition name="slide-down">
        <div v-if="showEOD" class="glass-panel rounded-xl p-6 space-y-6">

            <div class="flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">summarize</span>
                    End of Day Report — {{ todayLabel }}
                </h3>
                <button @click="showEOD = false"
                    class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <!-- EOD Stat Cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                    <div class="text-2xl font-bold text-blue-400">{{ todayTrips.length }}</div>
                    <div class="text-[10px] text-gray-500 uppercase tracking-wide mt-1">Total Trips</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                    <div class="text-2xl font-bold text-green-400">{{ completedCount }}</div>
                    <div class="text-[10px] text-gray-500 uppercase tracking-wide mt-1">Completed</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                    <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ totalWeightToday.toLocaleString() }} kg</div>
                    <div class="text-[10px] text-gray-500 uppercase tracking-wide mt-1">Total Weight</div>
                </div>
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                    <div class="text-2xl font-bold" :class="eodTotalLoss > 0 ? 'text-red-400' : 'text-green-400'">
                        {{ eodTotalLoss > 0 ? `-${eodTotalLoss}` : '0 losses' }}
                    </div>
                    <div class="text-[10px] text-gray-500 uppercase tracking-wide mt-1">Asset Losses</div>
                </div>
            </div>

            <!-- Per Trip Breakdown -->
            <div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-bold tracking-wider mb-3">Trip Breakdown</div>
                <div v-if="todayTrips.length === 0" class="text-center py-6 text-gray-500 text-sm">No trips today.</div>
                <div v-else class="space-y-2">
                    <div v-for="trip in todayTrips" :key="trip.id"
                        class="flex flex-wrap items-center justify-between gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-xl hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <div class="flex items-center gap-3 min-w-0">
                            <span class="font-mono text-xs font-bold text-gray-900 dark:text-white shrink-0">{{ trip.trackingCode || trip.id }}</span>
                            <span class="text-xs text-gray-500 truncate">{{ trip.driver }} · {{ trip.vehicle }}</span>
                        </div>
                        <div class="flex items-center gap-3 shrink-0">
                            <span class="text-xs text-gray-500">{{ trip.weight }} kg</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold border" :class="getStatusClass(trip.status)">
                                {{ formatStatus(trip.status) }}
                            </span>
                            <div v-if="getAssetLog(trip.id)" class="flex items-center gap-1 text-xs font-bold"
                                :class="hasAssetLoss(trip.id) ? 'text-red-400' : 'text-green-400'">
                                <span class="material-symbols-outlined text-[13px]">{{ hasAssetLoss(trip.id) ? 'warning' : 'check_circle' }}</span>
                                {{ hasAssetLoss(trip.id) ? 'Missing assets' : 'Assets OK' }}
                            </div>
                            <span v-else class="text-[10px] text-gray-500 italic">No asset log</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- EOD Asset Summary Table — only if any logs exist -->
            <div v-if="eodAssetSummary.length > 0">
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-bold tracking-wider mb-3">Total Packing Asset Summary</div>
                <div class="rounded-xl overflow-hidden border border-gray-200 dark:border-white/10">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                            <tr>
                                <th class="p-3 text-left">Item</th>
                                <th class="p-3 text-center">Total Sent</th>
                                <th class="p-3 text-center">Total Returned</th>
                                <th class="p-3 text-center">Net</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                            <tr v-for="item in eodAssetSummary" :key="item.name"
                                :class="item.totalSent - item.totalReturned > 0 ? 'bg-red-50/40 dark:bg-red-500/5' : ''">
                                <td class="p-3 text-gray-900 dark:text-white">
                                    <div class="flex items-center gap-2">
                                        <span class="material-symbols-outlined text-[15px] text-gray-400">{{ item.icon }}</span>
                                        {{ item.name }}
                                    </div>
                                </td>
                                <td class="p-3 text-center text-gray-900 dark:text-white">{{ item.totalSent }}</td>
                                <td class="p-3 text-center text-gray-900 dark:text-white">{{ item.totalReturned }}</td>
                                <td class="p-3 text-center">
                                    <span class="font-bold text-sm"
                                        :class="item.totalSent - item.totalReturned > 0 ? 'text-red-400' : 'text-green-400'">
                                        {{ item.totalSent - item.totalReturned > 0 ? `-${item.totalSent - item.totalReturned}` : '✓' }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-else class="text-center py-4 text-xs text-gray-500 italic">
                No asset logs recorded yet. Log assets per trip to see the summary here.
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { inject } from 'vue'
import { manifestPageKey } from './manifestPageContext'

const {
    completedCount,
    eodAssetSummary,
    eodTotalLoss,
    formatStatus,
    getAssetLog,
    getStatusClass,
    hasAssetLoss,
    showEOD,
    todayLabel,
    todayTrips,
    totalWeightToday,
} = inject(manifestPageKey)
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
    transition: all 0.25s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}
</style>
