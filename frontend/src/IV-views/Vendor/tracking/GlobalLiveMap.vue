<template>
    <!-- Live Map -->
    <div v-if="globalTab === 'map'" class="flex-1 glass-panel rounded-2xl overflow-hidden relative" style="min-height:500px;">
        <!-- Real Leaflet Map -->
        <l-map v-model:zoom="globalMapZoom" :center="globalMapCenter" :use-global-leaflet="false"
            style="position:absolute; inset:0; height:100%; width:100%;">
            <l-tile-layer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                layer-type="base"
                name="CartoDB Voyager"
            ></l-tile-layer>
            <!-- Active driver markers -->
            <l-marker v-for="d in activeDrivers" :key="'drv-' + d.order_id"
                :lat-lng="[d.latitude, d.longitude]">
                <l-popup>
                    <div class="text-xs p-1">
                        <div class="font-bold flex items-center gap-1 mb-1">
                            <span class="material-symbols-outlined text-[14px] text-blue-500">local_shipping</span>
                            {{ d.driver_name }}
                        </div>
                        <div class="text-gray-500 mb-0.5">Order: <span class="font-medium text-gray-800">{{ d.order_id }}</span></div>
                        <div class="text-gray-500 mb-0.5">Vehicle: <span class="font-medium text-gray-800">{{ d.vehicle_code }}</span></div>
                        <div class="mt-1 text-[9px] uppercase font-bold bg-blue-100 text-blue-700 rounded px-1.5 py-0.5 inline-block">{{ d.status }}</div>
                    </div>
                </l-popup>
            </l-marker>
        </l-map>
        <!-- No drivers overlay -->
        <div v-if="activeDrivers.length === 0" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style="z-index:500;">
            <span class="material-symbols-outlined text-5xl text-gray-400/50 mb-2">location_off</span>
            <p class="text-gray-400/70 text-sm font-medium">No active drivers on the road</p>
        </div>
        <!-- Fleet overlay -->
        <div class="absolute top-4 right-4 bottom-16 w-52 bg-white/90 dark:bg-black/50 backdrop-blur-md rounded-xl border border-gray-200 dark:border-white/10 hidden md:flex flex-col overflow-hidden shadow-lg" style="z-index:1000;">
            <div class="p-3 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
                <span class="text-[10px] font-bold text-gray-900 dark:text-white uppercase tracking-wider">Active Fleet</span>
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            </div>
            <div class="flex-1 overflow-y-auto p-2">
                <div v-for="s in store.activeShipments.slice(0, 6)" :key="'fleet-'+s.id" @click="selected = s"
                    class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 cursor-pointer transition-colors mb-1">
                    <div class="flex justify-between items-center mb-0.5">
                        <span class="text-[10px] font-mono font-bold text-blue-500 truncate">{{ s.id }}</span>
                        <span class="text-[9px] px-1.5 bg-blue-500/10 text-blue-600 rounded font-bold flex-shrink-0">{{ s.progress }}%</span>
                    </div>
                    <div class="text-[9px] text-gray-500 truncate">→ {{ s.destination }}</div>
                </div>
                <div v-if="store.activeShipments.length === 0" class="text-center py-4 text-[10px] text-gray-400">No active shipments</div>
            </div>
            <div class="p-2 bg-blue-500/5 text-center text-[9px] text-gray-500 border-t border-gray-100 dark:border-white/10">
                {{ store.activeShipments.length }} vehicles in motion
            </div>
        </div>
        <!-- Legend -->
        <div class="absolute bottom-4 left-4 right-4 md:right-60 bg-white/90 dark:bg-black/60 backdrop-blur-md p-3 rounded-xl border border-gray-200 dark:border-white/10 flex items-center justify-between" style="z-index:1000;">
            <div>
                <div class="text-[11px] font-bold text-gray-900 dark:text-white mb-1">Global Live Tracking</div>
                <div class="flex items-center gap-3 text-[9px] text-gray-600 dark:text-gray-300">
                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500 inline-block"></span> In-Transit</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span> Origin</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span> Destination</span>
                </div>
            </div>
            <div v-if="mapAlertCount > 0" class="px-2 py-1 bg-yellow-500/10 rounded-lg flex items-center gap-1.5">
                <span class="material-symbols-outlined text-yellow-500 text-[14px]">warning</span>
                <span class="text-[9px] font-bold text-yellow-600">{{ mapAlertCount }} Alert{{ mapAlertCount !== 1 ? 's' : '' }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { LMap, LMarker, LPopup, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    activeDrivers,
    globalMapCenter,
    globalMapZoom,
    globalTab,
    mapAlertCount,
    selected,
    store,
} = inject(vendorTrackingPageKey)
</script>
