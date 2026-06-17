<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-green-500">gps_fixed</span> Real-Time Tracking
        </h2>

        <!-- Active Orders Selector -->
        <div v-if="displayOrders.length > 1" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-4">
            <button v-for="order in displayOrders" :key="order.id" @click="selectOrder(order.id)"
                class="px-4 py-3 rounded-xl border transition-all text-left w-full shadow-sm"
                :class="selectedOrderId === order.id ? 'bg-green-50 dark:bg-green-900/20 border-green-500' : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-green-500/50'">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="font-bold text-sm font-mono"
                        :class="selectedOrderId === order.id ? 'text-green-700 dark:text-green-400' : 'text-gray-900 dark:text-white'">{{
                            order.id }}</span>
                    <span
                        class="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase"
                        :class="order.status === 'in-transit' ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400'
                            : order.status === 'dispatched' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
                            : order.status === 'delivered' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400'
                            : order.status === 'cancelled' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
                            : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400'">{{ 
                            order.status === 'dispatched' ? 'ASSIGNED' : order.status.replace('-', ' ') }}</span>
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]"><span
                        class="font-medium">{{ order.cargoType }}</span></div>
                <div class="text-xs text-gray-400 dark:text-gray-500 truncate max-w-[200px] mt-0.5">{{
                    order.pickup.split(',')[0] }} → {{ order.destination.split(',')[0] }}</div>
            </button>
        </div>

        <div v-if="activeMove && activeMove.status !== 'cancelled'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Map Area -->
            <div class="lg:col-span-2 space-y-4">
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

                <!-- Dwell Time Card -->
                <div v-if="activeMove.dwellTime && activeMove.dwellTime.total > 0"
                    class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-purple-500 text-lg">timer</span> Dwell Time Log
                    </h3>
                    <div class="grid grid-cols-3 gap-3">
                        <div
                            class="p-3 bg-blue-50 dark:bg-blue-500/5 rounded-lg text-center border border-blue-200 dark:border-blue-500/20">
                            <div class="text-xs text-gray-500 dark:text-gray-400">Loading</div>
                            <div class="text-xl font-bold text-blue-600 dark:text-blue-400">{{
                                activeMove.dwellTime.loading }}<span class="text-xs font-normal"> min</span></div>
                        </div>
                        <div
                            class="p-3 bg-amber-50 dark:bg-amber-500/5 rounded-lg text-center border border-amber-200 dark:border-amber-500/20">
                            <div class="text-xs text-gray-500 dark:text-gray-400">Unloading</div>
                            <div class="text-xl font-bold text-amber-600 dark:text-amber-400">{{
                                activeMove.dwellTime.unloading }}<span class="text-xs font-normal"> min</span></div>
                        </div>
                        <div
                            class="p-3 bg-purple-50 dark:bg-purple-500/5 rounded-lg text-center border border-purple-200 dark:border-purple-500/20">
                            <div class="text-xs text-gray-500 dark:text-gray-400">Total Dwell</div>
                            <div class="text-xl font-bold text-purple-600 dark:text-purple-400">{{
                                activeMove.dwellTime.total }}<span class="text-xs font-normal"> min</span></div>
                        </div>
                    </div>
                </div>

                <!-- Transport Log Timeline -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-blue-500 text-lg">timeline</span> Transport Log
                    </h3>
                    <div class="relative pl-8">
                        <div class="absolute left-[11px] top-2 bottom-0 w-[2px] bg-gradient-to-b from-green-500 via-blue-500 to-gray-200 dark:to-gray-700"></div>
                        <div v-for="(log, i) in activeMove.transportLog" :key="i" class="relative pb-5 last:pb-0 group">
                            <div class="absolute -left-8 top-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] shadow-md transition-transform group-hover:scale-110"
                                :style="{ backgroundColor: logColor(log.color) }">
                                <span class="material-symbols-outlined text-[12px]">{{ log.icon }}</span>
                            </div>
                            <div class="p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                                <div class="flex items-center gap-2">
                                    <span class="text-sm font-medium text-gray-900 dark:text-white">{{ log.event }}</span>
                                    <span v-if="isWarehouseEvent(log.event)" class="px-1.5 py-0.5 bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 text-[9px] font-bold rounded uppercase">
                                        Warehouse
                                    </span>
                                </div>
                                <div v-if="log.description" class="text-[11px] text-gray-600 dark:text-gray-400 mt-1 leading-snug">
                                    {{ log.description }}
                                </div>
                                <div class="text-[10px] text-gray-500 dark:text-gray-500 font-mono mt-0.5">{{ log.time }}</div>
                            </div>
                        </div>
                        <div v-if="!activeMove.transportLog?.length" class="text-center py-4 text-gray-400 text-sm">
                            No transport events yet
                        </div>
                    </div>
                </div>
            </div>

            <!-- Details Sidebar -->
            <div class="space-y-4">
                <!-- Driver Card -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl" v-if="activeMove.driver">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Driver & Crew</h3>
                    <div class="flex items-center gap-3 mb-3">
                        <div
                            class="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
                            {{activeMove.driver.name.split(' ').map(n => n[0]).join('')}}
                        </div>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white">{{ activeMove.driver.name }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">{{ activeMove.driver.rating }} ★ ·
                                Team Lead</div>
                        </div>
                    </div>
                    <div class="flex gap-2 mb-3">
                        <button @click="showCallModal = true"
                            class="flex-1 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-1"><span
                                class="material-symbols-outlined text-sm">call</span> Call</button>
                        <button @click="showChatModal = true"
                            class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white text-sm font-bold rounded-lg hover:bg-gray-200 dark:hover:bg-white/20 transition-colors flex items-center justify-center gap-1"><span
                                class="material-symbols-outlined text-sm">chat</span> Chat</button>
                    </div>
                    <!-- Crew Check-in -->
                    <div v-if="activeMove.crewCheckin" class="space-y-2">
                        <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Crew Check-In</div>
                        <div v-for="laborer in activeMove.crewCheckin.laborers" :key="laborer.name"
                            class="flex items-center justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <span class="text-gray-900 dark:text-white font-medium">{{ laborer.name }}</span>
                            <span v-if="laborer.checkedIn"
                                class="text-green-500 font-bold flex items-center gap-1"><span
                                    class="material-symbols-outlined text-xs">check_circle</span>Checked In</span>
                            <span v-else class="text-red-500 font-bold">Absent</span>
                        </div>
                    </div>
                </div>

                <!-- Vehicle Info -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Vehicle & Order</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Order
                                ID</span><span class="font-mono font-bold text-green-600 dark:text-green-400">{{
                                    activeMove.id }}</span></div>
                        <div class="flex justify-between"><span
                                class="text-gray-500 dark:text-gray-400">Vehicle</span><span
                                class="text-gray-900 dark:text-white font-medium uppercase">{{ activeMove.vehicleType
                                }}</span></div>
                        <div class="flex justify-between"><span
                                class="text-gray-500 dark:text-gray-400">Cargo</span><span
                                class="text-gray-900 dark:text-white font-medium">{{ activeMove.cargoType }}</span>
                        </div>
                        <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Service
                                Block</span><span class="text-purple-600 dark:text-purple-400 font-medium">{{
                                    activeMove.serviceTimeBlock }}</span></div>
                        <div class="flex justify-between"><span
                                class="text-gray-500 dark:text-gray-400">Helpers</span><span
                                class="text-gray-900 dark:text-white font-medium">{{ activeMove.laborCount }}
                                assigned</span></div>
                    </div>
                </div>

                <!-- Before/After Photos -->
                <div v-if="activeMove.beforeAfterPhotos && Object.keys(activeMove.beforeAfterPhotos).length > 0"
                    class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-amber-500 text-lg">photo_camera</span> Move Photos
                    </h3>
                    <div class="space-y-2">
                        <div v-for="(val, key) in activeMove.beforeAfterPhotos" :key="key"
                            class="flex items-center justify-between p-2 bg-gray-50 dark:bg-white/5 rounded-lg text-xs">
                            <span class="text-gray-700 dark:text-gray-300 font-medium capitalize">{{
                                key.replace(/([A-Z])/g, ' $1') }}</span>
                            <span :class="val ? 'text-green-500' : 'text-gray-400'">{{ val || 'Pending' }}</span>
                        </div>
                    </div>
                </div>

                <!-- Service Checklist -->
                <div class="glass-panel p-4 sm:p-5 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-purple-500 text-lg">checklist</span> Service
                        Checklist
                    </h3>
                    <div class="space-y-2">
                        <div v-for="task in serviceChecklist" :key="task.text" class="flex items-center gap-3 text-sm">
                            <span class="material-symbols-outlined text-lg"
                                :class="task.done ? 'text-green-500' : 'text-gray-300 dark:text-gray-600'">{{ task.done
                                    ? 'check_circle' : 'radio_button_unchecked' }}</span>
                            <span :class="task.done ? 'text-gray-400 line-through' : 'text-gray-900 dark:text-white'">{{
                                task.text }}</span>
                        </div>
                    </div>
                </div>

                <div class="space-y-1">
                    <button @click="toggleGeofence" :disabled="geofenceLoading"
                        class="w-full py-2.5 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2 border disabled:opacity-60 disabled:cursor-not-allowed"
                        :class="geofenceAlert
                            ? 'bg-green-500/10 border-green-500/30 text-green-600 dark:text-green-400 hover:bg-green-500/20'
                            : 'bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/5 text-gray-700 dark:text-white hover:bg-gray-200 dark:hover:bg-white/10'">
                        <span v-if="geofenceLoading" class="material-symbols-outlined text-sm animate-spin">sync</span>
                        <span v-else class="material-symbols-outlined text-sm">{{ geofenceAlert ? 'notifications_active' : 'notifications' }}</span>
                        {{ geofenceLoading ? 'Simulating...' : geofenceAlert ? 'Geofence Alert Active' : 'Simulate Arrival Alert' }}
                    </button>
                    <p v-if="geofenceError" class="text-[10px] text-amber-500 dark:text-amber-400 text-center">{{ geofenceError }}</p>
                </div>

                <!-- Slip downloads for delivered orders -->
                <div v-if="activeMove?.status === 'delivered'" class="flex gap-2">
                    <button @click="openSlipWithData('proofOfDelivery', activeMove, authStore.currentUser)"
                        class="flex-1 py-2.5 bg-green-500/10 hover:bg-green-500/20 text-green-600 dark:text-green-400 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-sm">verified</span> PoD
                    </button>
                    <button @click="openSlipWithData('finalTaxInvoice', activeMove, authStore.currentUser)"
                        class="flex-1 py-2.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-sm">request_quote</span> Invoice
                    </button>
                </div>
            </div>
        </div>

        <!-- Cancelled Order View -->
        <div v-else-if="activeMove && activeMove.status === 'cancelled'" class="space-y-4">
            <!-- Cancellation Banner -->
            <div class="glass-panel p-6 rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50/50 dark:bg-red-500/5">
                <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-red-500 text-3xl">cancel</span>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-lg font-bold text-red-700 dark:text-red-400 mb-1">Order Cancelled</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400">{{ activeMove.cancellation?.reason || 'This order was cancelled.' }}</p>
                        <div class="flex items-center gap-3 mt-2 flex-wrap">
                            <span class="text-xs font-mono text-gray-500 dark:text-gray-400">{{ activeMove.id }}</span>
                            <span v-if="activeMove.cancellation?.fee > 0" class="text-xs font-bold text-red-600 dark:text-red-400">
                                Cancellation fee: ₹{{ activeMove.cancellation.fee.toLocaleString('en-IN') }}
                            </span>
                            <span v-else class="text-xs text-green-600 dark:text-green-400 font-medium">No cancellation fee</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Transport Log for cancelled order -->
            <div class="glass-panel p-4 sm:p-5 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-500 text-lg">timeline</span> Transport Log
                </h3>
                <div class="relative pl-8">
                    <div class="absolute left-[11px] top-2 bottom-0 w-[2px] bg-gradient-to-b from-green-500 via-blue-500 to-red-400"></div>
                    <div v-for="(log, i) in activeMove.transportLog" :key="i" class="relative pb-5 last:pb-0 group">
                        <div class="absolute -left-8 top-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] shadow-md"
                            :style="{ backgroundColor: logColor(log.color) }">
                            <span class="material-symbols-outlined text-[12px]">{{ log.icon }}</span>
                        </div>
                        <div class="p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ log.event }}</span>
                            </div>
                            <div v-if="log.description" class="text-[11px] text-gray-600 dark:text-gray-400 mt-1 leading-snug">{{ log.description }}</div>
                            <div class="text-[10px] text-gray-500 dark:text-gray-500 font-mono mt-0.5">{{ log.time }}</div>
                        </div>
                    </div>
                    <div v-if="!activeMove.transportLog?.length" class="text-center py-4 text-gray-400 text-sm">
                        No transport events recorded.
                    </div>
                </div>
            </div>

            <router-link to="/individual/book-move"
                class="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded-xl transition-colors">
                <span class="material-symbols-outlined text-sm">add_circle</span> Book a New Move
            </router-link>
        </div>

        <div v-else class="glass-panel p-12 rounded-xl text-center text-gray-500 dark:text-gray-400">
            <span class="material-symbols-outlined text-5xl block mb-3">location_off</span>
            <p class="font-medium text-lg">No active move to track.</p>
            <router-link to="/individual/book-move"
                class="text-green-600 dark:text-green-400 text-sm font-bold hover:underline mt-2 inline-block">Book a
                Move →</router-link>
        </div>
        
        <!-- Call Modal -->
        <Teleport to="body">
            <div v-if="showCallModal && activeMove?.driver" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-slide-up border border-gray-100 dark:border-white/10">
                    <div class="p-6 text-center">
                        <div class="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-2xl font-bold mb-4 shadow-lg shadow-green-500/20">
                            {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                        </div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">{{ activeMove.driver.name }}</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Driver · {{ activeMove.vehicleType?.toUpperCase() }}</p>
                        
                        <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-xl mb-6">
                            <div class="text-xs text-gray-500 mb-1 uppercase font-bold">Phone Number</div>
                            <div class="text-lg font-mono font-bold text-gray-900 dark:text-white tracking-widest">{{ activeMove.driver.phone || '+91 98765 43210' }}</div>
                        </div>
                        
                        <div class="flex gap-3">
                            <button @click="showCallModal = false" class="flex-1 py-3 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors">Cancel</button>
                            <a :href="'tel:' + (activeMove.driver.phone || '+910000000000')" @click="showCallModal = false" class="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2">
                                <span class="material-symbols-outlined">call</span> Call
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Chat Modal -->
        <Teleport to="body">
            <div v-if="showChatModal && activeMove?.driver" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl flex flex-col h-[600px] max-h-[85vh] animate-slide-up border border-gray-100 dark:border-white/10 relative">
                    <!-- Chat Header -->
                    <div class="p-4 border-b border-gray-100 dark:border-white/10 flex items-center justify-between shrink-0 bg-gray-50 dark:bg-black/50 rounded-t-2xl">
                        <div class="flex items-center gap-3">
                            <div class="relative">
                                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                                    {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                                </div>
                                <div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-900 rounded-full"></div>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-900 dark:text-white text-sm">{{ activeMove.driver.name }}</h3>
                                <div class="text-[10px] text-green-600 dark:text-green-400 font-bold">Online</div>
                            </div>
                        </div>
                        <button @click="showChatModal = false" class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full text-gray-500 transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    
                    <!-- Chat Messages Area -->
                    <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 dark:bg-black/20" ref="chatScrollContainer">
                        <div class="text-center py-2">
                            <span class="bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-gray-400 text-[10px] px-3 py-1 rounded-full font-bold uppercase">Today</span>
                        </div>
                        
                        <!-- Incoming Message -->
                        <div class="flex gap-2">
                            <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-[10px] shrink-0 mt-1">
                                {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                            </div>
                            <div class="bg-white dark:bg-gray-800 p-3 rounded-2xl rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[80%]">
                                <p class="text-sm text-gray-800 dark:text-gray-200">Hi sir, I am reaching the pickup location in about 10 minutes.</p>
                                <div class="text-[10px] text-gray-400 mt-1 text-right">10:45 AM</div>
                            </div>
                        </div>
                        
                        <!-- System Message -->
                        <div class="text-center py-2">
                            <span class="text-gray-400 dark:text-gray-500 text-xs italic">Crew is nearing the location</span>
                        </div>
                        
                        <!-- Appended Dynamic Messages -->
                        <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex gap-2 justify-end">
                            <div class="bg-green-600 p-3 rounded-2xl rounded-tr-none shadow-sm text-white max-w-[80%]">
                                <p class="text-sm">{{ msg.text }}</p>
                                <div class="text-[10px] text-green-200 mt-1 flex justify-end items-center gap-1">
                                    {{ msg.time }}
                                    <span class="material-symbols-outlined text-[12px]">done_all</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Chat Input Area -->
                    <div class="p-3 border-t border-gray-100 dark:border-white/10 bg-white dark:bg-gray-900 rounded-b-2xl shrink-0">
                        <form @submit.prevent="sendChatMessage" class="flex items-center gap-2">
                            <input type="text" v-model="pendingMessage" placeholder="Message driver..." class="flex-1 bg-gray-100 dark:bg-white/5 border border-transparent focus:border-green-500 focus:ring-1 focus:ring-green-500 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none transition-all">
                            <button type="submit" :disabled="!pendingMessage.trim()" class="p-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:hover:bg-green-600 transition-colors flex items-center justify-center">
                                <span class="material-symbols-outlined text-sm">send</span>
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onActivated, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import { apiUrl } from '@/config/api'
import { LMap, LTileLayer, LMarker, LPopup, LPolyline } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix Leaflet icons issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

const route = useRoute()
const router = useRouter()
const store = useIndividualStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()

const allOrders = computed(() => store.orders)

const displayOrders = computed(() => {
    if (route.query.orderId) {
        return allOrders.value.filter(o => o.id === route.query.orderId)
    }
    return allOrders.value
})

const selectedOrderId = ref(route.query.orderId || (allOrders.value.length > 0 ? allOrders.value[0].id : null))
const activeMove = computed(() => {
    return allOrders.value.find(o => o.id === selectedOrderId.value) || allOrders.value[0] || null
})
const shouldPollLiveTracking = computed(() => !['delivered', 'cancelled'].includes(activeMove.value?.status || ''))

// ─── Real-Time Tracking Integration ───
const { driver: trackingDriver } = useRealTimeTracking(selectedOrderId, {
    mode: 'single',
    enabled: shouldPollLiveTracking,
})

// ─── Route Blueprint State ───
const mapRef = ref(null)
const mapPanelRef = ref(null)
const warehouseCoords = ref(null) // [lat, lng]
const routeCoords = ref([])       // [[lat,lng],...] full route polyline
const warehouseToPickupCoords = ref([])
const pickupToDestCoords = ref([])
const pickupCoords = ref(null)    // [lat, lng]
const destCoords = ref(null)      // [lat, lng]
const routeLoading = ref(false)
const mapFocusFlash = ref(false)
const routeFocusMode = ref('instant')
let routeRequestToken = 0
let mapFocusFlashTimer = null
const MAP_FIT_PADDING_TOP_LEFT = [72, 104]
const MAP_FIT_PADDING_BOTTOM_RIGHT = [72, 132]
const geocodeCache = new Map()
const orderRouteCache = new Map()
const routeResolvePromises = new Map()

// Custom map pin icons
function makePinIcon(color, label) {
    return L.divIcon({
        html: `<div style="width:30px;height:30px;background:${color};border:3px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 2px 8px rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;"><span style="transform:rotate(45deg);color:white;font-size:12px;font-weight:900;line-height:1;">${label}</span></div>`,
        className: '',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -34]
    })
}
const warehouseIcon = makePinIcon('#d97706', 'W')
const pickupIcon = makePinIcon('#16a34a', 'A')
const destIcon   = makePinIcon('#dc2626', 'B')
const driverIcon = L.divIcon({
    html: `<div style="width:38px;height:38px;background:#2563eb;border:3px solid white;border-radius:50%;box-shadow:0 2px 12px rgba(37,99,235,0.55);display:flex;align-items:center;justify-content:center;"><svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='white'><path d='M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z'/></svg></div>`,
    className: '',
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -22]
})

// Geocode an address string → [lat, lng] using Nominatim
async function geocodeAddress(address) {
    if (!address) return null

    const raw = String(address).trim()
    if (!raw) return null
    const cacheKey = raw.toLowerCase()

    if (geocodeCache.has(cacheKey)) {
        return geocodeCache.get(cacheKey)
    }

    try {
        const res = await fetch(apiUrl(`api/v1/geocoding/search?q=${encodeURIComponent(raw)}&limit=1`))
        if (res.ok) {
            const data = await res.json()
            if (Array.isArray(data) && data[0]) {
                const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
                geocodeCache.set(cacheKey, coords)
                return coords
            }
        }
    } catch {}

    const queries = raw.toLowerCase().includes('india') ? [raw] : [raw, `${raw}, India`]
    for (const query of queries) {
        try {
            const q = encodeURIComponent(query)
            const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=1`, {
                headers: { 'Accept-Language': 'en' }
            })
            const data = await res.json()
            if (data[0]) {
                const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
                geocodeCache.set(cacheKey, coords)
                return coords
            }
        } catch {}
    }

    return null
}

// Fetch full OSRM route geometry → [[lat,lng],...] for Leaflet polyline
async function fetchRouteGeometry(lat1, lon1, lat2, lon2) {
    try {
        const url = `https://router.project-osrm.org/route/v1/driving/${lon1},${lat1};${lon2},${lat2}?overview=full&geometries=geojson`
        const controller = new AbortController()
        const timer = setTimeout(() => controller.abort(), 8000)
        const res = await fetch(url, { signal: controller.signal })
        clearTimeout(timer)
        if (!res.ok) return null
        const data = await res.json()
        if (data.code !== 'Ok' || !data.routes?.[0]) return null
        // OSRM returns [lon, lat] — swap to [lat, lon] for Leaflet
        return data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon])
    } catch {
        return null
    }
}

