<template>
    <!-- ── Left: Shipment List ─────────────────────────────────────── -->
    <div class="w-80 flex-shrink-0 glass-panel rounded-2xl overflow-hidden flex flex-col">
        <!-- Search -->
        <div class="p-4 border-b border-gray-200 dark:border-white/5">
            <div class="relative">
                <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-[18px]">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search ID or destination…"
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl py-2 pl-9 pr-4 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500/50">
            </div>
        </div>
        <!-- List -->
        <div class="flex-1 overflow-y-auto p-3 space-y-2">
            <div v-if="filteredShipments.length === 0" class="py-16 text-center text-gray-400 text-sm">
                <span class="material-symbols-outlined text-4xl mb-2 block text-gray-300">inbox</span>
                No shipments found
            </div>
            <div v-for="s in filteredShipments" :key="s.id"
                @click="selected = s; detailTab = 'overview'"
                class="rounded-xl cursor-pointer transition-all border overflow-hidden"
                :class="selected?.id === s.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10 shadow-md shadow-blue-500/10'
                    : 'border-gray-100 dark:border-white/5 bg-white dark:bg-white/5 hover:border-blue-300 dark:hover:border-blue-500/30 hover:shadow-sm'">
                <!-- Color bar -->
                <div class="h-1 w-full" :class="{
                    'bg-yellow-400': s.statusKey === 'pending',
                    'bg-purple-500': s.statusKey === 'warehouse',
                    'bg-blue-500': s.statusKey === 'transit',
                    'bg-indigo-500': s.statusKey === 'delivery',
                    'bg-green-500': s.statusKey === 'delivered',
                    'bg-red-400': s.statusKey === 'cancelled',
                }"></div>
                <div class="p-3">
                    <div class="flex justify-between items-start mb-1.5">
                        <span class="font-mono font-bold text-gray-900 dark:text-white text-[11px]">{{ s.id }}</span>
                        <span class="text-[9px] font-bold px-2 py-0.5 rounded-full" :class="statusClass(s.statusKey)">{{ s.status }}</span>
                    </div>
                    <div class="flex items-center gap-1 text-[11px] text-gray-500 dark:text-gray-400 mb-2">
                        <span class="font-medium text-gray-700 dark:text-gray-300 truncate">{{ s.origin }}</span>
                        <span class="material-symbols-outlined text-[12px] flex-shrink-0 text-blue-400">arrow_forward</span>
                        <span class="truncate">{{ s.destination }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] text-gray-400 flex items-center gap-0.5">
                            <span class="material-symbols-outlined text-[10px]">schedule</span> {{ s.eta }}
                        </span>
                        <span class="text-xs font-bold text-green-600 dark:text-green-400">₹{{ s.amount.toLocaleString() }}</span>
                    </div>
                    <!-- Progress bar -->
                    <div v-if="s.progress > 0 && s.statusKey !== 'delivered' && s.statusKey !== 'cancelled'" class="mt-2">
                        <div class="w-full h-1 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500 rounded-full transition-all" :style="{ width: s.progress + '%' }"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    detailTab,
    filteredShipments,
    searchQuery,
    selected,
    statusClass,
} = inject(vendorTrackingPageKey)
</script>
