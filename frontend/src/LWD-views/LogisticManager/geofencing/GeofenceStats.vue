<template>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Total Zones</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ filteredZones.length }}</p>
            </div>
            <div class="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <span class="material-symbols-outlined">share_location</span>
            </div>
        </div>
        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Active Vehicles</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ vehiclesInZones }}</p>
            </div>
            <div class="w-10 h-10 rounded-full bg-green-50 dark:bg-green-500/10 flex items-center justify-center text-green-600 dark:text-green-400">
                <span class="material-symbols-outlined">local_shipping</span>
            </div>
        </div>
        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Breach Alerts</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ breachAlerts }}</p>
            </div>
            <div class="w-10 h-10 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center text-red-600 dark:text-red-400">
                <span class="material-symbols-outlined">warning</span>
            </div>
        </div>
        <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Coverage Area</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ totalArea }} km²</p>
            </div>
            <div class="w-10 h-10 rounded-full bg-purple-50 dark:bg-purple-500/10 flex items-center justify-center text-purple-600 dark:text-purple-400">
                <span class="material-symbols-outlined">layers</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { geofencingPageKey } from './geofencingPageContext'

const { breachAlerts, filteredZones, totalArea, vehiclesInZones } = inject(geofencingPageKey)
</script>