function fallbackRouteGeometry(pickup, dest) {
    if (pickup && dest) {
        if (Math.abs(pickup[0] - dest[0]) < 0.000001 && Math.abs(pickup[1] - dest[1]) < 0.000001) {
            return [clonePoint(pickup)]
        }
        return [clonePoint(pickup), clonePoint(dest)]
    }
    if (pickup) return [clonePoint(pickup)]
    if (dest) return [clonePoint(dest)]
    return []
}

function clonePoint(point) {
    return Array.isArray(point) ? [point[0], point[1]] : null
}

function cloneCoords(coords) {
    return Array.isArray(coords) ? coords.map(clonePoint).filter(Boolean) : []
}

function hasDetailedRoute(coords) {
    return Array.isArray(coords) && coords.length > 2
}

function pointsMatch(start, end) {
    return Array.isArray(start)
        && Array.isArray(end)
        && Math.abs(start[0] - end[0]) < 0.000001
        && Math.abs(start[1] - end[1]) < 0.000001
}

function pointFromValues(lat, lng) {
    if (lat === null || lat === undefined || lat === '' || lng === null || lng === undefined || lng === '') {
        return null
    }
    const safeLat = Number(lat)
    const safeLng = Number(lng)
    if (!Number.isFinite(safeLat) || !Number.isFinite(safeLng)) return null
    return [safeLat, safeLng]
}

