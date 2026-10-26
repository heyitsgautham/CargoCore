<template>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 glass-panel rounded-xl h-[400px] relative overflow-hidden">
            <!-- Real Leaflet map -->
            <l-map v-if="hasCrisisMapCenter" :zoom="crisisMapZoom" :center="crisisMapCenter" :use-global-leaflet="false" style="height:100%;width:100%;">
                <l-tile-layer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    layer-type="base"
                ></l-tile-layer>

                <!-- Live driver location markers (blue dots) -->
                <l-circle-marker
                    v-for="driver in activeDrivers"
                    :key="'driver-' + driver.driver_id"
                    :lat-lng="[driver.latitude, driver.longitude]"
                    :radius="8"
                    :options="getDriverMarkerOptions(driver)"
                >
                    <l-popup>
                        <div class="text-xs p-1 min-w-[140px]">
                            <div class="font-bold text-blue-500 mb-1 flex items-center gap-1">
                                <span class="inline-block w-2 h-2 rounded-full" :class="driver.status === 'active' ? 'bg-green-500' : 'bg-gray-400'"></span>
                                {{ driver.driver_name || driver.name || 'Driver' }}
                            </div>
                            <div class="text-gray-600">{{ driver.vehicle_code || 'No vehicle' }}</div>
                            <div class="text-gray-400 mt-1 text-[10px]">{{ driver.status || 'Unknown status' }}</div>
                        </div>
                    </l-popup>
                </l-circle-marker>

                <!-- Crisis incident markers (colored circle markers) -->
                <l-circle-marker
                    v-for="crisis in activeCrisesWithCoords"
                    :key="crisis.id"
                    :lat-lng="crisis.coords"
                    :radius="crisis.level === 'CRITICAL' ? 16 : 11"
                    :options="crisis.lat && crisis.lng
                        ? { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.95, weight: 3 }
                        : crisis.level === 'CRITICAL'
                            ? { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.75, weight: 2 }
                            : { color: '#eab308', fillColor: '#eab308', fillOpacity: 0.75, weight: 2 }"
                >
                    <l-popup>
                        <div class="text-xs p-1 min-w-[180px]">
                            <div class="font-bold mb-1" :class="crisis.level === 'CRITICAL' ? 'text-red-500' : 'text-yellow-500'">
                                {{ crisis.level }}: {{ crisis.title }}
                            </div>
                            <div class="text-gray-600">{{ crisis.description }}</div>
                            <div v-if="crisis.lat && crisis.lng" class="text-green-600 mt-1 text-[10px] font-bold">
                                📍 GPS: {{ crisis.lat.toFixed(4) }}, {{ crisis.lng.toFixed(4) }}
                            </div>
                            <div v-else class="text-orange-500 mt-1 text-[10px]">📍 Approx. location</div>
                            <div class="text-gray-400 mt-1 text-[10px]">{{ crisis.timeAgo }}</div>
                        </div>
                    </l-popup>
                </l-circle-marker>

                <!-- Disruption markers (lower severity, orange) -->
                <l-circle-marker
                    v-for="d in disruptionCrisesWithCoords"
                    :key="d.id"
                    :lat-lng="d.coords"
                    :radius="8"
                    :options="{ color: '#f97316', fillColor: '#f97316', fillOpacity: 0.7, weight: 1 }"
                >
                    <l-popup>
                        <div class="text-xs p-1">
                            <div class="font-bold text-orange-500 mb-1">{{ d.title }}</div>
                            <div class="text-gray-600">{{ d.detail }}</div>
                        </div>
                    </l-popup>
                </l-circle-marker>
            </l-map>
            <div v-else class="h-full flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-6 text-center">
                <div class="max-w-sm">
                    <div class="text-sm font-semibold text-gray-900 dark:text-white">Waiting for live operational coordinates</div>
                    <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">The crisis map will appear once alerts, live driver GPS, active order locations, or warehouse coordinates are available.</div>
                </div>
            </div>

            <!-- Overlay label -->
            <div v-if="hasCrisisMapCenter" class="absolute top-3 left-1/2 -translate-x-1/2 z-[400] pointer-events-none">
                <div class="bg-black/70 backdrop-blur border border-red-500/30 px-4 py-2 rounded-lg text-center">
                    <div class="text-red-400 font-bold text-sm">Live Crisis Map</div>
                    <div class="text-gray-400 text-[10px]">{{ activeCrises.length }} incidents • {{ activeDrivers.length }} drivers live • {{ approximateMarkerCount }} approximated</div>
                </div>
            </div>

            <!-- Weather overlay indicator -->
            <div v-if="weatherDisruptions.length" class="absolute bottom-4 right-4 z-[400] bg-white/90 dark:bg-black/80 backdrop-blur border border-gray-200 dark:border-white/10 rounded-lg p-3">
                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Weather Disruptions</div>
                <div v-for="wd in weatherDisruptions" :key="wd.id" class="flex items-center gap-2 text-xs text-yellow-400 mt-1">
                    <span class="material-symbols-outlined text-[16px]">thunderstorm</span> {{ wd.title }}
                </div>
            </div>
        </div>

        <!-- Re-Optimization Panel -->
        <div class="glass-panel rounded-xl p-6 flex flex-col">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">autorenew</span>
                Re-Optimization Engine
            </h3>
            <div class="space-y-3 flex-1">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Impacted Routes</div>
                    <div class="text-gray-900 dark:text-white font-bold text-xl">{{ activeCrises.length }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Orders to Reassign</div>
                    <div class="text-gray-900 dark:text-white font-bold text-xl">{{ activeCrises.reduce((sum, c) => sum + (c.affectedOrders?.length || 0), 0) || 0 }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Confirmed Orders With Destination GPS</div>
                    <div class="text-gray-900 dark:text-white font-bold text-xl">{{ reoptEligibleOrderCount }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Available Backup Drivers</div>
                    <div class="text-primary font-bold text-xl">{{ backupDriverCount }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Disruptions Detected</div>
                    <div class="text-yellow-400 font-bold text-xl">{{ disruptions.length }}</div>
                </div>

                <!-- Results after running -->
                <div v-if="reoptResult" class="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                    <div class="text-xs text-primary font-bold mb-2 flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">check_circle</span>
                        {{ reoptResult.routes.length }} routes optimized
                    </div>
                    <div v-for="r in reoptResult.routes" :key="r.driver_id" class="text-[11px] text-gray-700 dark:text-gray-300 flex justify-between py-0.5 border-b border-gray-200 dark:border-white/10 last:border-0">
                        <span class="truncate max-w-[120px]">{{ r.driver_name }}</span>
                        <span class="text-primary font-bold">{{ r.stops.length }} stops · {{ r.total_distance_km }} km</span>
                    </div>
                    <div v-if="reoptResult.error" class="text-xs text-red-400 mt-1">{{ reoptResult.error }}</div>
                </div>
            </div>
            <button @click="runReoptimization" :disabled="reoptRunning"
                class="mt-4 w-full bg-primary hover:bg-primary-dark text-black font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
                <span class="material-symbols-outlined" :class="{ 'animate-spin': reoptRunning }">{{ reoptRunning ? 'progress_activity' : 'bolt' }}</span>
                {{ reoptRunning ? 'Optimizing...' : 'Run Re-Optimization' }}
            </button>
            <div v-if="reoptRunning" class="mt-2 text-center text-xs text-primary animate-pulse">
                Fetching confirmed orders and building a recovery route plan...
            </div>
            <div class="mt-2 text-center text-[11px] text-gray-500 dark:text-gray-400">
                Uses confirmed orders only and builds a dispatcher recovery plan. It does not move in-transit jobs automatically.
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { LCircleMarker, LMap, LPopup, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { crisisPageKey } from './crisisPageContext'

const {
    activeCrises,
    activeCrisesWithCoords,
    activeDrivers,
    approximateMarkerCount,
    backupDriverCount,
    crisisMapCenter,
    crisisMapZoom,
    disruptionCrisesWithCoords,
    disruptions,
    getDriverMarkerOptions,
    hasCrisisMapCenter,
    reoptEligibleOrderCount,
    reoptResult,
    reoptRunning,
    runReoptimization,
    weatherDisruptions,
} = inject(crisisPageKey)
</script>
