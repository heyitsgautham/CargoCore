<template>
  <div>
    <div class="flex h-[calc(94vh-3.5rem)] overflow-hidden">

        <!-- Left Panel: Active Driver Roster -->
        <transition name="slide-left">
        <div v-show="showLeftPanel" class="w-80 bg-white dark:bg-card-dark border-r border-gray-200 dark:border-white/5 flex flex-col z-10 glass-panel flex-shrink-0">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">{{ showAllDrivers ? 'All Drivers' : 'Available Drivers' }} ({{ filteredDrivers.length }})</h3>
                <button @click="showAllDrivers = !showAllDrivers" class="text-xs text-primary hover:underline">{{ showAllDrivers ? 'Show Available' : 'View All' }}</button>
            </div>

            <div class="p-3 bg-gray-50 dark:bg-white/5">
                <div class="relative">
                    <span
                        class="material-symbols-outlined absolute left-2 top-1.5 text-gray-500 text-[18px]">search</span>
                    <input v-model="driverSearch" type="text" placeholder="Search driver..."
                        class="w-full bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-md py-1.5 pl-8 pr-3 text-xs text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                </div>
            </div>

            <div class="flex-1 overflow-y-auto no-scrollbar p-2 space-y-2"
                @dragover.prevent="onDriverPanelDragOver" @drop="onDropOnDriverPanel">
                <!-- Driver Card -->
                <div v-for="driver in filteredDrivers" :key="driver.id"
                    @click="selectDriver(driver)"
                    :class="[
                        selectedDriver?.id === driver.id ? 'border-primary/50 bg-primary/5' : 'border-gray-200/60 dark:border-transparent',
                        dragOverDriver === driver.id ? 'ring-2 ring-primary/50 scale-[1.02]' : '',
                        driver.isAssignable ? 'hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-300 dark:hover:border-white/10 cursor-pointer' : 'opacity-70 cursor-not-allowed'
                    ]"
                    class="p-3 rounded-lg bg-gray-50 dark:bg-white/5 border transition-all group"
                    @dragover.prevent="onDriverDragOver($event, driver)" @dragleave="dragOverDriver = null"
                    @drop.stop="onDropOnDriver($event, driver)">
                    <div class="flex items-center gap-3 mb-2">
                        <div class="relative">
                            <img :src="driver.avatar" class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 object-cover">
                            <span class="absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white dark:border-card-dark"
                                :class="driver.statusColor"></span>
                        </div>
                        <div>
                            <button @click.stop="viewDriverDetail(driver)" class="text-sm font-semibold text-gray-900 dark:text-white hover:text-primary transition-colors text-left">{{ driver.name }}</button>
                            <div class="text-[10px] text-gray-400">{{ driver.vehicle }} • {{ driver.id }}</div>
                        </div>
                        <span v-if="!driver.isAssignable" class="ml-auto rounded-full bg-yellow-500/15 px-2 py-0.5 text-[10px] font-semibold text-yellow-600 dark:text-yellow-400">
                            {{ driver.busyReason || 'Busy' }}
                        </span>
                    </div>

                    <div class="grid grid-cols-2 gap-2 text-[10px]">
                        <div class="bg-gray-100 dark:bg-black/20 rounded px-2 py-1">
                            <span class="text-gray-500 block">Load</span>
                            <span class="text-gray-900 dark:text-white font-mono">{{ driver.load }}%</span>
                        </div>
                        <div class="bg-gray-100 dark:bg-black/20 rounded px-2 py-1">
                            <span class="text-gray-500 block">Hours Left</span>
                            <span class="text-gray-900 dark:text-white font-mono">{{ driver.hours }}h</span>
                        </div>
                    </div>

                    <div
                        class="mt-2 pt-2 border-t border-gray-200 dark:border-white/5 flex justify-between items-center opacity-70 group-hover:opacity-100 transition-opacity">
                        <span class="text-[10px] text-gray-400 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[12px]">location_on</span> {{ driver.location }}
                        </span>
                        <button @click.stop="chatWithDriver(driver)" class="text-primary hover:text-gray-900 dark:text-white transition-colors">
                            <span class="material-symbols-outlined text-[16px]">chat</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        </transition>

        <!-- Center Panel: Interactive Map -->
        <div class="flex-1 bg-gray-200 dark:bg-gray-900 relative">
            <!-- Live Leaflet Map -->
            <div class="absolute inset-0 z-0">
                <l-map v-if="hasMapCenter" ref="map" :zoom="mapZoom" :center="mapCenter" :use-global-leaflet="false">
                    <!-- Base tile layer — switches between light/dark when Layers is toggled -->
                    <l-tile-layer
                        v-if="!mapLayers.layers"
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        layer-type="base"
                        name="CartoDB Voyager"
                    ></l-tile-layer>
                    <l-tile-layer
                        v-else
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        layer-type="base"
                        name="CartoDB Dark"
                    ></l-tile-layer>

                    <!-- Traffic overlay tile layer -->
                    <l-tile-layer
                        v-if="mapLayers.traffic"
                        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                        layer-type="overlay"
                        name="OpenStreetMap"
                        :options="{ opacity: 0.35 }"
                    ></l-tile-layer>

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
                            :lat-lngs="osrmRouteCoords[route.id] || [route.from, route.to]"
                            :options="{
                                color: route.status === 'IN_TRANSIT' ? '#3b82f6' : '#22c55e',
                                weight: 4,
                                opacity: 0.85,
                                dashArray: osrmRouteCoords[route.id]?.length > 2 ? null : '10 6'
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
                            :radius="getEtaCoverage(driver).radiusMeters"
                            :options="{
                                color: getEtaCoverage(driver).reachableCount > 0 ? '#22c55e' : '#f59e0b',
                                fillColor: getEtaCoverage(driver).reachableCount > 0 ? '#22c55e' : '#f59e0b',
                                fillOpacity: 0.08,
                                weight: 1,
                                dashArray: '4 4'
                            }"
                        >
                            <l-tooltip :permanent="false">
                                <div class="text-xs">
                                    <div :class="getEtaCoverage(driver).reachableCount > 0 ? 'text-green-600' : 'text-amber-600'">
                                        {{ getEtaCoverage(driver).reachableCount }} reachable stops within {{ etaCoverageThresholdMinutes }} min
                                    </div>
                                    <div class="text-gray-500">
                                        Nearest {{ getEtaCoverage(driver).nearestKindLabel }}: {{ getEtaCoverage(driver).nearestLabel }}
                                        <span v-if="getEtaCoverage(driver).nearestEtaMinutes"> • {{ getEtaCoverage(driver).nearestEtaMinutes }} min</span>
                                    </div>
                                </div>
                            </l-tooltip>
                            <l-popup>
                                <div class="text-xs p-1 min-w-[190px]">
                                    <div class="font-bold mb-1">{{ driver.driver_name || `Driver ${driver.driver_id}` }}</div>
                                    <div class="text-gray-500 mb-0.5">ETA coverage: {{ etaCoverageThresholdMinutes }} minutes</div>
                                    <div class="text-gray-500 mb-0.5">Speed baseline: {{ getEtaCoverage(driver).speedKmph }} km/h</div>
                                    <div class="text-gray-500 mb-0.5">Reachable live stops: {{ getEtaCoverage(driver).reachableCount }}</div>
                                    <div class="text-gray-500">
                                        Nearest {{ getEtaCoverage(driver).nearestKindLabel }}: {{ getEtaCoverage(driver).nearestLabel }}
                                        <span v-if="getEtaCoverage(driver).nearestEtaMinutes"> ({{ getEtaCoverage(driver).nearestEtaMinutes }} min)</span>
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
                </l-map>
                <div v-else class="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-gray-900">
                    <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-white/90 dark:bg-black/40 backdrop-blur px-5 py-4 text-center shadow-lg">
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">Loading map data…</div>
                        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">Waiting for your warehouse or live order coordinates.</div>
                    </div>
                </div>
            </div>

            <!-- Map layer legend overlay when traffic is on -->
            <div v-if="mapLayers.traffic" class="absolute top-14 left-1/2 -translate-x-1/2 z-20 bg-white/90 dark:bg-black/80 backdrop-blur border border-amber-400/30 rounded-lg px-3 py-1.5 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 pointer-events-none">
                <span class="material-symbols-outlined text-[14px]">traffic</span>
                Traffic overlay active — live road data
            </div>

            <!-- Left Panel Toggle -->
            <button
                @click="showLeftPanel = !showLeftPanel"
                class="absolute top-4 left-4 z-20 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-md backdrop-blur-xl p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition-colors group"
                :title="showLeftPanel ? 'Hide Drivers' : 'Show Drivers'"
            >
                <span
                    class="material-symbols-outlined text-[18px]"
                    :class="showLeftPanel ? 'text-primary' : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'"
                >
                    {{ showLeftPanel ? 'left_panel_close' : 'left_panel_open' }}
                </span>
            </button>

            <!-- Right Panel Toggle -->
            <button
                @click="showRightPanel = !showRightPanel"
                class="absolute top-4 right-4 z-20 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-md backdrop-blur-xl p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition-colors group"
                :title="showRightPanel ? 'Hide Loads' : 'Show Loads'"
            >
                <span
                    class="material-symbols-outlined text-[18px]"
                    :class="showRightPanel ? 'text-primary' : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'"
                >
                    {{ showRightPanel ? 'right_panel_close' : 'right_panel_open' }}
                </span>
            </button>

            <!-- Bottom Map Toolbar - Expanded with new layers -->
            <div class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 shadow-lg backdrop-blur-xl p-2 rounded-xl flex gap-1 flex-wrap justify-center max-w-[600px]">
                <!-- Base layer controls -->
                <button @click="toggleMapLayer('layers')" :class="mapLayers.layers ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Dark Map"><span class="material-symbols-outlined">layers</span></button>
                <button @click="toggleMapLayer('traffic')" :class="mapLayers.traffic ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Traffic Overlay"><span class="material-symbols-outlined">traffic</span></button>
                
                <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>
                
                <!-- Essential layers -->
                <button @click="toggleMapLayer('hubs')" :class="mapLayers.hubs ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Hubs/Warehouses"><span class="material-symbols-outlined">warehouse</span></button>
                <button @click="toggleMapLayer('pickups')" :class="mapLayers.pickups ? 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Pickup Points"><span class="material-symbols-outlined">inventory_2</span></button>
                
                <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>
                
                <!-- Optional layers -->
                <button @click="toggleMapLayer('destinations')" :class="mapLayers.destinations ? 'bg-orange-500/15 text-orange-600 dark:text-orange-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Delivery Destinations"><span class="material-symbols-outlined">location_on</span></button>
                <button @click="toggleMapLayer('routes')" :class="mapLayers.routes ? 'bg-teal-500/15 text-teal-600 dark:text-teal-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Route Lines"><span class="material-symbols-outlined">route</span></button>
                <button @click="toggleMapLayer('alerts')" :class="mapLayers.alerts ? 'bg-red-500/15 text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Alert Zones"><span class="material-symbols-outlined">warning</span></button>
                <button @click="toggleMapLayer('zones')" :class="mapLayers.zones ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Geofence Zones"><span class="material-symbols-outlined">share_location</span></button>
                
                <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>
                
                <!-- Analysis layers -->
                <button @click="toggleMapLayer('heatmap')" :class="mapLayers.heatmap ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Driver Density Heatmap"><span class="material-symbols-outlined">blur_on</span></button>
                <button @click="toggleMapLayer('eta')" :class="mapLayers.eta ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="ETA Coverage"><span class="material-symbols-outlined">schedule</span></button>
                <button @click="toggleMapLayer('history')" :class="mapLayers.history ? 'bg-violet-500/15 text-violet-600 dark:text-violet-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Route History"><span class="material-symbols-outlined">history</span></button>
                
                <div class="w-[1px] h-8 bg-gray-300 dark:bg-white/10 mx-1"></div>
                
                <!-- Legend toggle -->
                <button @click="showMapLegend = !showMapLegend" :class="showMapLegend ? 'bg-gray-500/15 text-gray-700 dark:text-gray-300' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors" title="Map Legend"><span class="material-symbols-outlined">info</span></button>
            </div>

            <!-- Map Legend Overlay -->
            <transition name="fade">
            <div v-if="showMapLegend" class="absolute bottom-24 right-4 z-20 bg-white/95 dark:bg-black/90 backdrop-blur border border-gray-200 dark:border-white/10 rounded-xl shadow-xl p-4 w-64">
                <div class="flex justify-between items-center mb-3">
                    <h4 class="font-bold text-sm text-gray-900 dark:text-white">Map Legend</h4>
                    <button @click="showMapLegend = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
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
        </div>

        <!-- Right Panel: Pending Load Queue -->
        <transition name="slide-right">
        <div v-show="showRightPanel" class="w-80 bg-white dark:bg-card-dark border-l border-gray-200 dark:border-white/5 flex flex-col z-10 glass-panel flex-shrink-0">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Pending Loads ({{ pendingLoads.length }})</h3>
                <button @click="showAssignModal = true"
                    class="flex items-center gap-1 text-xs bg-primary text-black font-semibold px-2.5 py-1 rounded-md hover:bg-primary-dark transition-colors shadow-sm">
                    <span class="material-symbols-outlined text-[14px]">add</span> Assign
                </button>
            </div>

            <div class="flex-1 overflow-y-auto no-scrollbar p-2 space-y-3">
                <!-- Drag hint -->
                <div v-if="pendingLoads.length" class="flex items-center gap-1.5 px-2 py-1 text-[10px] text-gray-400">
                    <span class="material-symbols-outlined text-[12px]">drag_indicator</span>
                    Drag load to an available driver on the left to assign
                </div>
                <div v-for="load in pendingLoads" :key="load.id"
                    draggable="true" @dragstart="onDragStart($event, load)" @dragend="onDragEnd"
                    :class="[draggingLoad?.id === load.id ? 'opacity-50 scale-95 border-primary/40' : 'border-gray-200/60 dark:border-transparent hover:border-primary/30']"
                    class="p-3 rounded-lg bg-gray-50 dark:bg-white/5 border transition-all select-none cursor-grab active:cursor-grabbing">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-gray-400 text-[14px] cursor-grab">drag_indicator</span>
                            <span class="text-xs font-mono text-gray-500 dark:text-gray-400">#{{ load.id }}</span>
                        </div>
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold"
                            :class="load.priority === 'URGENT' ? 'bg-red-500/20 text-red-400' : load.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'">{{ load.priority }}</span>
                    </div>

                    <div class="space-y-2 mb-3">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-gray-500 text-[14px]">inventory_2</span>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ load.type }}</span>
                        </div>
                        <div class="flex justify-between text-[11px] text-gray-500 dark:text-gray-400">
                            <span>{{ load.weight }} kg</span>
                            <span>{{ load.volume }} m³</span>
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-white/5">
                        <div class="text-[10px] text-gray-500 dark:text-gray-400">Hub: <span class="text-gray-700 dark:text-gray-300 font-medium">{{ load.hub }}</span>
                        </div>
                        <button @click.stop="toggleLoadDetail(load)" class="text-xs font-bold px-2 py-0.5 rounded transition-colors"
                            :class="expandedLoad?.id === load.id ? 'bg-primary/10 text-primary' : 'text-primary hover:bg-primary/10'">{{ expandedLoad?.id === load.id ? 'Close' : 'Details' }}</button>
                    </div>
                    <div v-if="expandedLoad?.id === load.id" class="mt-2 pt-2 border-t border-gray-200 dark:border-white/5 space-y-2">
                        <div class="grid grid-cols-2 gap-2">
                            <div class="p-1.5 bg-gray-100 dark:bg-black/20 rounded text-[10px]">
                                <span class="text-gray-500 block">Origin</span>
                                <span class="text-gray-900 dark:text-white font-medium">{{ load.hub }} Warehouse</span>
                            </div>
                            <div class="p-1.5 bg-gray-100 dark:bg-black/20 rounded text-[10px]">
                                <span class="text-gray-500 block">Window (Today)</span>
                                <span class="text-gray-900 dark:text-white font-medium">{{ load.deadline ? new Date(load.deadline).toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', hour12:false}) : 'TBD' }}</span>
                            </div>
                        </div>
                        <div class="p-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded text-[10px] flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-yellow-400 text-[12px]">schedule</span>
                            <span class="text-yellow-600 dark:text-yellow-300 font-medium">Unassigned — Awaiting dispatch</span>
                        </div>
                        <button @click.stop="assignLoad(load)" class="w-full text-center bg-primary hover:bg-primary-dark text-black font-bold py-1.5 rounded-lg text-xs transition-colors flex items-center justify-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">assignment_turned_in</span>
                            Quick Assign
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom Summary -->
            <div class="p-4 border-t border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <div class="text-xs text-gray-500 mb-2">Overall SLA Projection</div>
                <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-1">
                    <div class="h-full bg-gradient-to-r from-yellow-500 to-green-500 transition-all" :style="{ width: slaProjection.pct + '%' }"></div>
                </div>
                <div class="flex justify-between text-[10px]">
                    <span class="text-gray-900 dark:text-white">{{ slaProjection.pct }}% Predicted</span>
                    <span :class="slaProjection.delta >= 0 ? 'text-green-400' : 'text-red-400'">{{ slaProjection.delta >= 0 ? '+' : '' }}{{ slaProjection.delta }}% vs Target</span>
                </div>
            </div>
        </div>
        </transition>

    </div>

    <!-- Assign Modal -->
    <Teleport to="body">
    <div v-if="showAssignModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showAssignModal = false">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-md m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">assignment_turned_in</span> Quick Assign Load
            </h3>
            <div class="mb-3">
                <label class="text-xs text-gray-400 mb-1 block">Select Order</label>
                <select v-model="assignOrderId" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Choose order...</option>
                    <option v-for="load in pendingLoads" :key="load.id" :value="load.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ load.id }} — {{ load.type }} ({{ load.weight }}kg)</option>
                </select>
            </div>
            <div class="mb-4">
                <label class="text-xs text-gray-400 mb-1 block">Select Driver</label>
                <select v-model="assignDriverId" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Choose driver...</option>
                    <option v-for="d in assignableDrivers" :key="d.id" :value="d.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ d.name }} ({{ d.vehicle }}, {{ d.load }}% load)</option>
                </select>
            </div>
            <div class="flex gap-2">
                <button @click="confirmAssign" :disabled="!assignOrderId || !assignDriverId || assigning"
                    class="flex-1 bg-primary text-black font-bold py-2 rounded-lg text-sm disabled:opacity-50 hover:bg-primary-dark transition-colors flex items-center justify-center gap-1">
                    <span v-if="assigning" class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                    {{ assigning ? 'Assigning...' : 'Assign' }}
                </button>
                <button @click="showAssignModal = false" :disabled="assigning" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors disabled:opacity-50">Cancel</button>
            </div>
            <div v-if="assignSuccess" class="mt-3 text-center text-xs text-green-400 font-bold">✓ Order assigned successfully!</div>
            <div v-if="assignError" class="mt-3 text-center text-xs text-red-400 font-bold">{{ assignError }}</div>
        </div>
    </div>
    </Teleport>

    <!-- Driver Detail Modal -->
    <Teleport to="body">
    <div v-if="showDriverDetailModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverDetailModal = false">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-md m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <div class="flex items-center gap-4 mb-5">
                <img :src="detailDriver?.avatar" class="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 ring-2 ring-primary/30 object-cover">
                <div>
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ detailDriver?.name }}</h3>
                    <p class="text-sm text-gray-500">{{ detailDriver?.vehicle }} • {{ detailDriver?.id }}</p>
                    <div class="flex items-center gap-1.5 mt-1">
                        <span class="w-2 h-2 rounded-full" :class="detailDriver?.statusColor"></span>
                        <span class="text-xs" :class="detailDriver?.statusColor === 'bg-green-500' ? 'text-green-500' : detailDriver?.statusColor === 'bg-yellow-500' ? 'text-yellow-500' : 'text-gray-500'">{{ detailDriver?.statusColor === 'bg-green-500' ? 'Active' : detailDriver?.statusColor === 'bg-yellow-500' ? 'Busy' : 'Offline' }}</span>
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-3 gap-3 mb-5">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Load</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ detailDriver?.load }}%</div>
                    <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full mt-1 overflow-hidden">
                        <div class="h-full rounded-full" :class="detailDriver?.load > 80 ? 'bg-red-500' : 'bg-primary'" :style="{ width: detailDriver?.load + '%' }"></div>
                    </div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Hours Left</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ detailDriver?.hours }}h</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Location</div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{{ detailDriver?.location }}</div>
                </div>
            </div>
            <div class="flex gap-2">
                <button @click="chatWithDriver(detailDriver); showDriverDetailModal = false" class="flex-1 bg-primary hover:bg-primary-dark text-black font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">chat</span> Chat
                </button>
                <button @click="assignToDriverFromDetail" class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-900 dark:text-white font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">add_circle</span> Assign Load
                </button>
                <button @click="showDriverDetailModal = false" class="px-4 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-400 py-2 rounded-lg text-sm transition-colors">
                    <span class="material-symbols-outlined text-[16px]">close</span>
                </button>
            </div>
        </div>
    </div>
    </Teleport>

    <!-- Drag Assign Toast -->
    <Teleport to="body">
    <transition name="fade">
    <div v-if="dragAssignToast" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[9999] bg-green-500 text-black font-bold px-6 py-3 rounded-xl shadow-xl flex items-center gap-2 text-sm">
        <span class="material-symbols-outlined text-[18px]">check_circle</span>
        {{ dragAssignToast }}
    </div>
    </transition>
    </Teleport>

    <!-- Chat Modal -->
    <Teleport to="body">
    <div v-if="showChatModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showChatModal = false">
        <div class="bg-white dark:bg-card-dark rounded-2xl w-full max-w-sm m-4 border border-gray-200 dark:border-white/10 shadow-2xl flex flex-col h-[400px]">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <img :src="chatDriver?.avatar" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700">
                    <div><div class="text-sm font-bold text-gray-900 dark:text-white">{{ chatDriver?.name }}</div><div class="text-[10px] text-gray-400">{{ chatDriver?.id }}</div></div>
                </div>
                <button @click="showChatModal = false" class="text-gray-400 hover:text-gray-900 dark:text-white"><span class="material-symbols-outlined">close</span></button>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar p-4 space-y-2">
                <div v-for="msg in driverChatMessages" :key="msg.id" :class="msg.from === 'dispatch' ? 'flex justify-end' : 'flex justify-start'">
                    <div class="max-w-[80%] p-2 rounded-xl text-xs" :class="msg.from === 'dispatch' ? 'bg-primary/20 text-gray-900 dark:text-white' : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300'">{{ msg.text }}</div>
                </div>
            </div>
            <div class="p-3 border-t border-gray-200 dark:border-white/5 flex gap-2">
                <input v-model="chatMsg" @keyup.enter="sendDriverMsg" type="text" placeholder="Type message..."
                    class="flex-1 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full px-3 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none">
                <button @click="sendDriverMsg" class="p-1.5 bg-primary rounded-full text-black"><span class="material-symbols-outlined text-[16px]">send</span></button>
            </div>
        </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import { useLogisticStore } from '@/stores/logisticStore'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import { apiUrl } from '@/config/api'