function mergeRouteSegments(...segments) {
    const merged = []

    for (const segment of segments) {
        for (const point of cloneCoords(segment)) {
            const previous = merged[merged.length - 1]
            if (!previous || !pointsMatch(previous, point)) {
                merged.push(point)
            }
        }
    }

    return merged
}

function buildRouteBundle(data = {}) {
    const warehouse = clonePoint(data.warehouse)
    const pickup = clonePoint(data.pickup)
    const dest = clonePoint(data.dest)
    const warehouseToPickup = cloneCoords(data.warehouseToPickup)
    const pickupToDest = cloneCoords(data.pickupToDest)

    const normalizedWarehouseToPickup = warehouse && pickup
        ? (warehouseToPickup.length ? warehouseToPickup : fallbackRouteGeometry(warehouse, pickup))
        : []
    const normalizedPickupToDest = pickup && dest
        ? (pickupToDest.length ? pickupToDest : fallbackRouteGeometry(pickup, dest))
        : []

    return {
        warehouse,
        pickup,
        dest,
        warehouseToPickup: normalizedWarehouseToPickup,
        pickupToDest: normalizedPickupToDest,
        coords: mergeRouteSegments(normalizedWarehouseToPickup, normalizedPickupToDest),
    }
}

function hasUsableSegment(start, end, coords, { requireGeometry = false } = {}) {
    if (!start || !end) return true
    if (!Array.isArray(coords) || coords.length === 0) return false
    return requireGeometry ? hasDetailedRoute(coords) || coords.length >= 2 : coords.length >= 2
}

