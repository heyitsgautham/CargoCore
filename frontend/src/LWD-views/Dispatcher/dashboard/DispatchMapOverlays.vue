<template>
    <!-- Driver markers — color-coded by live status -->
    <l-marker v-for="driver in activeDrivers" :key="driver.driver_id" :lat-lng="[driver.latitude, driver.longitude]" :icon="getDriverIcon(getActiveDriverStatusColor(driver))">
        <l-tooltip :permanent="false" direction="top">
            <div class="text-xs min-w-[160px]">
                <div class="font-bold flex items-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-[13px] text-green-500">local_shipping</span>
                    {{ driver.driver_name }}
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-600 font-semibold">
                        ✓ {{ driverDeliveryMetrics.get(String(driver.driver_id))?.delivered ?? 0 }} Delivered
                    </span>
                    <span class="text-amber-500 font-semibold">
                        ⏳ {{ driverDeliveryMetrics.get(String(driver.driver_id))?.pending ?? 0 }} Pending
                    </span>
                </div>
            </div>
        </l-tooltip>
        <l-popup>
            <div class="text-xs p-1">
                <div class="font-bold flex items-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-[14px] text-green-500">local_shipping</span>
                    {{ driver.driver_name }}
                </div>
                <div class="text-gray-500 mb-0.5">Vehicle: <span class="text-gray-900 font-medium">{{ driver.vehicle_code }}</span></div>
                <div class="text-gray-500 mb-0.5">Status: <span class="font-medium" :class="driver.status === 'in-transit' ? 'text-blue-600' : 'text-green-600'">{{ driver.status }}</span></div>
                <div v-if="driver.last_updated" class="text-gray-400 text-[9px]">Updated: {{ new Date(driver.last_updated).toLocaleTimeString('en-IN', {hour:'2-digit',minute:'2-digit'}) }}</div>
            </div>
        </l-popup>
    </l-marker>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- ESSENTIAL: Hub/Warehouse Markers (always visible when toggled) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.hubs">
        <l-marker 
            v-for="hub in mappableHubs" 
            :key="'hub-' + hub.id" 
            :lat-lng="[hub.lat, hub.lng]"
            :icon="hubIcon"
        >
            <l-popup>
                <div class="text-xs p-1 min-w-[140px]">
                    <div class="font-bold flex items-center gap-1 mb-1 text-indigo-700">
                        <span class="material-symbols-outlined text-[14px]">warehouse</span>
                        {{ hub.name }}
                    </div>
                    <div class="text-gray-500 mb-0.5">{{ hub.address || hub.location || 'Hub Location' }}</div>
                    <div class="text-gray-500 text-[10px]">Vehicles: {{ hub.vehiclesActive || 0 }}/{{ hub.vehiclesTotal || 0 }}</div>
                    <div class="text-gray-500 text-[10px]">Staff: {{ hub.staffActive || 0 }}/{{ hub.staffTotal || 0 }}</div>
                </div>
            </l-popup>
        </l-marker>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- ESSENTIAL: Pickup Point Markers (pending orders awaiting dispatch) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.pickups">
        <l-marker
            v-for="pickup in pickupLocations"
            :key="'pickup-' + pickup.id"
            :lat-lng="[pickup.lat, pickup.lng]"
            :icon="getPickupIcon(pickup.priority)"
        >
            <l-tooltip :permanent="false" direction="top">
                <div class="text-xs">
                    <div class="font-bold">Pickup • Order #{{ pickup.orderId }}</div>
                    <div class="text-gray-500">{{ pickup.type }} • {{ pickup.weight }}kg</div>
                    <div class="text-gray-400">{{ pickup.locationLabel }}</div>
                </div>
            </l-tooltip>
            <l-popup>
                <div class="text-xs p-1 min-w-[170px]">
                    <div class="font-bold flex items-center gap-1 mb-1 text-cyan-700">
                        <span class="material-symbols-outlined text-[14px]">inventory_2</span>
                        Pickup • Order #{{ pickup.orderId }}
                    </div>
                    <div class="text-gray-500 mb-1">{{ pickup.locationLabel }}</div>
                    <div class="text-gray-500 text-[10px]">{{ pickup.type }} • {{ pickup.weight }}kg</div>
                </div>
            </l-popup>
        </l-marker>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- OPTIONAL: Delivery Destination Markers -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.destinations || mapLayers.routes">
        <l-marker
            v-for="order in ordersWithDeliveryCoords"
            :key="'dest-' + order.id"
            :lat-lng="[order.resolvedDeliveryLat, order.resolvedDeliveryLng]"
            :icon="getDestinationIcon(order.status)"
        >
            <l-popup>
                <div class="text-xs p-1 min-w-[130px]">
                    <div class="font-bold flex items-center gap-1 mb-1">
                        <span class="material-symbols-outlined text-[14px] text-orange-500">package_2</span>
                        Order #{{ order.id }}
                    </div>
                    <div class="text-gray-500 mb-0.5">{{ order.deliveryAddr || 'Delivery Location' }}</div>
                    <div class="text-gray-500 text-[10px]">Driver: {{ order.driver }}</div>
                    <div class="text-[10px] font-medium" :class="order.status === 'IN_TRANSIT' ? 'text-blue-600' : order.status === 'DELIVERED' ? 'text-green-600' : 'text-orange-600'">
                        {{ order.status }}
                    </div>
                </div>
            </l-popup>
        </l-marker>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- OPTIONAL: Alert/Crisis Zones -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.alerts">
        <l-circle
            v-for="crisis in mappableCrises"
            :key="'crisis-' + crisis.id"
            :lat-lng="[crisis.lat, crisis.lng]"
            :radius="1500"
            :options="{
                color: crisis.level === 'CRITICAL' ? '#dc2626' : crisis.level === 'HIGH' ? '#f97316' : '#eab308',
                fillColor: crisis.level === 'CRITICAL' ? '#dc2626' : crisis.level === 'HIGH' ? '#f97316' : '#eab308',
                fillOpacity: 0.25,
                weight: 3,
                dashArray: crisis.level === 'CRITICAL' ? '' : '8 4'
            }"
        >
            <l-tooltip :permanent="true" direction="top">
                <div class="text-xs">
                    <div class="font-bold flex items-center gap-1" :class="crisis.level === 'CRITICAL' ? 'text-red-600' : crisis.level === 'HIGH' ? 'text-orange-600' : 'text-yellow-600'">
                        <span class="material-symbols-outlined text-[12px]">warning</span>
                        {{ crisis.title }}
                    </div>
                    <div class="text-gray-500 text-[10px]">{{ crisis.description }}</div>
                </div>
            </l-tooltip>
        </l-circle>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- OPTIONAL: Geofence Zones -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.zones">
        <l-circle
            v-for="zone in mappableZones"
            :key="'zone-' + zone.id"
            :lat-lng="[zone.lat, zone.lng]"
            :radius="(parseFloat(zone.radius) || 1) * 1000"
            :options="{ 
                color: getZoneColor(zone.color), 
                fillColor: getZoneColor(zone.color), 
                fillOpacity: 0.12, 
                weight: 2,
                dashArray: zone.type === 'Exclusion' ? '8 5' : ''
            }"
        >
            <l-tooltip :permanent="false" direction="top">
                <div class="text-xs">
                    <div class="font-semibold">{{ zone.name }}</div>
                    <div class="text-gray-500">{{ zone.type }} • {{ zone.radius }}km</div>
                </div>
            </l-tooltip>
        </l-circle>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- OPTIONAL: Route Lines (Driver to Delivery) -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.routes">
        <l-polyline
            v-for="route in driverOrderRoutes"
            :key="route.id"
            :lat-lngs="roadCoords[route.id] || [route.from, route.to]"
            :options="{
                color: route.status === 'IN_TRANSIT' ? '#3b82f6' : '#22c55e',
                weight: 4,
                opacity: 0.85,
                dashArray: roadCoords[route.id]?.length > 2 ? null : '10 6'
            }"
        >
            <l-tooltip :permanent="false">
                <div class="text-xs">Order #{{ route.orderId }} • {{ route.destinationLabel }}</div>
            </l-tooltip>
            <l-popup>
                <div class="text-xs p-1 min-w-[190px]">
                    <div class="font-bold text-gray-900 mb-2">Order #{{ route.orderId }}</div>
                    <div class="text-gray-500 uppercase tracking-wide text-[9px] mb-0.5">Driver Current Location</div>
                    <div class="text-gray-900 font-medium">{{ route.driverName }}</div>
                    <div class="text-gray-500 mb-2">{{ route.driverLocationLabel }}</div>
                    <div class="text-gray-500 uppercase tracking-wide text-[9px] mb-0.5">Unloading Destination</div>
                    <div class="text-gray-900 font-medium">{{ route.destinationLabel }}</div>
                    <div class="mt-2 text-[10px] font-semibold" :class="route.status === 'IN_TRANSIT' ? 'text-blue-600' : 'text-emerald-600'">
                        {{ route.status }}
                    </div>
                </div>
            </l-popup>
        </l-polyline>
    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- NICE-TO-HAVE: ETA Coverage Circles -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="mapLayers.eta">
        <l-circle
            v-for="driver in activeDrivers"
            :key="'eta-' + driver.driver_id"
            :lat-lng="[driver.latitude, driver.longitude]"
            :radius="etaFor(driver).radiusMeters"
            :options="{
                color: etaFor(driver).reachableCount > 0 ? '#22c55e' : '#f59e0b',
                fillColor: etaFor(driver).reachableCount > 0 ? '#22c55e' : '#f59e0b',
                fillOpacity: 0.08,
                weight: 1,
                dashArray: '4 4'
            }"
        >
            <l-tooltip :permanent="false">
                <div class="text-xs">
                    <div :class="etaFor(driver).reachableCount > 0 ? 'text-green-600' : 'text-amber-600'">
                        {{ etaFor(driver).reachableCount }} reachable stops within {{ ETA_THRESHOLD_MINUTES }} min
                    </div>
                    <div class="text-gray-500">
                        Nearest {{ etaFor(driver).nearestKindLabel }}: {{ etaFor(driver).nearestLabel }}
                        <span v-if="etaFor(driver).nearestEtaMinutes"> • {{ etaFor(driver).nearestEtaMinutes }} min</span>
                    </div>
                </div>
            </l-tooltip>
            <l-popup>
                <div class="text-xs p-1 min-w-[190px]">
                    <div class="font-bold mb-1">{{ driver.driver_name || `Driver ${driver.driver_id}` }}</div>
                    <div class="text-gray-500 mb-0.5">ETA coverage: {{ ETA_THRESHOLD_MINUTES }} minutes</div>
                    <div class="text-gray-500 mb-0.5">Speed baseline: {{ etaFor(driver).speedKmph }} km/h</div>
                    <div class="text-gray-500 mb-0.5">Reachable live stops: {{ etaFor(driver).reachableCount }}</div>
                    <div class="text-gray-500">
                        Nearest {{ etaFor(driver).nearestKindLabel }}: {{ etaFor(driver).nearestLabel }}
                        <span v-if="etaFor(driver).nearestEtaMinutes"> ({{ etaFor(driver).nearestEtaMinutes }} min)</span>
                    </div>
                </div>
            </l-popup>
        </l-circle>
    </template>

    <!-- Heatmap: semi-transparent circles at driver positions -->
    <template v-if="mapLayers.heatmap">
        <l-circle
            v-for="driver in activeDrivers"
            :key="'heat-' + driver.driver_id"
            :lat-lng="[driver.latitude, driver.longitude]"
            :radius="800"
            :options="{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.18, weight: 0 }"
        ></l-circle>
    </template>

    <!-- History: recent real GPS trail built from live polling -->
    <template v-if="mapLayers.history">
        <l-polyline
            v-for="trail in routeHistoryTrails"
            :key="'trail-' + trail.driverId"
            :lat-lngs="trail.points"
            :options="{ color: '#8b5cf6', weight: 2, opacity: 0.7, dashArray: '6 4' }"
        >
            <l-tooltip :permanent="false">
                <div class="text-xs">
                    <div class="text-violet-700 font-semibold">{{ trail.driverName }}</div>
                    <div class="text-gray-500">{{ trail.pointCount }} GPS samples</div>
                </div>
            </l-tooltip>
            <l-popup>
                <div class="text-xs p-1 min-w-[190px]">
                    <div class="font-bold text-gray-900 mb-1">{{ trail.driverName }}</div>
                    <div class="text-gray-500 mb-0.5">Recent GPS points: {{ trail.pointCount }}</div>
                    <div class="text-gray-500 mb-0.5">Last update: {{ trail.lastUpdatedLabel }}</div>
                    <div class="text-gray-500">Order context: {{ trail.orderLabel }}</div>
                </div>
            </l-popup>
        </l-polyline>
    </template>
</template>

<script setup>
import { LMarker, LPopup, LCircle, LPolyline, LTooltip } from '@vue-leaflet/vue-leaflet'
import { getActiveDriverStatusColor, getDestinationIcon, getDriverIcon, getPickupIcon, getZoneColor, hubIcon } from './mapHelpers'
import { ETA_THRESHOLD_MINUTES, emptyEtaCoverage } from './etaCoverage'

const props = defineProps({
    mapLayers: { type: Object, required: true },
    mappableHubs: { type: Array, required: true },
    pickupLocations: { type: Array, required: true },
    ordersWithDeliveryCoords: { type: Array, required: true },
    mappableCrises: { type: Array, required: true },
    mappableZones: { type: Array, required: true },
    driverOrderRoutes: { type: Array, required: true },
    roadCoords: { type: Object, required: true },
    activeDrivers: { type: Array, required: true },
    driverDeliveryMetrics: { type: Map, required: true },
    etaCoverageByDriver: { type: Object, required: true },
    routeHistoryTrails: { type: Array, required: true },
})

function etaFor(driver) {
    return props.etaCoverageByDriver[String(driver.driver_id)] || emptyEtaCoverage(driver)
}
</script>