import { LMap, LTileLayer, LMarker, LPopup, LCircle, LPolyline, LTooltip } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix Leaflet icons issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

// ─── Inline-SVG DivIcons (Material Symbols font doesn't load inside Leaflet divIcon) ───

// Hub / Warehouse marker — indigo square with warehouse SVG
const hubIcon = L.divIcon({
    html: `<div style="background:#4f46e5;width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M1 11v11h22V11L12 2 1 11zm20 9H3v-8.5l9-7 9 7V20zm-9-6H8v5h6v-5z"/>
        </svg>
    </div>`,
    className: 'custom-hub-icon',
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
})

// Destination / delivery marker — stable orange location pin for route endpoints
function getDestinationIcon() {
    const color = '#f97316'
    return L.divIcon({
        html: `<div style="background:${color};width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
            </svg>
        </div>`,
        className: 'custom-dest-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    })
}

function getPickupIcon(priority) {
    const color = getPriorityColor(priority)
    return L.divIcon({
        html: `<div style="background:${color};width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v9c0 1.1.9 2 2 2h1a3 3 0 0 0 6 0h4a3 3 0 0 0 6 0h1c1.1 0 2-.9 2-2v-3l-3-4zM6 18.5A1.5 1.5 0 1 1 6 15.5a1.5 1.5 0 0 1 0 3zm11 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM17 12V9.5h2.5l1.96 2.5H17z"/>
            </svg>
        </div>`,
        className: 'custom-pickup-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    })
}

// Driver marker — color-coded by status with truck SVG
function getDriverIcon(statusColor) {
    // statusColor: 'bg-green-500' | 'bg-yellow-500' | 'bg-gray-500'
    let bg, border
    if (statusColor === 'bg-green-500') {
        bg = '#22c55e'; border = '#16a34a'
    } else if (statusColor === 'bg-yellow-500') {
        bg = '#eab308'; border = '#ca8a04'
    } else {
        bg = '#6b7280'; border = '#4b5563'
    }
    return L.divIcon({
        html: `<div style="background:${bg};width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid ${border};box-shadow:0 3px 10px rgba(0,0,0,0.4);">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white">
                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zm-.5 1.5 1.96 2.5H17V9.5h2.5zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
            </svg>
        </div>`,
        className: 'custom-driver-icon',
        iconSize: [34, 34],
        iconAnchor: [17, 17],
        popupAnchor: [0, -17],
    })
}

// Maps the raw status string from the tracking API to a Tailwind color token
function getActiveDriverStatusColor(driver) {
    const s = (driver.status || '').toLowerCase()
    if (s === 'active' || s === 'on_route' || s === 'on route' || s === 'in-transit' || s === 'in_transit') return 'bg-green-500'
    if (s === 'idle' || s === 'on_break' || s === 'on break') return 'bg-yellow-500'
    return 'bg-gray-500'
}

const { activeDrivers } = useRealTimeTracking()

const store = useDispatcherStore()
const authStore = useAuthStore()
const logisticStore = useLogisticStore()

const showLeftPanel = ref(false)
const showRightPanel = ref(false)
const driverSearch = ref('')
const showAllDrivers = ref(false)
const selectedDriver = ref(null)
const expandedLoad = ref(null)
const showAssignModal = ref(false)
const assignOrderId = ref('')
const assignDriverId = ref('')
const assignSuccess = ref(false)
const assigning = ref(false)
const assignError = ref('')
const showChatModal = ref(false)
const chatDriver = ref(null)
const chatMsg = ref('')
const mapLayers = ref({ 
    layers: false, 
    traffic: false, 
    heatmap: false, 
    history: false,
    // New optional toggles
    hubs: true,           // Essential - always on by default
    pickups: true,        // Essential - pending order pickup points
    destinations: true,   // Optional - delivery destinations (NOW ENABLED BY DEFAULT)
    alerts: false,        // Optional - crisis/alert zones
    zones: false,         // Optional - geofence zones
    routes: false,        // Optional - driver-to-order routes
    eta: false,           // Nice-to-have - ETA circles
    clusters: false,      // Nice-to-have - order clustering
})
const showDriverDetailModal = ref(false)
const detailDriver = ref(null)
const draggingLoad = ref(null)
const dragOverDriver = ref(null)
const dragAssignToast = ref('')
const showMapLegend = ref(false)

const drivers = computed(() => store.dispatcherDrivers)
const pendingLoads = computed(() => store.pendingOrders)
const slaProjection = computed(() => store.slaProjection)
const terminalOrderStatuses = new Set(['DELIVERED', 'CLOSED', 'CANCELLED'])

// Map data sources
const hubs = computed(() => store.hubs || [])
const activeOrders = computed(() => store.activeOrders || [])
const activeCrises = computed(() => store.activeCrises || [])
const zones = computed(() => store.filteredZones || [])
const geocodedOrderDestinations = ref({})
const geocodedOrderPickups = ref({})
const pendingDestinationLookups = new Set()
const pendingPickupLookups = new Set()

function hasValidCoordinate(value) {
    if (value === null || value === undefined || value === '') return false
    return Number.isFinite(Number(value))
}

function toCoordinatePair(lat, lng) {
    if (!hasValidCoordinate(lat) || !hasValidCoordinate(lng)) return null
    return [Number(lat), Number(lng)]
}

function getOrderDestinationLabel(order) {
    return order.deliveryAddr || `Order #${order.id} unloading point`
}

function getOrderPickupLabel(order) {
    return order.pickupAddr || `Order #${order.id} pickup point`
}

function getDriverLocationLabel(driver) {
    if (driver.location) return driver.location
    if (hasValidCoordinate(driver.latitude) && hasValidCoordinate(driver.longitude)) {
        return `${Number(driver.latitude).toFixed(5)}, ${Number(driver.longitude).toFixed(5)}`
    }
    return 'Live location unavailable'
}

function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function getResolvedDestinationCoords(order) {
    const directCoords = toCoordinatePair(order.deliveryLat, order.deliveryLng)
    if (directCoords) return directCoords
    const cachedCoords = geocodedOrderDestinations.value[order.id]
    return Array.isArray(cachedCoords) ? cachedCoords : null
}

function getResolvedPickupCoords(order) {
    const directCoords = toCoordinatePair(order.pickupLat, order.pickupLng)
    if (directCoords) return directCoords
    const cachedCoords = geocodedOrderPickups.value[order.id]
    return Array.isArray(cachedCoords) ? cachedCoords : null
}

function isMapVisibleOrder(order) {
    return !['DELIVERED', 'CLOSED', 'CANCELLED'].includes(String(order?.status || '').toUpperCase())
}

async function geocodeAddress(address) {
    const raw = String(address || '').trim()
    if (!raw) return null

    try {
        const response = await fetch(apiUrl(`api/v1/geocoding/search?q=${encodeURIComponent(raw)}&limit=1`))
        if (response.ok) {
            const data = await response.json()
            if (Array.isArray(data) && data[0]) {
                const coords = toCoordinatePair(data[0].lat, data[0].lon)
                if (coords) return coords
            }
        }
    } catch {}

    const queries = raw.toLowerCase().includes('india') ? [raw] : [raw, `${raw}, India`]
    for (const query of queries) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`, {
                headers: { 'Accept-Language': 'en' },
            })
            const data = await response.json()
            if (Array.isArray(data) && data[0]) {
                const coords = toCoordinatePair(data[0].lat, data[0].lon)
                if (coords) return coords
            }
        } catch {}
    }

    return null
}

async function ensureRouteDestinationCoords(order) {
    if (!order?.id || getResolvedDestinationCoords(order)) return
    const destinationLabel = getOrderDestinationLabel(order)
    if (!destinationLabel || pendingDestinationLookups.has(order.id)) return

    pendingDestinationLookups.add(order.id)
    try {
        const coords = await geocodeAddress(destinationLabel)
        if (coords) {
            geocodedOrderDestinations.value = {
                ...geocodedOrderDestinations.value,
                [order.id]: coords,
            }
        }
    } finally {
        pendingDestinationLookups.delete(order.id)
    }
}

async function ensurePickupCoords(order) {
    if (!order?.id || getResolvedPickupCoords(order)) return
    const pickupLabel = getOrderPickupLabel(order)
    if (!pickupLabel || pendingPickupLookups.has(order.id)) return

    pendingPickupLookups.add(order.id)
    try {
        const coords = await geocodeAddress(pickupLabel)
        if (coords) {
            geocodedOrderPickups.value = {
                ...geocodedOrderPickups.value,
                [order.id]: coords,
            }
        }
    } finally {
        pendingPickupLookups.delete(order.id)
    }
}

// Computed: Hubs with valid coordinates
const mappableHubs = computed(() => 
    hubs.value.filter(h => h.lat && h.lng && !isNaN(h.lat) && !isNaN(h.lng))
)

const scopedWarehouseHub = computed(() => {
    const explicitWarehouseId = String(logisticStore.activeWarehouse || 'all')
    const assignedWarehouseId = authStore.currentUser?.warehouse_id
        ? String(authStore.currentUser.warehouse_id)
        : null
    const targetWarehouseId = explicitWarehouseId !== 'all' ? explicitWarehouseId : assignedWarehouseId

    if (!targetWarehouseId) return null

    return mappableHubs.value.find((hub) => String(hub.id) === targetWarehouseId) || null
})

const liveMapOrders = computed(() => {
    const merged = new Map()

    for (const order of pendingLoads.value) {
        if (isMapVisibleOrder(order)) merged.set(String(order.id), order)
    }

    for (const order of activeOrders.value) {
        if (isMapVisibleOrder(order)) merged.set(String(order.id), order)
        else merged.delete(String(order.id))
    }

    return [...merged.values()]
})

// Computed: Orders with delivery coordinates
const ordersWithDeliveryCoords = computed(() => {
    const filtered = liveMapOrders.value
        .map((order) => {
            const coords = getResolvedDestinationCoords(order)
            if (!coords) return null
            return {
                ...order,
                resolvedDeliveryLat: coords[0],
                resolvedDeliveryLng: coords[1],
            }
        })
        .filter(Boolean)
    console.log('🗺️ ordersWithDeliveryCoords:', filtered.length, 'out of', activeOrders.value.length, 'total orders')
    if (filtered.length > 0) {
        console.log('Sample order:', filtered[0])
    }
    return filtered
})

// Computed: Crises with coordinates — falls back to hub/map-center when location is a non-coordinate string
const mappableCrises = computed(() => {
    const center = mapCenter.value || [0, 0]
    return activeCrises.value.map((c, i) => {
        if (c.lat && c.lng && !isNaN(c.lat) && !isNaN(c.lng)) return c
        // Spread alerts around the nearest hub (or map center) using golden-angle distribution
        const baseHub = mappableHubs.value[0]
        const baseLat = baseHub ? baseHub.lat : center[0]
        const baseLng = baseHub ? baseHub.lng : center[1]
        const angle = (i * 137.508) * (Math.PI / 180)   // golden angle keeps them well-spaced
        const dist = 0.03 + i * 0.02                     // ~3-5 km spacing
        return {
            ...c,
            lat: baseLat + Math.sin(angle) * dist,
            lng: baseLng + Math.cos(angle) * dist,
        }
    })
})

// Computed: Zones with coordinates
const mappableZones = computed(() =>
    zones.value.filter(z => z.lat && z.lng && !isNaN(z.lat) && !isNaN(z.lng) && z.radius)
)

// Dynamic map center - always use real operational data; never fall back to a hardcoded city.
const mapCenter = computed(() => {
    // First priority: assigned/current warehouse for this dispatcher
    if (scopedWarehouseHub.value) {
        return [scopedWarehouseHub.value.lat, scopedWarehouseHub.value.lng]
    }
    // Next best: first live customer pickup point
    if (firstPickupLocation.value) {
        return [firstPickupLocation.value.lat, firstPickupLocation.value.lng]
    }
    // Next best: first live unloading destination
    if (firstDestinationLocation.value) {
        return [firstDestinationLocation.value.resolvedDeliveryLat, firstDestinationLocation.value.resolvedDeliveryLng]
    }
    // Then: active driver GPS
    if (activeDrivers.value.length > 0) {
        const driver = activeDrivers.value.find(d => d.latitude && d.longitude)
        if (driver) {
            return [driver.latitude, driver.longitude]
        }
    }
    // Then: first hub with coordinates
    if (mappableHubs.value.length > 0) {
        const hub = mappableHubs.value[0]
        return [hub.lat, hub.lng]
    }
    // Then: first zone
    if (mappableZones.value.length > 0) {
        const zone = mappableZones.value[0]
        return [zone.lat, zone.lng]
    }
    return null
})

const hasMapCenter = computed(() => Array.isArray(mapCenter.value) && mapCenter.value.length === 2)

// Dynamic zoom level based on data availability
const mapZoom = computed(() => {
    // If we have the dispatcher's current warehouse, focus that area first
    if (scopedWarehouseHub.value) return 13
    if (firstPickupLocation.value || firstDestinationLocation.value) return 13
    // If we have hubs, zoom to city level
    if (mappableHubs.value.length > 0) return 13
    // If we have drivers, zoom closer
    if (activeDrivers.value.length > 0) return 12
    // Default zoom
    return 11
})

// Generate pickup locations from live orders using actual pickup coordinates only.
const pickupLocations = computed(() => {
    const locations = []
    for (const order of liveMapOrders.value) {
        const pickupCoords = getResolvedPickupCoords(order)
        if (pickupCoords) {
            locations.push({
                id: order.id,
                lat: pickupCoords[0],
                lng: pickupCoords[1],
                orderId: order.id,
                priority: order.priority,
                type: order.type,
                weight: order.weight,
                locationLabel: order.pickupAddr || order.hub || 'Customer Pickup',
            })
        }
    }
    return locations
})

const firstPickupLocation = computed(() => pickupLocations.value[0] || null)
const firstDestinationLocation = computed(() => ordersWithDeliveryCoords.value[0] || null)
const etaCoverageThresholdMinutes = 15
const etaCoverageByDriver = ref({})
let etaCoverageTimer = null
const DRIVER_TRAIL_STORAGE_KEY = 'dispatcher-driver-route-history-v1'
const DRIVER_TRAIL_RETENTION_MS = 6 * 60 * 60 * 1000
const DRIVER_TRAIL_MIN_SAMPLE_GAP_MS = 45 * 1000
const DRIVER_TRAIL_MIN_MOVE_KM = 0.08
const DRIVER_TRAIL_MAX_POINTS = 120
const driverTrailHistory = ref(loadDriverTrailHistory())

const etaTargets = computed(() => {
    const targets = []
    for (const order of liveMapOrders.value) {
        const pickupCoords = getResolvedPickupCoords(order)
        if (pickupCoords) {
            targets.push({
                id: `pickup-${order.id}`,
                orderId: order.id,
                kind: 'pickup',
                label: `Pickup • Order #${order.id}`,
                coords: pickupCoords,
            })
        }

        const destinationCoords = getResolvedDestinationCoords(order)
        if (destinationCoords) {
            targets.push({
                id: `delivery-${order.id}`,
                orderId: order.id,
                kind: 'delivery',
                label: `Unloading • Order #${order.id}`,
                coords: destinationCoords,
            })
        }
    }
    return targets
})

