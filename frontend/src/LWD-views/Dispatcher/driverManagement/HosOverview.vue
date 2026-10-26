<template>
    <div v-if="showHOS" class="glass-panel p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-lg">HOS Compliance Overview</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto pr-2">
            <div v-for="d in drivers" :key="d.id" class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ d.name }}</div>
                    <span v-if="d.suspended" class="text-[9px] px-1.5 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/20 font-bold ml-2 shrink-0">SUSP</span>
                </div>
                <div class="space-y-2">
                    <div class="flex items-center gap-2">
                        <div class="flex-1 h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div class="h-full rounded-full transition-all duration-500"
                                :class="getHOSBarClass(d.hours, d.maxHours)"
                                :style="{ width: (d.hosPct ?? 0) + '%' }"></div>
                        </div>
                        <span class="text-xs font-mono font-bold" :class="getHOSTextClass(d.hours, d.maxHours)">{{ d.hours }}h</span>
                    </div>
                    <div class="text-xs font-semibold" :class="getHOSStatusClass(d.hours, d.maxHours)">
                        {{ d.hours === 0 ? 'Not on shift' : getHOSStatus(d.hours, d.maxHours) }}
                    </div>
                    <div class="text-[10px] text-gray-500 dark:text-gray-400 pt-1 flex justify-between">
                        <span>Max: {{ d.maxHours }}h</span>
                        <span>{{ d.stops }} active order{{ d.stops !== 1 ? 's' : '' }}</span>
                        <span v-if="d.totalWeightKg > 0">{{ d.totalWeightKg }} kg</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { driverManagementPageKey } from './driverManagementPageContext'

const {
    drivers,
    getHOSBarClass,
    getHOSStatus,
    getHOSStatusClass,
    getHOSTextClass,
    showHOS,
} = inject(driverManagementPageKey)
</script>
