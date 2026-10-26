<template>
    <!-- Trip Detail + Asset Logger -->
    <Transition name="slide-down">
        <div v-if="selectedTrip" ref="detailPanel" class="glass-panel rounded-xl p-6 space-y-6">

            <!-- Detail Header -->
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary">inventory_2</span>
                        Asset Log — {{ selectedTrip.trackingCode || selectedTrip.id }}
                    </h3>
                    <p class="text-xs text-gray-500 mt-1">Trip slips live here so queue actions stay focused on dispatching.</p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <button @click="openTripManifest(selectedTrip)"
                        class="bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/20 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">assignment</span>
                        Manifest Slip
                    </button>
                    <button @click="openTripAssetKit(selectedTrip)"
                        class="bg-orange-500/10 hover:bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-500/20 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">inventory_2</span>
                        Asset Kit Slip
                    </button>
                    <button @click="selectedTrip = null"
                        class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
            </div>

            <!-- Trip Info Row -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Driver</div>
                    <div class="text-gray-900 dark:text-white font-bold text-sm mt-1">{{ selectedTrip.driver || '—' }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Vehicle</div>
                    <div class="text-emerald-400 font-bold font-mono text-sm mt-1">{{ selectedTrip.vehicle || '—' }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Cargo Weight</div>
                    <div class="text-gray-900 dark:text-white font-bold text-sm mt-1">{{ selectedTrip.weight }} kg</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Trip Status</div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border mt-1 inline-block" :class="getStatusClass(selectedTrip.status)">
                        {{ formatStatus(selectedTrip.status) }}
                    </span>
                </div>
            </div>

            <!-- Route Strip -->
            <div class="flex items-center gap-3">
                <div class="flex-1 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                    <div class="text-[10px] text-blue-400 font-bold uppercase mb-1">Pickup Location</div>
                    <div class="text-gray-900 dark:text-white text-sm">{{ selectedTrip.pickupAddr || '—' }}</div>
                </div>
                <div class="flex flex-col items-center gap-1 shrink-0">
                    <span class="material-symbols-outlined text-gray-400 text-[20px]">arrow_forward</span>
                    <span class="text-[9px] text-gray-500 uppercase font-bold">Route</span>
                </div>
                <div class="flex-1 p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
                    <div class="text-[10px] text-green-400 font-bold uppercase mb-1">Destination</div>
                    <div class="text-gray-900 dark:text-white text-sm">{{ selectedTrip.deliveryAddr || '—' }}</div>
                </div>
            </div>

            <!-- Asset Logger Table -->
            <div>
                <div class="flex justify-between items-center mb-3">
                    <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase font-bold tracking-wider">Packing Asset Log</div>
                    <div v-if="getAssetLog(selectedTrip.id)" class="flex items-center gap-1 text-xs font-bold"
                        :class="hasAssetLoss(selectedTrip.id) ? 'text-red-400' : 'text-green-400'">
                        <span class="material-symbols-outlined text-[14px]">{{ hasAssetLoss(selectedTrip.id) ? 'warning' : 'check_circle' }}</span>
                        {{ hasAssetLoss(selectedTrip.id) ? 'Some assets not returned' : 'All assets accounted for' }}
                    </div>
                    <span v-else class="text-[10px] text-gray-500 italic">Fill in quantities and save</span>
                </div>

                <div class="rounded-xl overflow-hidden border border-gray-200 dark:border-white/10">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                            <tr>
                                <th class="p-3 text-left">Packing Item</th>
                                <th class="p-3 text-center">Sent Out</th>
                                <th class="p-3 text-center">Returned</th>
                                <th class="p-3 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                            <tr v-for="item in currentAssetLog" :key="item.name"
                                class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                                :class="item.sentOut > 0 && item.returned < item.sentOut ? 'bg-red-50/50 dark:bg-red-500/5' : ''">
                                <td class="p-3">
                                    <div class="flex items-center gap-2 text-gray-900 dark:text-white">
                                        <span class="material-symbols-outlined text-[16px] text-gray-400">{{ item.icon }}</span>
                                        {{ item.name }}
                                    </div>
                                </td>
                                <td class="p-3 text-center">
                                    <input type="number" v-model.number="item.sentOut" min="0"
                                        @input="onAssetChange"
                                        class="w-16 text-center bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-gray-900 dark:text-white text-xs focus:outline-none focus:border-primary/60 transition-colors">
                                </td>
                                <td class="p-3 text-center">
                                    <!-- Read-only when driver submitted their count -->
                                    <div v-if="selectedTrip && getDriverReturn(selectedTrip.id)" class="flex flex-col items-center gap-0.5">
                                        <span class="inline-block w-16 text-center rounded-lg px-2 py-1.5 text-xs font-bold"
                                            :class="item.sentOut > 0 && item.returned < item.sentOut
                                                ? 'bg-red-500/10 text-red-400'
                                                : 'bg-primary/10 text-primary'">
                                            {{ item.returned }}
                                        </span>
                                        <span class="text-[9px] text-gray-500">Driver reported</span>
                                    </div>
                                    <!-- Editable when no driver submission -->
                                    <input v-else type="number" v-model.number="item.returned" min="0" :max="item.sentOut"
                                        @input="onAssetChange"
                                        class="w-16 text-center border rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors"
                                        :class="item.sentOut > 0 && item.returned < item.sentOut
                                            ? 'bg-red-500/10 border-red-500/40 text-red-400 dark:text-red-400 focus:border-red-500/60'
                                            : 'bg-gray-100 dark:bg-black/30 border-gray-200 dark:border-white/10 text-gray-900 dark:text-white focus:border-primary/60'">
                                </td>
                                <td class="p-3 text-center">
                                    <span v-if="item.sentOut === 0" class="text-[10px] text-gray-500">—</span>
                                    <span v-else-if="item.returned >= item.sentOut"
                                        class="flex items-center justify-center gap-0.5 text-[10px] font-bold text-green-400">
                                        <span class="material-symbols-outlined text-[12px]">check_circle</span> OK
                                    </span>
                                    <span v-else
                                        class="flex items-center justify-center gap-0.5 text-[10px] font-bold text-red-400">
                                        <span class="material-symbols-outlined text-[12px]">warning</span>
                                        -{{ item.sentOut - item.returned }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Notes -->
                <div class="mt-3">
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Notes (optional)</label>
                    <textarea v-model="assetNotes" rows="2" placeholder="e.g. 1 dolly left at customer site, driver to collect tomorrow..."
                        class="w-full bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-xs focus:outline-none focus:border-primary/50 resize-none transition-colors">
                    </textarea>
                </div>

                <!-- No packing items for this order -->
                <div v-if="!tripItemsLoading && currentAssetLog.length === 0"
                    class="py-6 text-center text-sm text-gray-500 italic">
                    No packing materials were selected for this order.
                </div>

                <!-- Loading trip items -->
                <div v-if="tripItemsLoading" class="py-8 flex items-center justify-center gap-2 text-sm text-gray-500">
                    <span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                    Loading packing items…
                </div>

                <!-- Driver submitted banner -->
                <div v-if="getDriverReturn(selectedTrip.id)"
                    class="mt-3 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-between gap-3">
                    <div class="flex items-center gap-2 text-xs text-blue-400">
                        <span class="material-symbols-outlined text-[16px]">phone_android</span>
                        <span>Driver submitted their count from the app</span>
                    </div>
                    <button @click="importDriverReturn(selectedTrip.id)"
                        class="shrink-0 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 font-bold py-1.5 px-3 rounded-lg text-xs transition-colors flex items-center gap-1 border border-blue-500/30">
                        <span class="material-symbols-outlined text-[13px]">download</span>
                        Import as Returned
                    </button>
                </div>

                <!-- Actions -->
                <div class="flex items-center gap-2 mt-3">
                    <button @click="saveAssetLog"
                        class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg text-sm transition-colors flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">save</span>
                        Save Asset Log
                    </button>
                    <button @click="clearAssetLog"
                        class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 text-gray-700 dark:text-gray-300 font-bold py-2 px-4 rounded-lg text-sm transition-colors">
                        Reset
                    </button>
                    <span v-if="logDirty" class="text-[10px] text-yellow-500 flex items-center gap-0.5">
                        <span class="material-symbols-outlined text-[12px]">edit</span> Unsaved changes
                    </span>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { inject } from 'vue'
import { manifestPageKey } from './manifestPageContext'

const {
    assetNotes,
    clearAssetLog,
    currentAssetLog,
    detailPanel,
    formatStatus,
    getAssetLog,
    getDriverReturn,
    getStatusClass,
    hasAssetLoss,
    importDriverReturn,
    logDirty,
    onAssetChange,
    openTripAssetKit,
    openTripManifest,
    saveAssetLog,
    selectedTrip,
    tripItemsLoading,
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