const driverOrderContextMap = computed(() => {
    const rank = { IN_TRANSIT: 0, ASSIGNED: 1, CONFIRMED: 2 }
    const mapped = new Map()

    for (const order of liveMapOrders.value) {
        if (!order.driverId) continue
        const driverId = String(order.driverId)
        const current = mapped.get(driverId)
        const nextRank = rank[String(order.status || '').toUpperCase()] ?? 99
        if (!current || nextRank < current.rank) {
            mapped.set(driverId, {
                rank: nextRank,
                orderId: order.id,
                status: order.status,
                label: order.deliveryAddr || order.pickupAddr || `Order #${order.id}`,
            })
        }
    }

    return mapped
})

const driverDeliveryMetrics = computed(() => {
    const metrics = new Map()
    for (const order of activeOrders.value) {
        if (!order.driverId) continue
        const id = String(order.driverId)
        if (!metrics.has(id)) metrics.set(id, { delivered: 0, pending: 0 })
        const m = metrics.get(id)
        if (String(order.status || '').toUpperCase() === 'DELIVERED') m.delivered++
        else m.pending++
    }
    return metrics
})

const routeHistoryTrails = computed(() => {
    const activeDriverMap = new Map(
        activeDrivers.value.map((driver) => [String(driver.driver_id), driver])
    )

    return Object.entries(driverTrailHistory.value)
        .map(([driverId, samples]) => {
            const activeDriver = activeDriverMap.get(driverId)
            if (!activeDriver || !Array.isArray(samples) || samples.length < 2) return null

            const points = samples
                .map((sample) => toCoordinatePair(sample.lat, sample.lng))
                .filter(Boolean)

            if (points.length < 2) return null

            const lastSample = samples[samples.length - 1]
            const lastUpdated = lastSample?.ts ? new Date(lastSample.ts) : null

            return {
                driverId,
                driverName: activeDriver.driver_name || `Driver ${driverId}`,
                points,
                pointCount: points.length,
                orderId: lastSample?.orderId || null,
                orderStatus: lastSample?.orderStatus || null,
                orderLabel: lastSample?.orderLabel || 'Recent route trail',
                lastUpdatedLabel: lastUpdated && !Number.isNaN(lastUpdated.getTime())
                    ? lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
                    : 'Unknown',
            }
        })
        .filter(Boolean)
})

