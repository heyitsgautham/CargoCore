<template>
    <!-- Live Fleet Map (Takes up 2 columns) -->
    <div class="lg:col-span-2 glass-panel rounded-2xl p-0 overflow-hidden flex flex-col relative group">
        <div class="absolute top-4 left-4 z-10 glass-panel px-3 py-1 rounded-full flex items-center gap-2" style="z-index:1000">
            <span class="w-2 h-2 rounded-full animate-pulse" :class="wsConnected ? 'bg-green-500' : 'bg-yellow-500'"></span>
            <span class="text-xs font-semibold text-gray-900 dark:text-white">LIVE FLEET VIEW</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ liveDrivers.length }} active</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" :class="wsConnected ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                {{ wsConnected ? 'WS' : 'POLL' }}
            </span>
        </div>

        <!-- Real Leaflet Map -->
        <div class="flex-1 relative" style="min-height:0">
            <l-map
                ref="fleetMap"
                :zoom="fleetMapZoom"
                :center="fleetMapCenter"
                :use-global-leaflet="false"
                style="height:100%;width:100%;z-index:1"
                @ready="onMapReady"
            >
                <l-tile-layer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    layer-type="base"
                    name="CartoDB Voyager"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                />
                <l-marker
                    v-for="driver in liveDrivers"
                    :key="driver.driver_id"
                    :lat-lng="[driver.latitude, driver.longitude]"
                    :icon="getDriverIcon(driver)"
                >
                    <l-popup>
                        <div style="min-width:140px">
                            <div style="font-weight:700;font-size:13px;margin-bottom:4px">{{ driver.driver_name }}</div>
                            <div style="font-size:11px;color:#6b7280;text-transform:capitalize">{{ driver.status }}</div>
                            <div v-if="driver.vehicle_code" style="font-size:11px;color:#6b7280">Vehicle: {{ driver.vehicle_code }}</div>
                            <div v-if="driver.last_updated" style="font-size:10px;color:#9ca3af;margin-top:4px">
                                Updated {{ new Date(driver.last_updated).toLocaleTimeString() }}
                            </div>
                        </div>
                    </l-popup>
                </l-marker>
            </l-map>

            <!-- Empty state overlay when no drivers have location -->
            <div v-if="liveDrivers.length === 0 && !fleetLoading"
                class="absolute inset-0 flex flex-col items-center justify-center bg-white/60 dark:bg-background-dark/60 pointer-events-none"
                style="z-index:2">
                <span class="material-symbols-outlined text-4xl text-gray-400 mb-2">local_shipping</span>
                <div class="text-sm text-gray-500 dark:text-gray-400">No active drivers with location data</div>
            </div>
        </div>

        <!-- Map Controls Overlay -->
        <div class="absolute bottom-4 right-4 flex flex-col gap-2" style="z-index:1000">
            <button @click="mapZoomIn"
                class="w-8 h-8 glass-panel rounded-lg flex items-center justify-center hover:bg-white/10 text-gray-700 dark:text-white transition-colors"><span
                    class="material-symbols-outlined text-[18px]">add</span></button>
            <button @click="mapZoomOut"
                class="w-8 h-8 glass-panel rounded-lg flex items-center justify-center hover:bg-white/10 text-gray-700 dark:text-white transition-colors"><span
                    class="material-symbols-outlined text-[18px]">remove</span></button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { LMap, LMarker, LPopup, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { lmDashboardPageKey } from './lmDashboardPageContext'

const {
    fleetLoading,
    fleetMap,
    fleetMapCenter,
    fleetMapZoom,
    getDriverIcon,
    liveDrivers,
    mapZoomIn,
    mapZoomOut,
    onMapReady,
    wsConnected,
} = inject(lmDashboardPageKey)
</script>