function hasUsableRouteData(data, { allowGeometry = false } = {}) {
    if (!data) return false

    const normalized = buildRouteBundle(data)
    if (!normalized.coords.length && !normalized.pickup && !normalized.dest && !normalized.warehouse) {
        return false
    }

    return hasUsableSegment(normalized.warehouse, normalized.pickup, normalized.warehouseToPickup, { requireGeometry: allowGeometry })
        && hasUsableSegment(normalized.pickup, normalized.dest, normalized.pickupToDest, { requireGeometry: allowGeometry })
}

function getCachedRouteData(orderId) {
    const cached = orderRouteCache.get(String(orderId))
    if (!cached) return null

    return buildRouteBundle(cached)
}

function setCachedRouteData(orderId, data) {
    orderRouteCache.set(String(orderId), buildRouteBundle(data))
}

function haversineKm(start, end) {
    if (!start || !end) return 0
    const [lat1, lon1] = start
    const [lat2, lon2] = end
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function getRouteFocusSettings(coords) {
    if (!Array.isArray(coords) || coords.length < 2) {
        return { maxZoom: 12, duration: 0.8, padFactor: 0.35 }
    }

    const distanceKm = haversineKm(coords[0], coords[coords.length - 1])

    if (distanceKm <= 1.5) return { maxZoom: 10, duration: 0.78, padFactor: 1.15 }
    if (distanceKm <= 4) return { maxZoom: 11, duration: 0.82, padFactor: 0.9 }
    if (distanceKm <= 10) return { maxZoom: 11, duration: 0.88, padFactor: 0.65 }
    if (distanceKm <= 30) return { maxZoom: 10, duration: 0.96, padFactor: 0.45 }
    if (distanceKm <= 80) return { maxZoom: 9, duration: 1.05, padFactor: 0.28 }
    return { maxZoom: 8, duration: 1.12, padFactor: 0.18 }
}

async function ensureRouteData(order, { allowGeometry = true } = {}) {
    const orderKey = order?.id ? String(order.id) : '__draft__'
    const pendingKey = `${orderKey}:${allowGeometry ? 'route' : 'pins'}`
    const cached = getCachedRouteData(orderKey)

    if (hasUsableRouteData(cached, { allowGeometry })) {
        return cached
    }

    if (routeResolvePromises.has(pendingKey)) {
        return routeResolvePromises.get(pendingKey)
    }

    const promise = (async () => {
        const warehouseCandidates = [
            pointFromValues(order?.warehouseLat, order?.warehouseLng),
            cached?.warehouse,
        ].filter(Boolean)
        let warehouse = warehouseCandidates[0] || null

        if (!warehouse) {
            const warehouseQueries = [
                order?.warehouseAddress,
                order?.warehouseName && order?.warehouseAddress ? `${order.warehouseName}, ${order.warehouseAddress}` : null,
                order?.warehouseName,
            ].filter(Boolean)

            for (const query of warehouseQueries) {
                warehouse = await geocodeAddress(query)
                if (warehouse) break
            }
        }

        const pickup = cached?.pickup || await geocodeAddress(order?.pickup)
        const dest = cached?.dest || await geocodeAddress(order?.destination)

        let warehouseToPickup = cached?.warehouseToPickup?.length
            ? cloneCoords(cached.warehouseToPickup)
            : fallbackRouteGeometry(warehouse, pickup)
        let pickupToDest = cached?.pickupToDest?.length
            ? cloneCoords(cached.pickupToDest)
            : fallbackRouteGeometry(pickup, dest)

        if (allowGeometry && warehouse && pickup && !hasDetailedRoute(warehouseToPickup)) {
            warehouseToPickup = await fetchRouteGeometry(warehouse[0], warehouse[1], pickup[0], pickup[1]) || warehouseToPickup
        }

        if (allowGeometry && pickup && dest && !hasDetailedRoute(pickupToDest)) {
            pickupToDest = await fetchRouteGeometry(pickup[0], pickup[1], dest[0], dest[1]) || pickupToDest
        }

        const resolved = buildRouteBundle({
            warehouse,
            pickup,
            dest,
            warehouseToPickup,
            pickupToDest,
        })

        setCachedRouteData(orderKey, resolved)
        return getCachedRouteData(orderKey)
    })()

    routeResolvePromises.set(pendingKey, promise)

    try {
        return await promise
    } finally {
        routeResolvePromises.delete(pendingKey)
    }
}

function warmDisplayOrderMapData(orders = []) {
    const priorityOrders = orders.slice(0, 6)
    for (const order of priorityOrders) {
        ensureRouteData(order, { allowGeometry: true }).catch(() => {})
    }
}

function requestSmoothMapFocus() {
    routeFocusMode.value = 'smooth'
    mapFocusFlash.value = true

    clearTimeout(mapFocusFlashTimer)
    mapFocusFlashTimer = setTimeout(() => {
        mapFocusFlash.value = false
    }, 1400)
}

async function fitMapToRoute(coords, { animate = false } = {}) {
    await nextTick()
    const leaflet = mapRef.value?.leafletObject
    if (!leaflet || !coords?.length) return

    leaflet.invalidateSize?.()
    leaflet.stop?.()

    if (coords.length === 1) {
        if (animate && leaflet.flyTo) {
            leaflet.flyTo(coords[0], 10, { animate: true, duration: 0.72, easeLinearity: 0.2 })
        } else {
            leaflet.setView(coords[0], 10)
        }
        return
    }

    const baseBounds = L.latLngBounds(coords)
    const { maxZoom, duration, padFactor } = getRouteFocusSettings(coords)
    const bounds = baseBounds.pad(padFactor)
    if (animate && leaflet.flyToBounds) {
        leaflet.flyToBounds(bounds, {
            paddingTopLeft: MAP_FIT_PADDING_TOP_LEFT,
            paddingBottomRight: MAP_FIT_PADDING_BOTTOM_RIGHT,
            maxZoom,
            duration,
            easeLinearity: 0.18
        })
        return
    }

    leaflet.fitBounds(bounds, {
        paddingTopLeft: MAP_FIT_PADDING_TOP_LEFT,
        paddingBottomRight: MAP_FIT_PADDING_BOTTOM_RIGHT,
        maxZoom
    })
}

function applyRouteToMap(data) {
    const bundle = buildRouteBundle(data)
    warehouseCoords.value = bundle.warehouse
    pickupCoords.value = bundle.pickup
    destCoords.value = bundle.dest
    warehouseToPickupCoords.value = bundle.warehouseToPickup
    pickupToDestCoords.value = bundle.pickupToDest
    routeCoords.value = bundle.coords
}

function clearRouteFromMap() {
    warehouseCoords.value = null
    pickupCoords.value = null
    destCoords.value = null
    warehouseToPickupCoords.value = []
    pickupToDestCoords.value = []
    routeCoords.value = []
}

async function loadRouteForOrder(order) {
    if (!order) return
    const requestToken = ++routeRequestToken
    const shouldAnimate = routeFocusMode.value === 'smooth'
    routeFocusMode.value = 'instant'
    const cached = getCachedRouteData(order.id)
    const hasCachedRoute = Boolean(
        cached?.warehouse
        || cached?.pickup
        || cached?.dest
        || cached?.warehouseToPickup?.length
        || cached?.pickupToDest?.length
        || cached?.coords?.length
    )

    if (hasCachedRoute) {
        applyRouteToMap(cached)
        await fitMapToRoute(routeCoords.value, { animate: shouldAnimate })
    }

    routeLoading.value = true
    if (!hasCachedRoute) {
        clearRouteFromMap()
    }

    try {
        const resolved = await ensureRouteData(order, { allowGeometry: true })
        if (requestToken !== routeRequestToken) return

        applyRouteToMap(resolved)

        if (!hasCachedRoute) {
            await fitMapToRoute(routeCoords.value, { animate: shouldAnimate })
        }
    } finally {
        if (requestToken === routeRequestToken) {
            routeLoading.value = false
        }
    }
}

function getRouteCenter(coords) {
    if (!Array.isArray(coords) || !coords.length) return null
    if (coords.length === 1) return coords[0]
    const center = L.latLngBounds(coords).getCenter()
    return [center.lat, center.lng]
}

const mapCenter = computed(() => {
    const order = activeMove.value
    if (order?.status === 'delivered') {
        const deliveredCenter = getRouteCenter(routeCoords.value)
        if (deliveredCenter) return deliveredCenter
    }
    if (trackingDriver.value?.latitude && trackingDriver.value?.longitude) {
        return [trackingDriver.value.latitude, trackingDriver.value.longitude]
    }
    const routeCenter = getRouteCenter(routeCoords.value)
    if (routeCenter) return routeCenter
    if (warehouseCoords.value) return warehouseCoords.value
    if (pickupCoords.value) return pickupCoords.value
    if (destCoords.value) return destCoords.value
    return [19.0760, 72.8777]
})
const zoom = ref(13)

watch(() => route.query.orderId, (newId) => {
    if (newId) {
        requestSmoothMapFocus()
        selectedOrderId.value = newId
    } else if (!selectedOrderId.value && allOrders.value.length > 0) {
        selectedOrderId.value = allOrders.value[0].id
    }
}, { immediate: true })

watch(() => displayOrders.value.map(order => `${order.id}:${order.status}`).join('|'), () => {
    warmDisplayOrderMapData(displayOrders.value)
}, { immediate: false })

const activeRouteSignature = computed(() => {
    if (!activeMove.value) return ''
    return [
        activeMove.value.id,
        activeMove.value.warehouseId || '',
        activeMove.value.warehouseName || '',
        activeMove.value.warehouseAddress || '',
        activeMove.value.warehouseLat ?? '',
        activeMove.value.warehouseLng ?? '',
        activeMove.value.pickup,
        activeMove.value.destination,
        activeMove.value.status,
    ].join('|')
})

watch(activeRouteSignature, () => {
    if (activeMove.value && activeMove.value.status !== 'cancelled') {
        loadRouteForOrder(activeMove.value)
    }
}, { immediate: false })

function selectOrder(id) {
    requestSmoothMapFocus()

    if (selectedOrderId.value === id) {
        const currentCoords = routeCoords.value.length
            ? routeCoords.value
            : buildRouteBundle({
                warehouse: warehouseCoords.value,
                pickup: pickupCoords.value,
                dest: destCoords.value,
                warehouseToPickup: warehouseToPickupCoords.value,
                pickupToDest: pickupToDestCoords.value,
            }).coords
        fitMapToRoute(currentCoords, { animate: true })
        return
    }

    selectedOrderId.value = id
    // We don't push the route query here if they are in 'all orders' mode
    // because doing so would filter the list down to 1 item inside displayOrders.
    // So we just update the local state.
}
const geofenceAlert = ref(false)
const geofenceLoading = ref(false)
const geofenceError = ref('')

const GEOFENCE_KEY = 'geofence_alerts'

function loadGeofenceState(orderId) {
    if (!orderId) return false
    try {
        const saved = JSON.parse(localStorage.getItem(GEOFENCE_KEY) || '{}')
        return !!saved[orderId]
    } catch { return false }
}

function saveGeofenceState(orderId, active) {
    if (!orderId) return
    try {
        const saved = JSON.parse(localStorage.getItem(GEOFENCE_KEY) || '{}')
        if (active) {
            saved[orderId] = true
        } else {
            delete saved[orderId]
        }
        localStorage.setItem(GEOFENCE_KEY, JSON.stringify(saved))
    } catch {}
}

// Restore persisted state whenever the active order changes
watch(
    () => activeMove.value?.backendId || activeMove.value?.id,
    (orderId) => {
        geofenceAlert.value = loadGeofenceState(orderId)
        geofenceError.value = ''
    },
    { immediate: true }
)

async function toggleGeofence() {
    if (geofenceAlert.value) {
        geofenceAlert.value = false
        const orderId = activeMove.value?.backendId || activeMove.value?.id
        saveGeofenceState(orderId, false)
        return
    }

    const orderId = activeMove.value?.backendId || activeMove.value?.id
    if (!orderId) {
        geofenceAlert.value = true
        return
    }

    geofenceLoading.value = true
    geofenceError.value = ''
    try {
        const res = await fetch(apiUrl(`api/v1/orders/${orderId}/simulate-arrival`), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json',
            },
        })
        if (res.ok) {
            geofenceAlert.value = true
            saveGeofenceState(orderId, true)
        } else {
            const data = await res.json().catch(() => ({}))
            geofenceError.value = data.detail || 'Could not simulate arrival'
            geofenceAlert.value = true
            saveGeofenceState(orderId, true)
        }
    } catch {
        geofenceAlert.value = true
        saveGeofenceState(orderId, true)
    } finally {
        geofenceLoading.value = false
    }
}
function logColor(c) { return { green: '#22c55e', blue: '#3b82f6', amber: '#f59e0b', purple: '#a855f7', red: '#ef4444' }[c] || '#6b7280' }

