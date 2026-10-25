<template>
    <!-- Vehicle Profile Modal -->
    <Teleport to="body">
        <div v-if="activeVehicleProfile"
            class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            @click.self="closeVehicleProfile">
            <div
                class="bg-white dark:bg-card-dark w-full max-w-2xl rounded-2xl shadow-2xl border border-gray-200 dark:border-white/10 overflow-hidden flex flex-col">
                <div
                    class="px-6 py-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-gray-400">local_shipping</span>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ activeVehicleProfile.id }}
                            Overview</h3>
                    </div>
                    <button @click="closeVehicleProfile"
                        class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="p-6">
                    <div v-if="activeVehicleProfile.viewMode === 'full'">
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Status</p>
                                <span class="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider"
                                    :class="activeVehicleProfile.status === 'Active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-500' : 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-500'">
                                    {{ activeVehicleProfile.status }}
                                </span>
                            </div>
                            <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Model /
                                    Year</p>
                                <p class="text-sm font-bold text-gray-900 dark:text-white">{{ activeVehicleProfile.model
                                }} ({{ activeVehicleProfile.year }})</p>
                            </div>
                            <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Current
                                    Odometer</p>
                                <p class="text-sm font-bold text-gray-900 dark:text-white">{{
                                    activeVehicleProfile.mileage.toLocaleString() }} mi</p>
                            </div>
                            <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Assigned
                                    Driver</p>
                                <p class="text-sm font-bold text-gray-900 dark:text-white">{{
                                    activeVehicleProfile.driver }}</p>
                            </div>
                        </div>


                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <!-- Left: Spec & Metrics -->
                            <div>
                                <h4 class="font-bold text-gray-900 dark:text-white mb-3">Vehicle Metrics</h4>
                                <div class="space-y-3">
                                    <div
                                        class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                        <span class="text-gray-500">License Plate</span>
                                        <span class="font-medium text-gray-900 dark:text-white">{{
                                            activeVehicleProfile.licensePlate }}</span>
                                    </div>
                                    <div
                                        class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                        <span class="text-gray-500">Vehicle Type</span>
                                        <span class="font-medium text-gray-900 dark:text-white">{{
                                            activeVehicleProfile.type }}</span>
                                    </div>
                                    <div
                                        class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                        <span class="text-gray-500">Avg Fuel Efficiency</span>
                                        <span class="font-medium text-gray-900 dark:text-white">{{
                                            activeVehicleProfile.fuelEfficiency }}</span>
                                    </div>
                                    <div
                                        class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                        <span class="text-gray-500">Total Repair Expense</span>
                                        <span class="font-medium text-gray-900 dark:text-white">
                                            ₹{{ activeVehicleProfile.totalMaintenanceCost.toLocaleString() }} (YTD)
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: Service Logs -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-bold text-gray-900 dark:text-white">Recent Service</h4>
                                    <span class="text-xs text-primary font-bold">Next: {{
                                        activeVehicleProfile.nextService }}</span>
                                </div>
                                <div class="space-y-3">
                                    <div v-for="log in activeVehicleProfile.serviceHistory.slice(0, 2)" :key="log.id" class="p-3 border border-gray-200 dark:border-white/10 rounded-lg">
                                        <div class="flex justify-between items-center mb-1">
                                            <span class="text-sm font-bold text-gray-900 dark:text-white">{{ log.service }}</span>
                                            <span class="text-xs text-gray-500">{{ log.date }}</span>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span
                                                class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">{{ log.type }}</span>
                                            <span class="text-xs font-mono font-bold text-gray-900 dark:text-white">₹{{ log.cost }}</span>
                                        </div>
                                    </div>
                                    <button @click="activeVehicleProfile.viewMode = 'history'" class="w-full text-center text-xs text-primary hover:underline mt-2">View Full History</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- History Mode View -->
                    <div v-else-if="activeVehicleProfile.viewMode === 'history'" class="flex flex-col h-full">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="font-bold text-gray-900 dark:text-white">Full Service Ledger</h4>
                            <div class="bg-gray-100 dark:bg-white/5 px-3 py-1 rounded-lg">
                                <span class="text-xs text-gray-500 uppercase font-bold mr-2">Total Cost</span>
                                <span class="font-mono font-bold text-gray-900 dark:text-white">₹{{ activeVehicleProfile.totalMaintenanceCost.toLocaleString() }}</span>
                            </div>
                        </div>

                        <div class="overflow-y-auto max-h-[400px] border rounded-lg border-gray-200 dark:border-white/10">
                            <table class="w-full text-left text-sm">
                                <thead class="bg-gray-50 dark:bg-white/5 sticky top-0 backdrop-blur-md">
                                    <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                        <th class="py-2 px-3 font-medium">Date</th>
                                        <th class="py-2 px-3 font-medium">Service Performed</th>
                                        <th class="py-2 px-3 font-medium">Description</th>
                                        <th class="py-2 px-3 font-medium text-right">Cost</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                    <tr v-for="item in activeVehicleProfile.serviceHistory" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                        <td class="py-3 px-3 text-gray-600 dark:text-gray-300 font-mono text-xs">{{ item.date }}</td>
                                        <td class="py-3 px-3 text-gray-900 dark:text-white font-medium">{{ item.service }}</td>
                                        <td class="py-3 px-3">
                                            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider" 
                                                :class="item.type === 'Routine' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-500' : 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-500'">
                                                {{ item.type }}
                                            </span>
                                        </td>
                                        <td class="py-3 px-3 text-right text-gray-900 dark:text-white font-mono font-bold">₹{{ item.cost.toFixed(2) }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <button @click="activeVehicleProfile.viewMode = 'full'" class="mt-4 flex items-center gap-2 text-primary hover:underline text-sm font-medium">
                            <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Overview
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const { activeVehicleProfile, closeVehicleProfile } = inject(fleetPageKey)
</script>
