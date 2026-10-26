<template>
    <!-- Step 1: Shipment picker (shown until chat is started) -->
    <div v-if="!chatStarted" class="flex-1 flex flex-col items-center justify-center gap-4 px-6 py-8 overflow-y-auto">
        <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center shadow-lg">
            <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
        </div>
        <div class="text-center">
            <p class="font-bold text-gray-800 dark:text-white/80 text-sm">Start Support Chat</p>
            <p class="text-gray-500 dark:text-white/40 text-xs mt-1 max-w-[260px]">
                Select an active shipment for context, or start a general chat without one.
            </p>
        </div>
        <div class="w-full max-w-sm space-y-2">
            <div v-if="selectableShipments.length > 0">
                <button
                    v-for="s in selectableShipments"
                    :key="s.backendId"
                    @click="selectShipment(s)"
                    class="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-blue-400/60 hover:bg-blue-50/50 dark:hover:bg-white/8 transition-all group text-left mb-2"
                >
                    <div>
                        <div class="font-bold text-sm text-gray-900 dark:text-white font-mono">{{ s.id }}</div>
                        <div class="text-[11px] text-gray-500 dark:text-white/40 mt-0.5">{{ s.origin }} → {{ s.destination }}</div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                        <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                            :class="shipmentStatusBadge(s.statusKey)">{{ s.status }}</span>
                        <span class="material-symbols-outlined text-gray-400 group-hover:text-blue-500 transition-colors text-[16px]">arrow_forward</span>
                    </div>
                </button>
            </div>
            <div v-else class="text-center text-xs text-gray-400 dark:text-white/30 py-3">
                No active shipments found.
            </div>
            <!-- Chat without shipment -->
            <div class="pt-2 border-t border-gray-200 dark:border-white/10">
                <button
                    @click="startWithoutShipment"
                    class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-dashed border-gray-300 dark:border-white/15 bg-gray-50 dark:bg-white/5 hover:border-blue-400/60 hover:bg-blue-50/30 dark:hover:bg-white/8 transition-all text-sm text-gray-600 dark:text-gray-400 hover:text-blue-700 dark:hover:text-blue-400"
                >
                    <span class="material-symbols-outlined text-[18px]">chat</span>
                    Chat without selecting a shipment
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    chatStarted,
    selectShipment,
    selectableShipments,
    shipmentStatusBadge,
    startWithoutShipment,
} = inject(vendorSupportPageKey)
</script>
