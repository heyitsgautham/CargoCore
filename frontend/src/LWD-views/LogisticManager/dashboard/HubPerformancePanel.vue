<template>
    <!-- Hub Performance Table / Interactive View -->
    <div class="glass-panel p-4 lg:p-5 rounded-2xl flex flex-col justify-between h-full overflow-hidden">
        <!-- Header -->
        <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                <span v-if="store.activeWarehouse === 'all'">Hub Performance</span>
                <span v-else>{{ store.activeWarehouseName }} Overview</span>
            </h3>
            <button v-if="store.activeWarehouse !== 'all'" @click="store.setWarehouse('all')"
                class="text-xs text-primary hover:underline font-medium flex items-center">
                <span class="material-symbols-outlined text-[14px] mr-0.5">arrow_back</span>
                View All
            </button>
        </div>

        <!-- ALL HUBS VIEW -->
        <div v-if="store.activeWarehouse === 'all'" class="overflow-x-auto my-auto py-2">
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr
                        class="text-xs text-gray-500 dark:text-gray-500 border-b border-gray-200 dark:border-white/10">
                        <th class="py-2 font-medium">Hub Name</th>
                        <th class="py-2 font-medium">Capacity</th>
                        <th class="py-2 font-medium">Efficiency</th>
                        <th class="py-2 font-medium">Process Rate</th>
                        <th class="py-2 font-medium">Status</th>
                    </tr>
                </thead>
                <tbody class="text-sm">
                    <tr v-for="hub in store.hubs" :key="hub.id"
                        class="border-b border-b-gray-100 dark:border-b-white/5 last:border-0 transition-all cursor-pointer relative"
                        :class="[
                            store.activeWarehouse === hub.id
                                ? 'bg-primary/5 dark:bg-primary/10 border-l-4 border-l-primary'
                                : 'hover:bg-gray-50 dark:hover:bg-white/5 border-l-4 border-l-transparent'
                        ]" @click="store.setWarehouse(hub.id)">
                        <td class="py-3 text-gray-900 dark:text-white font-medium">{{ hub.name }}</td>
                        <td class="py-3 text-gray-500 dark:text-gray-300">
                            <div class="flex items-center gap-2">
                                <div
                                    class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div class="h-full" :class="hub.bg" :style="{ width: hub.capacity + '%' }">
                                    </div>
                                </div>
                                <span class="text-xs">{{ hub.capacity }}%</span>
                            </div>
                        </td>
                        <!-- Added Efficiency Column -->
                        <td class="py-3 text-gray-500 dark:text-gray-300">
                            <div class="flex items-center gap-2">
                                <span class="text-xs font-semibold"
                                    :class="hub.efficiency > 85 ? 'text-green-500' : (hub.efficiency > 60 ? 'text-yellow-500' : 'text-red-500')">
                                    {{ hub.efficiency }}%
                                </span>
                            </div>
                        </td>
                        <td class="py-3 text-gray-500 dark:text-gray-300">{{
                            hub.processRate.toLocaleString() }}
                            pkgs/hr</td>
                        <td class="py-3">
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                :class="hub.status.toLowerCase() === 'optimal' ? 'bg-green-500/20 text-green-600 dark:text-green-500' : (hub.status.toLowerCase() === 'congested' ? 'bg-red-500/20 text-red-600 dark:text-red-500' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-500')">
                                {{ hub.status }}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- SINGLE HUB INTERACTIVE VIEW -->
        <div v-else-if="currentHub" class="flex flex-col h-full animate-fade-in py-2">
            <div class="flex flex-wrap lg:flex-nowrap items-center justify-between gap-4 lg:gap-6 my-auto">

                <!-- Main Stats Group -->
                <div class="flex items-center gap-4">
                    <!-- Capacity Circular Progress -->
                    <div class="relative w-20 h-20 lg:w-24 lg:h-24 flex-shrink-0 group">
                        <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="transition-all duration-1000 ease-out"
                                :class="currentHub.capacity > 85 ? 'stroke-red-500' : (currentHub.capacity > 60 ? 'stroke-yellow-500' : 'stroke-green-500')"
                                stroke-width="3" :stroke-dasharray="`${currentHub.capacity}, 100`"
                                stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute inset-0 flex flex-col items-center justify-center">
                            <span
                                class="text-lg lg:text-2xl font-bold text-gray-900 dark:text-white leading-none">
                                {{ currentHub.capacity }}%
                            </span>
                            <span
                                class="text-[9px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5 lg:mt-1">Load</span>
                        </div>
                    </div>

                    <!-- Pkgs/Hr Stats & Status -->
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border"
                                :class="currentHub.status.toLowerCase() === 'optimal' ? 'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-500' : (currentHub.status.toLowerCase() === 'congested' ? 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-500' : 'bg-yellow-50 border-yellow-200 text-yellow-600 dark:bg-yellow-500/10 dark:border-yellow-500/20 dark:text-yellow-500')">
                                <span class="inline-block w-1.5 h-1.5 rounded-full mr-0.5"
                                    :class="currentHub.status.toLowerCase() === 'optimal' ? 'bg-green-500' : (currentHub.status.toLowerCase() === 'congested' ? 'bg-red-500' : 'bg-yellow-500')"></span>
                                {{ currentHub.status }}
                            </span>
                        </div>
                        <div class="flex items-baseline gap-1">
                            <span class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">{{
                                currentHub.processRate.toLocaleString() }}</span>
                            <span
                                class="text-xs lg:text-sm font-medium text-gray-500 dark:text-gray-400">pkgs/hr</span>
                        </div>
                    </div>
                </div>

                <!-- Secondary Metrics Group (Circular) -->
                <div class="flex items-center gap-3 lg:gap-4 justify-around w-full lg:w-auto mt-4 lg:mt-0">
                    <!-- Efficiency Circular -->
                    <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                        <svg class="w-full h-full transform -rotate-90 drop-shadow-sm" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="transition-all duration-1000 ease-out"
                                :class="currentHub.efficiency > 85 ? 'stroke-green-500' : (currentHub.efficiency > 60 ? 'stroke-yellow-500' : 'stroke-red-500')"
                                stroke-width="3" :stroke-dasharray="`${currentHub.efficiency}, 100`"
                                stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute inset-0 flex flex-col items-center justify-center">
                            <span
                                class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                {{ currentHub.efficiency }}%
                            </span>
                            <span
                                class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Effic.</span>
                        </div>
                    </div>

                    <!-- Staff Circular -->
                    <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                        <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="transition-all duration-1000 ease-out stroke-blue-500" stroke-width="3"
                                :stroke-dasharray="`${staffFillPercent}, 100`"
                                stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute inset-0 flex flex-col items-center justify-center">
                            <span
                                class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                {{ currentHub.staffActive }}<span
                                    class="text-[10px] lg:text-xs text-gray-400 font-normal">/{{
                                        currentHub.staffTotal }}</span>
                            </span>
                            <span
                                class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Staff</span>
                        </div>
                    </div>

                    <!-- Vehicles Circular -->
                    <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                        <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                            <circle cx="18" cy="18" r="15.9155" fill="none"
                                class="transition-all duration-1000 ease-out stroke-purple-500" stroke-width="3"
                                :stroke-dasharray="`${vehicleFillPercent}, 100`"
                                stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute inset-0 flex flex-col items-center justify-center">
                            <span
                                class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                {{ currentHub.vehiclesActive }}<span
                                    class="text-[10px] lg:text-xs text-gray-400 font-normal">/{{
                                        currentHub.vehiclesTotal
                                    }}</span>
                            </span>
                            <span
                                class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Vehs</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Interactive Actions -->
            <div class="grid grid-cols-2 gap-3 mt-6">
                <button @click="optimizeHub" :disabled="isOptimizing"
                    class="border rounded-xl p-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300"
                    :class="isOptimizing ? 'bg-primary/20 text-primary border-primary/20 cursor-wait' : 'bg-primary/10 hover:bg-primary/20 text-primary border-primary/20'">
                    <span v-if="!isOptimizing" class="material-symbols-outlined text-[18px]">tune</span>
                    <span v-else class="material-symbols-outlined text-[18px] animate-spin">sync</span>
                    {{ isOptimizing ? 'Optimizing...' : 'Optimize Load' }}
                </button>
                <button @click="contactHub"
                    class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 border border-transparent rounded-xl p-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300">
                    <span class="material-symbols-outlined text-[18px]">support_agent</span>
                    Contact Hub
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const {
    contactHub,
    currentHub,
    isOptimizing,
    optimizeHub,
    staffFillPercent,
    store,
    vehicleFillPercent,
} = inject(lmDashboardPageKey)
</script>
