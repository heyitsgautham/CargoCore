<template>
    <div class="glass-panel rounded-xl p-5">
        <h3 class="mb-4 font-bold text-gray-900 dark:text-white">What AI Handles Here</h3>
        <div class="space-y-3">
            <div v-for="capability in aiCapabilities" :key="capability.title" class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-white/5 dark:bg-white/5">
                <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-primary">{{ capability.icon }}</span>
                    <div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white">{{ capability.title }}</div>
                        <div class="mt-1 text-[11px] leading-5 text-gray-500 dark:text-gray-400">{{ capability.description }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="glass-panel rounded-xl p-5">
        <h3 class="mb-4 font-bold text-gray-900 dark:text-white">Dispatch Watchlist</h3>
        <div v-if="watchlist.length === 0" class="text-[11px] text-gray-500 dark:text-gray-400">
            No driver-assignment risks are open right now.
        </div>
        <div v-else class="space-y-3">
            <div v-for="item in watchlist" :key="item.id" class="rounded-xl border p-3"
                :class="item.risk.level === 'High' ? 'border-red-200 bg-red-50 dark:border-red-500/20 dark:bg-red-500/10' : 'border-yellow-200 bg-yellow-50 dark:border-yellow-500/20 dark:bg-yellow-500/10'">
                <div class="flex items-start justify-between gap-2">
                    <div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.trackingCode || item.id }}</div>
                        <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">{{ item.risk.text }}</div>
                    </div>
                    <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="riskBadgeClass(item.risk.level)">
                        {{ item.risk.level }}
                    </span>
                </div>
            </div>
        </div>
    </div>
    <div class="glass-panel rounded-xl p-5">
        <h3 class="mb-4 font-bold text-gray-900 dark:text-white">Gemini Dispatch Mode</h3>
        <div class="space-y-3 text-[11px] leading-5 text-gray-500 dark:text-gray-400">
            <div class="rounded-xl border border-blue-200 bg-blue-50 p-3 dark:border-blue-500/20 dark:bg-blue-500/10">
                <div class="font-bold text-blue-800 dark:text-blue-300">Rule engine stays in control</div>
                <div class="mt-1">One driver gets one order. Standard warehouse jobs keep the warehouse vehicle lock, while direct recurring/vendor non-packing jobs let dispatcher confirm the AI vehicle suggestion.</div>
            </div>
            <div class="rounded-xl border border-primary/20 bg-primary/10 p-3">
                <div class="font-bold text-gray-900 dark:text-white">Gemini assists with reasoning</div>
                <div class="mt-1">Best driver suggestion, delay prediction, no-driver alerts, reassignment suggestions, and plain-language explanations.</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { smartAssignmentPageKey } from './smartAssignmentPageContext'

const { aiCapabilities, riskBadgeClass, watchlist } = inject(smartAssignmentPageKey)
</script>