function isWarehouseEvent(event) {
    const warehouseEvents = ['labourer', 'picking', 'packing', 'quality check', 'dispatch', 'queued', 'on hold']
    return warehouseEvents.some(w => event.toLowerCase().includes(w))
}

const hasWarehouseRoutePoint = computed(() => Boolean(
    activeMove.value?.warehouseName
    || activeMove.value?.warehouseAddress
    || warehouseCoords.value
))

const routeStageLabels = computed(() => {
    if (hasWarehouseRoutePoint.value) {
        return ['Warehouse', 'Pickup', 'Destination']
    }
    return ['Pickup', 'En Route', 'Destination']
})

const routeLegendItems = computed(() => {
    const items = []
    const delivered = activeMove.value?.status === 'delivered'
    const hasWarehouseLeg = hasWarehouseRoutePoint.value
        && (warehouseToPickupCoords.value.length > 0 || (warehouseCoords.value && pickupCoords.value))
    const hasDestinationLeg = pickupToDestCoords.value.length > 0 || (pickupCoords.value && destCoords.value)

    if (hasWarehouseLeg) {
        items.push({
            key: 'warehouse-pickup',
            label: 'Warehouse -> Pickup',
            color: '#f59e0b',
            dashed: !delivered,
            opacity: delivered ? 0.95 : 0.75,
        })
    }

    if (hasDestinationLeg) {
        items.push({
            key: 'pickup-destination',
            label: 'Pickup -> Destination',
            color: delivered ? '#10b981' : '#3b82f6',
            dashed: !delivered,
            opacity: delivered ? 0.95 : 0.8,
        })
    }

    return items
})