function getDriverSpeedKmph(driver) {
    const reported = Number(driver.avg_speed ?? driver.avgSpeed ?? 0)
    return Number.isFinite(reported) && reported > 0 ? Math.max(18, reported) : 24
}

function getEtaCoverage(driver) {
    return etaCoverageByDriver.value[String(driver.driver_id)] || {
        radiusMeters: Math.max(1500, Math.round((getDriverSpeedKmph(driver) * (etaCoverageThresholdMinutes / 60)) * 1000)),
        reachableCount: 0,
        nearestEtaMinutes: null,
        nearestLabel: 'No live pickup or unloading points',
        nearestKindLabel: 'stop',
        speedKmph: getDriverSpeedKmph(driver),
        thresholdMinutes: etaCoverageThresholdMinutes,
        loading: false,
    }
}

function refreshEtaCoverage() {
    if (!mapLayers.value.eta) {
        etaCoverageByDriver.value = {}
        return
    }

    const driversWithCoords = activeDrivers.value.filter((driver) => toCoordinatePair(driver.latitude, driver.longitude))
    const targets = etaTargets.value
    const entries = driversWithCoords.map((driver) => {
        const driverKey = String(driver.driver_id)
        const speedKmph = getDriverSpeedKmph(driver)
        const defaultRadiusMeters = Math.max(1500, Math.round((speedKmph * (etaCoverageThresholdMinutes / 60)) * 1000))

        if (!targets.length) {
            return [driverKey, {
                radiusMeters: defaultRadiusMeters,
                reachableCount: 0,
                nearestEtaMinutes: null,
                nearestLabel: 'No live pickup or unloading points',
                nearestKindLabel: 'stop',
                speedKmph,
                thresholdMinutes: etaCoverageThresholdMinutes,
                loading: false,
            }]
        }

        const analyses = targets
            .map((target) => {
                const linearKm = haversineKm(
                    Number(driver.latitude),
                    Number(driver.longitude),
                    target.coords[0],
                    target.coords[1]
                )
                const estimatedRoadKm = linearKm * 1.25
                const etaMinutes = Math.max(1, Math.round((estimatedRoadKm / speedKmph) * 60))
                return { ...target, linearKm, estimatedRoadKm, etaMinutes }
            })
            .sort((a, b) => a.linearKm - b.linearKm)
            .slice(0, 12)

        const reachable = analyses.filter((target) => target.etaMinutes <= etaCoverageThresholdMinutes)
        const nearest = analyses.slice().sort((a, b) => a.etaMinutes - b.etaMinutes)[0] || null
        const farthestReachableLinearMeters = reachable.length > 0
            ? Math.max(...reachable.map((target) => Math.round(target.linearKm * 1000)))
            : defaultRadiusMeters

        return [driverKey, {
            radiusMeters: Math.max(defaultRadiusMeters, farthestReachableLinearMeters),
            reachableCount: reachable.length,
            nearestEtaMinutes: nearest?.etaMinutes ?? null,
            nearestLabel: nearest?.label || 'No live pickup or unloading points',
            nearestKindLabel: nearest?.kind === 'pickup' ? 'pickup' : nearest?.kind === 'delivery' ? 'unloading' : 'stop',
            speedKmph,
            thresholdMinutes: etaCoverageThresholdMinutes,
            loading: false,
        }]
    })

    etaCoverageByDriver.value = Object.fromEntries(entries)
}

