<template>
    <!-- Route Hero Card -->
    <div class="glass-panel rounded-2xl overflow-hidden">
        <!-- Map visualization - Real Leaflet Map -->
        <div class="relative h-52 overflow-hidden">
            <l-map :zoom="selectedMapZoom" :center="selectedMapCenter" :use-global-leaflet="false"
                style="position:absolute; inset:0; height:100%; width:100%;">
                <l-tile-layer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    layer-type="base"
                ></l-tile-layer>
                <!-- Driver live position -->
                <l-marker v-if="selectedHasLiveTracking && selected?.driverLat && selected?.driverLng"
                    :lat-lng="[selected.driverLat, selected.driverLng]">
                    <l-popup>
                        <div class="text-xs p-1">
                            <div class="font-bold flex items-center gap-1 mb-1">
                                <span class="material-symbols-outlined text-[14px] text-blue-500">local_shipping</span>
                                {{ selected.driver || 'Driver' }}
                            </div>
                            <div class="text-gray-500">Vehicle: <span class="font-medium text-gray-800">{{ selected.vehicle }}</span></div>
                            <div class="mt-1 text-[9px] uppercase font-bold bg-blue-100 text-blue-700 rounded px-1.5 py-0.5 inline-block">{{ selectedDriverMapStatusLabel }}</div>
                        </div>
                    </l-popup>
                </l-marker>
            </l-map>
            <div v-if="selectedIsDelivered" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none bg-slate-950/25" style="z-index:500;">
                <span class="material-symbols-outlined text-3xl text-green-400/90 mb-1">verified</span>
                <p class="text-green-100 text-xs font-semibold">Shipment delivered</p>
                <p class="text-white/60 text-[11px] mt-1">Live route tracking has ended for this order</p>
            </div>
            <div v-else-if="selectedIsCancelled" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none bg-slate-950/25" style="z-index:500;">
                <span class="material-symbols-outlined text-3xl text-red-300/80 mb-1">cancel</span>
                <p class="text-red-100 text-xs font-semibold">Shipment cancelled</p>
            </div>
            <!-- No GPS fallback -->
            <div v-else-if="!selectedHasLiveTracking" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style="z-index:500;">
                <span class="material-symbols-outlined text-3xl text-gray-400/50 mb-1">gps_off</span>
                <p class="text-gray-400/60 text-xs font-medium">Live GPS not available</p>
            </div>
            <!-- Origin label -->
            <div class="absolute top-3 left-3" style="z-index:1000;">
                <div class="bg-black/70 text-white text-[9px] px-2 py-1 rounded-lg whitespace-nowrap font-medium flex items-center gap-1.5 shadow">
                    <span class="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></span>{{ selected.origin }}
                </div>
            </div>
            <!-- Destination label -->
            <div class="absolute top-3 right-3" style="z-index:1000;">
                <div class="bg-black/70 text-white text-[9px] px-2 py-1 rounded-lg whitespace-nowrap font-medium flex items-center gap-1.5 shadow">
                    {{ selected.destination }}<span class="w-2 h-2 bg-red-400 rounded-full flex-shrink-0"></span>
                </div>
            </div>
            <!-- Arriving Soon badge -->
            <div v-if="selected.progress >= 80 && selected.statusKey !== 'delivered'"
                class="absolute bottom-3 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 animate-pulse shadow-lg shadow-green-500/30" style="z-index:1000;">
                <span class="material-symbols-outlined text-sm">my_location</span>
                Arriving in ~{{ Math.max(5, Math.round((100 - selected.progress) * 1.5)) }} min
            </div>
        </div>
        <!-- Progress strip -->
        <div class="px-6 py-4 flex items-center gap-4 border-t border-gray-100 dark:border-white/5">
            <div class="flex-1">
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400">Trip Progress</span>
                    <span class="text-sm font-black text-blue-600 dark:text-blue-400">{{ selected.progress }}%</span>
                </div>
                <div class="w-full h-2.5 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-700"
                        :style="{ width: selected.progress + '%' }"></div>
                </div>
            </div>
            <div class="text-right">
                <div class="text-[10px] text-gray-400 uppercase font-bold">ETA</div>
                <div class="text-sm font-bold" :class="selectedEtaClass">{{ selectedEtaLabel }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { LMap, LMarker, LPopup, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    selected,
    selectedDriverMapStatusLabel,
    selectedEtaClass,
    selectedEtaLabel,
    selectedHasLiveTracking,
    selectedIsCancelled,
    selectedIsDelivered,
    selectedMapCenter,
    selectedMapZoom,
} = inject(vendorTrackingPageKey)
</script>
