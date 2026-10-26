<template>
    <!-- Row 3: Transit Log — full width, horizontal scroll of steps -->
    <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-2">
                <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <span class="material-symbols-outlined text-blue-500 text-[15px]">timeline</span>
                </div>
                <h4 class="font-bold text-gray-900 dark:text-white text-sm">Transit Log</h4>
                <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            </div>
            <button class="text-xs font-bold text-blue-500 bg-blue-500/10 hover:bg-blue-500/20 px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-colors">
                <span class="material-symbols-outlined text-[13px]">download</span> Export
            </button>
        </div>

        <div v-if="trackingLogs.length === 0" class="text-center py-8 text-gray-400 text-sm">
            <span class="material-symbols-outlined text-3xl block mb-2 text-gray-300">history</span>
            No status history yet
        </div>

        <!-- Horizontal step-by-step timeline -->
        <div v-else class="overflow-x-auto pb-2">
            <div class="flex items-start gap-0 min-w-max">
                <div v-for="(log, idx) in trackingLogs" :key="'log-'+idx" class="flex items-start">
                    <!-- Step -->
                    <div class="flex flex-col items-center w-40">
                        <!-- Icon -->
                        <div class="w-10 h-10 rounded-full flex items-center justify-center shadow-sm flex-shrink-0 transition-all"
                            :class="log.isCurrent
                                ? 'bg-blue-500 shadow-blue-500/30 ring-4 ring-blue-500/20'
                                : 'bg-green-500 shadow-green-500/20'">
                            <span class="material-symbols-outlined text-white text-[16px]">{{ log.icon }}</span>
                        </div>
                        <!-- Label -->
                        <div class="mt-3 text-center px-2">
                            <div class="text-xs font-bold leading-tight"
                                :class="log.isCurrent ? 'text-blue-600 dark:text-blue-400' : 'text-gray-800 dark:text-gray-200'">
                                {{ log.action }}
                            </div>
                            <div class="text-[10px] text-gray-400 mt-1 flex items-center justify-center gap-0.5">
                                <span class="material-symbols-outlined text-[10px]">location_on</span>
                                <span class="truncate max-w-[100px]">{{ log.location }}</span>
                            </div>
                            <div class="text-[9px] text-gray-400 mt-0.5">{{ log.date }} {{ log.time }}</div>
                            <div v-if="log.isCurrent" class="mt-1.5 inline-flex items-center gap-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[9px] font-bold px-2 py-0.5 rounded-full">
                                <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                                Now
                            </div>
                        </div>
                    </div>
                    <!-- Connector line between steps -->
                    <div v-if="idx < trackingLogs.length - 1"
                        class="flex-shrink-0 flex items-center mt-5">
                        <div class="w-8 h-px bg-gray-200 dark:bg-white/10"></div>
                        <span class="material-symbols-outlined text-gray-300 dark:text-white/20 text-[14px]">chevron_right</span>
                        <div class="w-8 h-px bg-gray-200 dark:bg-white/10"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { trackingLogs } = inject(vendorTrackingPageKey)
</script>