function scheduleEtaCoverageRefresh() {
    if (etaCoverageTimer) clearTimeout(etaCoverageTimer)
    etaCoverageTimer = setTimeout(() => {
        refreshEtaCoverage()
    }, 100)
}

function loadDriverTrailHistory() {
    if (typeof window === 'undefined') return {}

    try {
        const raw = window.localStorage.getItem(DRIVER_TRAIL_STORAGE_KEY)
        if (!raw) return {}
        const parsed = JSON.parse(raw)
        return pruneDriverTrailHistory(parsed)
    } catch {
        return {}
    }
}

function saveDriverTrailHistory(history) {
    if (typeof window === 'undefined') return
    try {
        window.localStorage.setItem(DRIVER_TRAIL_STORAGE_KEY, JSON.stringify(pruneDriverTrailHistory(history)))
    } catch {}
}

function pruneDriverTrailHistory(history) {
    const now = Date.now()
    const nextHistory = {}

    for (const [driverId, samples] of Object.entries(history || {})) {
        const cleaned = Array.isArray(samples)
            ? samples
                .filter((sample) =>
                    hasValidCoordinate(sample?.lat) &&
                    hasValidCoordinate(sample?.lng) &&
                    sample?.ts &&
                    now - Number(sample.ts) <= DRIVER_TRAIL_RETENTION_MS
                )
                .slice(-DRIVER_TRAIL_MAX_POINTS)
            : []

        if (cleaned.length > 0) {
            nextHistory[driverId] = cleaned
        }
    }

    return nextHistory
}

