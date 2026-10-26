<template>
    <!-- Transport Log Timeline -->
    <div class="glass-panel p-4 sm:p-5 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm flex items-center gap-2">
            <span class="material-symbols-outlined text-blue-500 text-lg">timeline</span> Transport Log
        </h3>
        <div class="relative pl-8">
            <div class="absolute left-[11px] top-2 bottom-0 w-[2px] bg-gradient-to-b from-green-500 via-blue-500 to-gray-200 dark:to-gray-700"></div>
            <div v-for="(log, i) in activeMove.transportLog" :key="i" class="relative pb-5 last:pb-0 group">
                <div class="absolute -left-8 top-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] shadow-md transition-transform group-hover:scale-110"
                    :style="{ backgroundColor: logColor(log.color) }">
                    <span class="material-symbols-outlined text-[12px]">{{ log.icon }}</span>
                </div>
                <div class="p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ log.event }}</span>
                        <span v-if="isWarehouseEvent(log.event)" class="px-1.5 py-0.5 bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 text-[9px] font-bold rounded uppercase">
                            Warehouse
                        </span>
                    </div>
                    <div v-if="log.description" class="text-[11px] text-gray-600 dark:text-gray-400 mt-1 leading-snug">
                        {{ log.description }}
                    </div>
                    <div class="text-[10px] text-gray-500 dark:text-gray-500 font-mono mt-0.5">{{ log.time }}</div>
                </div>
            </div>
            <div v-if="!activeMove.transportLog?.length" class="text-center py-4 text-gray-400 text-sm">
                No transport events yet
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove, isWarehouseEvent, logColor } = inject(customerTrackingPageKey)
</script>
