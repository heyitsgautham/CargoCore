<template>
    <!-- Tab Content: Fleet Vehicles -->
    <div v-if="activeTab === 'Fleet Vehicles'" class="flex flex-col gap-6">
        <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Vehicle Roster</h3>
            <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                        <tr
                            class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                            <th class="py-2 px-2 font-medium">Vehicle ID</th>
                            <th class="py-2 font-medium">Warehouse</th>
                            <th class="py-2 font-medium">Type / Model</th>
                            <th class="py-2 font-medium">Driver</th>
                            <th class="py-2 font-medium text-right">Status</th>
                            <th class="py-2 px-2 text-right"></th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="vehicle in searchedVehicles" :key="vehicle.id"
                            @click.stop="openVehicleProfile(vehicle)"
                            class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer relative">
                            <td class="py-3 px-2 text-gray-700 dark:text-white font-mono font-medium">{{ vehicle.code || vehicle.id
                            }}<br /><span class="text-[10px] text-gray-500">{{ vehicle.licensePlate }}</span>
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                {{ store.hubs.find(h => h.id === vehicle.hubId)?.name || 'Main Hub' }}
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300">{{ vehicle.type }}<br /><span
                                    class="text-xs text-gray-400">{{ vehicle.model }} ({{ vehicle.year }})</span>
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300 font-medium">{{ vehicle.driver }}</td>
                            <td class="py-3 text-right">
                                <span
                                    class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
                                    :class="vehicle.status === 'Active' ? 'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-500' :
                                        (vehicle.status === 'In Shop' ? 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-500' : 'bg-yellow-50 border-yellow-200 text-yellow-600 dark:bg-yellow-500/10 dark:border-yellow-500/20 dark:text-yellow-500')">
                                    {{ vehicle.status }}
                                </span>
                            </td>
                            <td class="py-3 px-2 text-right relative">
                                <button @click.stop="toggleVehicleDropdown(vehicle.id)"
                                    class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white cursor-pointer transition-colors p-1 rounded-full hover:bg-gray-100 dark:hover:bg-white/10">
                                    <span class="material-symbols-outlined">more_vert</span>
                                </button>

                                <!-- Action Dropdown for Vehicles -->
                                <div v-if="activeDropdown === vehicle.id" @click.stop
                                    class="absolute right-6 top-10 w-40 bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-xl shadow-lg z-50 py-1 overflow-hidden">
                                    <button @click="openVehicleModal('edit', vehicle); activeDropdown = null"
                                        class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                                        <span class="material-symbols-outlined text-[18px]">edit</span> Edit Details
                                    </button>
                                    <button
                                        @click="store.updateVehicleStatus(vehicle.id, vehicle.status === 'Active' ? 'In Shop' : 'Active'); activeDropdown = null"
                                        class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                                        <span class="material-symbols-outlined text-[18px]">engineering</span>
                                        Toggle Status
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Maintenance Alerts -->
        <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden">
            <div class="absolute top-0 right-0 p-6 opacity-5 dark:opacity-10 pointer-events-none">
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0 z-10">Pending Maintenance</h3>
            <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar z-10">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                        <tr
                            class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                            <th class="py-2 px-2 font-medium">Vehicle ID</th>
                            <th class="py-2 font-medium">Issue / Description</th>
                            <th class="py-2 font-medium">Warehouse</th>
                            <th class="py-2 font-medium">Type / Model</th>
                            <th class="py-2 font-medium text-right">Approx Cost</th>
                            <th class="py-2 font-medium text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="issue in searchedMaintenance" :key="issue.id"
                            class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer relative"
                            @click="openVehicleProfile(store.filteredVehicles.find(v => v.id === issue.id), 'history')">
                            <td class="py-3 px-2 text-gray-700 dark:text-white font-mono font-medium">
                                {{ store.filteredVehicles.find(v => v.id === issue.id)?.code || store.filteredVehicles.find(v => v.id === issue.id)?.id || issue.id }}<br />
                                <span class="text-[10px] text-gray-500">
                                    {{ store.filteredVehicles.find(v => v.id === issue.id)?.licensePlate || 'N/A' }}
                                </span>
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300 font-medium">
                                {{ issue.issue }}
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                {{ store.hubs.find(h => h.id === issue.hubId)?.name || 'Main Hub' }}
                            </td>
                            <td class="py-3 text-gray-600 dark:text-gray-300">
                                <div class="font-medium text-gray-900 dark:text-white">
                                    {{ store.filteredVehicles.find(v => v.id === issue.id)?.type || '—' }}
                                </div>
                                <div class="text-[10px] text-gray-500">
                                    {{ store.filteredVehicles.find(v => v.id === issue.id)?.model || '—' }}
                                    <template v-if="store.filteredVehicles.find(v => v.id === issue.id)?.year">({{ store.filteredVehicles.find(v => v.id === issue.id)?.year }})</template>
                                </div>
                            </td>
                            <td class="py-3 text-right text-gray-600 dark:text-gray-300 font-mono">
                                {{ maintenanceCost(issue.id) }}
                            </td>
                            <td class="py-3 text-right">
                                <span
                                    class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
                                    :class="issue.statusClass">{{ issue.status }}</span>
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
    activeDropdown,
    activeTab,
    maintenanceCost,
    openVehicleModal,
    openVehicleProfile,
    searchedMaintenance,
    searchedVehicles,
    store,
    toggleVehicleDropdown,
} = inject(fleetPageKey)
</script>
