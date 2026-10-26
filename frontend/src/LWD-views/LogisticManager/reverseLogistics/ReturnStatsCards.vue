<template>
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-orange-500/30 transition-colors">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-6xl text-orange-500">pending_actions</span>
            </div>
            <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Reported (New)</div>
            <div class="flex items-end gap-2 z-10 mt-1">
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ reportedCount }}</div>
                <span v-if="reportedCount > 0" class="text-xs font-bold text-orange-500 bg-orange-50 dark:bg-orange-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">
                    Requires Action
                </span>
            </div>
        </div>

        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-blue-500/30 transition-colors">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-6xl text-blue-500">photo_camera</span>
            </div>
            <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Photo Review</div>
            <div class="flex items-end gap-2 z-10 mt-1">
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ photoReviewCount }}</div>
                <span class="text-xs font-bold text-blue-500 bg-blue-50 dark:bg-blue-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Flow 1</span>
            </div>
        </div>

        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-purple-500/30 transition-colors">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-6xl text-purple-500">local_shipping</span>
            </div>
            <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Pickup Inspection</div>
            <div class="flex items-end gap-2 z-10 mt-1">
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ pickupInspectionCount }}</div>
                <span class="text-xs font-bold text-purple-500 bg-purple-50 dark:bg-purple-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Flow 2</span>
            </div>
        </div>

        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-teal-500/30 transition-colors">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-6xl text-teal-500">rate_review</span>
            </div>
            <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Awaiting LM Decision</div>
            <div class="flex items-end gap-2 z-10 mt-1">
                <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ awaitingLMCount }}</div>
                <span v-if="awaitingLMCount > 0" class="text-xs font-bold text-teal-500 bg-teal-50 dark:bg-teal-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Act Now</span>
            </div>
        </div>

        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-green-500/30 transition-colors">
            <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <span class="material-symbols-outlined text-6xl text-green-500">currency_exchange</span>
            </div>
            <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Total Refund Value</div>
            <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">₹{{ refundValue.toLocaleString() }}</div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    awaitingLMCount,
    photoReviewCount,
    pickupInspectionCount,
    refundValue,
    reportedCount,
} = inject(reverseLogisticsPageKey)
</script>
