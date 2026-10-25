<template>
    <transition name="fade">
    <div v-if="show" class="absolute bottom-24 right-4 z-20 bg-white/95 dark:bg-black/90 backdrop-blur border border-gray-200 dark:border-white/10 rounded-xl shadow-xl p-4 w-64">
        <div class="flex justify-between items-center mb-3">
            <h4 class="font-bold text-sm text-gray-900 dark:text-white">Map Legend</h4>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
                <span class="material-symbols-outlined text-[16px]">close</span>
            </button>
        </div>
        <div class="space-y-2 text-xs">
            <!-- Drivers -->
            <div class="flex items-center gap-2">
                <div class="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                    <span class="material-symbols-outlined text-white text-[12px]">local_shipping</span>
                </div>
                <span class="text-gray-700 dark:text-gray-300">Active Drivers</span>
            </div>
            <!-- Hubs -->
            <div v-if="mapLayers.hubs" class="flex items-center gap-2">
                <div class="w-5 h-5 bg-indigo-600 rounded flex items-center justify-center">
                    <span class="material-symbols-outlined text-white text-[12px]">warehouse</span>
                </div>
                <span class="text-gray-700 dark:text-gray-300">Hubs/Warehouses</span>
            </div>
            <!-- Pickups -->
            <div v-if="mapLayers.pickups" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full border-2 border-blue-500 bg-blue-500/30"></div>
                <span class="text-gray-700 dark:text-gray-300">Pending Pickups</span>
            </div>
            <!-- Destinations -->
            <div v-if="mapLayers.destinations" class="flex items-center gap-2">
                <div class="w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center">
                    <span class="material-symbols-outlined text-white text-[10px]">location_on</span>
                </div>
                <span class="text-gray-700 dark:text-gray-300">Delivery Destinations</span>
            </div>
            <!-- Routes -->
            <div v-if="mapLayers.routes" class="flex items-center gap-2">
                <div class="w-5 h-1 bg-blue-500 rounded" style="border-style: dashed;"></div>
                <span class="text-gray-700 dark:text-gray-300">Active Routes</span>
            </div>
            <!-- Alerts -->
            <div v-if="mapLayers.alerts" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full border-2 border-red-500 bg-red-500/25"></div>
                <span class="text-gray-700 dark:text-gray-300">Alert Zones (red=critical, orange=high, yellow=medium)</span>
            </div>
            <!-- Zones -->
            <div v-if="mapLayers.zones" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full border-2 border-purple-500 bg-purple-500/15"></div>
                <span class="text-gray-700 dark:text-gray-300">Geofence Zones</span>
            </div>
            <!-- ETA -->
            <div v-if="mapLayers.eta" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full border border-dashed border-green-500 bg-green-500/10"></div>
                <span class="text-gray-700 dark:text-gray-300">ETA Coverage (~15 min)</span>
            </div>
            <!-- Heatmap -->
            <div v-if="mapLayers.heatmap" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full bg-red-500/30"></div>
                <span class="text-gray-700 dark:text-gray-300">Driver Density</span>
            </div>
            <!-- History -->
            <div v-if="mapLayers.history" class="flex items-center gap-2">
                <div class="w-5 h-0.5 bg-violet-500" style="border-style: dashed;"></div>
                <span class="text-gray-700 dark:text-gray-300">Route History</span>
            </div>
        </div>
        <!-- Active layers count -->
        <div class="mt-3 pt-3 border-t border-gray-200 dark:border-white/10">
            <div class="text-[10px] text-gray-500">{{ activeLayersCount }} layers active</div>
        </div>
    </div>
    </transition>
</template>

<script setup>
defineProps({
    show: { type: Boolean, default: false },
    mapLayers: { type: Object, required: true },
    activeLayersCount: { type: Number, required: true },
})

defineEmits(['close'])
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
}
</style>
