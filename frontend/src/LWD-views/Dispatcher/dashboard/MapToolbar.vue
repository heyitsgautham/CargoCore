<template>
    <div class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-lg backdrop-blur-xl p-2 rounded-xl flex gap-1 flex-wrap justify-center max-w-[600px]">
        <!-- Base layer controls -->
        <button @click="$emit('toggle-layer', 'layers')" :class="mapLayers.layers ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Dark Map"><span class="material-symbols-outlined">layers</span></button>
        <button @click="$emit('toggle-layer', 'traffic')" :class="mapLayers.traffic ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Traffic Overlay"><span class="material-symbols-outlined">traffic</span></button>

        <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>

        <!-- Essential layers -->
        <button @click="$emit('toggle-layer', 'hubs')" :class="mapLayers.hubs ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Hubs/Warehouses"><span class="material-symbols-outlined">warehouse</span></button>
        <button @click="$emit('toggle-layer', 'pickups')" :class="mapLayers.pickups ? 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Pickup Points"><span class="material-symbols-outlined">inventory_2</span></button>

        <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>

        <!-- Optional layers -->
        <button @click="$emit('toggle-layer', 'destinations')" :class="mapLayers.destinations ? 'bg-orange-500/15 text-orange-600 dark:text-orange-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Delivery Destinations"><span class="material-symbols-outlined">location_on</span></button>
        <button @click="$emit('toggle-layer', 'routes')" :class="mapLayers.routes ? 'bg-teal-500/15 text-teal-600 dark:text-teal-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Route Lines"><span class="material-symbols-outlined">route</span></button>
        <button @click="$emit('toggle-layer', 'alerts')" :class="mapLayers.alerts ? 'bg-red-500/15 text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Alert Zones"><span class="material-symbols-outlined">warning</span></button>
        <button @click="$emit('toggle-layer', 'zones')" :class="mapLayers.zones ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Geofence Zones"><span class="material-symbols-outlined">share_location</span></button>

        <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>

        <!-- Analysis layers -->
        <button @click="$emit('toggle-layer', 'heatmap')" :class="mapLayers.heatmap ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Driver Density Heatmap"><span class="material-symbols-outlined">blur_on</span></button>
        <button @click="$emit('toggle-layer', 'eta')" :class="mapLayers.eta ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="ETA Coverage"><span class="material-symbols-outlined">schedule</span></button>
        <button @click="$emit('toggle-layer', 'history')" :class="mapLayers.history ? 'bg-violet-500/15 text-violet-600 dark:text-violet-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Route History"><span class="material-symbols-outlined">history</span></button>

        <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>

        <!-- Legend toggle -->
        <button @click="$emit('toggle-legend')" :class="showMapLegend ? 'bg-gray-500/15 text-gray-700 dark:text-gray-300' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Map Legend"><span class="material-symbols-outlined">info</span></button>
    </div>
</template>

<script setup>
defineProps({
    mapLayers: { type: Object, required: true },
    showMapLegend: { type: Boolean, default: false },
})

defineEmits(['toggle-layer', 'toggle-legend'])
</script>