function updateDriverTrailHistory() {
    const nextHistory = pruneDriverTrailHistory(driverTrailHistory.value)

    for (const driver of activeDrivers.value) {
        const coords = toCoordinatePair(driver.latitude, driver.longitude)
        if (!coords) continue

        const driverId = String(driver.driver_id)
        const existing = nextHistory[driverId] ? [...nextHistory[driverId]] : []
        const lastSample = existing[existing.length - 1] || null
        const orderContext = driverOrderContextMap.value.get(driverId) || null
        const nextSample = {
            lat: coords[0],
            lng: coords[1],
            ts: Date.now(),
            orderId: orderContext?.orderId || null,
            orderStatus: orderContext?.status || null,
            orderLabel: orderContext?.label || 'Recent route trail',
        }

        if (!lastSample) {
            existing.push(nextSample)
        } else {
            const movedKm = haversineKm(lastSample.lat, lastSample.lng, nextSample.lat, nextSample.lng)
            const elapsedMs = nextSample.ts - Number(lastSample.ts || 0)
            const sameOrder = String(lastSample.orderId || '') === String(nextSample.orderId || '')
            const sameStatus = String(lastSample.orderStatus || '') === String(nextSample.orderStatus || '')

            if (!sameOrder || !sameStatus || movedKm >= DRIVER_TRAIL_MIN_MOVE_KM || elapsedMs >= DRIVER_TRAIL_MIN_SAMPLE_GAP_MS) {
                existing.push(nextSample)
            } else {
                existing[existing.length - 1] = { ...lastSample, ...nextSample }
            }
        }

        nextHistory[driverId] = existing.slice(-DRIVER_TRAIL_MAX_POINTS)
    }

    driverTrailHistory.value = nextHistory
    saveDriverTrailHistory(nextHistory)
}

