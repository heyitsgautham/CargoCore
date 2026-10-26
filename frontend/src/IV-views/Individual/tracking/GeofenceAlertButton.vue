<template>
    <div class="space-y-1">
        <button @click="toggleGeofence" :disabled="geofenceLoading"
            class="w-full py-2.5 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2 border disabled:opacity-60 disabled:cursor-not-allowed"
            :class="geofenceAlert
                ? 'bg-green-500/10 border-green-500/30 text-green-600 dark:text-green-400 hover:bg-green-500/20'
                : 'bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/5 text-gray-700 dark:text-white hover:bg-gray-200 dark:hover:bg-white/10'">
            <span v-if="geofenceLoading" class="material-symbols-outlined text-sm animate-spin">sync</span>
            <span v-else class="material-symbols-outlined text-sm">{{ geofenceAlert ? 'notifications_active' : 'notifications' }}</span>
            {{ geofenceLoading ? 'Simulating...' : geofenceAlert ? 'Geofence Alert Active' : 'Simulate Arrival Alert' }}
        </button>
        <p v-if="geofenceError" class="text-[10px] text-amber-500 dark:text-amber-400 text-center">{{ geofenceError }}</p>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { geofenceAlert, geofenceError, geofenceLoading, toggleGeofence } = inject(customerTrackingPageKey)
</script>
