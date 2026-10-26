<template>
    <div class="glass-panel rounded-xl p-4">
        <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
            <span class="material-symbols-outlined text-yellow-400 text-[18px]">pending_actions</span>
            Manual Assignment
        </h3>

        <div v-if="unassignedOrders.length === 0" class="text-center py-4 text-gray-500 text-xs">All orders assigned.</div>

        <div v-for="order in unassignedOrders" :key="order.id"
            class="mb-2 p-3 rounded-lg border border-gray-200 dark:border-white/10 hover:border-yellow-500/30 transition-all">
            <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-mono font-bold text-gray-900 dark:text-white">{{ order.trackingCode || order.id.slice(0,8) }}</span>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" :class="priorityClass(order.priority)">{{ order.priority || 'NORMAL' }}</span>
            </div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate mb-1">
                <span class="material-symbols-outlined text-[11px] align-middle text-orange-400">trip_origin</span>
                {{ order.pickupAddr || 'Pickup not set' }}
            </div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate mb-2">
                <span class="material-symbols-outlined text-[11px] align-middle text-blue-400">place</span>
                {{ order.deliveryAddr || 'Delivery not set' }}
            </div>
            <div class="flex gap-2">
                <select v-if="needsDispatcherVehicle(order)" v-model="orderVehiclePick[order.id]"
                    class="flex-1 text-[10px] bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-gray-900 dark:text-white outline-none">
                    <option value="">AI vehicle: {{ recommendedVehicleLabel(order) || 'No vehicle available' }}</option>
                    <option v-for="vehicle in availableVehicles" :key="vehicle.id" :value="vehicle.id">{{ vehicleLabel(vehicle) }}</option>
                </select>
                <select v-model="orderDriverPick[order.id]"
                    class="flex-1 text-[10px] bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-gray-900 dark:text-white outline-none">
                    <option value="">Select Driver</option>
                    <option v-for="d in availableDrivers" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
                <button @click="manualAssign(order)"
                    :disabled="!orderDriverPick[order.id] || assigningId === order.id || !canAssignOrder(order)"
                    class="px-3 py-1.5 bg-primary disabled:opacity-40 hover:bg-primary/80 text-black text-[10px] font-bold rounded-lg transition-colors">
                    {{ assigningId === order.id ? '...' : needsDispatcherVehicle(order) ? 'Assign Both' : 'Assign' }}
                </button>
            </div>
        </div>
    </div>

</template>

<script setup>
import { inject } from 'vue'
import { clusteringPageKey } from './clusteringPageContext'

const {
    assigningId,
    availableDrivers,
    availableVehicles,
    canAssignOrder,
    manualAssign,
    needsDispatcherVehicle,
    orderDriverPick,
    orderVehiclePick,
    priorityClass,
    recommendedVehicleLabel,
    unassignedOrders,
    vehicleLabel,
} = inject(clusteringPageKey)
</script>