// Cache for OSRM road route geometries keyed by "lat1,lon1|lat2,lon2"
const osrmRouteCache = new Map()
// Reactive store of fetched road route coords keyed by route id
const osrmRouteCoords = ref({})

async function fetchOsrmRoute(lat1, lon1, lat2, lon2) {
    const cacheKey = `${lat1.toFixed(5)},${lon1.toFixed(5)}|${lat2.toFixed(5)},${lon2.toFixed(5)}`
    if (osrmRouteCache.has(cacheKey)) return osrmRouteCache.get(cacheKey)
    try {
        const url = `https://router.project-osrm.org/route/v1/driving/${lon1},${lat1};${lon2},${lat2}?overview=full&geometries=geojson`
        const controller = new AbortController()
        const timer = setTimeout(() => controller.abort(), 8000)
        const res = await fetch(url, { signal: controller.signal })
        clearTimeout(timer)
        if (!res.ok) throw new Error('OSRM error')
        const data = await res.json()
        if (data.code !== 'Ok' || !data.routes?.[0]) throw new Error('No route')
        // OSRM returns [lon, lat] — swap to [lat, lon] for Leaflet
        const coords = data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon])
        osrmRouteCache.set(cacheKey, coords)
        return coords
    } catch {
        // Fallback: straight line
        return [[lat1, lon1], [lat2, lon2]]
    }
}

// Generate routes from drivers to their assigned orders
const driverOrderRoutes = computed(() => {
    const routes = []
    for (const driver of activeDrivers.value) {
        const driverCoords = toCoordinatePair(driver.latitude, driver.longitude)
        if (!driverCoords) continue
        const driverOrders = liveMapOrders.value.filter(o =>
            o.driverId && String(o.driverId) === String(driver.driver_id) &&
            !['DELIVERED', 'CLOSED', 'CANCELLED'].includes(String(o.status || '').toUpperCase())
        )
        for (const order of driverOrders) {
            const destinationCoords = getResolvedDestinationCoords(order)
            if (!destinationCoords) continue
            routes.push({
                id: `route-${driver.driver_id}-${order.id}`,
                driverId: driver.driver_id,
                orderId: order.id,
                driverName: driver.driver_name || `Driver ${driver.driver_id}`,
                driverLocationLabel: getDriverLocationLabel(driver),
                destinationLabel: getOrderDestinationLabel(order),
                from: driverCoords,
                to: destinationCoords,
                status: order.status,
            })
        }
    }
    return routes
})

// Zone color helper (inspired by Geofencing.vue)
function getZoneColor(colorToken) {
    const colors = {
        blue: '#3b82f6',
        green: '#22c55e',
        red: '#ef4444',
        yellow: '#eab308',
        purple: '#a855f7',
        orange: '#f97316',
        teal: '#14b8a6',
        pink: '#ec4899',
    }
    return colors[colorToken] || colors.blue
}

// Priority color helper
function getPriorityColor(priority) {
    if (priority === 'URGENT') return '#ef4444'
    if (priority === 'HIGH') return '#f97316'
    return '#3b82f6'
}

// Count active layers for legend
const activeLayersCount = computed(() => {
    return Object.values(mapLayers.value).filter(Boolean).length
})

const busyDriverIds = computed(() => {
    const ids = new Set()
    for (const order of activeOrders.value) {
        const status = String(order?.status || '').toUpperCase()
        if (!order?.driverId || terminalOrderStatuses.has(status)) continue
        ids.add(String(order.driverId))
    }
    return ids
})

function isDriverAssignable(driver) {
    if (!driver || !driver.id) return false
    if (driver.suspended || driver.maintenance) return false
    if (driver.statusColor === 'bg-gray-500') return false
    return !busyDriverIds.value.has(String(driver.id))
}

function getDriverBusyReason(driver) {
    if (!driver) return ''
    if (driver.suspended) return 'Suspended'
    if (driver.maintenance) return 'Maintenance'
    if (busyDriverIds.value.has(String(driver.id))) return 'Assigned'
    if (driver.statusColor === 'bg-gray-500') return 'Offline'
    return ''
}

const assignableDrivers = computed(() => (
    drivers.value.filter((driver) => isDriverAssignable(driver))
))

const filteredDrivers = computed(() => {
    let list = showAllDrivers.value ? drivers.value : assignableDrivers.value
    list = list.map((driver) => ({
        ...driver,
        isAssignable: isDriverAssignable(driver),
        busyReason: getDriverBusyReason(driver),
    }))
    if (driverSearch.value) {
        const q = driverSearch.value.toLowerCase()
        list = list.filter(d => d.name.toLowerCase().includes(q) || d.id.toLowerCase().includes(q) || d.vehicle.toLowerCase().includes(q))
    }
    return list
})

// Map ref for invalidation
const map = ref(null)

// Fit map bounds to show all hubs/drivers when data loads
function fitMapBounds() {
    nextTick(() => {
        setTimeout(() => {
            if (!map.value?.leafletObject) return
            const leafletMap = map.value.leafletObject
            
            // Collect all points to include in bounds
            const points = []

            // Anchor the dashboard to the dispatcher's current warehouse when available.
            if (scopedWarehouseHub.value) {
                points.push([scopedWarehouseHub.value.lat, scopedWarehouseHub.value.lng])
            } else {
                mappableHubs.value.forEach(h => points.push([h.lat, h.lng]))
            }
            
            // Add active driver locations
            activeDrivers.value.forEach(d => {
                if (d.latitude && d.longitude) {
                    points.push([d.latitude, d.longitude])
                }
            })

            if (mapLayers.value.pickups) {
                pickupLocations.value.forEach((pickup) => {
                    points.push([pickup.lat, pickup.lng])
                })
            }
            
            // Add delivery destinations if layer is on
            if (mapLayers.value.destinations) {
                ordersWithDeliveryCoords.value.forEach(o => {
                    points.push([o.resolvedDeliveryLat, o.resolvedDeliveryLng])
                })
            }
            
            // If we have multiple points, fit bounds
            if (points.length > 1) {
                const bounds = L.latLngBounds(points)
                leafletMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })
            } else if (points.length === 1) {
                // Single point - just center on it
                leafletMap.setView(points[0], 13)
            }
        }, 600)
    })
}

// Invalidate map size when panels toggle (fixes rendering issues)
function invalidateMapSize() {
    nextTick(() => {
        setTimeout(() => {
            if (map.value?.leafletObject) {
                map.value.leafletObject.invalidateSize()
            }
        }, 350) // Wait for panel transition to complete
    })
}

