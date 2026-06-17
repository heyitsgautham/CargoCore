<template>
    <div class="space-y-6">

        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Manifest Centre</h2>
                <p class="text-sm text-gray-400 mt-0.5">Today's trip log & packing asset tracker</p>
            </div>
            <div class="flex gap-2">
                <button @click="refreshTrips" :disabled="loading"
                    class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-white/10 py-2 px-3 rounded-lg transition-colors flex items-center gap-1 text-sm font-bold disabled:opacity-50">
                    <span class="material-symbols-outlined text-[18px]" :class="loading ? 'animate-spin' : ''">refresh</span>
                </button>
                <button @click="showEOD = !showEOD"
                    class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 text-sm transition-colors">
                    <span class="material-symbols-outlined text-[18px]">summarize</span>
                    End of Day Report
                </button>
            </div>
        </div>

        <!-- Stat Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500">
                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Total Trips</div>
                <div class="text-3xl font-bold text-blue-400 mt-1">{{ todayTrips.length }}</div>
                <div class="text-xs text-gray-500 mt-1">Today</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-yellow-500">
                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Active</div>
                <div class="text-3xl font-bold text-yellow-400 mt-1">{{ activeCount }}</div>
                <div class="text-xs text-gray-500 mt-1">In transit</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500">
                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Completed</div>
                <div class="text-3xl font-bold text-green-400 mt-1">{{ completedCount }}</div>
                <div class="text-xs text-gray-500 mt-1">Delivered</div>
            </div>
            <div class="glass-panel p-4 rounded-xl" :class="assetAlertCount > 0 ? 'border-l-4 border-red-500' : 'border-l-4 border-gray-400 dark:border-gray-600'">
                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wide">Asset Alerts</div>
                <div class="text-3xl font-bold mt-1" :class="assetAlertCount > 0 ? 'text-red-400' : 'text-gray-400'">{{ assetAlertCount }}</div>
                <div class="text-xs text-gray-500 mt-1">Missing items</div>
            </div>
        </div>

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
                                        <input type="number" v-model.number="item.returned" min="0" :max="item.sentOut"
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

        <!-- Toast -->
        <Teleport to="body">
            <Transition name="fade">
                <div v-if="toast"
                    class="fixed bottom-6 right-6 z-[9999] bg-green-600 text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">check_circle</span>
                    {{ toast }}
                </div>
            </Transition>
        </Teleport>

    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { API_BASE_URL as API_BASE, getStoredAccessToken } from '@/config/api'

const store = useDispatcherStore()
const { openSlipWithData, prefetchSlips } = useSlipPrinter()

// ── State ──────────────────────────────────────────────────────────────────
const loading = ref(false)
const selectedTrip = ref(null)
const detailPanel = ref(null)
const showEOD = ref(false)
const toast = ref('')
const logDirty = ref(false)
const assetNotes = ref('')
const currentAssetLog = ref([])
const assetLogs = ref({})  // { [tripId]: [...items] }
const tripItemsLoading = ref(false)

const ASSET_KEY_PREFIX = 'mc_asset_v1_'

// ── SKU → display metadata (matches driver app) ────────────────────────────
const PKG_DISPLAY_MAP = {
    'PKG-CARTON':        { name: 'Cardboard Boxes',      icon: 'inventory_2'  },
    'PKG-BUBBLE-WRAP':   { name: 'Bubble Wrap (rolls)',  icon: 'layers'       },
    'PKG-PLASTIC-CRATE': { name: 'Plastic Crates',       icon: 'cases'        },
    'PKG-BLANKET':       { name: 'Moving Blankets',      icon: 'king_bed'     },
    'PKG-WARDROBE-BOX':  { name: 'Wardrobe Boxes',       icon: 'checkroom'    },
    'PKG-TAPE':          { name: 'Tape Rolls',            icon: 'straighten'  },
}

const PACKING_KEYWORDS = ['pack', 'wrap', 'box', 'carton', 'tape', 'blanket',
    'crate', 'film', 'pallet', 'protector', 'bag', 'bubble', 'foam', 'wardrobe']

function isPackingItem(sku, name) {
    if (sku && sku.startsWith('PKG-')) return true
    if (!name) return false
    const lower = name.toLowerCase()
    return PACKING_KEYWORDS.some(kw => lower.includes(kw))
}

