<template>
    <div ref="mapPanelRef"
        class="glass-panel rounded-xl overflow-hidden transition-all duration-700"
        :class="mapFocusFlash ? 'ring-2 ring-green-500/30 shadow-lg shadow-green-500/10' : ''">
        <div class="h-[24rem] sm:h-[30rem] lg:h-[34rem] relative z-0 rounded-t-xl overflow-hidden">
            <l-map ref="mapRef" v-model:zoom="zoom" :center="mapCenter" :use-global-leaflet="false">
                <l-tile-layer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    layer-type="base"
                    name="CartoDB Voyager"
                ></l-tile-layer>

                <!-- ── Route polylines ── -->
                <!-- In Transit: warehouse → pickup -->
                <l-polyline
                    v-if="warehouseToPickupCoords.length > 0 && activeMove?.status !== 'delivered'"
                    :lat-lngs="warehouseToPickupCoords"
                    color="#f59e0b"
                    :weight="4"
                    :opacity="0.6"
                    dash-array="10, 6"
                />
                <!-- In Transit: pickup → destination -->
                <l-polyline
                    v-if="pickupToDestCoords.length > 0 && activeMove?.status !== 'delivered'"
                    :lat-lngs="pickupToDestCoords"
                    color="#3b82f6"
                    :weight="4"
                    :opacity="0.7"
                    dash-array="12, 6"
                />
                <!-- Delivered blueprint: warehouse → pickup glow -->
                <l-polyline
                    v-if="warehouseToPickupCoords.length > 0 && activeMove?.status === 'delivered'"
                    :lat-lngs="warehouseToPickupCoords"
                    color="#fcd34d"
                    :weight="10"
                    :opacity="0.2"
                />
                <!-- Delivered blueprint: warehouse → pickup -->
                <l-polyline
                    v-if="warehouseToPickupCoords.length > 0 && activeMove?.status === 'delivered'"
                    :lat-lngs="warehouseToPickupCoords"
                    color="#f59e0b"
                    :weight="5"
                    :opacity="0.9"
                />
                <!-- Delivered blueprint: pickup → destination glow -->
                <l-polyline
                    v-if="pickupToDestCoords.length > 0 && activeMove?.status === 'delivered'"
                    :lat-lngs="pickupToDestCoords"
                    color="#6ee7b7"
                    :weight="12"
                    :opacity="0.25"
                />
                <!-- Delivered blueprint: pickup → destination -->
                <l-polyline
                    v-if="pickupToDestCoords.length > 0 && activeMove?.status === 'delivered'"
                    :lat-lngs="pickupToDestCoords"
                    color="#10b981"
                    :weight="6"
                    :opacity="0.9"
                />

                <!-- ── Warehouse pin (W) ── -->
                <l-marker v-if="warehouseCoords" :lat-lng="warehouseCoords" :icon="warehouseIcon">
                    <l-popup>
                        <div class="text-xs p-1 min-w-[160px]">
                            <div class="font-bold text-amber-700 flex items-center gap-1 mb-1">
                                <span class="material-symbols-outlined text-[14px]">warehouse</span>
                                Warehouse
                            </div>
                            <div class="text-gray-900 font-medium leading-snug">{{ activeMove?.warehouseName || 'Assigned Warehouse' }}</div>
                            <div class="text-gray-600 leading-snug mt-1">{{ activeMove?.warehouseAddress }}</div>
                        </div>
                    </l-popup>
                </l-marker>

                <!-- ── Pickup pin (A) ── -->
                <l-marker v-if="pickupCoords" :lat-lng="pickupCoords" :icon="pickupIcon">
                    <l-popup>
                        <div class="text-xs p-1 min-w-[140px]">
                            <div class="font-bold text-green-700 flex items-center gap-1 mb-1">
                                <span class="material-symbols-outlined text-[14px]">home</span>
                                Pickup Location
                            </div>
                            <div class="text-gray-600 leading-snug">{{ activeMove?.pickup }}</div>
                        </div>
                    </l-popup>
                </l-marker>

                <!-- ── Destination pin (B) ── -->
                <l-marker v-if="destCoords" :lat-lng="destCoords" :icon="destIcon">
                    <l-popup>
                        <div class="text-xs p-1 min-w-[140px]">
                            <div class="font-bold text-red-700 flex items-center gap-1 mb-1">
                                <span class="material-symbols-outlined text-[14px]">flag</span>
                                Destination
                            </div>
                            <div class="text-gray-600 leading-snug">{{ activeMove?.destination }}</div>
                        </div>
                    </l-popup>
                </l-marker>

                <!-- ── Live driver truck (only when in transit) ── -->
                <l-marker
                    v-if="trackingDriver?.latitude && activeMove?.status !== 'delivered'"
                    :lat-lng="[trackingDriver.latitude, trackingDriver.longitude]"
                    :icon="driverIcon">
                    <l-popup>
                        <div class="text-xs p-1">
                            <div class="font-bold flex items-center gap-1 mb-1">
                                <span class="material-symbols-outlined text-[14px] text-blue-500">local_shipping</span>
                                {{ trackingDriver.driver_name }}
                            </div>
                            <div class="text-gray-500 mb-0.5">Vehicle: <span class="text-gray-900 font-medium whitespace-nowrap">{{ trackingDriver.vehicle_code || activeMove?.vehicleType }}</span></div>
                            <div class="text-gray-500 mt-1 uppercase text-[9px] font-bold bg-gray-100 rounded px-1.5 py-0.5 inline-block">
                                {{ trackingDriver.status }}
                            </div>
                        </div>
                    </l-popup>
                </l-marker>
            </l-map>

            <!-- Route loading overlay -->
            <div v-if="routeLoading"
                class="absolute inset-0 flex items-end justify-center pb-4 pointer-events-none z-10">
                <div class="bg-black/70 text-white text-[11px] font-medium px-3 py-1.5 rounded-full flex items-center gap-2">
                    <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    Plotting route…
                </div>
            </div>

            <!-- ETA overlay (left) -->
            <div class="absolute top-3 left-3 z-[1000] bg-white/90 dark:bg-black/80 backdrop-blur-sm px-4 py-2 rounded-lg shadow-sm">
                <div class="text-[10px] text-gray-500 uppercase font-bold">
                    {{ activeMove?.status === 'delivered' ? 'Status' : 'ETA' }}
                </div>
                <div class="text-lg font-bold"
                    :class="activeMove?.status === 'delivered' ? 'text-emerald-600 dark:text-emerald-400' : 'text-green-600 dark:text-green-400'">
                    {{ activeMove?.status === 'delivered' ? 'Delivered ✓' : (activeMove.eta || 'Calculating...') }}
                </div>
            </div>

            <!-- Progress overlay (right) -->
            <div class="absolute top-3 right-3 z-[1000] bg-white/90 dark:bg-black/80 backdrop-blur-sm px-4 py-2 rounded-lg shadow-sm">
                <div class="text-[10px] text-gray-500 uppercase font-bold">Progress</div>
                <div class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ activeMove.progress }}%</div>
            </div>

            <!-- Route legend -->
            <div v-if="routeLegendItems.length > 0"
                class="absolute top-[4.85rem] right-3 z-[1000] bg-white/95 dark:bg-black/85 backdrop-blur-sm px-3 py-2 rounded-lg shadow-sm max-w-[220px] border border-white/60 dark:border-white/10">
                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1.5">Route Guide</div>
                <div class="space-y-1.5">
                    <div v-for="item in routeLegendItems" :key="item.key"
                        class="flex items-center gap-2 text-[11px] text-gray-700 dark:text-gray-200">
                        <span class="w-7 shrink-0 border-t-[3px] rounded-full"
                            :style="{
                                borderTopColor: item.color,
                                borderTopStyle: item.dashed ? 'dashed' : 'solid',
                                opacity: item.opacity,
                            }"></span>
                        <span class="leading-tight">{{ item.label }}</span>
                    </div>
                </div>
            </div>

            <!-- Delivered: route blueprint banner -->
            <div v-if="activeMove?.status === 'delivered' && routeCoords.length > 0"
                class="absolute bottom-3 left-3 right-3 z-[1000] bg-emerald-700/90 backdrop-blur-sm text-white px-3 py-2 rounded-lg flex items-center gap-2 shadow-lg text-xs">
                <span class="material-symbols-outlined text-[18px] shrink-0">route</span>
                <span class="truncate">
                    <strong>Route Blueprint</strong> —
                    {{ routeBlueprintLabel }}
                </span>
                <span class="ml-auto bg-white/20 px-2 py-0.5 rounded-full font-bold shrink-0">{{ activeMove.progress }}%</span>
            </div>

            <!-- In transit geofence alert -->
            <div v-if="geofenceAlert && activeMove?.status !== 'delivered'"
                class="absolute bottom-3 left-3 right-3 z-[1000] bg-green-600 text-white px-4 py-3 rounded-lg flex items-center gap-3 animate-pulse shadow-lg">
                <span class="material-symbols-outlined">location_on</span>
                <div>
                    <div class="text-sm font-bold">Crew Arriving!</div>
                    <div class="text-xs">Your driver is within 50 meters of the pickup location.</div>
                </div>
            </div>
        </div>
        <div class="p-4 border-t border-gray-200 dark:border-white/5">
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
                <span>{{ routeStageLabels[0] }}</span>
                <span>{{ routeStageLabels[1] }}</span>
                <span>{{ routeStageLabels[2] }}</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                <div class="bg-green-500 h-full rounded-full transition-all duration-500"
                    :style="{ width: activeMove.progress + '%' }"></div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { LMap, LMarker, LPolyline, LPopup, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const {
    activeMove,
    destCoords,
    destIcon,
    driverIcon,
    geofenceAlert,
    mapCenter,
    mapFocusFlash,
    mapPanelRef,
    mapRef,
    pickupCoords,
    pickupIcon,
    pickupToDestCoords,
    routeBlueprintLabel,
    routeCoords,
    routeLegendItems,
    routeLoading,
    routeStageLabels,
    trackingDriver,
    warehouseCoords,
    warehouseIcon,
    warehouseToPickupCoords,
    zoom,
} = inject(customerTrackingPageKey)
</script>