const routeBlueprintLabel = computed(() => {
    const order = activeMove.value
    if (!order) return ''

    const pickupLabel = order.pickup?.split(',')?.[0] || 'Pickup'
    const destLabel = order.destination?.split(',')?.[0] || 'Destination'
    const warehouseLabel = order.warehouseName || 'Warehouse'

    if (hasWarehouseRoutePoint.value) {
        return `${warehouseLabel} → ${pickupLabel} → ${destLabel}`
    }

    return `${pickupLabel} → ${destLabel}`
})



const serviceChecklist = computed(() => {
    const status = activeMove.value?.warehouseSubstatus || ''
    const orderStatus = activeMove.value?.status || ''
    const progress = activeMove.value?.progress ?? 0

    // Define status progression
    const statusOrder = ['AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED']
    const currentIdx = statusOrder.indexOf(status)

    return [
        { text: 'Order confirmed', done: progress >= 5 || orderStatus !== 'pending' },
        { text: 'Crew assigned', done: progress >= 10 || (activeMove.value?.laborCount > 0 && currentIdx >= 0) },
        { text: 'Picking completed', done: currentIdx >= statusOrder.indexOf('PICKED') || progress >= 30 },
        { text: 'Packing completed', done: currentIdx >= statusOrder.indexOf('PACKED') || progress >= 50 },
        { text: 'Quality verified', done: currentIdx >= statusOrder.indexOf('QC_PASSED') || progress >= 60 },
        { text: 'Shipment in transit', done: currentIdx >= statusOrder.indexOf('DISPATCHED') || progress >= 70 },
        { text: 'Delivery completed', done: orderStatus === 'delivered' || progress >= 100 },
    ]
})