function resolveDisplay(sku, nameFromApi) {
    if (sku && PKG_DISPLAY_MAP[sku]) return PKG_DISPLAY_MAP[sku]
    return { name: nameFromApi || sku || 'Item', icon: 'inventory_2' }
}

async function fetchTripPackingItems(tripId) {
    try {
        const token = store.authToken || getStoredAccessToken()
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE}/api/v1/orders/${tripId}/items`, { headers })
        if (!res.ok) return []
        const items = await res.json()
        return (items || []).filter(i => isPackingItem(i.sku, i.name))
    } catch {
        return []
    }
}

function buildLogFromOrderItems(orderItems) {
    return orderItems.map(i => {
        // Prefer the real inventory name returned from the API; fall back to display map then SKU
        const display = resolveDisplay(i.sku, i.name || i.sku)
        return {
            name: display.name,
            icon: display.icon,
            sku: i.sku || null,
            sentOut: i.quantity || 0,
            returned: 0,
        }
    })
}

function freshLog() {
    // No hardcoded items — returns empty; callers should use fetchTripPackingItems instead
    return []
}

// ── Trip data from store ───────────────────────────────────────────────────
const todayTrips = computed(() => {
    // ASSIGNED and IN_TRANSIT are always "today" — a driver is actively on them.
    // DELIVERED: filter to today so old completed jobs don't clutter the board.
    const todayStart = new Date()
    todayStart.setHours(0, 0, 0, 0)

    return store.activeOrders.filter(o => {
        if (!['ASSIGNED', 'IN_TRANSIT', 'DELIVERED'].includes(o.status)) return false
        // Active trips always show regardless of when the order was created
        if (o.status === 'ASSIGNED' || o.status === 'IN_TRANSIT') return true
        // For delivered, use deliveredAt if available, fall back to lastUpdated, then always show
        const completedDate = o.deliveredAt || o.lastUpdated
        if (!completedDate) return true
        return new Date(completedDate) >= todayStart
    })
})

const activeCount    = computed(() => todayTrips.value.filter(t => t.status === 'IN_TRANSIT').length)
const completedCount = computed(() => todayTrips.value.filter(t => t.status === 'DELIVERED').length)
const totalWeightToday = computed(() => todayTrips.value.reduce((s, t) => s + Number(t.weight || 0), 0))

const assetAlertCount = computed(() => todayTrips.value.filter(t => hasAssetLoss(t.id)).length)

const todayLabel = computed(() =>
    new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
)

// ── EOD aggregates ─────────────────────────────────────────────────────────
const eodTotalLoss = computed(() => {
    let total = 0
    for (const items of Object.values(assetLogs.value)) {
        total += items.reduce((s, i) => s + Math.max(0, (i.sentOut || 0) - (i.returned || 0)), 0)
    }
    return total
})

const eodAssetSummary = computed(() => {
    // Build summary dynamically from whatever was actually logged — no hardcoded item list
    const map = {}
    for (const items of Object.values(assetLogs.value)) {
        for (const item of items) {
            const key = item.sku || item.name
            if (!map[key]) {
                map[key] = { name: item.name, icon: item.icon || 'inventory_2', totalSent: 0, totalReturned: 0 }
            }
            map[key].totalSent     += item.sentOut  || 0
            map[key].totalReturned += item.returned || 0
        }
    }
    return Object.values(map).filter(i => i.totalSent > 0)
})

// ── Asset log helpers ──────────────────────────────────────────────────────
function getAssetLog(tripId) {
    return assetLogs.value[tripId] || null
}

function hasAssetLoss(tripId) {
    const log = assetLogs.value[tripId]
    if (!log) return false
    return log.some(i => (i.sentOut || 0) > 0 && (i.returned || 0) < (i.sentOut || 0))
}

function getTripDriverContext(trip) {
    const matchedDriver = store.dispatcherDrivers.find(driver => String(driver.id) === String(trip?.driverId || ''))
    return {
        id: trip?.driverId || matchedDriver?.id || trip?.id || '',
        name: trip?.driver || matchedDriver?.name || '—',
        phone: matchedDriver?.phone || '—',
        vehicle: trip?.vehicle || matchedDriver?.vehicle || '—',
    }
}

function getTripVehicleContext(trip) {
    const matchedVehicle = store.filteredVehicles.find(vehicle => String(vehicle.id) === String(trip?.vehicleId || ''))
    return {
        code: trip?.vehicle || matchedVehicle?.code || matchedVehicle?.licensePlate || matchedVehicle?.model || '—',
        licensePlate: matchedVehicle?.licensePlate || trip?.vehicle || '—',
        type: trip?.vehicleType || matchedVehicle?.type || matchedVehicle?.model || 'Assigned vehicle',
        vehicle_number: matchedVehicle?.vehicle_number || matchedVehicle?.code || matchedVehicle?.licensePlate || trip?.vehicle || '—',
    }
}

function getTripAssetItems(trip) {
    if (selectedTrip.value?.id === trip?.id && currentAssetLog.value.length > 0) {
        return JSON.parse(JSON.stringify(currentAssetLog.value))
    }
    const saved = getAssetLog(trip?.id)
    if (saved?.length) return JSON.parse(JSON.stringify(saved))
    return []
}

function buildTripSlipPayload(trip) {
    const driverContext = getTripDriverContext(trip)
    const vehicleContext = getTripVehicleContext(trip)
    const tripNotes = selectedTrip.value?.id === trip?.id
        ? assetNotes.value
        : (typeof window !== 'undefined'
            ? localStorage.getItem(ASSET_KEY_PREFIX + trip.id + '_notes') || ''
            : '')
    return {
        ...trip,
        orderId: trip?.id,
        trackingCode: trip?.trackingCode || trip?.id,
        driver: trip?.driver || driverContext.name,
        driverId: trip?.driverId || driverContext.id,
        driverPhone: driverContext.phone,
        driver_phone: driverContext.phone,
        vehicle: trip?.vehicle || vehicleContext.code,
        vehicleType: trip?.vehicleType || vehicleContext.type,
        licenseNo: driverContext.id ? `LIC-${String(driverContext.id).slice(0, 8).toUpperCase()}` : 'To be assigned',
        notes: tripNotes || trip?.specialInstructions || '',
        specialInstructions: trip?.specialInstructions || '',
        assetItems: getTripAssetItems(trip),
    }
}

async function openTripManifest(trip) {
    if (!trip) return
    const opened = await openSlipWithData('tripManifest', buildTripSlipPayload(trip))
    if (!opened) {
        showToast('Manifest slip could not be opened')
    }
}

async function openTripAssetKit(trip) {
    if (!trip) return
    const opened = await openSlipWithData('assetCheckout', buildTripSlipPayload(trip), getTripVehicleContext(trip))
    if (!opened) {
        showToast('Asset kit slip could not be opened')
    }
}

async function selectTrip(trip) {
    if (selectedTrip.value?.id === trip.id) {
        selectedTrip.value = null
        return
    }
    selectedTrip.value = trip
    logDirty.value = false
    assetNotes.value = localStorage.getItem(ASSET_KEY_PREFIX + trip.id + '_notes') || ''

    const existing = assetLogs.value[trip.id]
    if (existing) {
        // Restore previously saved log for this trip
        currentAssetLog.value = JSON.parse(JSON.stringify(existing))
    } else {
        // Fetch real packing items from the order and pre-fill sentOut quantities
        tripItemsLoading.value = true
        const orderItems = await fetchTripPackingItems(trip.id)
        tripItemsLoading.value = false
        currentAssetLog.value = orderItems.length > 0
            ? buildLogFromOrderItems(orderItems)
            : freshLog()
    }

    // Merge in any driver-submitted return counts
    const driverData = getDriverReturn(trip.id)
    if (driverData?.items?.length && currentAssetLog.value.length > 0) {
        driverData.items.forEach(driverItem => {
            const item = currentAssetLog.value.find(
                i => i.sku === driverItem.sku || i.name === driverItem.name
            )
            if (item && item.returned === 0) item.returned = driverItem.count || 0
        })
    }

    // Scroll the asset panel into view after it renders
    nextTick(() => {
        detailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
}

function onAssetChange() {
    logDirty.value = true
}

async function saveAssetLog() {
    if (!selectedTrip.value) return
    const snapshot = JSON.parse(JSON.stringify(currentAssetLog.value))
    assetLogs.value = { ...assetLogs.value, [selectedTrip.value.id]: snapshot }
    localStorage.setItem(ASSET_KEY_PREFIX + selectedTrip.value.id, JSON.stringify(snapshot))
    localStorage.setItem(ASSET_KEY_PREFIX + selectedTrip.value.id + '_notes', assetNotes.value)
    logDirty.value = false

    // Persist to backend and restore returned items to inventory
    try {
        const token = getStoredAccessToken()
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
        const body = JSON.stringify({
            items: snapshot.map(i => ({
                name: i.name,
                sku: i.sku || null,
                sent_out: i.sentOut || 0,
                returned: i.returned || 0,
            })),
            notes: assetNotes.value || '',
        })
        const res = await fetch(`${API_BASE}/api/v1/orders/${selectedTrip.value.id}/asset-log`, {
            method: 'POST',
            headers,
            body,
        })
        if (res.ok) {
            const result = await res.json()
            showToast(`Asset log saved — ${result.items_restored} item type(s) restored to inventory`)
        } else {
            showToast('Asset log saved locally (backend sync failed)')
        }
    } catch {
        showToast('Asset log saved locally (offline)')
    }
}

function clearAssetLog() {
    currentAssetLog.value = freshLog()
    assetNotes.value = ''
    logDirty.value = false
    if (selectedTrip.value) {
        const next = { ...assetLogs.value }
        delete next[selectedTrip.value.id]
        assetLogs.value = next
        localStorage.removeItem(ASSET_KEY_PREFIX + selectedTrip.value.id)
        localStorage.removeItem(ASSET_KEY_PREFIX + selectedTrip.value.id + '_notes')
    }
}

// ── Driver-submitted packing return (written by driver app via backend) ────
// Key matches what PackingReturn.vue saves in driver-side localStorage.
// In production this would come from the backend order's packing_return field.
// For now we check the browser localStorage in case dispatcher and driver share
// a device (rare) — the real path is backend → order detail → deliveryNotes.
const DRIVER_RETURN_KEY = 'driver_packing_return_v1_'

function getDriverReturn(tripId) {
    const trip = todayTrips.value.find(t => t.id === tripId)

    // 1. packing_return_data — stored by the new packing-return endpoint
    if (trip?.packingReturnData?.items?.length) {
        return trip.packingReturnData
    }

    // 2. Legacy: delivery_notes stored as JSON (old path)
    if (trip?.deliveryNotes) {
        try {
            const parsed = JSON.parse(trip.deliveryNotes)
            if (parsed?.items?.length) return parsed
        } catch {}
    }

    // 3. Fallback: localStorage (same-device scenario)
    try {
        const raw = localStorage.getItem(DRIVER_RETURN_KEY + tripId)
        if (raw) return JSON.parse(raw)
    } catch {}

    return null
}

function importDriverReturn(tripId) {
    const driverData = getDriverReturn(tripId)
    if (!driverData?.items?.length) return

    // Map driver counts into the "returned" column of the current asset log
    driverData.items.forEach(driverItem => {
        const item = currentAssetLog.value.find(
            i => (driverItem.sku && i.sku === driverItem.sku) || i.name === driverItem.name
        )
        if (item) item.returned = driverItem.count || 0
    })
    logDirty.value = true
    showToast('Driver counts imported as returned quantities')
}

function loadAllAssetLogs() {
    const logs = {}
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key?.startsWith(ASSET_KEY_PREFIX) && !key.endsWith('_notes')) {
            const tripId = key.replace(ASSET_KEY_PREFIX, '')
            try { logs[tripId] = JSON.parse(localStorage.getItem(key)) } catch {}
        }
    }
    assetLogs.value = logs
}

// ── Formatting helpers ─────────────────────────────────────────────────────
function getStatusClass(status) {
    return {
        ASSIGNED:   'bg-blue-500/10 text-blue-500 border-blue-500/20',
        IN_TRANSIT: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        DELIVERED:  'bg-green-500/10 text-green-500 border-green-500/20',
    }[status] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'
}

function formatStatus(status) {
    return {
        ASSIGNED:   'Assigned',
        IN_TRANSIT: 'In Transit',
        DELIVERED:  'Delivered',
        CONFIRMED:  'Confirmed',
    }[status] || status
}

function formatTime(dateStr) {
    if (!dateStr) return '—'
    try {
        return new Date(dateStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    } catch { return '—' }
}

function showToast(msg) {
    toast.value = msg
    setTimeout(() => { toast.value = '' }, 2500)
}

// ── Refresh ────────────────────────────────────────────────────────────────
async function refreshTrips() {
    loading.value = true
    try {
        await store.fetchActiveOrders()
    } finally {
        loading.value = false
    }
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
    prefetchSlips(['tripManifest', 'assetCheckout']).catch(() => {})
    loadAllAssetLogs()
    if (store.activeOrders.length === 0) {
        await refreshTrips()
    }
})
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

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
