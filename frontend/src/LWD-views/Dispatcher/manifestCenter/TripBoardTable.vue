<template>
    <!-- Trip Board Table -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div class="p-5 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
            <h3 class="font-bold text-gray-900 dark:text-white">Today's Trip Board</h3>
            <div class="text-xs text-gray-500">Auto-populated from dispatch assignments</div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="p-16 text-center">
            <span class="material-symbols-outlined text-4xl text-gray-400 animate-spin">progress_activity</span>
            <p class="text-sm text-gray-500 mt-3">Fetching trips...</p>
        </div>

        <!-- Empty -->
        <div v-else-if="todayTrips.length === 0" class="p-16 text-center">
            <span class="material-symbols-outlined text-5xl text-gray-400 opacity-40">local_shipping</span>
            <p class="text-gray-500 mt-3 text-sm">No trips dispatched today yet.</p>
            <p class="text-gray-600 dark:text-gray-500 text-xs mt-1">Assign drivers from the Pending Queue to see trips here.</p>
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                    <tr>
                        <th class="p-4">Trip / Order</th>
                        <th class="p-4">Driver</th>
                        <th class="p-4">Vehicle</th>
                        <th class="p-4">Route</th>
                        <th class="p-4">Weight</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Assets</th>
                        <th class="p-4">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                    <tr v-for="trip in todayTrips" :key="trip.id"
                        class="hover:bg-gray-100 dark:hover:bg-white/5 transition-colors cursor-pointer"
                        :class="selectedTrip?.id === trip.id ? 'bg-primary/5 dark:bg-primary/10 border-l-2 border-primary' : ''"
                        @click="selectTrip(trip)">

                        <td class="p-4">
                            <div class="font-mono font-bold text-gray-900 dark:text-white text-xs">{{ trip.trackingCode || trip.id }}</div>
                            <div class="text-[10px] text-gray-500 mt-0.5">{{ formatTime(trip.createdAt) }}</div>
                        </td>

                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-[14px] text-primary">person</span>
                                <span class="text-gray-900 dark:text-white text-xs">{{ trip.driver || '—' }}</span>
                            </div>
                            <div v-if="trip.laborCount > 0" class="flex items-center gap-1 mt-0.5">
                                <span class="material-symbols-outlined text-[11px] text-blue-400">groups</span>
                                <span class="text-[10px] text-blue-400">+{{ trip.laborCount }} crew</span>
                            </div>
                        </td>

                        <td class="p-4">
                            <span class="font-mono text-xs text-emerald-600 dark:text-emerald-400 font-bold">{{ trip.vehicle || '—' }}</span>
                        </td>

                        <td class="p-4 max-w-[200px]">
                            <div class="flex items-start gap-1 text-xs text-gray-600 dark:text-gray-300">
                                <span class="material-symbols-outlined text-[11px] text-blue-400 mt-0.5 shrink-0">location_on</span>
                                <span class="truncate">{{ trip.pickupAddr || '—' }}</span>
                            </div>
                            <div class="flex items-start gap-1 mt-0.5 text-xs text-gray-600 dark:text-gray-300">
                                <span class="material-symbols-outlined text-[11px] text-green-400 mt-0.5 shrink-0">flag</span>
                                <span class="truncate">{{ trip.deliveryAddr || '—' }}</span>
                            </div>
                        </td>

                        <td class="p-4 text-gray-600 dark:text-gray-300 text-xs whitespace-nowrap">{{ trip.weight }} kg</td>

                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="getStatusClass(trip.status)">
                                {{ formatStatus(trip.status) }}
                            </span>
                        </td>

                        <td class="p-4">
                            <div v-if="getAssetLog(trip.id)" class="flex items-center gap-1 text-xs font-bold"
                                :class="hasAssetLoss(trip.id) ? 'text-red-400' : 'text-green-400'">
                                <span class="material-symbols-outlined text-[14px]">{{ hasAssetLoss(trip.id) ? 'warning' : 'check_circle' }}</span>
                                {{ hasAssetLoss(trip.id) ? 'Missing' : 'All OK' }}
                            </div>
                            <div v-else-if="getDriverReturn(trip.id)" class="flex items-center gap-1 text-xs font-bold text-blue-400">
                                <span class="material-symbols-outlined text-[14px]">phone_android</span>
                                Driver logged
                            </div>
                            <span v-else class="text-[10px] text-gray-500 italic">Not logged</span>
                        </td>

                        <td class="p-4">
                            <div class="flex flex-wrap items-center gap-2">
                                <button @click.stop="selectTrip(trip)"
                                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors border whitespace-nowrap"
                                    :class="selectedTrip?.id === trip.id
                                        ? 'bg-primary/20 text-primary border-primary/30'
                                        : 'bg-gray-100 dark:bg-white/5 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10'">
                                    {{ selectedTrip?.id === trip.id ? 'Viewing' : 'Log Assets' }}
                                </button>
                                <button @click.stop="openTripManifest(trip)"
                                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors border whitespace-nowrap bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/20">
                                    Manifest
                                </button>
                                <button @click.stop="openTripAssetKit(trip)"
                                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors border whitespace-nowrap bg-orange-500/10 hover:bg-orange-500/20 text-orange-600 dark:text-orange-400 border-orange-500/20">
                                    Asset Kit
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { manifestPageKey } from './manifestPageContext'

const {
    formatStatus,
    formatTime,
    getAssetLog,
    getDriverReturn,
    getStatusClass,
    hasAssetLoss,
    loading,
    openTripAssetKit,
    openTripManifest,
    selectTrip,
    selectedTrip,
    todayTrips,
} = inject(manifestPageKey)
</script>
