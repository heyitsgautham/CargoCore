<template>
    <!-- 4. WORKFORCE & ROLES -->
    <div v-if="activeTab === 'workforce'" class="space-y-6 animate-fade-in">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div
                class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Labour Allocation</h3>
                <div class="h-74 relative flex justify-center">
                    <Doughnut :data="workforceData" :options="doughnutOptions" />
                </div>
            </div>

            <!-- Vendor Performance -->
            <div
                class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Vendor Performance & Lead Time</h3>
                <div class="h-74 relative">
                    <Line :data="vendorLeadTimeData" :options="chartOptions" />
                </div>
            </div>

            <!-- Safety Incident Trends (New to fill gap) -->
            <div
                class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Safety Incident Alerts</h3>
                <div class="h-74 relative">
                    <Bar :data="safetyIncidentData" :options="chartOptions" />
                </div>
            </div>
        </div>

        <!-- Warehouse Dwell Time -->
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 mb-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Warehouse Dwell Time Analytics
                (Loading/Unloading)</h3>
            <div class="h-74 relative">
                <Bar :data="dwellTimeData" :options="chartOptions" />
            </div>
        </div>

        <!-- Dynamic Roles Table -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                <div class="p-4 border-b border-gray-100 dark:border-white/10 flex justify-between">
                    <h3 class="font-bold text-gray-900 dark:text-white">Warehouse Staff & Dispatchers</h3>
                    <div class="flex gap-2">
                        <button class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-1 rounded">Metrics</button>
                        <button class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-1 rounded">Roster</button>
                    </div>
                </div>
                <table class="w-full text-left text-xs">
                    <thead
                        class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                        <tr>
                            <th class="p-3">Staff</th>
                            <th class="p-3">Role</th>
                            <th class="p-3">Shift Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="user in store.filteredUsers" :key="user.email"
                            class="hover:bg-gray-50 dark:hover:bg-white/5">
                            <td class="p-3 flex items-center gap-3">
                                <img :src="user.avatar" class="w-8 h-8 rounded-full">
                                <div>
                                    <p class="font-bold text-gray-900 dark:text-white">{{ user.name }}</p>
                                    <p class="text-[10px] text-gray-400">{{ user.email }}</p>
                                </div>
                            </td>
                            <td class="p-3">
                                <span
                                    class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100">{{
                                    user.role }}</span>
                            </td>
                            <td class="p-3 text-green-500 font-bold">{{ user.status }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Staff Efficiency & Overtime (Filling the gap) -->
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col p-6">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Shift Efficiency & Overtime</h3>
                <div class="h-64 relative">
                    <Bar :data="shiftEfficiencyData" :options="chartOptions" />
                </div>
            </div>
        </div>

        <!-- Driver Performance Scorecard -->
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
            <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                <h3 class="font-bold text-gray-900 dark:text-white">Driver Performance Scorecard</h3>
            </div>
            <table class="w-full text-left text-xs">
                <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-3">Driver</th>
                        <th class="p-3 text-center">Rating</th>
                        <th class="p-3 text-center">Safety Incidents</th>
                        <th class="p-3 text-center">Fuel Eff.</th>
                        <th class="p-3 text-center">Avg Speed</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="d in store.filteredDrivers" :key="d.id"
                        class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-3 font-bold text-gray-900 dark:text-white">{{ d.name }}</td>
                        <td class="p-3 text-center">
                            <div class="flex items-center justify-center gap-1 text-yellow-500">
                                <span class="font-bold text-gray-900 dark:text-white">{{ d.rating.toFixed(1) }}</span>
                                <span class="material-symbols-outlined text-[14px]">star</span>
                            </div>
                        </td>
                        <td class="p-3 text-center font-bold"
                            :class="d.safetyIncidents > 0 ? 'text-red-500' : 'text-gray-300'">{{ d.safetyIncidents }}</td>
                        <td class="p-3 text-center font-mono text-green-600">{{ d.fuelEfficiencyScore }}</td>
                        <td class="p-3 text-center font-mono">{{ d.avgSpeed }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    chartOptions,
    doughnutOptions,
    dwellTimeData,
    safetyIncidentData,
    shiftEfficiencyData,
    store,
    vendorLeadTimeData,
    workforceData,
} = inject(reportsPageKey)
</script>
