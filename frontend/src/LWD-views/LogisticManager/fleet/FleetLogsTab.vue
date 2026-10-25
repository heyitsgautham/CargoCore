<template>
    <!-- Tab Content: Fuel Logs (New) -->
    <!-- Tab Content: Fleet Logs (Dynamic) -->
    <div v-if="activeTab === 'Fleet Logs'" class="grid grid-cols-1 lg:grid-cols-3 gap-6 text-sm">
        <!-- Left Panel: Dynamic Stats & Selector -->
        <div class="glass-panel rounded-xl p-6 lg:col-span-1 border border-gray-200 dark:border-white/5 h-[500px] flex flex-col">
            <div class="mb-6">
                <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Select Log Category</label>
                <div class="relative">
                    <select v-model="activeLogType" class="w-full appearance-none bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white font-bold rounded-lg py-3 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow cursor-pointer">
                        <option v-for="type in logTypes" :key="type" :value="type" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ type }}</option>
                    </select>
                    <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">expand_more</span>
                </div>
            </div>

            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2 flex-shrink-0">
                <span class="material-symbols-outlined" :class="`text-${logStats.color}-500`">{{ logStats.icon }}</span>
                {{ logStats.title }}
            </h3>

            <div class="space-y-4 overflow-y-auto custom-scrollbar pr-2">
                <div class="p-4 rounded-xl border" 
                    :class="`bg-${logStats.color}-50 dark:bg-${logStats.color}-500/10 border-${logStats.color}-100 dark:border-${logStats.color}-500/20`">
                    <p class="text-xs uppercase font-bold tracking-wider mb-1" :class="`text-${logStats.color}-600 dark:text-${logStats.color}-400`">Total Cost (This Month)</p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">₹{{ logStats.totalCost.toLocaleString(undefined, {minimumFractionDigits: 2}) }}</p>
                    <p class="text-xs mt-1 opacity-80" :class="`text-${logStats.color}-600 dark:text-${logStats.color}-400`">↑ 2.4% vs last month</p>
                </div>

                 <div class="grid grid-cols-2 gap-4">
                    <div v-for="(tile, idx) in logStats.tiles" :key="idx" class="bg-gray-50 dark:bg-white/5 p-4 rounded-xl">
                        <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">{{ tile.label }}</p>
                        <p class="text-lg font-bold text-gray-900 dark:text-white">{{ tile.value }}</p>
                    </div>
                </div>

                <div class="p-4 border-t border-gray-100 dark:border-white/5 mt-4">
                    <p class="text-xs text-gray-500 uppercase font-bold tracking-wider mb-2">{{ logStats.trend.label }}</p>
                    <div class="w-full bg-gray-200 dark:bg-white/10 rounded-full h-2 mb-1">
                        <div class="h-2 rounded-full" :class="`bg-${logStats.color}-500`" :style="`width: ${logStats.trend.pct}%`"></div>
                    </div>
                    <div class="flex justify-between text-xs text-gray-500">
                        <span>{{ logStats.trend.value }}</span>
                        <span>Target: {{ logStats.trend.target }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right Panel: Data Table -->
        <div class="glass-panel rounded-xl p-6 lg:col-span-2 border border-gray-200 dark:border-white/5 h-[500px] flex flex-col relative overflow-hidden">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">{{ activeLogType }} Overview</h3>
            <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                        <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                            <th class="py-2 px-2 font-medium">Date</th>
                            <th class="py-2 font-medium">Vehicle ID</th>
                            <th class="py-2 font-medium">Warehouse</th>

                            <!-- Dynamic Headers -->
                            <th v-if="activeLogType === 'Fuel Logs'" class="py-2 font-medium">Station</th>
                            <th v-if="activeLogType === 'Fuel Logs'" class="py-2 font-medium text-right">Gallons</th>

                            <th v-if="activeLogType === 'Service Logs'" class="py-2 font-medium">Service</th>
                            <th v-if="activeLogType === 'Service Logs'" class="py-2 font-medium">Provider</th>

                            <th v-if="activeLogType === 'Maintenance Logs'" class="py-2 font-medium">Issue</th>
                            <th v-if="activeLogType === 'Maintenance Logs'" class="py-2 font-medium">Mechanic</th>

                            <th v-if="activeLogType === 'Cleaning Logs'" class="py-2 font-medium">Type</th>
                            <th v-if="activeLogType === 'Cleaning Logs'" class="py-2 font-medium">Provider</th>

                            <th class="py-2 font-medium text-right">Cost</th>
                            <th class="py-2 font-medium text-right">Status</th>
                        </tr>
                    </thead>
                   <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="log in searchedLogs" :key="log.id" 
                            class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                            @click="openVehicleProfile(store.filteredVehicles.find(v => v.id === log.vehicleId), 'history')">

                            <td class="py-3 px-2 text-gray-600 dark:text-gray-300 font-mono">{{ log.date }}</td>
                            <td class="py-3 text-gray-900 dark:text-white font-medium">{{ log.vehicleId }}</td>
                            <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                {{ store.hubs.find(h => h.id === log.hubId)?.name || 'Main Hub' }}
                            </td>

                            <!-- Dynamic Cells -->
                            <td v-if="activeLogType === 'Fuel Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.station }}</td>
                            <td v-if="activeLogType === 'Fuel Logs'" class="py-3 text-gray-600 dark:text-gray-300 text-right">{{ log.gallons }}</td>

                            <td v-if="activeLogType === 'Service Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.service }}</td>
                            <td v-if="activeLogType === 'Service Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.provider }}</td>

                            <td v-if="activeLogType === 'Maintenance Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.issue }}</td>
                            <td v-if="activeLogType === 'Maintenance Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.mechanic }}</td>

                            <td v-if="activeLogType === 'Cleaning Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.type }}</td>
                            <td v-if="activeLogType === 'Cleaning Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.provider }}</td>

                            <td class="py-3 text-gray-900 dark:text-white font-bold text-right">₹{{ log.cost }}</td>
                            <td class="py-3 text-right">
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border" 
                                    :class="log.status === 'Completed' || log.status === 'Verified' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400'">
                                    {{ log.alert ? 'Anomaly' : (log.status || 'Verified') }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    activeLogType,
    activeTab,
    logStats,
    logTypes,
    openVehicleProfile,
    searchedLogs,
    store,
} = inject(fleetPageKey)
</script>