// ─── Modals State ───
const showCallModal = ref(false)
const showChatModal = ref(false)

const chatMessages = ref([
    { text: 'Okay perfect. Please park near Gate B.', time: '10:48 AM' }
])
const pendingMessage = ref('')
const chatScrollContainer = ref(null)

const sendChatMessage = () => {
    if (!pendingMessage.value.trim()) return
    
    chatMessages.value.push({
        text: pendingMessage.value,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    pendingMessage.value = ''
    
    nextTick(() => {
        if (chatScrollContainer.value) {
            chatScrollContainer.value.scrollTop = chatScrollContainer.value.scrollHeight
        }
    })
}

let pollTimer = null

onMounted(async () => {
    await store.fetchTrackingOrders()
    warmDisplayOrderMapData(displayOrders.value)
    if (!selectedOrderId.value && allOrders.value.length > 0) {
        selectedOrderId.value = allOrders.value[0].id
    }
    if (activeMove.value && activeMove.value.status !== 'cancelled') {
        loadRouteForOrder(activeMove.value)
    }
    // Poll every 15 seconds for live warehouse updates
    pollTimer = setInterval(() => store.fetchTrackingOrders(), 15000)
})

onActivated(async () => {
    await store.fetchTrackingOrders()
    warmDisplayOrderMapData(displayOrders.value)
    if (!pollTimer) {
        pollTimer = setInterval(() => store.fetchTrackingOrders(), 15000)
    }
})

onUnmounted(() => {
    clearInterval(pollTimer)
    pollTimer = null
    clearTimeout(mapFocusFlashTimer)
})
</script>