// Watch for panel changes
watch([showLeftPanel, showRightPanel], () => {
    invalidateMapSize()
})

// Watch for hub data changes to re-fit bounds
watch(mappableHubs, (newHubs, oldHubs) => {
    if (newHubs.length !== oldHubs?.length) {
        fitMapBounds()
    }
}, { deep: true })

watch(scopedWarehouseHub, (newHub, oldHub) => {
    if (newHub?.id !== oldHub?.id) {
        fitMapBounds()
    }
}, { deep: true })

watch(mapCenter, (newCenter, oldCenter) => {
    const changed = JSON.stringify(newCenter) !== JSON.stringify(oldCenter)
    if (changed && newCenter) {
        invalidateMapSize()
        fitMapBounds()
    }
}, { deep: true })

watch(ordersWithDeliveryCoords, (newOrders, oldOrders) => {
    if (newOrders.length !== (oldOrders?.length || 0)) {
        fitMapBounds()
    }
}, { deep: true })

watch(pickupLocations, (newPickups, oldPickups) => {
    if (newPickups.length !== (oldPickups?.length || 0)) {
        fitMapBounds()
    }
}, { deep: true })

watch([() => mapLayers.value.eta, activeDrivers, etaTargets], () => {
    scheduleEtaCoverageRefresh()
}, { immediate: true, deep: true })

watch([activeDrivers, driverOrderContextMap], () => {
    updateDriverTrailHistory()
}, { immediate: true, deep: true })

watch(liveMapOrders, (orders) => {
    orders.forEach((order) => {
        const hasDriver = Boolean(order.driverId)
        if (!getResolvedPickupCoords(order) && order.pickupAddr) {
            void ensurePickupCoords(order)
        }
        if (hasDriver && !getResolvedDestinationCoords(order) && order.deliveryAddr) {
            void ensureRouteDestinationCoords(order)
        }
    })
}, { immediate: true, deep: true })

// Fetch real OSRM road routes for each driver→destination pair
watch(driverOrderRoutes, async (routes) => {
    for (const route of routes) {
        if (osrmRouteCoords.value[route.id]) continue // already fetched
        const [lat1, lon1] = route.from
        const [lat2, lon2] = route.to
        fetchOsrmRoute(lat1, lon1, lat2, lon2).then(coords => {
            osrmRouteCoords.value = { ...osrmRouteCoords.value, [route.id]: coords }
        })
    }
}, { immediate: true, deep: false })

onMounted(() => {
    console.log('🚀 Dashboard mounted, initializing store...')
    driverTrailHistory.value = pruneDriverTrailHistory(driverTrailHistory.value)
    saveDriverTrailHistory(driverTrailHistory.value)
    store.initialize().catch(() => {})
    scheduleEtaCoverageRefresh()
    // Invalidate map and fit bounds after initial render
    setTimeout(() => {
        invalidateMapSize()
        fitMapBounds()
    }, 500)
})

onUnmounted(() => {
    if (etaCoverageTimer) {
        clearTimeout(etaCoverageTimer)
        etaCoverageTimer = null
    }
})

function selectDriver(driver) {
    if (!driver?.isAssignable && !showAllDrivers.value) return
    selectedDriver.value = selectedDriver.value?.id === driver.id ? null : driver
}
function toggleLoadDetail(load) { expandedLoad.value = expandedLoad.value?.id === load.id ? null : load }
function toggleMapLayer(layer) { mapLayers.value[layer] = !mapLayers.value[layer] }

function assignLoad(load) {
    assignOrderId.value = load.id
    showAssignModal.value = true
}

async function confirmAssign() {
    if (!assignOrderId.value || !assignDriverId.value) return
    const driver = drivers.value.find((candidate) => String(candidate.id) === String(assignDriverId.value))
    if (!isDriverAssignable(driver)) {
        assignError.value = 'Selected driver is already assigned or unavailable.'
        return
    }
    assigning.value = true
    assignError.value = ''
    const ok = await store.assignOrder(assignOrderId.value, assignDriverId.value)
    assigning.value = false
    if (ok) {
        assignSuccess.value = true
        setTimeout(() => { showAssignModal.value = false; assignSuccess.value = false; assignOrderId.value = ''; assignDriverId.value = '' }, 1200)
    } else {
        assignError.value = 'Failed to assign. Please try again.'
    }
}

const driverChatMessages = ref([])
let chatMsgId = 1
function chatWithDriver(driver) {
    chatDriver.value = driver
    driverChatMessages.value = [
        { id: chatMsgId++, from: 'driver', text: `Hi dispatch, I\'m at ${driver.location}. Ready for next instructions.` },
        { id: chatMsgId++, from: 'dispatch', text: `Copy ${driver.name.split(' ')[0]}. Stand by for assignment update.` }
    ]
    showChatModal.value = true
}

function sendDriverMsg() {
    if (!chatMsg.value.trim()) return
    const text = chatMsg.value
    driverChatMessages.value.push({ id: chatMsgId++, from: 'dispatch', text })
    chatMsg.value = ''
    store.sendMessageToDriver(chatDriver.value?.id, text)
    setTimeout(() => {
        driverChatMessages.value.push({ id: chatMsgId++, from: 'driver', text: text.includes('?') ? 'Yes, copy that. I\'ll check and confirm.' : 'Roger, acknowledged.' })
    }, 1000)
}

// Driver Detail Modal
function viewDriverDetail(driver) {
    detailDriver.value = driver
    showDriverDetailModal.value = true
}

function assignToDriverFromDetail() {
    showDriverDetailModal.value = false
    assignDriverId.value = detailDriver.value?.id || ''
    showAssignModal.value = true
}

// Drag and Drop
function onDragStart(event, load) {
    draggingLoad.value = load
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', load.id)
}

function onDragEnd() {
    draggingLoad.value = null
    dragOverDriver.value = null
}

function onDriverPanelDragOver(event) {
    event.dataTransfer.dropEffect = 'move'
}

function onDriverDragOver(event, driver) {
    if (!isDriverAssignable(driver)) {
        event.dataTransfer.dropEffect = 'none'
        dragOverDriver.value = null
        return
    }
    event.dataTransfer.dropEffect = 'move'
    dragOverDriver.value = driver.id
}

function onDropOnDriverPanel(event) {
    dragOverDriver.value = null
}

async function onDropOnDriver(event, driver) {
    event.preventDefault()
    dragOverDriver.value = null
    if (!draggingLoad.value) return
    if (!isDriverAssignable(driver)) {
        dragAssignToast.value = `${driver.name} is already assigned or unavailable`
        draggingLoad.value = null
        setTimeout(() => { dragAssignToast.value = '' }, 2500)
        return
    }
    const load = draggingLoad.value
    draggingLoad.value = null
    const ok = await store.assignOrder(load.id, driver.id)
    if (ok) {
        dragAssignToast.value = `${load.id} → ${driver.name}`
        setTimeout(() => { dragAssignToast.value = '' }, 2500)
    } else {
        dragAssignToast.value = `Failed to assign ${load.id}`
        setTimeout(() => { dragAssignToast.value = '' }, 2500)
    }
}
</script>

<style scoped>
.slide-left-enter-active, .slide-left-leave-active {
    transition: width 0.3s ease, opacity 0.3s ease;
    overflow: hidden;
}
.slide-left-enter-from, .slide-left-leave-to {
    width: 0 !important;
    opacity: 0;
}
.slide-right-enter-active, .slide-right-leave-active {
    transition: width 0.3s ease, opacity 0.3s ease;
    overflow: hidden;
}
.slide-right-enter-from, .slide-right-leave-to {
    width: 0 !important;
    opacity: 0;
}
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
}
</style>
