<template>
    <!-- Live Tracking Modal -->
    <Teleport to="body">
    <div v-if="showTrackingModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)">
        <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-md m-4 overflow-hidden">

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-400 text-[20px] animate-pulse">gps_fixed</span>
                    <div>
                        <div class="text-sm font-bold text-white">Live Tracking</div>
                        <div class="text-[10px] text-gray-400">{{ trackingMove?.title }} · {{ trackingMove?.id }}</div>
                    </div>
                </div>
                <button @click="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)" class="text-gray-500 hover:text-white transition-colors">
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            </div>

            <!-- No driver state -->
            <div v-if="!trackedDriver" class="px-5 py-10 text-center">
                <span class="material-symbols-outlined text-gray-600 text-[48px] block mb-3">location_off</span>
                <div class="text-gray-400 text-sm">No driver assigned or location unavailable.</div>
                <div class="text-gray-500 text-xs mt-1">Assign a driver to this move to enable live tracking.</div>
            </div>

            <!-- Driver has location -->
            <div v-else>
                <!-- Driver info bar -->
                <div class="flex items-center gap-3 px-5 py-3 bg-white/5 border-b border-white/5">
                    <span class="w-2.5 h-2.5 rounded-full flex-shrink-0 ring-2 ring-offset-1 ring-offset-gray-900"
                        :class="trackedDriver.status?.toLowerCase() === 'active' ? 'bg-green-500 ring-green-500/40' : 'bg-yellow-500 ring-yellow-500/40'"></span>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-bold text-white truncate">{{ trackedDriver.driver_name }}</div>
                        <div class="text-xs text-gray-400 capitalize">{{ trackedDriver.status }} · {{ trackedDriver.vehicle_code || 'No vehicle' }}</div>
                    </div>
                    <div class="text-[10px] text-gray-500 text-right">
                        <div>Last updated</div>
                        <div class="text-gray-300 font-medium">{{ trackedDriver.last_updated ? new Date(trackedDriver.last_updated).toLocaleTimeString() : '—' }}</div>
                    </div>
                </div>

                <!-- Leaflet map with driver marker -->
                <div v-if="trackedDriver.latitude && trackedDriver.longitude" class="h-56">
                    <l-map :zoom="14" :center="[trackedDriver.latitude, trackedDriver.longitude]" :use-global-leaflet="false" style="height:100%;width:100%;">
                        <l-tile-layer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
                        <l-marker
                            :lat-lng="[trackedDriver.latitude, trackedDriver.longitude]"
                            :icon="driverMapIcon"
                        >
                            <l-tooltip :permanent="true" direction="top" :offset="[0, -26]">
                                <span style="font-size:11px;font-weight:700;">{{ trackedDriver.driver_name }}</span>
                            </l-tooltip>
                        </l-marker>
                        <!-- Delivery destination marker -->
                        <l-circle-marker
                            v-if="trackingMove?.deliveryLat && trackingMove?.deliveryLng"
                            :lat-lng="[trackingMove.deliveryLat, trackingMove.deliveryLng]"
                            :radius="8"
                            color="#ef4444"
                            fill-color="#ef4444"
                            :fill-opacity="0.9"
                            :weight="2"
                        >
                            <l-tooltip :permanent="true" direction="top" :offset="[0,-12]">
                                <span style="font-size:10px;">Drop-off</span>
                            </l-tooltip>
                        </l-circle-marker>
                    </l-map>
                </div>
                <!-- No GPS yet -->
                <div v-else class="h-32 flex items-center justify-center bg-white/5">
                    <div class="text-center">
                        <span class="material-symbols-outlined text-gray-500 text-[32px] block mb-1">location_searching</span>
                        <div class="text-xs text-gray-400">Waiting for GPS signal…</div>
                    </div>
                </div>

                <!-- Route info -->
                <div class="px-5 py-3 flex items-center gap-3 border-t border-white/5">
                    <div class="flex flex-col items-center gap-1">
                        <span class="w-2 h-2 rounded-full bg-green-500"></span>
                        <div class="w-px h-5 bg-gray-600"></div>
                        <span class="w-2 h-2 rounded-full bg-red-500"></span>
                    </div>
                    <div class="flex-1 space-y-2 text-xs">
                        <div class="text-gray-400 truncate"><span class="text-gray-500">From:</span> {{ trackingMove?.pickup }}</div>
                        <div class="text-gray-400 truncate"><span class="text-gray-500">To:</span> {{ trackingMove?.delivery }}</div>
                    </div>
                </div>
            </div>

            <div class="px-5 pb-4">
                <button @click="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)"
                    class="w-full bg-white/10 hover:bg-white/15 text-white py-2.5 rounded-xl text-sm font-bold transition-colors">
                    Close
                </button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { LCircleMarker, LMap, LMarker, LTileLayer, LTooltip } from '@vue-leaflet/vue-leaflet'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const { driverMapIcon, showTrackingModal, trackedDriver, trackingMove } = inject(serviceMovesPageKey)
</script>
